# placement_extractor.py (Corrected to use the SIGN_ABBREVIATION_MAP)

from typing import List, Dict, Any, Set

# =============================================================================
# 1. CONFIGURATION CONSTANTS
# =============================================================================
PLANET_IDS: Set[str] = {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"}
NODE_IDS: Set[str] = {"north_node", "south_node"}
ANGLE_IDS: Set[str] = {"ascendant", "imum_coeli", "descendant", "midheaven"}
ASTEROID_IDS: Set[str] = {"chiron", "mean_lilith"}

# This map is required to translate sign abbreviations from the API.
SIGN_ABBREVIATION_MAP: Dict[str, str] = {
    "ari": "aries", "tau": "taurus", "gem": "gemini", "can": "cancer",
    "leo": "leo", "vir": "virgo", "lib": "libra", "sco": "scorpio",
    "sag": "sagittarius", "cap": "capricorn", "aqu": "aquarius", "pis": "pisces"
}

HOUSE_ABBREVIATION_MAP: Dict[str, str] = {
    "first": "1", "second": "2", "third" : "3", "fourth" : "4", "fifth" : "5",
    "sixth" : "6", "seventh" : "7", "eighth" : "8", "ninth" : "9", "tenth" : "10",
    "eleventh" : "11", "twelfth" : "12"
}

# =============================================================================
# 2. MAIN ORCHESTRATION FUNCTION
# =============================================================================

def extract_all_placement_objects(full_chart_object: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Orchestrates the extraction of all placements from the live chart object format.
    """
    celestial_points = full_chart_object.get("celestial_points", [])
    houses = full_chart_object.get("houses", [])
    aspect_list = full_chart_object.get("aspects", [])

    points_map = {p['id']: p for p in celestial_points}
    houses_map = {h['id']: h for h in houses}

    if not points_map and not houses_map:
        return []

    all_features = []
    all_features.extend(_extract_points_in_signs(points_map))
    all_features.extend(_extract_points_in_houses(points_map))
    all_features.extend(_extract_signs_on_houses(houses_map))
    all_features.extend(_extract_aspects(aspect_list, points_map))

    return all_features

# =============================================================================
# 3. HELPER EXTRACTION FUNCTIONS (REWRITTEN)
# =============================================================================

def _extract_points_in_signs(points_map: Dict[str, Any]) -> List[Dict]:
    """Extracts all celestial points in signs, using the abbreviation map."""
    features = []
    for point_id, point_info in points_map.items():
        # Get the sign abbreviation (e.g., 'lib')
        sign_abbr = point_info.get("zodiac_sign", {}).get("id")
        if not sign_abbr:
            continue
            
        # Use the map to get the full name (e.g., 'libra')
        sign_full_name = SIGN_ABBREVIATION_MAP.get(sign_abbr.lower())
        if not sign_full_name:
            continue
        
        point_type = "node" if point_id in NODE_IDS else \
                     "angle" if point_id in ANGLE_IDS else \
                     "asteroid" if point_id in ASTEROID_IDS else \
                     "planet"

        features.append({
            "display": f"{point_info.get('name')} in {sign_full_name.capitalize()}",
            "components": [{"type": point_type, "id": point_id}, {"type": "zodiac_sign", "id": sign_full_name}]
        })
    return features

def _extract_points_in_houses(points_map: Dict[str, Any]) -> List[Dict]:
    """
    Extracts all celestial points in houses, *excluding angles* as their house
    placement is inherently defined by their nature.
    """
    features = []
    for point_id, point_info in points_map.items():
        if point_id in ANGLE_IDS: 
            continue 


        house_info = point_info.get("house") #
        if not house_info: #
            continue #

        house_id = house_info.get("id") #
        if not house_id: #
            continue #

        numeric_house_id = house_id.replace('_house', '') #
        numeric_house_id = HOUSE_ABBREVIATION_MAP.get(numeric_house_id) #
        point_type = "node" if point_id in NODE_IDS else \
                     "asteroid" if point_id in ASTEROID_IDS else \
                     "planet" #

        features.append({ #
            "display": f"{point_info.get('name')} in {house_info.get('name')}", #
            "components": [{"type": point_type, "id": point_id}, {"type": "house", "id": numeric_house_id}] #
        })
    return features 

def _extract_signs_on_houses(houses_map: Dict[str, Any]) -> List[Dict]:
    """Extracts the sign on each house cusp, using the abbreviation map."""
    features = []
    for house_id, house_info in houses_map.items():
        # Get the sign abbreviation (e.g., 'ari')
        sign_abbr = house_info.get("zodiac_sign", {}).get("id")
        if not sign_abbr:
            continue
        
        # Use the map to get the full name (e.g., 'aries')
        sign_full_name = SIGN_ABBREVIATION_MAP.get(sign_abbr.lower())
        if not sign_full_name:
            continue
        
        numeric_house_id = house_id.replace('_house', '')
        numeric_house_id = HOUSE_ABBREVIATION_MAP.get(numeric_house_id)
        
        features.append({
            "display": f"{sign_full_name.capitalize()} on {house_info.get('name')} Cusp",
            "components": [{"type": "zodiac_sign", "id": sign_full_name}, {"type": "house", "id": numeric_house_id}]
        })
    return features

def _extract_aspects(aspect_list: List[Dict[str, Any]], points_map: Dict[str, Any]) -> List[Dict]:
    """Extracts major aspects between points."""
    features = []
    all_point_ids = PLANET_IDS.union(ASTEROID_IDS)

    for aspect in aspect_list:
        p1_id = aspect.get("point_1_id")
        p2_id = aspect.get("point_2_id")
        aspect_id = aspect.get("aspect_id")

        if not (p1_id and p2_id and aspect_id):
            continue

        if aspect_id in {"conjunction", "square", "trine", "opposition", "sextile"}:
            if p1_id in all_point_ids and p2_id in all_point_ids:
                p1_display = points_map.get(p1_id, {}).get("name", p1_id)
                p2_display = points_map.get(p2_id, {}).get("name", p2_id)
                p1_type = "asteroid" if p1_id in ASTEROID_IDS else "planet"
                p2_type = "asteroid" if p2_id in ASTEROID_IDS else "planet"
                
                features.append({
                    "display": f"{p1_display} {aspect_id.capitalize()} {p2_display}",
                    "components": [
                        {"type": p1_type, "id": p1_id},
                        {"type": "dynamic", "id": aspect_id},
                        {"type": p2_type, "id": p2_id}
                    ]
                })
    return features