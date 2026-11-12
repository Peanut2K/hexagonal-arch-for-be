import json
import re

def parse_malformed_geo_json(geo_str: str):
    """
    Parses a string representation of GEO_COOR.
    Handles malformed JSON arrays that are missing commas (e.g., ][ instead of ],[).
    This can be reused for any similar malformed coordinate string.
    """
    if not geo_str or str(geo_str).strip() == "":
        return None
    
    # Try to parse it directly in case it's valid JSON
    try:
        return json.loads(geo_str)
    except json.JSONDecodeError:
        fixed_str = str(geo_str).strip()
        # Missing commas between array elements like ][ -> ],[
        fixed_str = re.sub(r'\]\s*\[', '],[', fixed_str)
        # Trailing commas before a closing bracket/brace like ,] -> ] (invalid JSON)
        fixed_str = re.sub(r',(\s*[\]\}])', r'\1', fixed_str)
        try:
            return json.loads(fixed_str)
        except json.JSONDecodeError:
            return geo_str # Return as is if we really can't parse it
