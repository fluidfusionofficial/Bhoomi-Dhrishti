# ETL Mapping Engine - Bhoomi Dhrishti Interoperability Service

## Overview

The ETL Mapping Engine is a YAML-driven transformation pipeline that ingests heterogeneous state land records data and outputs canonical LADM-aligned records. It provides:

- **YAML-driven field mapping** - Declarative configuration for source-to-target transformations
- **Transformation library** - District-aware area conversions, date normalization, transliteration, etc.
- **Data quality validation** - Pydantic schemas + Great Expectations for comprehensive DQ checks
- **Bulk loading** - Async SQLAlchemy with conflict resolution (upsert/ignore strategies)
- **REST API** - Upload files, track jobs, manage mappings

## Architecture

```
┌─────────────────┐
│  Source Data    │
│  (CSV/JSON)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Mapping YAML   │─────▶│   Mapper     │
│  Configuration  │      │   Engine     │
└─────────────────┘      └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ Transforms   │
                         │  Library     │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  Validator   │
                         │  (Pydantic+  │
                         │   GE)        │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  DQ Report   │
                         │  (JSON)      │
                         └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  Data Loader │
                         │  (SQLAlchemy)│
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  PostgreSQL  │
                         │  Database    │
                         └──────────────┘
```

## Directory Structure

```
services/interoperability/
├── app/
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── mapper.py         # YAML-driven field mapping
│   │   ├── transforms.py     # Transformation functions
│   │   ├── validator.py      # Pydantic + Great Expectations
│   │   └── loader.py         # SQLAlchemy bulk loader
│   ├── routers/
│   │   └── ingest.py         # REST API endpoints
│   └── main.py
├── data/
│   ├── mappings/
│   │   ├── tn_rural/
│   │   │   └── mapping.yaml  # TN rural revenue mapping
│   │   └── tn_sro/
│   │       └── mapping.yaml  # TN SRO registration mapping
│   └── processed/
│       └── *_dq_report.json  # Data quality reports
└── requirements.txt
```

## Mapping YAML Schema

### Example: Revenue RoR Mapping

```yaml
source_type: revenue_ror
source_system: TN_BHOOMI
source_department: TN Revenue Department

field_mapping:
  survey_number:
    source_field: "Survey_No"
    transform: normalize_survey_number
    type: str
  
  area_sq_m:
    source_field: "Extent"
    transform: convert_area
    type: float
  
  owner_name_phonetic:
    source_field: "Pattadar_Name_Tamil"
    transform: transliterate_to_latin
    script: tamil

conversions:
  area_units:
    cent: 40.47  # sq_m per cent
    veli: 6670

data_quality:
  required_fields: [survey_number, district_code]
  unique_fields: [survey_number]
```

### Field Configuration

Each field mapping supports:

- `source_field`: Source column name (supports nested: "address.district")
- `transform`: Transformation function name (optional)
- `type`: Target type (str, float, int, bool)
- `script`: For transliteration (tamil, devanagari, etc.)
- `unit_native`: For area conversions

### Supported Transforms

1. **normalize_survey_number** - Strip leading zeros, normalize separators (123/4A)
2. **normalize_date** - Handle DD/MM/YYYY, Fasli year, Saka era → ISO 8601
3. **convert_area** - District-aware area conversion (bigha varies by district)
4. **transliterate_to_latin** - IAST/Hunterian for Tamil/Devanagari
5. **generate_phonetic_key** - Soundex-like for Indian names
6. **validate_geometry** - Shapely validation for WKT/GeoJSON
7. **parse_address** - Extract district/village/pincode components

## REST API Usage

### 1. Upload and Ingest Data

```bash
curl -X POST "http://localhost:8005/ingest/revenue_ror?state_code=tn&context=rural" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@tn_revenue_sample.csv"
```

**Response:**
```json
{
  "job_id": "a1b2c3d4-...",
  "status": "completed",
  "total_records": 200,
  "rows_loaded": 185,
  "quality_score": 92.5,
  "dq_report": {
    "source_type": "revenue_ror",
    "total_rows": 200,
    "valid_rows": 185,
    "quality_score": 92.5,
    "field_statistics": {...},
    "issues": [...]
  }
}
```

### 2. Check Job Status

```bash
curl "http://localhost:8005/ingest/status/a1b2c3d4-..."
```

### 3. List Available Mappings

```bash
curl "http://localhost:8005/ingest/sources"
```

**Response:**
```json
{
  "sources": [
    {
      "identifier": "tn_rural",
      "source_type": "revenue_ror",
      "path": ".../tn_rural/mapping.yaml",
      "source_system": "TN_BHOOMI"
    },
    {
      "identifier": "tn_sro",
      "source_type": "sro_registration",
      "path": ".../tn_sro/mapping.yaml",
      "source_system": "TNREGINET"
    }
  ]
}
```

### 4. Get Mapping Configuration

```bash
curl "http://localhost:8005/ingest/mappings/tn_rural"
```

### 5. Update Mapping (Admin Only)

```bash
curl -X POST "http://localhost:8005/ingest/mappings/tn_rural" \
  -H "Content-Type: application/json" \
  -d '{"yaml_content": "..."}'
```

