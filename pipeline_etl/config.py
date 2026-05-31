"""
Configuration for ETL pipeline.
Set DATABASE_URL to switch between SQLite (dev) and SQL Server (prod).
"""

import os

# Database — SQL Server (LocalDB) for development.
# SQLite fallback: set PIPELINE_DB_URL=sqlite:///pipeline_monitor.db
_LOCALDB_CONN = (
    "DRIVER=ODBC Driver 17 for SQL Server;"
    "SERVER=(localdb)\\MSSQLLocalDB;"
    "DATABASE=PipelineDB;"
    "Trusted_Connection=yes;"
)
# URL-encode for SQLAlchemy's pyodbc dialect
import urllib.parse
_LOCALDB_URL = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(_LOCALDB_CONN)

DATABASE_URL = os.getenv("PIPELINE_DB_URL", _LOCALDB_URL)

# Path to the GeoJSON file (relative to project root)
GEOJSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Pipelines.geojson",
)

# Simulation settings
SIMULATION_INTERVAL_SECONDS = int(os.getenv("SIMULATION_INTERVAL", "60"))

# Asset generation: how many additional random assets to scatter near each pipeline
EXTRA_ASSETS_PER_PIPELINE = 3
