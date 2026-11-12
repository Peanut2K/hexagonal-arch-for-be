import os
import asyncio
import logging
import httpx
from app.errors import AppError, NotFound
from app.places.schemas import PlaceDetailResponse

logger = logging.getLogger(__name__)

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"
PLACES_PHOTO_URL = "https://places.googleapis.com/v1/{photo_name}/media"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.types",
    "places.primaryTypeDisplayName",
    "places.photos",
    "places.internationalPhoneNumber",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.regularOpeningHours",
    "places.rating",
    "places.userRatingCount",
    "places.googleMapsUri",
    "places.plusCode",
])
# Place Details takes the same fields without the `places.` prefix
DETAILS_FIELD_MASK = FIELD_MASK.replace("places.", "")
SUMMARY_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.primaryTypeDisplayName",
    "places.googleMapsUri",
])
DETAILS_SUMMARY_FIELD_MASK = SUMMARY_FIELD_MASK.replace("places.", "")

TYPE_MAP = {
    "condominium_complex": "Condominium",
    "housing_development": "Condominium",
    "apartment_complex": "Condominium",
    "office_building": "Office Building",
    "hotel": "Hotel",
    "hospital": "Hospital",
    "shopping_mall": "Shopping Mall",
}


def _resolve_type(types: list[str], display_name: str | None = None) -> str:
    for t in (types or []):
        if t in TYPE_MAP:
            return TYPE_MAP[t]
    # Non-real-estate Places (shops, restaurants, ...) clicked on the map
    return display_name or "Building / Real Estate"


async def _resolve_photo(photo: dict, api_key: str, client: httpx.AsyncClient) -> dict | None:
    """Resolve a Google Places photo and preserve its required author credits."""
    try:
        url = PLACES_PHOTO_URL.format(photo_name=photo["name"])
        resp = await client.get(
            url,
            params={"maxWidthPx": 800, "skipHttpRedirect": "true"},
            headers={"X-Goog-Api-Key": api_key},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            photo_uri = data.get("photoUri")
            source = photo.get("googleMapsUri")
            if photo_uri and source:
                return {
                    "url": photo_uri,
                    "attributions": photo.get("authorAttributions") or [],
                    "source": source,
                }
    except Exception:
        pass
    return None


# @desc    Fetch place details from Google Places API (New)
# @route   GET /api/places/details?query=... | ?place_id=...
# @access  Public
async def get_place_details(
    query: str | None = None, place_id: str | None = None, summary: bool = False
) -> PlaceDetailResponse:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        raise AppError("GOOGLE_MAPS_API_KEY is not configured", status=500)
    async with httpx.AsyncClient() as client:
        # ── 1. Look up place: by id (map POI click) or by text search ─
        if place_id:
            resp = await client.get(
                PLACES_DETAILS_URL.format(place_id=place_id),
                params={"languageCode": "th"},
                headers={
                    "X-Goog-Api-Key": api_key,
                    "X-Goog-FieldMask": DETAILS_SUMMARY_FIELD_MASK if summary else DETAILS_FIELD_MASK,
                },
                timeout=15,
            )
            if resp.status_code == 404:
                raise NotFound("Place not found")
        else:
            resp = await client.post(
                PLACES_SEARCH_URL,
                json={"textQuery": query, "languageCode": "th"},
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": api_key,
                    "X-Goog-FieldMask": SUMMARY_FIELD_MASK if summary else FIELD_MASK,
                },
                timeout=15,
            )

        if resp.status_code != 200:
            # Don't forward Google's status/body: it can expose key/project
            # details, and a 401 would sign the user out in the frontend.
            logger.error("Google Places API error %s", resp.status_code)
            raise AppError("Google Places API error", status=502)
        if place_id:
            place = resp.json()
        else:
            place = (resp.json().get("places") or [None])[0]

        if not place:
            raise NotFound("Place not found")
        # ── 2. Resolve photo URLs concurrently for maximum performance ──────
        photos = [] if summary else [p for p in (place.get("photos") or [])[:6] if p.get("name") and p.get("googleMapsUri")]
        photo_tasks = [
            _resolve_photo(photo, api_key, client)
            for photo in photos
        ]
        resolved_photos = [photo for photo in await asyncio.gather(*photo_tasks) if photo]

        # ── 3. Format response ───────────────────────────────────────
        lat = place.get("location", {}).get("latitude", 13.754862)
        lng = place.get("location", {}).get("longitude", 100.563868)

        opening_hours = None
        weekday_descriptions = (
            place.get("regularOpeningHours", {}).get("weekdayDescriptions") or []
        )
        if weekday_descriptions:
            opening_hours = weekday_descriptions[0]

        plus_code = (
            place.get("plusCode", {}).get("compoundCode")
            or place.get("plusCode", {}).get("globalCode")
        )

        return PlaceDetailResponse(
            id=place.get("id", ""),
            name=place.get("displayName", {}).get("text", query or ""),
            nameEn=query,
            type=_resolve_type(
                place.get("types", []),
                place.get("primaryTypeDisplayName", {}).get("text"),
            ),
            rating=place.get("rating"),
            userRatingCount=place.get("userRatingCount"),
            address=place.get("formattedAddress", ""),
            position=[lat, lng],
            phoneNumber=place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"),
            websiteUri=place.get("websiteUri"),
            googleMapsUri=place.get("googleMapsUri"),
            openingHours=opening_hours,
            plusCode=plus_code,
            photos=[photo["url"] for photo in resolved_photos],
            photoAttributions=[photo["attributions"] for photo in resolved_photos],
            photoSources=[photo["source"] for photo in resolved_photos],
        )
