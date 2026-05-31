"""
Data simulation and ETL.

Responsibilities:
  1. Seed assets extracted from GeoJSON into the database (run once / idempotent).
  2. On each tick: generate new temperature + pressure readings for every asset,
     apply cleaning thresholds, update asset status, and persist.

Usage (standalone, without Dagster):
  python simulate.py seed     # one-off: create assets
  python simulate.py tick     # one tick: generate readings for all assets
  python simulate.py run      # loop forever, one tick per minute
"""

import os
import random
import sys
import time
from datetime import datetime, timezone

# Allow running from project root without PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline_etl.models import Asset, Reading, SessionLocal, init_db
from pipeline_etl.extract_nodes import extract_assets

# ── operational ranges ─────────────────────────────────────────────
TEMP_NORMAL = (10.0, 40.0)       # Celsius — normal operating band
PRESSURE_NORMAL = (200.0, 800.0)  # PSI
TEMP_CRITICAL_HIGH = 55.0
TEMP_CRITICAL_LOW = -5.0
PRESSURE_CRITICAL_HIGH = 950.0
PRESSURE_CRITICAL_LOW = 100.0

# How much each reading can drift from the previous one (random walk step)
TEMP_DRIFT_MAX = 3.0    # ± °C per tick
PRESSURE_DRIFT_MAX = 40.0  # ± PSI per tick

# ── helpers ────────────────────────────────────────────────────────

def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _compute_status(temp, pressure):
    """Determine asset status from readings."""
    if (temp > TEMP_CRITICAL_HIGH or temp < TEMP_CRITICAL_LOW
            or pressure > PRESSURE_CRITICAL_HIGH or pressure < PRESSURE_CRITICAL_LOW):
        return "alarm"
    if (temp > 48.0 or temp < 2.0 or pressure > 880.0 or pressure < 150.0):
        return "warning"
    return "normal"


# ── seeding ────────────────────────────────────────────────────────

def seed_assets():
    """Idempotent: insert asset definitions from GeoJSON nodes into DB."""
    init_db()
    session = SessionLocal()
    try:
        existing = session.query(Asset).count()
        if existing > 0:
            print(f"Assets table already has {existing} rows — skipping seed.")
            return

        nodes = extract_assets()
        now = datetime.now(timezone.utc)
        for n in nodes:
            asset = Asset(
                name=n["name"],
                type=n["type"],
                longitude=n["longitude"],
                latitude=n["latitude"],
                status=n["status"],
                updated_at=now,
            )
            session.add(asset)
        session.commit()
        print(f"Seeded {len(nodes)} assets.")
    finally:
        session.close()


# ── tick: one simulation step ──────────────────────────────────────

def tick():
    """Generate one round of readings for all assets."""
    init_db()
    session = SessionLocal()
    try:
        assets = session.query(Asset).all()
        if not assets:
            print("No assets in database. Run 'seed' first.")
            return

        now = datetime.now(timezone.utc)

        # Get last reading per asset so we can random-walk from it
        last_readings = {}
        for a in assets:
            last = (
                session.query(Reading)
                .filter(Reading.asset_id == a.id)
                .order_by(Reading.timestamp.desc())
                .first()
            )
            last_readings[a.id] = last

        new_readings = []
        for asset in assets:
            prev = last_readings.get(asset.id)

            if prev:
                # Random walk
                temp = prev.temperature + random.uniform(-TEMP_DRIFT_MAX, TEMP_DRIFT_MAX)
                pressure = prev.pressure + random.uniform(-PRESSURE_DRIFT_MAX, PRESSURE_DRIFT_MAX)
            else:
                # First reading — start from normal range centre
                temp = random.uniform(*TEMP_NORMAL)
                pressure = random.uniform(*PRESSURE_NORMAL)

            # Clamp to physical plausibility
            temp = _clamp(temp, -20.0, 70.0)
            pressure = _clamp(pressure, 0.0, 1200.0)

            reading = Reading(
                asset_id=asset.id,
                timestamp=now,
                temperature=round(temp, 2),
                pressure=round(pressure, 2),
            )
            new_readings.append(reading)

            # Update asset status
            asset.status = _compute_status(temp, pressure)
            asset.updated_at = now

        session.add_all(new_readings)
        session.commit()
        print(f"[{now.isoformat()}] Generated {len(new_readings)} readings across {len(assets)} assets.")
    finally:
        session.close()


# ── continuous loop ────────────────────────────────────────────────

def run_loop(interval: int = 60):
    """Run tick() every `interval` seconds indefinitely."""
    print(f"Starting simulation loop every {interval}s. Press Ctrl+C to stop.")
    while True:
        try:
            tick()
        except Exception as exc:
            print(f"Tick failed: {exc}")
        time.sleep(interval)


# ── CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simulate.py [seed|tick|run]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "seed":
        seed_assets()
    elif cmd == "tick":
        tick()
    elif cmd == "run":
        run_loop()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
