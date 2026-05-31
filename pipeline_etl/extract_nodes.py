"""
Extract pipeline endpoints and intersection nodes from GeoJSON.

Strategy:
  - Collect every segment's start and end coordinate from every MultiLineString.
  - Cluster points within PROXIMITY_THRESHOLD_M into single nodes.
  - Nodes shared by >= 2 distinct pipeline endpoints → intersection (sensor).
  - Nodes with only 1 pipeline endpoint → terminal (valve).

Returns a list of asset dicts ready for DB insertion.
"""

import json
import math
import os
import sys

# Allow running from project root without PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline_etl.config import GEOJSON_PATH

PROXIMITY_THRESHOLD_M = 60.0  # metres


def _distance_m(lon1, lat1, lon2, lat2):
    """Haversine distance in metres."""
    R = 6_371_000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _all_segment_endpoints(coords):
    """Return every segment's (start, end) from a MultiLineString coordinate list."""
    pts = []
    for seg in coords:
        pts.append(tuple(seg[0]))
        pts.append(tuple(seg[-1]))
    return pts


def _cluster(points):
    """
    Greedy single-linkage clustering by PROXIMITY_THRESHOLD_M.
    Returns list of (centroid_lon, centroid_lat, member_count, members).
    """
    clusters = []  # each is list of (lon, lat, pipeline_name)
    for lon, lat, pname in points:
        matched = None
        for ci, cluster in enumerate(clusters):
            for mlon, mlat, _ in cluster:
                if _distance_m(lon, lat, mlon, mlat) <= PROXIMITY_THRESHOLD_M:
                    matched = ci
                    break
            if matched is not None:
                break
        if matched is not None:
            clusters[matched].append((lon, lat, pname))
        else:
            clusters.append([(lon, lat, pname)])

    result = []
    for cluster in clusters:
        avg_lon = sum(p[0] for p in cluster) / len(cluster)
        avg_lat = sum(p[1] for p in cluster) / len(cluster)
        # Count distinct pipelines in this cluster
        distinct_pipelines = len(set(p[2] for p in cluster))
        pipeline_names = sorted(set(p[2] for p in cluster))
        result.append((round(avg_lon, 6), round(avg_lat, 6), distinct_pipelines, pipeline_names))
    return result


def extract_assets():
    """Main entry point: returns list of asset definitions."""
    with open(GEOJSON_PATH, "r") as f:
        data = json.load(f)

    features = data["features"]

    # Collect every segment endpoint tagged with its pipeline name
    tagged_points = []
    for feat in features:
        pname = feat["properties"]["name"]
        coords = feat["geometry"]["coordinates"]
        for pt in _all_segment_endpoints(coords):
            tagged_points.append((pt[0], pt[1], pname))

    # Cluster nearby points into nodes
    clustered = _cluster(tagged_points)

    # Build assets
    assets = []
    asset_id = 1

    for lon, lat, pipeline_count, pipelines in clustered:
        if pipeline_count >= 2:
            node_type = "intersection"
            asset_type = "sensor"
        else:
            node_type = "terminal"
            asset_type = "valve"

        label = " / ".join(pipelines)

        assets.append({
            "id": asset_id,
            "name": f"{label} - {node_type.title()}",
            "type": asset_type,
            "longitude": lon,
            "latitude": lat,
            "status": "normal",
        })
        asset_id += 1

    return assets


if __name__ == "__main__":
    result = extract_assets()
    print(f"Extracted {len(result)} asset nodes:")
    for a in result:
        print(f"  [{a['id']}] {a['name']:60s} | {a['type']:6s} | ({a['longitude']:.4f}, {a['latitude']:.4f})")
