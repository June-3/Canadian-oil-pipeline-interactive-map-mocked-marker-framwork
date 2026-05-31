"""
Configuration for ETL pipeline.
Set DATABASE_URL to switch between SQLite (dev) and SQL Server (prod).
"""

import os

# Database — defaults to SQLite for local dev; swap for SQL Server in production.
# SQL Server example:
#   DATABASE_URL = "mssql+pyodbc://user:pass@host:1433/PipelineDB?driver=ODBC+Driver+17+for+SQL+Server"
DATABASE_URL = os.getenv(
    "PIPELINE_DB_URL",
    "sqlite:///pipeline_monitor.db",
)

# Path to the GeoJSON file (relative to project root)
GEOJSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Pipelines.geojson",
)

# Simulation settings
SIMULATION_INTERVAL_SECONDS = int(os.getenv("SIMULATION_INTERVAL", "60"))

# Asset generation: how many additional random assets to scatter near each pipeline
EXTRA_ASSETS_PER_PIPELINE = 3
