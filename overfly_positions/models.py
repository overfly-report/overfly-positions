"""Lightweight data models for flight records and positions."""

from typing import NamedTuple


class BoundingBox(NamedTuple):
    """Geographic bounding box (lat/lon)."""
    lat_min: float
    lon_min: float
    lat_max: float
    lon_max: float
