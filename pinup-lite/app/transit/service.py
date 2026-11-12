import math
import re

import httpx
from app.errors import AppError

from app.config import require_google_maps_api_key
from app.transit.loader import load_transit_data, normalize_text

GOOGLE_PLACES_NEARBY_URL = (
    "https://places.googleapis.com/v1/places:searchNearby"
)
BUS_SYSTEM = "BUS"
TRANSIT_SYSTEM = "TRANSIT"
UNKNOWN_METADATA = "Unknown"
SYSTEM_TO_STATION_TYPE = {
    "BTS": "bts_station",
    "MRT": "mrt_station",
    "BRT": "brt_station",
    "PORT": "port_station",
    "BUS": "bus_station",
}
NAME_SYSTEM_PATTERNS = (
    ("BTS", re.compile(r"\b(bts|skytrain)\b", re.IGNORECASE)),
    ("MRT", re.compile(r"\b(mrt|metro|subway)\b", re.IGNORECASE)),
    ("BRT", re.compile(r"\b(brt|bus rapid transit)\b", re.IGNORECASE)),
    (
        "PORT",
        re.compile(r"\b(port|pier|harbor|harbour|ferry)\b", re.IGNORECASE),
    ),
    ("BUS", re.compile(r"\b(bus|bus stop|bus terminal)\b", re.IGNORECASE)),
)
STATION_FEATURE_SUFFIX_PATTERN = re.compile(
    r"\s+(?:station\s+)?(?:entrance|exit|platform|concourse|transit\s+hub)"
    r"(?:\s*(?:no\.?\s*)?\d+)?$"
)
STATION_SUB_PLACE_PATTERN = re.compile(
    r"\b(entrance|exit|platform|concourse|transit hub)\b"
)


def _calculate_distance_meters(
    origin_lat: float, origin_lng: float, lat: float, lng: float
) -> int:
    """Calculate the great-circle distance between two WGS84 coordinates."""
    origin_lat_rad, origin_lng_rad, lat_rad, lng_rad = map(
        math.radians, (origin_lat, origin_lng, lat, lng)
    )
    delta_lat = lat_rad - origin_lat_rad
    delta_lng = lng_rad - origin_lng_rad
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(origin_lat_rad)
        * math.cos(lat_rad)
        * math.sin(delta_lng / 2) ** 2
    )
    return round(2 * 6_371_000 * math.asin(math.sqrt(haversine)))


def _place_name(place: dict) -> str:
    return (
        place.get("name") or place.get("displayName", {}).get("text", "") or ""
    )


def _google_place_system(place: dict) -> str:
    """Classify a Google Place only when no local record identifies it."""
    name = _place_name(place)
    for system, pattern in NAME_SYSTEM_PATTERNS:
        if pattern.search(name):
            return system

    place_types = {
        str(place_type).lower() for place_type in place.get("types", [])
    }
    if "bus_station" in place_types:
        return BUS_SYSTEM
    if "subway_station" in place_types:
        return "MRT"
    
    else:
        return BUS_SYSTEM

    return TRANSIT_SYSTEM


def _extract_place_location(place: dict) -> dict | None:
    for location in (
        place.get("location"),
        place.get("geometry", {}).get("location"),
        place.get("geo", {}).get("location"),
    ):
        if not location:
            continue
        lat = location.get("latitude", location.get("lat"))
        lng = location.get("longitude", location.get("lng"))
        if lat is not None and lng is not None:
            return {"lat": lat, "lng": lng}
    return None


def _extract_place_address(place: dict) -> str:
    return (
        place.get("formattedAddress")
        or place.get("formatted_address")
        or place.get("vicinity")
        or ""
    )


def _extract_place_id(place: dict) -> str:
    return place.get("id") or place.get("place_id") or place.get("placeId", "")


def _matches_transport_type(station: dict, transport_type: str | None) -> bool:
    return (
        transport_type is None
        or station.get("system", "").lower() == transport_type
    )


def _normalize_transport_type(value: str | None) -> str | None:
    if value is None:
        return None
    alias = re.sub(r"[-_]+", " ", value.strip().lower())
    return load_transit_data()["transport_type_aliases"].get(alias)


def _get_lookup_candidates(place: dict) -> list[str]:
    values = []
    name = _place_name(place)
    address = _extract_place_address(place)
    if name:
        values.append(name)
    if address:
        values.append(address)
    return values


def _build_lookup_keys(text: str) -> tuple[str, ...]:
    normalized = normalize_text(text)
    if not normalized:
        return ()

    without_feature = STATION_FEATURE_SUFFIX_PATTERN.sub(
        "", normalized
    ).strip()
    if without_feature == normalized:
        return (normalized,)
    return normalized, without_feature


