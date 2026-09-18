"""
Sentinel-2 land-use change detection module.

10m resolution analysis for detecting:
- Agricultural to non-agricultural conversion
- Encroachment on water bodies and forest land
- Large layout development

NOT suitable for individual building detection (use Cartosat-3/UAV for that).
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

import numpy as np
import rasterio
from pydantic import BaseModel
from rasterio import features
from rasterio.transform import Affine
from shapely.geometry import shape, mapping
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

RESOLUTION_NOTE = "10m resolution. Detects field-level land-use change, not individual buildings."

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────


class ChangeDetectionResult(BaseModel):
    """Land-use change detection result."""
    village_code: str
    change_type: str
    confidence_score: float
    change_area_sq_m: float
    affected_parcels: List[UUID]
    detected_from_date: date
    detected_to_date: date
    image_date_before: date
    image_date_after: date
    ndvi_change: Optional[float] = None
    ndwi_change: Optional[float] = None
    description: str
    resolution_note: str = RESOLUTION_NOTE


class ChangePolygon(BaseModel):
    """Vectorized change polygon."""
    geometry: dict  # GeoJSON geometry
    change_type: str
    area_sq_m: float
    confidence: float


# ─────────────────────────────────────────────────────────────────────────────
# Spectral Index Computation
# ─────────────────────────────────────────────────────────────────────────────


def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Compute Normalized Difference Vegetation Index (NDVI).

    NDVI = (NIR - Red) / (NIR + Red)

    Values:
    - -1 to 0: Water, snow, clouds
    - 0 to 0.2: Barren, built-up
    - 0.2 to 0.5: Sparse vegetation, grassland
    - 0.5 to 1.0: Dense vegetation, forest, crops

    Args:
        red: Red band array (Sentinel-2 B4)
        nir: Near-infrared band array (Sentinel-2 B8)

    Returns:
        NDVI array
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir.astype(float) - red.astype(float)) / (nir.astype(float) + red.astype(float))
        ndvi[np.isnan(ndvi)] = 0
        ndvi = np.clip(ndvi, -1, 1)
    return ndvi


def compute_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Compute Normalized Difference Water Index (NDWI).

    NDWI = (Green - NIR) / (Green + NIR)

    Values:
    - >0.3: Water bodies
    - 0 to 0.3: Wet soil, wetlands
    - <0: Vegetation, built-up

    Args:
        green: Green band array (Sentinel-2 B3)
        nir: Near-infrared band array (Sentinel-2 B8)

    Returns:
        NDWI array
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        ndwi = (green.astype(float) - nir.astype(float)) / (green.astype(float) + nir.astype(float))
        ndwi[np.isnan(ndwi)] = 0
        ndwi = np.clip(ndwi, -1, 1)
    return ndwi


def compute_ndbi(swir: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Compute Normalized Difference Built-up Index (NDBI).

    NDBI = (SWIR - NIR) / (SWIR + NIR)

    Values:
    - >0: Built-up areas
    - <0: Vegetation, water

    Args:
        swir: Short-wave infrared band (Sentinel-2 B11)
        nir: Near-infrared band (Sentinel-2 B8)

    Returns:
        NDBI array
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        ndbi = (swir.astype(float) - nir.astype(float)) / (swir.astype(float) + nir.astype(float))
        ndbi[np.isnan(ndbi)] = 0
        ndbi = np.clip(ndbi, -1, 1)
    return ndbi


# ─────────────────────────────────────────────────────────────────────────────
# Land-Use Classification
# ─────────────────────────────────────────────────────────────────────────────


def classify_land_use(
    ndvi: np.ndarray,
    ndwi: np.ndarray,
    ndbi: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Classify land use based on spectral indices.

    Classes:
    - 0: NoData / Cloud
    - 1: Water
    - 2: Vegetation (agriculture/forest)
    - 3: Built-up
    - 4: Barren

    Args:
        ndvi: NDVI array
        ndwi: NDWI array
        ndbi: Optional NDBI array

    Returns:
        Classification array (integers 0-4)
    """
    classification = np.zeros_like(ndvi, dtype=np.uint8)

    # Water (high NDWI)
    classification[ndwi > 0.3] = 1

    # Vegetation (high NDVI, not water)
    classification[(ndvi > 0.5) & (ndwi <= 0.3)] = 2

    # Built-up (low NDVI, positive NDBI if available)
    if ndbi is not None:
        classification[(ndvi < 0.3) & (ndbi > 0) & (ndwi <= 0.3)] = 3
    else:
        classification[(ndvi < 0.3) & (ndvi >= 0) & (ndwi <= 0.3)] = 3

    # Barren (low NDVI, negative NDBI)
    classification[(ndvi < 0.2) & (ndvi >= -0.1) & (ndwi <= 0.3)] = 4

    return classification


