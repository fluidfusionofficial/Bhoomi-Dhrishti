"""ML inference modules."""

from app.modules.spatial_conflicts import (
    ConflictReport,
    detect_overlapping_parcels,
    detect_gaps_slivers,
    detect_area_geometry_divergence,
    detect_encroachment_on_restricted_zones,
    run_all_spatial_checks,
)

__all__ = [
    "ConflictReport",
    "detect_overlapping_parcels",
    "detect_gaps_slivers",
    "detect_area_geometry_divergence",
    "detect_encroachment_on_restricted_zones",
    "run_all_spatial_checks",
]
