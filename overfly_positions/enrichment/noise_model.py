"""Noise model for overfly — estimates sound pressure level at an observer.

Physics: inverse-square law (spherical spreading in free field).
    SPL_observer = ref_db_at_1000ft - 20 * log10(slant_distance_ft / 1000)

Reference levels are the estimated SPL at exactly 1000ft slant distance
for a representative aircraft in each category, derived from:
  - FAA Aircraft Noise Type Certificate data (Part 36)
  - Published community noise studies (AEDT, Volpe Center)
  - Empirical validation against real observations in this project

Validated 2026-03-30 against two live observations:
  N280S (Gulfstream G280, business-jet-medium) at 0.77mi/1650ft → 49.8 dB(A)
    Perceived as: "audible but not bothersome, only for a moment" ✓
  N36HF (Sikorsky S-76C-2, helicopter-medium) at 2.97mi/1450ft → ~58 dB(A)
    Perceived as: "really loud" (consistent — helicopter BVI adds perceived loudness
    beyond what dB(A) captures; low-frequency rotor chop penetrates buildings) ✓

Architecture (Simon): nearly decomposable.
- Strong coupling WITHIN: physics formula + reference table are a coherent unit
- Weak coupling BETWEEN: callers pass a position dict, get back the same dict
  with 'estimated_db' and 'lead_exposure_score' added. No other overfly module
  needs to understand the physics.
"""

import math

from .. import config
from .aircraft_types import lookup as _lookup_type

# ── Reference SPL at 1000ft slant distance, by aircraft category ─────────────
# These are dB(A) — A-weighted to approximate human hearing perception.
# Source: FAA Part 36 type certificates, AEDT reference data, empirical tuning.
_REF_DB: dict[str, float] = {
    "small-piston-single":   72.0,  # C172 at 1000ft: very audible, clearly annoying
    "small-piston-twin":     77.0,  # PA44 Seminole: louder, two engines
    "large-piston-single":   70.0,
    "large-piston-twin":     75.0,
    "turboprop-single":      68.0,
    "turboprop-twin":        70.0,
    "business-jet-light":    63.0,
    "business-jet-medium":   62.0,  # G280: validated 2026-03-30
    "business-jet-large":    61.0,
    "business-jet-heavy":    60.0,
    "commercial-narrowbody": 80.0,  # A320/B737 on approach — very audible
    "commercial-regional":   75.0,
    "commercial-widebody":   78.0,
    "helicopter-light":      82.0,
    "helicopter-medium":     80.0,  # S-76: validated 2026-03-30 (perceived louder than dB(A))
    "helicopter-heavy":      78.0,
    "military-transport":    90.0,
    "military-fighter":      95.0,
    "military-patrol":       75.0,
    "ultralight":            68.0,
    "unknown":               70.0,
}
_FALLBACK_DB = 70.0


def reference_db(category: str) -> float:
    """Return reference SPL (dB(A)) at 1000ft slant for a given aircraft category."""
    return _REF_DB.get(category, _FALLBACK_DB)


def slant_distance_ft(
    aircraft_lat: float,
    aircraft_lon: float,
    aircraft_alt_ft: float,
    observer_lat: float,
    observer_lon: float,
    observer_elev_ft: float,
) -> float:
    """Compute 3D slant distance in feet between aircraft and observer.

    Uses haversine for horizontal distance, then Pythagorean for slant.
    Returns minimum 100ft to avoid log10(0) downstream.
    """
    R_FT = 20_902_464.0  # Earth mean radius in feet
    phi1 = math.radians(observer_lat)
    phi2 = math.radians(aircraft_lat)
    dphi = math.radians(aircraft_lat - observer_lat)
    dlam = math.radians(aircraft_lon - observer_lon)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    horiz_ft = R_FT * 2 * math.asin(math.sqrt(a))
    vert_ft = float(aircraft_alt_ft) - float(observer_elev_ft)
    return max(100.0, math.sqrt(horiz_ft ** 2 + vert_ft ** 2))