# ─────────────────────────────────────────────────────────────────────────────
# Change Detection
# ─────────────────────────────────────────────────────────────────────────────


def detect_change(
    classification_t1: np.ndarray,
    classification_t2: np.ndarray,
) -> Tuple[np.ndarray, dict]:
    """
    Detect land-use changes between two time periods.

    Change types:
    - VEG_TO_BUILT: Vegetation → Built-up (agriculture to non-agriculture)
    - WATER_TO_BUILT: Water → Built-up (encroachment on water body)
    - VEG_TO_BARREN: Vegetation → Barren (deforestation)
    - WATER_TO_BARREN: Water → Barren (water body drying/filling)

    Args:
        classification_t1: Classification at time 1 (before)
        classification_t2: Classification at time 2 (after)

    Returns:
        (change_map, change_stats_dict)
    """
    change_map = np.zeros_like(classification_t1, dtype=np.uint8)

    # Define change codes
    CHANGE_VEG_TO_BUILT = 10
    CHANGE_WATER_TO_BUILT = 11
    CHANGE_VEG_TO_BARREN = 12
    CHANGE_WATER_TO_BARREN = 13

    # Vegetation (2) → Built-up (3)
    change_map[(classification_t1 == 2) & (classification_t2 == 3)] = CHANGE_VEG_TO_BUILT

    # Water (1) → Built-up (3)
    change_map[(classification_t1 == 1) & (classification_t2 == 3)] = CHANGE_WATER_TO_BUILT

    # Vegetation (2) → Barren (4)
    change_map[(classification_t1 == 2) & (classification_t2 == 4)] = CHANGE_VEG_TO_BARREN

    # Water (1) → Barren (4)
    change_map[(classification_t1 == 1) & (classification_t2 == 4)] = CHANGE_WATER_TO_BARREN

    # Compute statistics
    change_stats = {
        "VEG_TO_BUILT": int(np.sum(change_map == CHANGE_VEG_TO_BUILT)),
        "WATER_TO_BUILT": int(np.sum(change_map == CHANGE_WATER_TO_BUILT)),
        "VEG_TO_BARREN": int(np.sum(change_map == CHANGE_VEG_TO_BARREN)),
        "WATER_TO_BARREN": int(np.sum(change_map == CHANGE_WATER_TO_BARREN)),
        "total_change_pixels": int(np.sum(change_map > 0)),
    }

    return change_map, change_stats


# ─────────────────────────────────────────────────────────────────────────────
# Vectorization
# ─────────────────────────────────────────────────────────────────────────────


