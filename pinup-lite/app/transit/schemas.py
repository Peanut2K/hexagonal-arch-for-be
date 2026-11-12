from pydantic import BaseModel, Field


class Location(BaseModel):
    lat: float
    lng: float


class TransitStation(BaseModel):
    id: str
    name: str
    system: str
    type: str
    location: Location
    address: str
    distanceMeters: int
    line: str | None = Field(None, description="Transit line (e.g., 'Sukhumvit', 'Blue')")
    code: str | None = Field(None, description="Station code (e.g., 'E4', 'BL22')")
    busRoutes: list[str] | None = Field(None, description="Bus route numbers if this is a bus stop")


class NearbyTransitStationsResponse(BaseModel):
    origin: Location
    stations: list[TransitStation]
