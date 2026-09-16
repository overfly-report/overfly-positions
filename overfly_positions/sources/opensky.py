"""OpenSky Network source adapter.

Free REST API with bounding-box queries. Anonymous access: 400 credits/day,
10-second resolution, 18 fields per aircraft.

Docs: https://openskynetwork.github.io/opensky-api/rest.html
"""

import datetime

import requests
import loguru

from ..models import BoundingBox

OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

# OpenSky state vector field indices (from API docs)
_FIELD_NAMES = [
    "icao24",           # 0: ICAO24 transponder address (hex)
    "callsign",         # 1: callsign (8 chars max, may be None)
    "origin_country",   # 2: country of registration
    "time_position",    # 3: unix timestamp of last position update
    "last_contact",     # 4: unix timestamp of last contact
    "longitude",        # 5: WGS-84 longitude
    "latitude",         # 6: WGS-84 latitude
    "baro_altitude",    # 7: barometric altitude (meters)
    "on_ground",        # 8: true if on ground
    "velocity",         # 9: ground speed (m/s)
    "true_track",       # 10: track angle (degrees clockwise from north)
    "vertical_rate",    # 11: vertical rate (m/s)
    "sensors",          # 12: IDs of receivers (array)
    "geo_altitude",     # 13: geometric altitude (meters)
    "squawk",           # 14: transponder squawk code
    "spi",              # 15: special purpose indicator
    "position_source",  # 16: 0=ADS-B, 1=ASTERIX, 2=MLAT, 3=FLARM
    "category",         # 17: aircraft category (0-20)
]

_POSITION_SOURCE_NAMES = {
    0: "ADS-B",
    1: "ASTERIX",
    2: "MLAT",
    3: "FLARM",
}


def get_area_traffic(bbox: BoundingBox) -> list[dict]:
    """Fetch aircraft positions from OpenSky Network for a bounding box.

    Returns a list of dicts, one per aircraft currently in the area.
    """
    loguru.logger.debug(
        f"OpenSky: querying bbox ({bbox.lat_min},{bbox.lon_min})-({bbox.lat_max},{bbox.lon_max})"
    )

    try:
        response = requests.get(
            OPENSKY_API_URL,
            params={
                "lamin": bbox.lat_min,
                "lomin": bbox.lon_min,
                "lamax": bbox.lat_max,
                "lomax": bbox.lon_max,
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException:
        loguru.logger.opt(exception=True).warning("OpenSky: request failed")
        return []

    data = response.json()
    timestamp = data.get("time", 0)
    states = data.get("states") or []

    loguru.logger.debug(f"OpenSky: got {len(states)} aircraft at timestamp {timestamp}")

    results = []
    for state in states:
        record = _parse_state_vector(state, timestamp)
        if record is not None:
            results.append(record)

    return results


def _parse_state_vector(state: list, query_timestamp: int) -> dict | None:
    """Parse an OpenSky state vector array into a dict."""
    if len(state) < 17:
        return None

    icao24 = state[0]
    callsign = (state[1] or "").strip()
    latitude = state[6]
    longitude = state[5]

    # Skip aircraft without position data
    if latitude is None or longitude is None:
        return None

    pos_time = state[3]
    pos_source = state[16] if len(state) > 16 else 0

    record = {
        "source": "opensky",
        "icao24": icao24,
        "callsign": callsign,
        "origin_country": state[2],
        "latitude": latitude,
        "longitude": longitude,
        "baro_altitude_m": state[7],
        "geo_altitude_m": state[13] if len(state) > 13 else None,
        "on_ground": state[8],
        "velocity_ms": state[9],
        "true_track_deg": state[10],
        "vertical_rate_ms": state[11],
        "squawk": state[14] if len(state) > 14 else None,
        "position_source": _POSITION_SOURCE_NAMES.get(pos_source, str(pos_source)),
        "timestamp": datetime.datetime.utcfromtimestamp(pos_time) if pos_time else None,
        "query_timestamp": datetime.datetime.utcfromtimestamp(query_timestamp) if query_timestamp else None,
    }

    # Add derived fields for convenience
    if record["baro_altitude_m"] is not None:
        record["baro_altitude_ft"] = round(record["baro_altitude_m"] * 3.28084)
    if record["velocity_ms"] is not None:
        record["velocity_kts"] = round(record["velocity_ms"] * 1.94384, 1)

    return record
