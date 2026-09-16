"""Output writers for position data.

Trimmed from overfly-scraper's output.py (ADR-0035): only the two writers
the open-data position sources use. The two writers for the private
scraper's other sources stay there, permanently.
"""

import datetime
import os
from pathlib import Path

import yaml
import loguru


def write_area_positions(positions: list[dict], output_folder: str = "logs"):
    """Write OpenSky-style position snapshots to YAML files.

    Output path: {output_folder}/opensky/{date}/{icao24}-{timestamp}.yaml
    """
    written = 0
    for pos in positions:
        icao24 = pos.get("icao24", "unknown")
        ts = pos.get("timestamp")
        if ts is None:
            continue

        date_str = ts.strftime("%Y-%m-%d")
        time_str = ts.strftime("%H%M%S")

        path = os.path.abspath(os.path.join(
            ".",
            output_folder,
            "opensky",
            date_str,
            f"{icao24}-{time_str}.yaml",
        ))

        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(yaml.dump(pos, indent=2))
        written += 1

    loguru.logger.info(f"Wrote {written} area positions from OpenSky")
    return written


def write_position_snapshot(
    positions: list[dict],
    source: str,
    output_folder: str = "logs",
) -> int:
    """Write all positions from one snapshot into a single consolidated YAML file.

    One file per run, not one file per aircraft. Keeps git history manageable
    for high-frequency polling.

    Output path: {output_folder}/positions/{source}/{date}/{HHMM}.yaml
    """
    if not positions:
        return 0

    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")

    path = os.path.abspath(os.path.join(
        ".", output_folder, "positions", source, date_str, f"{time_str}.yaml"
    ))
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write(yaml.dump(positions, indent=2, default_flow_style=False))

    loguru.logger.info(f"Wrote {len(positions)} positions from {source} → {path}")
    return len(positions)