## Data Quality Report

After ingestion, a JSON report is generated at `data/processed/{source_type}_{job_id}_dq_report.json`:

```json
{
  "source_type": "revenue_ror",
  "total_rows": 200,
  "valid_rows": 185,
  "quality_score": 92.5,
  "field_statistics": {
    "survey_number": {
      "null_count": 6,
      "null_rate": 0.03
    },
    "area_sq_m": {
      "null_count": 0,
      "min": 0.5,
      "max": 45.2,
      "mean": 5.3,
      "median": 4.8
    }
  },
  "issues": [
    {
      "row": 15,
      "field": "survey_number",
      "issue": "null_value"
    },
    {
      "row": 23,
      "field": "area_sq_m",
      "issue": "negative_value",
      "value": -2.3
    }
  ]
}
```

## Programmatic Usage

### Python Example

```python
from app.engine import SourceMapper, DataQualityValidator, DataLoader
from app.db import AsyncSessionLocal

# Load mapping
mapper = SourceMapper("data/mappings/tn_rural/mapping.yaml")

# Apply to records
source_records = [
    {
        "Survey_No": "0123/4A",
        "Extent": "5.5",
        "Unit": "cent",
        "Pattadar_Name": "John Doe",
        "District_Code": "33001"
    }
]

canonical_records = [
    mapper.apply_mapping(rec, context={"district_lgd_code": rec["District_Code"]})
    for rec in source_records
]

# Validate
validator = DataQualityValidator("revenue_ror")
dq_report = validator.validate_records(canonical_records)

print(f"Quality Score: {dq_report.quality_score}")
print(f"Valid Rows: {dq_report.valid_rows}/{dq_report.total_rows}")

# Load to database
async with AsyncSessionLocal() as session:
    loader = DataLoader(session)
    rows_loaded = await loader.load_ror_records(
        canonical_records,
        conflict_strategy="update"
    )
    print(f"Loaded {rows_loaded} rows")
```

## Transformation Examples

### Area Conversion (District-Aware)

```python
from app.engine.transforms import convert_area

# Standard bigha
area_sq_m = convert_area(2.5, from_unit="bigha", to_unit="sq_m")
# Returns: 6323.25

# District-specific bigha (TN district 33001)
area_sq_m = convert_area(
    2.5,
    from_unit="bigha",
    to_unit="sq_m",
    district_lgd_code="33001"
)
# Returns: 4046.75 (TN has different bigha)
```

### Date Normalization

```python
from app.engine.transforms import normalize_date

# DD/MM/YYYY
normalize_date("15/08/2020")  # → "2020-08-15"

# Fasli year
normalize_date("1430 Fasli")  # → "2022-01-01" (approx)

# Saka era
normalize_date("1945 Saka")   # → "2023-01-01" (approx)
```

### Transliteration

```python
from app.engine.transforms import transliterate_to_latin

# Tamil to Latin
transliterate_to_latin("முருகன்", script="tamil")
# → "Murugan"

# Devanagari to Latin
transliterate_to_latin("राम", script="devanagari")
# → "Ram"
```

## Conflict Resolution Strategies

When loading data, you can specify conflict resolution:

1. **update** (default) - ON CONFLICT DO UPDATE (upsert)
2. **ignore** - ON CONFLICT DO NOTHING (skip duplicates)

```bash
# Upsert (update existing records)
curl -X POST "http://localhost:8005/ingest/revenue_ror?conflict_strategy=update" \
  -F "file=@data.csv"

# Ignore conflicts
curl -X POST "http://localhost:8005/ingest/revenue_ror?conflict_strategy=ignore" \
  -F "file=@data.csv"
```

## Adding New Mappings

1. Create directory: `data/mappings/{state_code}_{context}/`
2. Create `mapping.yaml` with required structure
3. Define `source_type`, `field_mapping`, and `data_quality` rules
4. Test with sample data
5. Deploy and use via API

## Error Handling

- **Mapping errors** - Logged with row index, continue processing
- **Validation failures** - Tracked in DQ report, records marked invalid
- **Load errors** - Transaction rollback, job marked as failed

## Performance Considerations

- Batch size: 1000 records per database batch
- CSV parsing: pandas read_csv with chunking for large files
- Async I/O: All database operations use asyncpg
- Validation: Great Expectations runs on pandas DataFrames (vectorized)

## Security

- PII hashing: `hash_pii()` uses SHA-256 for Aadhaar, etc.
- Admin-only: Mapping updates require `admin` or `officer` role
- Audit trail: All ingestions logged with source file, timestamp, user

## Next Steps

1. Add authentication/authorization checks
2. Implement background job processing (Celery/Redis)
3. Add support for Excel files (.xlsx)
4. Implement Great Expectations validation suites
5. Add cross-source matching engine
6. Build UI for mapping configuration
7. Add data lineage tracking

## Support

For issues or questions:
- Check logs: `structlog` output in JSON format
- Review DQ reports: `data/processed/*_dq_report.json`
- Contact: bhoomi-dhrishti-support@example.com
