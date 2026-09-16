"""Configuration for overfly-positions.

Trimmed from overfly-scraper's config.py (ADR-0035): only the fields the
open-data position sources use. Dropped AIRPORTS/AIRPORT_COORDS/
TRACK_BACKFILL_RULES — those are private-scraper-specific and stay there.
"""

from .models import BoundingBox

# ─── Observer location ────────────────────────────────────────────────────────
# Primary observer: Pennington NJ 08534 — already-published posture (see
# overfly.report's own explainers). KTTN (Trenton-Mercer Airport) is ~2 miles
# SW; its traffic pattern (downwind leg) passes directly over this location.
OBSERVER_LAT = 40.3340
OBSERVER_LON = -74.7890
OBSERVER_ELEV_FT = 100  # approximate ground elevation

# ─── Bounding boxes ───────────────────────────────────────────────────────────
# 5-mile radius around observer — primary polling box
PENNINGTON_BBOX = BoundingBox(
    lat_min=40.25,
    lon_min=-74.90,
    lat_max=40.42,
    lon_max=-74.65,
)

# Wider box (~25-mile radius) for catching commercial overflights at altitude
WIDE_BBOX = BoundingBox(
    lat_min=40.10,
    lon_min=-75.20,
    lat_max=40.60,
    lon_max=-74.30,
)

OUTPUT_FOLDER = "logs"
