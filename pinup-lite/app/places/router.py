from fastapi import APIRouter, HTTPException, Query
from app.places.schemas import PlaceDetailResponse
from app.places import service as places_service

router = APIRouter(tags=["Places"])


# @desc    Get place details from Google Places API
# @route   GET /api/places/details?query=Life+Asoke+Rama+9
# @route   GET /api/places/details?place_id=ChIJ...
# @access  Public
@router.get("/places/details", response_model=PlaceDetailResponse)
async def get_place_details(
    query: str | None = Query(None, min_length=1, description="ชื่อสถานที่ที่ต้องการค้นหา"),
    summary: bool = Query(False, description="Return basic Place information without photos or contact details"),
    place_id: str | None = Query(
        None,
        min_length=1,
        max_length=512,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Google Place ID (จากการคลิกหมุดบนแผนที่)",
    ),
):
    if bool(query) == bool(place_id):
        raise HTTPException(status_code=422, detail="Provide exactly one of `query` or `place_id`")
    return await places_service.get_place_details(query=query, place_id=place_id, summary=summary)
