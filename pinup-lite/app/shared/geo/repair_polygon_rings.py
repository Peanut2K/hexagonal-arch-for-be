import math
import statistics

# Calibrated for the land/street/building-footprint layers, whose features are
# parcel/building-scale. No legitimate vertex in those layers sits more than
# this far from its own ring's center; a vertex beyond it indicates a
# corrupt/mislocated coordinate in the source. Zoning polygons (bdi-data/area.csv)
# can legitimately span kilometers, so that layer bypasses this check entirely
# (see load_csv_as_geojson's skip_repair) rather than sharing this threshold.
MAX_VERTEX_RADIUS_M = 250.0

# Degrees -> approximate metres near this latitude (~13.6 N). Only used for a
# coarse outlier threshold, so the ~10% anisotropy between lat/lon is immaterial.
_DEG_TO_M = 1e5

# Some BDI parcels store their ring vertices in coordinate (scan) order rather
# than traced around the boundary, e.g. TL, TR, BL, BR. Rendered as-is this draws
# a self-intersecting "bowtie". When (and only when) a ring self-intersects we
# reorder its vertices by angle around the centroid, which recovers a simple
# polygon for convex parcels. Rings that are already simple (including correctly
# ordered concave shapes) are left untouched.
#
# All geometry tests run in a *local* frame (coordinates shifted to a nearby
# origin). Bangkok lon/lat are ~100.6 / ~13.6 while a parcel spans ~0.0001 deg,
# so orientation tests on the raw values suffer catastrophic floating-point
# cancellation and can misjudge whether a ring self-intersects. Shifting to a
# local origin restores precision. We reorder the *original* coordinate objects,
# so no precision is lost in the values we emit.
#
# Caveat: angular ordering assumes a convex parcel. A genuinely concave parcel
# whose vertices are stored out of order cannot be recovered from the points
# alone (the true edge order is lost in the source); it is normalized toward its
# convex ordering. It also cannot fix a corrupt/outlier vertex — that stays
# mislocated and should be flagged back to the data provider.


def _open(ring):
    """Drop the closing duplicate vertex if present."""
    if len(ring) > 1 and ring[0] == ring[-1]:
        return ring[:-1]
    return ring[:]


def _ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_cross(p, q, r, s):
    return (_ccw(r, s, p) > 0) != (_ccw(r, s, q) > 0) and \
           (_ccw(p, q, r) > 0) != (_ccw(p, q, s) > 0)


def _self_intersects(pts):
    """pts: open list of [x, y] in a local frame."""
    n = len(pts)
    segs = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            # skip adjacent segments (they share an endpoint) and the wrap-around pair
            if abs(i - j) <= 1 or (i == 0 and j == n - 1):
                continue
            if _segments_cross(segs[i][0], segs[i][1], segs[j][0], segs[j][1]):
                return True
    return False


def _angular_order(local_pts):
    """Return vertex indices ordered by angle around the centroid (local frame)."""
    cx = sum(p[0] for p in local_pts) / len(local_pts)
    cy = sum(p[1] for p in local_pts) / len(local_pts)
    return sorted(
        range(len(local_pts)),
        key=lambda k: math.atan2(local_pts[k][1] - cy, local_pts[k][0] - cx),
    )


def _repair_ring(ring):
    if not isinstance(ring, list) or len(ring) < 4:
        return ring
    if not all(isinstance(p, list) and len(p) == 2 for p in ring):
        return ring

    pts = _open(ring)
    if len(pts) < 3:
        return ring

    # Shift to a local origin so orientation tests are numerically stable.
    ox = min(p[0] for p in pts)
    oy = min(p[1] for p in pts)
    local = [[p[0] - ox, p[1] - oy] for p in pts]

    if not _self_intersects(local):
        return ring

    order = _angular_order(local)
    reordered = [pts[k] for k in order]  # original coordinate values, reordered
    return reordered + [reordered[0]]    # re-close


def repair_polygon_coordinates(geo_type, coordinates):
    """
    Repair self-intersecting rings for (Multi)Polygon geometries. Non-polygon
    geometries and unparseable coordinates are returned unchanged.
    """
    if coordinates is None:
        return coordinates
    t = (geo_type or "").strip().lower()
    try:
        if t == "polygon":
            return [_repair_ring(ring) for ring in coordinates]
        if t == "multipolygon":
            return [[_repair_ring(ring) for ring in poly] for poly in coordinates]
    except (TypeError, IndexError):
        return coordinates
    return coordinates


def _ring_has_outlier(ring):
    pts = _open(ring)
    if len(pts) < 3:
        return False
    mx = statistics.median(p[0] for p in pts)
    my = statistics.median(p[1] for p in pts)
    for p in pts:
        dx = (p[0] - mx) * _DEG_TO_M
        dy = (p[1] - my) * _DEG_TO_M
        if math.hypot(dx, dy) > MAX_VERTEX_RADIUS_M:
            return True
    return False


def has_outlier_vertex(geo_type, coordinates):
    """
    True if a (Multi)Polygon has a vertex grossly far from its ring's center,
    signalling a corrupt/mislocated source coordinate that geometry repair
    cannot recover. Non-polygon or unparseable geometries return False.
    """
    if coordinates is None:
        return False
    t = (geo_type or "").strip().lower()
    try:
        if t == "polygon":
            return any(_ring_has_outlier(ring) for ring in coordinates)
        if t == "multipolygon":
            return any(_ring_has_outlier(ring) for poly in coordinates for ring in poly)
    except (TypeError, IndexError):
        return False
    return False
