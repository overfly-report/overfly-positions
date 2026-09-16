"""ADSB.lol source adapter — free community ADS-B aggregator.

API: GET https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{nm}
No authentication required. Radius-based query in nautical miles.
Returns 1090MHz ADS-B + MLAT + TIS-B data from community feeders.

Independent from OpenSky — different feeder network, different
coverage gaps. Use as a second source for resilience.

Tested 2026-03-29: 19 aircraft within 50nm of Pennington NJ.
Fields include registration (r) and type code (t) directly.
"""

import datetime
import requests
import loguru

# 1 nautical mile = 1.15078 statute miles
# 20nm ≈ 23mi — captures KTTN pattern traffic + low-altitude overflights
DEFAULT_RADIUS_NM = 20


def get_area_traffic(
    lat: float,
    lon: float,
    radius_nm: int = DEFAULT_RADIUS_NM,
) -> list[dict]:
    """Fetch aircraft positions from ADSB.lol within radius_nm of (lat, lon).

    Returns a list of position dicts in the same shape as the other adapters' output.
    """
    url = f"https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{radius_nm}"
    loguru.logger.debug(f"ADSB.lol: querying {radius_nm}nm radius around ({lat:.3f},{lon:.3f})")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        loguru.logger.opt(exception=True).warning("ADSB.lol: request failed")
        return []

    data = response.json()
    aircraft = data.get("ac") or []
    query_time = data.get("now", 0)
    # ADSB.lol returns timestamps in milliseconds
    if query_time and query_time > 1e10:
        query_time = query_time / 1000

    loguru.logger.debug(f"ADSB.lol: got {len(aircraft)} aircraft")

    results = []
    for ac in aircraft:
        record = _parse_aircraft(ac, query_time)
        if record is not None:
            results.append(record)

    return results


def _parse_aircraft(ac: dict, query_timestamp: float) -> dict | None:
    """Convert ADSB.lol aircraft dict to our position record format."""
    lat = ac.get("lat")
    lon = ac.get("lon")
    if lat is None or lon is None:
        return None

    alt = ac.get("alt_baro")
    # "ground" is returned as a string when aircraft is on ground
    on_ground = (alt == "ground") or ac.get("on_ground", False)
    if on_ground:
        alt = 0

    ts = datetime.datetime.utcfromtimestamp(query_timestamp) if query_timestamp else None

    # Determine position source from type field
    src_map = {
        "adsb_icao": "ADS-B",
        "adsb_icao_nt": "ADS-B",
        "adsr_icao": "ADS-R",
        "tisb_icao": "TIS-B",
        "mlat": "MLAT",
        "other": "other",
    }
    src_type = ac.get("type", "")
    position_source = src_map.get(src_type, src_type)

    callsign = (ac.get("flight") or "").strip()
    registration = (ac.get("r") or "").strip()
    typecode = (ac.get("t") or "").strip()

    record = {
        "source": "adsbhub",
        "icao24": ac.get("hex", "").lower(),
        "callsign": callsign,
        "registration": registration,
        "typecode": typecode,
        "latitude": lat,
        "longitude": lon,
        "altitude_ft": int(alt) if isinstance(alt, (int, float)) else None,
        "ground_speed_kts": ac.get("gs"),
        "heading_deg": ac.get("track"),
        "vertical_rate_fpm": ac.get("baro_rate"),
        "squawk": ac.get("squawk"),
        "on_ground": on_ground,
        "position_source": position_source,
        "distance_nm": ac.get("dst"),
        "timestamp": ts,
        "query_timestamp": ts,
    }

    # Derived fields
    if record["altitude_ft"] is not None:
        record["baro_altitude_ft"] = record["altitude_ft"]

    return record
