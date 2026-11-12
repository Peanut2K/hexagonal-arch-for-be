from pydantic import BaseModel
from typing import Optional

class SearchResultItem(BaseModel):
    id: str
    name: str    
    type: str             # place, road
    priority: int         # place=1, road=2
    lat: Optional[float] = None
    lon: Optional[float] = None
    address_detail: Optional[str] = None 

    class Config:
        from_attributes = True