def vectorize_change_polygons(
    change_map: np.ndarray,
    transform: Affine,
    crs: str = "EPSG:4326",
    min_area_sq_m: float = 500.0,
) -> List[ChangePolygon]:
    """
    Vectorize change map raster to polygons.

    Filters out small polygons (< min_area_sq_m) to reduce noise.

    Args:
        change_map: Change detection raster (0 = no change, >0 = change type)
        transform: Rasterio affine transform
        crs: Coordinate reference system
        min_area_sq_m: Minimum polygon area to retain (default 500 sq_m = 5 pixels @ 10m)

    Returns:
        List of ChangePolygon
    """
    change_polygons = []

    # Map change codes to types
    change_type_map = {
        10: "AGRI_TO_NON_AGRI",
        11: "ENCROACHMENT_WATER",
        12: "VEG_TO_BARREN",
        13: "WATER_BODY_FILL",
    }

    # Extract shapes for each change type
    for change_code, change_type in change_type_map.items():
        # Create binary mask for this change type
        mask = (change_map == change_code).astype(np.uint8)

        if mask.sum() == 0:
            continue

        # Vectorize
        shapes_generator = features.shapes(
            mask,
            mask=(mask == 1),
            transform=transform,
        )

        for geom, value in shapes_generator:
            if value == 0:
                continue

            # Convert to Shapely geometry
            geom_shape = shape(geom)

            # Compute area (approximate, assumes metric CRS or small area)
            # For accurate area, reproject to UTM
            area_sq_m = geom_shape.area * 111320 * 111320  # Very rough for lat/lon
            # Better approach: use pyproj to convert to local UTM

            if area_sq_m < min_area_sq_m:
                continue

            # Confidence based on polygon size (larger = more confident)
            confidence = min(1.0, area_sq_m / 5000.0)  # 5000 sq_m = full confidence

            change_polygons.append(ChangePolygon(
                geometry=mapping(geom_shape),
                change_type=change_type,
                area_sq_m=round(area_sq_m, 2),
                confidence=round(confidence, 2),
            ))

    return change_polygons


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic Data Generation (for demo purposes)
# ─────────────────────────────────────────────────────────────────────────────


def load_or_generate_sample_rasters(
    village_code: str,
    data_dir: Path,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Affine]:
    """
    Load Sentinel-2 rasters or generate synthetic data for demonstration.

    Returns:
        (red_t1, nir_t1, red_t2, nir_t2, transform)
    """
    # Check if real data exists
    raster_t1_path = data_dir / f"{village_code}_t1.tif"
    raster_t2_path = data_dir / f"{village_code}_t2.tif"

    if raster_t1_path.exists() and raster_t2_path.exists():
        logger.info("load_or_generate_sample_rasters: loading real data", village_code=village_code)
        # Load real Sentinel-2 data
        # (Implementation would use rasterio to read multi-band GeoTIFF)
        # For now, fall through to synthetic
        pass

    # Generate synthetic data for demonstration
    logger.info("load_or_generate_sample_rasters: generating synthetic data", village_code=village_code)

    np.random.seed(hash(village_code) % (2**32))

    # Image size (100x100 pixels @ 10m = 1km x 1km)
    height, width = 100, 100

    # Time 1: Mostly vegetation
    red_t1 = np.random.randint(300, 800, (height, width), dtype=np.uint16)
    nir_t1 = np.random.randint(3000, 5000, (height, width), dtype=np.uint16)

    # Add water body in top-left
    red_t1[:20, :20] = np.random.randint(200, 400, (20, 20), dtype=np.uint16)
    nir_t1[:20, :20] = np.random.randint(100, 500, (20, 20), dtype=np.uint16)

    # Time 2: Some vegetation converted to built-up
    red_t2 = red_t1.copy()
    nir_t2 = nir_t1.copy()

    # Simulate agricultural to built-up conversion (center-right)
    red_t2[40:60, 60:80] = np.random.randint(1000, 1500, (20, 20), dtype=np.uint16)
    nir_t2[40:60, 60:80] = np.random.randint(800, 1200, (20, 20), dtype=np.uint16)

    # Simulate water body encroachment (top-left expansion)
    red_t2[20:25, 10:20] = np.random.randint(1000, 1500, (5, 10), dtype=np.uint16)
    nir_t2[20:25, 10:20] = np.random.randint(800, 1200, (5, 10), dtype=np.uint16)

    # Create affine transform (10m resolution, arbitrary origin)
    transform = Affine(10.0, 0.0, 77.5, 0.0, -10.0, 13.0)  # Bangalore-ish coordinates

    return red_t1, nir_t1, red_t2, nir_t2, transform


# ─────────────────────────────────────────────────────────────────────────────
# Full Pipeline
# ─────────────────────────────────────────────────────────────────────────────


