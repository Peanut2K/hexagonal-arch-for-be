from pydantic import BaseModel
from typing import Optional, List


class PlaceDetailResponse(BaseModel):
    id: str
    name: str
    nameEn: Optional[str] = None
    type: str
    rating: Optional[float] = None
    userRatingCount: Optional[int] = None
    address: str
    position: List[float]  # [lat, lng]
    phoneNumber: Optional[str] = None
    websiteUri: Optional[str] = None
    googleMapsUri: Optional[str] = None
    openingHours: Optional[str] = None
    plusCode: Optional[str] = None
    photos: Optional[List[str]] = None
    photoAttributions: Optional[List[List[dict]]] = None
    photoSources: Optional[List[str]] = None
