import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
STATIONS_PATH = DATA_DIR / "stations.json"
BUS_STOPS_PATH = DATA_DIR / "bus_stops.json"
TRANSIT_ALIASES_PATH = DATA_DIR / "transit_aliases.json"
TRANSPORT_TYPE_ALIASES_PATH = DATA_DIR / "transport_type_aliases.json"


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9ก-๙]+", " ", text)
    text = re.sub(
        r"\b(station|stn|stop|bus|bts|mrt|metro|subway|skytrain|line)\b",
        " ",
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def _read_json(path: Path) -> Any:
    if not path.exists():
        return [] if path.suffix == ".json" else {}

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_lookup(records: list[dict], field_name: str = "aliases") -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for record in records:
        canonical_name = record.get("canonicalName") or record.get("name") or ""
        aliases = [canonical_name] + list(record.get(field_name, []) or [])
        for alias in aliases:
            key = normalize_text(alias)
            if key:
                lookup[key] = record
    return lookup


@lru_cache(maxsize=1)
def load_transit_data() -> dict:
    stations = _read_json(STATIONS_PATH)
    bus_stops = _read_json(BUS_STOPS_PATH)
    transit_aliases = _read_json(TRANSIT_ALIASES_PATH)
    transport_type_aliases = _read_json(TRANSPORT_TYPE_ALIASES_PATH)

    station_lookup = _build_lookup(stations)
    bus_lookup = _build_lookup(bus_stops)
    records_by_id = {record["id"]: record for record in stations + bus_stops if record.get("id")}

    alias_lookup: dict[str, str] = {}
    for alias, record_id in transit_aliases.items():
        key = normalize_text(alias)
        if key:
            alias_lookup[key] = record_id

    return {
        "stations": stations,
        "bus_stops": bus_stops,
        "station_lookup": station_lookup,
        "bus_lookup": bus_lookup,
        "alias_lookup": alias_lookup,
        "records_by_id": records_by_id,
        "transport_type_aliases": transport_type_aliases,
    }
