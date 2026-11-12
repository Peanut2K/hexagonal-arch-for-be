"""
Geographic, Soil & Flood Risk Evaluation Module for PINUP
Reference: Geographic, Soil & Flood Risk Brief (Bangkok & Udom Suk - Bang Na)
"""

# Default neutral risk response (All Low / ต่ำ)
DEFAULT_RISK = {
    "flood_risk": "ต่ำ",
    "landslide_risk": "ต่ำ",
    "soil_settlement_risk": "ต่ำ",
    "risk_alert_text": "-",
}

# District / Specific Area Risk Mapping Table
# Formatted per PINUP Feasibility Risk Briefs
DISTRICT_RISK_MAP = {
    "บางนา": {
        "flood_risk": "ปานกลาง-สูง",
        "landslide_risk": "ต่ำ",
        "soil_settlement_risk": "สูง",
        "risk_alert_text": (
            "พื้นที่บริเวณเขตบางนา ตั้งอยู่บนชั้นดินเหนียวอ่อนกรุงเทพ (Bangkok Clay) "
            "และเป็นพื้นที่ราบต่ำเมือง มีความเสี่ยงจากน้ำท่วมขังเมืองและการระบายน้ำไม่ทัน "
            "ควรตรวจชั้นดินจริงด้วย borehole/SPT และตรวจสอบระดับท่อระบายน้ำ กทม."
        ),
    },
    "พระโขนง": {
        "flood_risk": "ปานกลาง-สูง",
        "landslide_risk": "ต่ำ",
        "soil_settlement_risk": "สูง",
        "risk_alert_text": (
            "พื้นที่บริเวณเขตพระโขนง ตั้งอยู่บนชั้นดินเหนียวอ่อนกรุงเทพ (Bangkok Clay) "
            "มีความเสี่ยงจากน้ำท่วมขังเมืองและการระบายน้ำไม่ทัน ควรตรวจชั้นดินจริงด้วย borehole/SPT"
        ),
    },
    "ประเวศ": {
        "flood_risk": "ปานกลาง-สูง",
        "landslide_risk": "ต่ำ",
        "soil_settlement_risk": "สูง",
        "risk_alert_text": (
            "พื้นที่บริเวณเขตประเวศ เป็นพื้นที่รับน้ำและราบต่ำเมือง มีความเสี่ยงจากน้ำท่วมขังเมือง "
            "ควรตรวจสอบระดับคันกั้นน้ำและระบบท่อระบายน้ำ กทม."
        ),
    },
    "สวนหลวง": {
        "flood_risk": "ปานกลาง-สูง",
        "landslide_risk": "ต่ำ",
        "soil_settlement_risk": "สูง",
        "risk_alert_text": (
            "พื้นที่บริเวณเขตสวนหลวง ตั้งอยู่บนชั้นดินเหนียวอ่อนกรุงเทพ มีความเสี่ยงจากน้ำท่วมขังเมือง"
        ),
    },
}


def evaluate_geographic_risks(district: str, subdistrict: str, province: str) -> dict:
    """
    Evaluates flood risk, landslide risk, soil settlement risk, and generates
    risk alert text based on DISTRICT_RISK_MAP.
    Defaults to all Low (ต่ำ) if area is not in high-risk mapped zones.
    """
    if not district or district == "-":
        return DEFAULT_RISK

    # Match district keyword in DISTRICT_RISK_MAP
    for d_key, risk_data in DISTRICT_RISK_MAP.items():
        if d_key in district:
            return risk_data

    # Default neutral return if no risk alert triggered
    return DEFAULT_RISK
