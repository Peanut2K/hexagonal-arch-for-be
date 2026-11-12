# [HTTP] /api/search
from fastapi import APIRouter, Query

from app.search import service
from app.search.schemas import SearchResultItem

router = APIRouter(tags=["Search"])


@router.get("/", response_model=list[SearchResultItem])
def search_locations(q: str = Query(..., min_length=1, description="คำค้นหา เช่น 'ส'")):
    return service.search_locations(q)