def _resolve_transit_record(place: dict) -> dict | None:
    transit_data = load_transit_data()
    for text in _get_lookup_candidates(place):
        for key in _build_lookup_keys(text):
            if record_id := transit_data["alias_lookup"].get(key):
                return transit_data["records_by_id"].get(record_id)
            if record := transit_data["station_lookup"].get(key):
                return record
            if record := transit_data["bus_lookup"].get(key):
                return record
    return None


def _station_type_from_system(system: str) -> str:
    return SYSTEM_TO_STATION_TYPE.get(
        (system or "").upper(), "transit_station"
    )


def _station_representative_score(station: dict) -> tuple[int, int]:
    """Rank a primary station Place above exits and other sub-places."""
    place_name = normalize_text(
        station.get("_placeName") or station.get("name")
    )
    sub_place = bool(STATION_SUB_PLACE_PATTERN.search(place_name))
    return int(not sub_place), -station.get("distanceMeters", 0)


def _deduplicate_stations(stations: list[dict]) -> list[dict]:
    deduplicated: list[dict] = []
    for station in stations:
        matched_index = None
        for index, existing in enumerate(deduplicated):
            if station.get("id") == existing.get("id"):
                matched_index = index
                break

        if matched_index is None:
            deduplicated.append(station)
            continue

        existing = deduplicated[matched_index]
        if _station_representative_score(
            station
        ) > _station_representative_score(existing):
            deduplicated[matched_index] = station

    return deduplicated


def _prepare_station_response(stations: list[dict]) -> list[dict]:
    """Deduplicate and order stations, excluding private ranking fields."""
    response_stations = [
        {
            key: value
            for key, value in station.items()
            if not key.startswith("_")
        }
        for station in _deduplicate_stations(stations)
    ]
    response_stations.sort(key=lambda station: station["distanceMeters"])
    return response_stations


def _map_google_place_to_transit_station(
    place: dict, origin_lat: float, origin_lng: float
) -> dict:
    location = _extract_place_location(place)
    if location is None:
        raise ValueError("Place result is missing location data")

    distance_meters = _calculate_distance_meters(
        origin_lat, origin_lng, location["lat"], location["lng"]
    )
    name = _place_name(place)
    record = _resolve_transit_record(place)

    if record is not None:
        system = (record.get("system") or BUS_SYSTEM).upper()
        station_type = _station_type_from_system(system)
        station = {
            "id": record.get("id") or _extract_place_id(place),
            "name": record.get("name") or name,
            "system": system,
            "type": station_type,
            "location": {"lat": location["lat"], "lng": location["lng"]},
            "address": _extract_place_address(place),
            "distanceMeters": distance_meters,
            "line": record.get("line") or UNKNOWN_METADATA,
            "code": str(record.get("code") or UNKNOWN_METADATA),
            "_placeName": name,
        }
        if record.get("routes") and system == BUS_SYSTEM:
            station["busRoutes"] = record["routes"]
        return station

    system = _google_place_system(place)
    return {
        "id": _extract_place_id(place),
        "name": name,
        "system": system,
        "type": _station_type_from_system(system),
        "location": {"lat": location["lat"], "lng": location["lng"]},
        "address": _extract_place_address(place),
        "distanceMeters": distance_meters,
        "_placeName": name,
    }


async def get_nearby_stations(
    lat: float, lng: float, radius: int, transport_type: str | None = None
) -> dict:
    """Return nearby transit stations, optionally filtered by type."""

    normalized_transport_type = _normalize_transport_type(transport_type)
    if transport_type is not None and normalized_transport_type is None:
        raise AppError("Unsupported transport type")
    api_key = require_google_maps_api_key()
    body = {
        "includedTypes": [
            "transit_station",
            "bus_station",
            "train_station",
            "subway_station",
        ],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius),
            }
        },
    }
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.location,"
            "places.formattedAddress,places.types"
        ),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GOOGLE_PLACES_NEARBY_URL,
                headers=headers,
                json=body,
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as e:
            detail = e.response.text
            try:
                error_payload = e.response.json()
                if "error" in error_payload:
                    detail = error_payload["error"].get("message", detail)
            except ValueError:
                pass
            raise AppError(detail, status=e.response.status_code)
        except httpx.RequestError as e:
            raise AppError(f"Google Maps request failed: {str(e)}", status=503)
    if "error" in payload:
        error_detail = payload["error"].get(
            "message", "Unknown Google Places error"
        )
        raise AppError(f"Google Places error: {error_detail}", status=502)
    places = payload.get("places", [])
    stations = [
        _map_google_place_to_transit_station(place, lat, lng)
        for place in places
        if _extract_place_location(place)
    ]
    stations = [
        station
        for station in stations
        if _matches_transport_type(station, normalized_transport_type)
    ]

    stations = _prepare_station_response(stations)
    return {"origin": {"lat": lat, "lng": lng}, "stations": stations}
