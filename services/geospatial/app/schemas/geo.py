"""
Pydantic v2 schemas for the geospatial service API.

GeoJSON structures follow RFC 7946.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# GeoJSON primitives
# ---------------------------------------------------------------------------

class GeoJSONGeometry(BaseModel):
    """GeoJSON geometry object (RFC 7946 §3.1)."""
    type: str  # Point | LineString | Polygon | MultiPolygon | etc.
    coordinates: Any

    model_config = {"extra": "allow"}


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature (RFC 7946 §3.2)."""
    type: Literal["Feature"] = "Feature"
    geometry: Optional[GeoJSONGeometry] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[Union[str, int]] = None

    model_config = {"extra": "allow"}


class GeoJSONPolygon(BaseModel):
    """Polygon geometry body used in spatial query requests."""
    type: Literal["Polygon"]
    coordinates: List[List[List[float]]]  # [ [ [lon, lat], ... ] ]


# ---------------------------------------------------------------------------
# Parcel geometry
# ---------------------------------------------------------------------------

class ParcelGeometryResponse(BaseModel):
    """
    Full geometry response for a single parcel.
    Returns a GeoJSON Feature with geometry + attribute properties.
    """
    type: Literal["Feature"] = "Feature"
    geometry: Optional[GeoJSONGeometry] = None
    properties: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Topology conflicts
# ---------------------------------------------------------------------------

class TopologyConflictResponse(BaseModel):
    id: uuid.UUID
    conflict_type: str
    parcel_id_1: Optional[uuid.UUID] = None
    parcel_id_2: Optional[uuid.UUID] = None
    overlap_area_sq_m: Optional[float] = None
    detected_at: datetime
    resolution_status: str

    model_config = {"from_attributes": True}


class ConflictListResponse(BaseModel):
    items: List[TopologyConflictResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# On-demand conflict detection
# ---------------------------------------------------------------------------

class DetectedOverlap(BaseModel):
    """One overlap entry from an on-demand topology check."""
    overlapping_bdpr: str
    overlapping_parcel_id: uuid.UUID
    overlap_area_sq_m: float


class ConflictDetectionResponse(BaseModel):
    parcel_id: uuid.UUID
    overlaps_found: int
    overlaps: List[DetectedOverlap] = Field(default_factory=list)
    checked_at: datetime


# ---------------------------------------------------------------------------
# Spatial queries
# ---------------------------------------------------------------------------

class WithinQueryRequest(BaseModel):
    """GeoJSON Polygon to search within."""
    type: Literal["Polygon"]
    coordinates: List[List[List[float]]]


class NearbyQueryRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude")
    radius_metres: float = Field(
        ..., gt=0, le=50_000, description="Search radius in metres (max 50 km)"
    )


class ParcelSpatialResult(BaseModel):
    """Compact parcel entry in spatial query results."""
    parcel_id: uuid.UUID
    bdpr: str
    ulpin: Optional[str] = None
    state_code: str
    district_code: str
    is_urban: bool
    area_sq_m: Optional[float] = None
    accuracy_class: Optional[str] = None
    distance_metres: Optional[float] = None  # present in nearby queries


class SpatialQueryResponse(BaseModel):
    items: List[ParcelSpatialResult]
    count: int
