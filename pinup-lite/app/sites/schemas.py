from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SiteAnalyzeRequest(BaseModel):
    geometry: dict = Field(..., description="GeoJSON Polygon geometry")
    name: Optional[str] = Field(None, description="Optional site name")


class CadastralRow(BaseModel):
    id: int = 1
    title_deed: str = "-"
    sheet_no: str = "-"
    parcel_no: str = "-"
    survey_no: str = "-"
    rai: float = 0.0
    ngan: float = 0.0
    sq_wa: float = 0.0
    price_per_sq_wa: str = "-"
    total_price: str = "-"


class ZoningRegulationItem(BaseModel):
    category: Optional[str] = "ทั่วไป"
    activity: str
    condition: str = "อนุญาตปกติ"
    note: Optional[str] = None


class SiteAnalysis(BaseModel):
    zoning_code: str = "-"
    zoning_name: str = "-"
    zoning_color: str = "#808080"
    address: str = "-"
    subdistrict: str = "-"
    district: str = "-"
    province: str = "-"
    zipcode: str = "-"
    land_status: str = "-"
    ownership_status: str = "-"
    area_sqm: float = 0.0
    cadastral: List[CadastralRow] = Field(default_factory=list)
    regulations: List[ZoningRegulationItem] = Field(default_factory=list)
    nearest_road_name: str = "-"
    nearest_road_type: str = "-"
    nearest_road_width_m: float = 0.0
    flood_risk: str = "ต่ำ"
    landslide_risk: str = "ต่ำ"
    soil_settlement_risk: str = "ต่ำ"
    risk_alert_text: str = "-"
    far: float = 0.0
    far_bonus: float = 0.0
    osr: float = 0.0
    gfa_max: float = 0.0


class SiteResponse(BaseModel):
    id: str
    name: str
    geometry: dict
    analysis: SiteAnalysis
    created_at: datetime
    updated_at: datetime
