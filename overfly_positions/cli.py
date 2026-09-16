"""CLI entry point for overfly-positions.

Usage:
  python -m overfly_positions.cli

Polls the open-data position sources (OpenSky, ADSB.lol) and writes one
consolidated YAML snapshot per source per run. No proprietary or
ToS-sensitive source code here — see ADR-0035 (overfly-scraper/hq) for
why: this is a new, smaller entry point, not the old scraper's combined
flag renamed. That flag polled a ToS-sensitive source unconditionally,
which is exactly the surface this repo exists to never carry.
"""

import time

import loguru

from . import config
from .sources import opensky, adsbhub
from .enrichment import aircraft_types, noise_model
from .output import write_area_positions, write_position_snapshot


def _enrich(positions: list[dict]) -> list[dict]:
    """Enrich a list of position records with aircraft type + noise data."""
    for pos in positions:
        aircraft_types.enrich(pos)
        noise_model.enrich_with_noise(pos)
    return positions


def main():
    loguru.logger.info("overfly-positions scrape starting")
    start = time.time()
    total_positions = 0

    # OpenSky — REST API, independent feeder network
    try:
        opensky_positions = _enrich(opensky.get_area_traffic(config.PENNINGTON_BBOX))
        if opensky_positions:
            total_positions += write_area_positions(opensky_positions, config.OUTPUT_FOLDER)
    except Exception:
        loguru.logger.opt(exception=True).warning("Failed to poll OpenSky")

    # ADSB.lol — community-fed aggregator, radius-based, includes registration
    try:
        hub_positions = _enrich(adsbhub.get_area_traffic(
            config.OBSERVER_LAT, config.OBSERVER_LON
        ))
        if hub_positions:
            total_positions += write_position_snapshot(
                hub_positions, "adsbhub", config.OUTPUT_FOLDER)
    except Exception:
        loguru.logger.opt(exception=True).warning("Failed to poll ADSB.lol")

    elapsed = time.time() - start
    loguru.logger.info(
        f"overfly-positions complete: {total_positions} positions, {elapsed:.1f}s"
    )


if __name__ == "__main__":
    main()