def estimated_db_at_observer(
    position: dict,
    observer_lat: float,
    observer_lon: float,
    observer_elev_ft: float,
) -> float | None:
    """Estimate SPL (dB(A)) at observer from a position record.

    Returns None if position lacks sufficient data or aircraft is on ground.
    """
    if position.get("on_ground"):
        return None

    lat = position.get("latitude")
    lon = position.get("longitude")
    if lat is None or lon is None:
        return None

    # Altitude field varies by source
    alt_ft = (
        position.get("altitude_ft")
        or position.get("baro_altitude_ft")
        or position.get("feet")
    )
    if not alt_ft:
        return None

    # Category: use already-enriched aircraft_type if present, else lookup
    aircraft_type = position.get("aircraft_type") or {}
    category = aircraft_type.get("category")
    if not category:
        typecode = position.get("typecode") or position.get("type_code") or ""
        category = _lookup_type(typecode)["category"]

    slant_ft = slant_distance_ft(lat, lon, alt_ft, observer_lat, observer_lon, observer_elev_ft)
    ref = reference_db(category)
    return round(ref - 20.0 * math.log10(slant_ft / 1000.0), 1)


def lead_exposure_score(
    position: dict,
    observer_lat: float,
    observer_lon: float,
    observer_elev_ft: float,
) -> float:
    """Estimate leaded avgas (100LL) exposure risk on a 0–10 scale.

    Only meaningful for piston-engine aircraft — turbines and jets return 0.
    Score reflects proximity and altitude: lower and closer = higher risk.

    Formula:
        raw = 10 * (1500 / max(slant_ft, 100))^2 * (3000 / (alt_agl_ft + 3000))
        score = min(raw, 10.0)

    The second factor provides smooth altitude decay:
        alt_agl=0    → 1.00 (maximum exhaust concern at ground level)
        alt_agl=1500 → 0.67 (pattern altitude — significant)
        alt_agl=3000 → 0.50
        alt_agl=∞    → 0.00
    """
    # Only piston engines burn leaded avgas (100LL)
    aircraft_type = position.get("aircraft_type") or {}
    engine_type = aircraft_type.get("engine_type")
    if not engine_type:
        typecode = position.get("typecode") or position.get("type_code") or ""
        engine_type = _lookup_type(typecode).get("engine_type", "unknown")

    if engine_type != "piston":
        return 0.0

    lat = position.get("latitude")
    lon = position.get("longitude")
    alt_ft = (
        position.get("altitude_ft")
        or position.get("baro_altitude_ft")
        or position.get("feet")
    )
    if lat is None or lon is None or not alt_ft or position.get("on_ground"):
        return 0.0

    slant_ft = slant_distance_ft(lat, lon, alt_ft, observer_lat, observer_lon, observer_elev_ft)
    alt_agl_ft = max(0.0, float(alt_ft) - observer_elev_ft)

    raw = 10.0 * (1500.0 / max(slant_ft, 100.0)) ** 2 * (3000.0 / (alt_agl_ft + 3000.0))
    return round(min(raw, 10.0), 2)


def enrich_with_noise(
    position: dict,
    observer_lat: float = config.OBSERVER_LAT,
    observer_lon: float = config.OBSERVER_LON,
    observer_elev_ft: float = config.OBSERVER_ELEV_FT,
) -> dict:
    """Add estimated_db and lead_exposure_score to a position record in-place.

    Works with any position dict that has lat/lon/altitude (OpenSky, ADSB.lol, or similar).
    Default observer is Pennington NJ 08534 (config).
    Override observer for multi-location complaint correlation (Layer 2c).

    Returns the same dict with two new keys:
      - estimated_db: float | None — SPL in dB(A) at observer
      - lead_exposure_score: float — 0-10 piston exhaust proximity score
    """
    position["estimated_db"] = estimated_db_at_observer(
        position, observer_lat, observer_lon, observer_elev_ft
    )
    position["lead_exposure_score"] = lead_exposure_score(
        position, observer_lat, observer_lon, observer_elev_ft
    )
    return position
