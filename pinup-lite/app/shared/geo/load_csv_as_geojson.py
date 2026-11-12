import csv
import os
from app.shared.geo.parse_malformed_geo_json import parse_malformed_geo_json
from app.shared.geo.repair_polygon_rings import (
    repair_polygon_coordinates,
    has_outlier_vertex,
)

GEO_COL = 'GEO_COOR'

# CSV files use inconsistent casing (e.g. "PolyGon"); normalize to valid
# GeoJSON geometry type names.
_GEO_TYPE_ALIASES = {
    "polygon": "Polygon",
    "multipolygon": "MultiPolygon",
    "linestring": "LineString",
    "multilinestring": "MultiLineString",
    "point": "Point",
    "multipoint": "MultiPoint",
}

# Columns tried, in order, for a human-readable label when logging skips.
_NAME_COLS = ("BUILDING_NAME", "STREET_NAME", "LOCATION_NAME")


def _normalize_geo_type(raw: str):
    if not raw:
        return None
    return _GEO_TYPE_ALIASES.get(raw.strip().lower(), raw.strip())


def _label(row):
    for col in _NAME_COLS:
        if row.get(col):
            return row[col]
    return ""


def load_csv_as_geojson(file_path: str, geo_col: str = GEO_COL, skip_repair: bool = False):
    """
    Read a CSV file and return a GeoJSON FeatureCollection.

    Every non-geometry column becomes part of the feature's `properties`;
    the parsed `GEO_COOR` column becomes the geometry. Coordinates are kept
    in standard GeoJSON [lon, lat] order (no swap) because the frontend
    renders these through deck.gl's GeoJsonLayer, which expects [lon, lat].

    Features whose geometry is unusable are dropped (not emitted): either the
    source has no coordinates, or a vertex is a gross spatial outlier (a corrupt
    coordinate). Dropped features are logged so they can be reported back to the
    data provider.

    `skip_repair` bypasses ring-reorder repair and the outlier-vertex check.
    The repair/outlier heuristics assume parcel/building-scale rings (see
    repair_polygon_rings.py); zoning polygons can legitimately span kilometers,
    so a layer whose geometry has already been manually reviewed should set
    this to avoid having correct features misdetected as corrupt and dropped.
    """
    features = []
    skipped = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = row.get('ID')
                geo_raw = row.get(geo_col)
                coordinates = parse_malformed_geo_json(geo_raw) if geo_raw else None

                if coordinates is None:
                    skipped.append((fid, _label(row), "empty geometry"))
                    continue

                geo_type = _normalize_geo_type(row.get('GEO_TYPE'))
                if not skip_repair:
                    coordinates = repair_polygon_coordinates(geo_type, coordinates)

                    if has_outlier_vertex(geo_type, coordinates):
                        skipped.append((fid, _label(row), "outlier vertex"))
                        continue

                features.append({
                    "type": "Feature",
                    "id": fid,
                    "geometry": {
                        "type": geo_type,
                        "coordinates": coordinates,
                    },
                    "properties": {k: v for k, v in row.items() if k != geo_col},
                })
    except Exception as e:
        print(f"Error loading {file_path}: {e}")

    if skipped:
        name = os.path.basename(file_path)
        print(
            f"[bdi] {name}: skipped {len(skipped)} feature(s) with unusable geometry: "
            + ", ".join(f"#{fid} '{label}' ({reason})" for fid, label, reason in skipped)
        )

    return {"type": "FeatureCollection", "features": features}
