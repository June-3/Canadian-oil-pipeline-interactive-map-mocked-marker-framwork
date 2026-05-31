"""
Dagster pipeline: scheduled ETL for pipeline asset monitoring.

Assets:
  - seed_assets: one-off asset seeding (idempotent)
  - generate_readings: per-minute reading generation

Schedule:
  - every 1 minute (configurable via SIMULATION_INTERVAL env var)

Run with:
  dagster dev -f dagster_pipeline.py
"""

import os
import sys

# Allow running from project root without PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dagster import (
    AssetExecutionContext,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
)

from pipeline_etl.simulate import seed_assets as do_seed, tick as do_tick
from pipeline_etl.config import SIMULATION_INTERVAL_SECONDS


@asset(description="Seed pipeline assets from GeoJSON nodes (idempotent)")
def seed_assets(context: AssetExecutionContext):
    context.log.info("Seeding assets...")
    do_seed()
    context.log.info("Seed complete.")


@asset(
    deps=[seed_assets],
    description="Generate one round of temperature/pressure readings for all assets",
)
def generate_readings(context: AssetExecutionContext):
    context.log.info("Generating readings...")
    do_tick()
    context.log.info("Readings generated.")


reading_job = define_asset_job(
    name="generate_readings_job",
    selection=[generate_readings],
)

reading_schedule = ScheduleDefinition(
    name="every_minute_reading",
    cron_schedule=f"*/{max(1, SIMULATION_INTERVAL_SECONDS // 60)} * * * *",
    job=reading_job,
    description=f"Generate readings every {SIMULATION_INTERVAL_SECONDS}s",
)

defs = Definitions(
    assets=[seed_assets, generate_readings],
    schedules=[reading_schedule],
)