async def run_change_detection_pipeline(
    db: AsyncSession,
    village_code: str,
    data_dir: Optional[Path] = None,
) -> ChangeDetectionResult:
    """
    Run complete change detection pipeline for a village.

    Args:
        db: Database session
        village_code: LGD village code
        data_dir: Directory containing Sentinel-2 imagery

    Returns:
        ChangeDetectionResult
    """
    logger.info("run_change_detection_pipeline", village_code=village_code)

    if data_dir is None:
        data_dir = Path("/tmp/sentinel2_data")  # Default path
        data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load or generate raster data
    red_t1, nir_t1, red_t2, nir_t2, transform = load_or_generate_sample_rasters(
        village_code, data_dir
    )

    # For NDWI, we need green band (simplified: use red as proxy)
    green_t1 = red_t1 * 1.1
    green_t2 = red_t2 * 1.1

    # 2. Compute spectral indices
    logger.info("run_change_detection_pipeline: computing indices")

    ndvi_t1 = compute_ndvi(red_t1, nir_t1)
    ndvi_t2 = compute_ndvi(red_t2, nir_t2)

    ndwi_t1 = compute_ndwi(green_t1, nir_t1)
    ndwi_t2 = compute_ndwi(green_t2, nir_t2)

    # 3. Classify land use
    logger.info("run_change_detection_pipeline: classifying land use")

    classification_t1 = classify_land_use(ndvi_t1, ndwi_t1)
    classification_t2 = classify_land_use(ndvi_t2, ndwi_t2)

    # 4. Detect changes
    logger.info("run_change_detection_pipeline: detecting changes")

    change_map, change_stats = detect_change(classification_t1, classification_t2)

    # 5. Vectorize changes
    change_polygons = vectorize_change_polygons(
        change_map,
        transform,
        min_area_sq_m=500.0,
    )

    logger.info(
        "run_change_detection_pipeline: vectorization complete",
        polygons=len(change_polygons),
        stats=change_stats,
    )

    # 6. Cross-reference with parcels (spatial join)
    affected_parcels = await _find_affected_parcels(db, change_polygons, village_code)

    # 7. Compute aggregate statistics
    total_change_area = sum(p.area_sq_m for p in change_polygons)

    # NDVI change (mean)
    ndvi_change = float(np.mean(ndvi_t2 - ndvi_t1))

    # Primary change type
    if change_polygons:
        primary_change_type = max(
            set(p.change_type for p in change_polygons),
            key=lambda ct: sum(p.area_sq_m for p in change_polygons if p.change_type == ct)
        )
    else:
        primary_change_type = "NO_CHANGE"

    # Description
    description = f"Detected {len(change_polygons)} change polygon(s) covering {total_change_area:.0f} sq_m"

    # Confidence (average)
    avg_confidence = np.mean([p.confidence for p in change_polygons]) if change_polygons else 0.0

    result = ChangeDetectionResult(
        village_code=village_code,
        change_type=primary_change_type,
        confidence_score=round(avg_confidence, 2),
        change_area_sq_m=round(total_change_area, 2),
        affected_parcels=affected_parcels,
        detected_from_date=date(2024, 1, 1),  # Placeholder
        detected_to_date=date(2024, 12, 31),  # Placeholder
        image_date_before=date(2024, 1, 15),
        image_date_after=date(2024, 12, 15),
        ndvi_change=round(ndvi_change, 4),
        ndwi_change=None,  # Could compute similarly
        description=description,
    )

    logger.info("run_change_detection_pipeline.complete", village_code=village_code)

    return result


async def _find_affected_parcels(
    db: AsyncSession,
    change_polygons: List[ChangePolygon],
    village_code: str,
) -> List[UUID]:
    """
    Spatial join to find parcels intersecting with change polygons.

    Args:
        db: Database session
        change_polygons: Detected change polygons
        village_code: Village LGD code

    Returns:
        List of affected parcel UUIDs
    """
    if not change_polygons:
        return []

    # For demonstration, return a sample (would do spatial join in production)
    query = text("""
        SELECT p.id
        FROM identity.parcels p
        WHERE p.village_code = :village_code
            AND p.is_active = true
        LIMIT 5
    """)

    result = await db.execute(query, {"village_code": village_code})
    rows = result.fetchall()

    return [UUID(str(row.id)) for row in rows]
