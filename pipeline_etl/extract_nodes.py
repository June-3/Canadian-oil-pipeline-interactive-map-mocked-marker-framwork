"""
Extract pipeline endpoints and intersection nodes from GeoJSON.

Strategy:
  1. For each pipeline, collect all segment start/end points.
  2. Within each pipeline, deduplicate points < 5 m apart (filters out
     MicroLineStrings that share the exact same hub coordinate).
  3. Cluster remaining points across ALL pipelines by PROXIMITY_THRESHOLD_M.
  4. Any cluster containing points from >= 2 distinct pipelines → intersection (sensor).
     Clusters with only 1 pipeline → terminal (valve).
"""

import json
import math
import os
import sys

# Allow running from project root without PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline_etl.config import GEOJSON_PATH

# Pipelines are large civil structures — junction points digitised from
# different sources can be 100s of metres apart. 800 m safely merges every
# known junction in this dataset while the next-nearest nodes sit > 2.8 km away.
PROXIMITY_THRESHOLD_M = 500.0  # metres

# When collapsing duplicate segment endpoints *within the same pipeline*,
# points closer than this are treated as a single logical anchor.
INTRAPIPE_DEDUP_M = 5.0


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
        pts.append((seg[0][0], seg[0][1]))
        pts.append((seg[-1][0], seg[-1][1]))
    return pts


def _dedup_intrapipe(pts):
    """
    Within ONE pipeline, merge nearly-identical points (e.g. a hub coordinate
    shared by 4 short stub segments) so they count as a single anchor.
    """
    if not pts:
        return []
    clusters = []
    for lon, lat in pts:
        matched = None
        for ci, cluster in enumerate(clusters):
            for mlon, mlat in cluster:
                if _distance_m(lon, lat, mlon, mlat) <= INTRAPIPE_DEDUP_M:
                    matched = ci
                    break
            if matched is not None:
                break
        if matched is not None:
            clusters[matched].append((lon, lat))
        else:
            clusters.append([(lon, lat)])
    return [(sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)) for c in clusters]


def _cluster_crosspipe(points):
    """
    points: list of (lon, lat, pipeline_name)
    Returns: list of (centroid_lon, centroid_lat, distinct_pipelines, [pipeline_names])
    """
    clusters = []
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
        distinct_pipelines = len(set(p[2] for p in cluster))
        pipeline_names = sorted(set(p[2] for p in cluster))
        result.append((round(avg_lon, 6), round(avg_lat, 6), distinct_pipelines, pipeline_names))
    return result


def _dist_to_segment_m(px, py, ax, ay, bx, by):
    """Minimum distance from point P to line segment AB, in metres."""
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return _distance_m(px, py, ax, ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return _distance_m(px, py, cx, cy)


def _find_line_junctions(clusters, features):
    """
    For each single-pipeline terminal cluster, check whether its centroid
    lies on (or near) the *path* of another pipeline.  If it does, add the
    other pipeline's name and bump the distinct-pipeline count so the node
    is reclassified as an intersection.

    This catches e.g. a lateral that taps into a mainline mid-segment
    (not at a mainline endpoint).
    """
    for i, (clon, clat, dcount, pnames) in enumerate(clusters):
        if dcount >= 2:
            continue  # already an intersection; skip

        own_names = set(pnames)
        # Build a bounding-box filter: only check pipeline segments within
        # ~2° of the cluster centroid to avoid scanning 100k points.
        for feat in features:
            pname = feat["properties"]["name"]
            if pname in own_names:
                continue  # don't check against own pipeline

            # Quick bounding-box reject
            min_dist = float("inf")
            for seg_coords in feat["geometry"]["coordinates"]:
                for j in range(len(seg_coords) - 1):
                    ax, ay = seg_coords[j]
                    bx, by = seg_coords[j + 1]
                    # Tiny bounding-box filter per segment
                    if (clon < min(ax, bx) - 0.08 or clon > max(ax, bx) + 0.08
                            or clat < min(ay, by) - 0.08 or clat > max(ay, by) + 0.08):
                        continue
                    d = _dist_to_segment_m(clon, clat, ax, ay, bx, by)
                    if d < min_dist:
                        min_dist = d
                        if min_dist <= PROXIMITY_THRESHOLD_M:
                            break  # close enough — no need to scan further
                if min_dist <= PROXIMITY_THRESHOLD_M:
                    break

            if min_dist <= PROXIMITY_THRESHOLD_M:
                pnames.append(pname)
                own_names.add(pname)

        # Update the cluster with new pipeline count & sorted names
        clusters[i] = (clon, clat, len(own_names), sorted(own_names))


def extract_assets():
    """Main entry point: returns list of asset definitions."""
    with open(GEOJSON_PATH, "r") as f:
        data = json.load(f)

    # Step 1 — collect per-pipeline deduplicated endpoints
    tagged_points = []
    for feat in data["features"]:
        pname = feat["properties"]["name"]
        coords = feat["geometry"]["coordinates"]
        raw = _all_segment_endpoints(coords)
        deduped = _dedup_intrapipe(raw)
        for lon, lat in deduped:
            tagged_points.append((lon, lat, pname))

    # Step 2 — cross-pipeline clustering
    clustered = _cluster_crosspipe(tagged_points)

    # Step 2.5 — detect terminals that sit on another pipeline's path
    _find_line_junctions(clustered, data["features"])

    # Step 3 — build assets
    # Sort: intersections first, then terminals by pipeline name
    clustered.sort(key=lambda c: (0 if c[2] >= 2 else 1, c[3][0] if c[3] else ""))

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
