from fastapi import APIRouter, Query

from app.transit.schemas import NearbyTransitStationsResponse
from app.transit import service as transit_service


router = APIRouter(prefix="/transit", tags=["Transit"])


@router.get("/nearby-stations", response_model=NearbyTransitStationsResponse)
async def get_nearby_stations(
    lat: float = Query(..., ge=-90, le=90, description="Origin latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Origin longitude"),
    radius: int = Query(500, gt=0, le=50000, description="Search radius in metres"),
    transport_type: str | None = Query(
        None,
        description="Filter stations by type: bts, mrt, brt, port, or bus",
    ),
):
    return await transit_service.get_nearby_stations(lat, lng, radius, transport_type)
