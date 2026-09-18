"""REST API for ETL data ingestion."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.engine.loader import DataLoader
from app.engine.mapper import SourceMapper
from app.engine.validator import DataQualityValidator

logger = structlog.get_logger()

router = APIRouter(prefix="/ingest")

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
MAPPINGS_DIR = BASE_DIR / "data" / "mappings"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Ensure directories exist
MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job tracking (in production, use Redis or database)
job_store: Dict[str, Dict[str, Any]] = {}


@router.post("/{source_type}", status_code=status.HTTP_202_ACCEPTED)
async def ingest_data(
    source_type: str,
    file: UploadFile = File(...),
    state_code: str = "tn",
    context: str = "rural",
    conflict_strategy: str = "update",
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest data file and run ETL pipeline.

    Args:
        source_type: Type of data (revenue_ror, sro_registration)
        file: Uploaded CSV/JSON/JSONL file
        state_code: State code (default: tn)
        context: Context identifier (default: rural)
        conflict_strategy: "update" (upsert) or "ignore" (skip conflicts)
        db: Database session

    Returns:
        Job ID and initial status
    """
    job_id = str(uuid.uuid4())

    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".csv", ".json", ".jsonl"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported: .csv, .json, .jsonl"
            )

        # Read file content
        content = await file.read()

        # Parse file based on type
        if file_ext == ".csv":
            records = _parse_csv(content)
        elif file_ext == ".json":
            records = _parse_json(content)
        elif file_ext == ".jsonl":
            records = _parse_jsonl(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if not records:
            raise HTTPException(status_code=400, detail="No records found in file")

        logger.info(
            "ingestion_started",
            job_id=job_id,
            source_type=source_type,
            filename=file.filename,
            record_count=len(records)
        )

        # Initialize job status
        job_store[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "source_type": source_type,
            "filename": file.filename,
            "total_records": len(records),
            "created_at": datetime.utcnow().isoformat(),
        }

        # Load mapping configuration
        mapping_path = MAPPINGS_DIR / f"{state_code}_{context}" / "mapping.yaml"
        if not mapping_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found: {state_code}_{context}"
            )

        mapper = SourceMapper(mapping_path)

        # Apply mappings
        logger.info("applying_mappings", job_id=job_id, mapping=str(mapping_path))
        canonical_records = []
        mapping_errors = 0

        for idx, record in enumerate(records):
            try:
                canonical = mapper.apply_mapping(
                    record,
                    context={"district_lgd_code": record.get("district_code")}
                )
                canonical_records.append(canonical)
            except Exception as e:
                logger.warning("record_mapping_error", row=idx, error=str(e))
                mapping_errors += 1

        # Validate data quality
        logger.info("validating_data", job_id=job_id, record_count=len(canonical_records))
        validator = DataQualityValidator(source_type)
        dq_report = validator.validate_records(canonical_records)

        # Save DQ report
        report_path = PROCESSED_DIR / f"{source_type}_{job_id}_dq_report.json"
        with open(report_path, "w") as f:
            json.dump(dq_report.model_dump(), f, indent=2)

        # Load to database
        logger.info("loading_to_database", job_id=job_id, valid_rows=dq_report.valid_rows)
        loader = DataLoader(db)

        rows_loaded = 0
        if source_type == "revenue_ror":
            rows_loaded = await loader.load_ror_records(
                canonical_records,
                conflict_strategy=conflict_strategy
            )
        elif source_type == "sro_registration":
            rows_loaded = await loader.load_registrations(
                canonical_records,
                conflict_strategy=conflict_strategy
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown source type: {source_type}"
            )

        # Update job status
        job_store[job_id].update({
            "status": "completed",
            "rows_loaded": rows_loaded,
            "quality_score": dq_report.quality_score,
            "mapping_errors": mapping_errors,
            "validation_issues": len(dq_report.issues),
            "dq_report_path": str(report_path),
            "completed_at": datetime.utcnow().isoformat(),
        })

        logger.info(
            "ingestion_completed",
            job_id=job_id,
            rows_loaded=rows_loaded,
            quality_score=dq_report.quality_score
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "total_records": len(records),
            "rows_loaded": rows_loaded,
            "quality_score": dq_report.quality_score,
            "dq_report": dq_report.model_dump(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("ingestion_error", job_id=job_id, error=str(e))
        if job_id in job_store:
            job_store[job_id].update({
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat(),
            })
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get ingestion job status.

    Args:
        job_id: Job identifier

    Returns:
        Job status and details
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    return job_store[job_id]


@router.get("/sources")
async def list_sources():
    """
    List all configured source mappings.

    Returns:
        List of available source configurations
    """
    sources = []

    try:
        for state_context_dir in MAPPINGS_DIR.iterdir():
            if state_context_dir.is_dir():
                mapping_file = state_context_dir / "mapping.yaml"
                if mapping_file.exists():
                    try:
                        mapper = SourceMapper(mapping_file)
                        sources.append({
                            "identifier": state_context_dir.name,
                            "source_type": mapper.get_source_type(),
                            "path": str(mapping_file),
                            "source_system": mapper.config.get("source_system"),
                            "source_department": mapper.config.get("source_department"),
                        })
                    except Exception as e:
                        logger.warning(
                            "mapping_parse_error",
                            path=str(mapping_file),
                            error=str(e)
                        )

        return {"sources": sources}

    except Exception as e:
        logger.error("list_sources_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list sources: {str(e)}")


@router.get("/mappings/{state_code}_{context}")
async def get_mapping(state_code: str, context: str):
    """
    Get mapping configuration.

    Args:
        state_code: State code (e.g., "tn")
        context: Context identifier (e.g., "rural")

    Returns:
        Mapping YAML content
    """
    mapping_path = MAPPINGS_DIR / f"{state_code}_{context}" / "mapping.yaml"

    if not mapping_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Mapping not found: {state_code}_{context}"
        )

    try:
        with open(mapping_path, "r") as f:
            content = f.read()

        return JSONResponse(
            content={"content": content, "path": str(mapping_path)},
            status_code=200
        )

    except Exception as e:
        logger.error("get_mapping_error", path=str(mapping_path), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to read mapping: {str(e)}")


@router.post("/mappings/{state_code}_{context}")
async def update_mapping(state_code: str, context: str, content: Dict[str, str]):
    """
    Update mapping configuration (admin-only).

    Args:
        state_code: State code
        context: Context identifier
        content: Dict with "yaml_content" key

    Returns:
        Success status
    """
    # TODO: Add authentication check for admin role

    mapping_dir = MAPPINGS_DIR / f"{state_code}_{context}"
    mapping_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = mapping_dir / "mapping.yaml"

    try:
        yaml_content = content.get("yaml_content")
        if not yaml_content:
            raise HTTPException(status_code=400, detail="Missing yaml_content")

        # Validate YAML by attempting to load it
        try:
            mapper = SourceMapper._load_yaml.__func__(SourceMapper, mapping_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

        # Write to file
        with open(mapping_path, "w") as f:
            f.write(yaml_content)

        logger.info("mapping_updated", path=str(mapping_path))

        return {"status": "success", "path": str(mapping_path)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_mapping_error", path=str(mapping_path), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update mapping: {str(e)}")


def _parse_csv(content: bytes) -> List[Dict[str, Any]]:
    """Parse CSV file content to list of dicts."""
    import io

    try:
        df = pd.read_csv(io.BytesIO(content))
        return df.to_dict("records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


def _parse_json(content: bytes) -> List[Dict[str, Any]]:
    """Parse JSON file content to list of dicts."""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Assume single record
            return [data]
        else:
            raise ValueError("JSON must be array or object")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse JSON: {str(e)}")


def _parse_jsonl(content: bytes) -> List[Dict[str, Any]]:
    """Parse JSONL file content to list of dicts."""
    try:
        lines = content.decode("utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines if line.strip()]
        return records
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse JSONL: {str(e)}")
