# services/interpretation-service/app/placement_extractor.py

from typing import List, Dict, Any, Set
from collections import defaultdict


# =============================================================================
# 1. CONFIGURATION CONSTANTS
# =============================================================================
PLANET_IDS: Set[str] = {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"}
# Note: The calculation service now removes angles, but we keep the ID set here for clarity and potential future use.
ANGLE_IDS: Set[str] = {"ascendant", "imum_coeli", "descendant", "midheaven", "medium_coeli"} 
# Corrected 'mean_node' to 'north_node' to match potential future API versions.
NODE_IDS: Set[str] = {"north_node", "south_node", "mean_node", "true_node", "mean_south_node", "true_south_node"}
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

STELLIUM_PLANET_COUNT = 3
STELLIUM_ORB = 20.0 # Max degrees between the first and last planet in the group

# =============================================================================
# 2. MAIN ORCHESTRATION FUNCTION
# =============================================================================

def extract_all_placement_objects(full_chart_object: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Orchestrates the extraction of all placements from the chart object.
    
    This function now checks for a 'chart_type' flag to determine whether
    to extract house-based placements, making it safe for "no time" charts.
    """

    # 1. Extract data from the chart object. 'houses' may be None.
    celestial_points = full_chart_object.get("celestial_points", [])
    houses = full_chart_object.get("houses") # Do not provide a default, so we can check for None
    aspect_list = full_chart_object.get("aspects", [])
    
    # 2. Check the chart_type flag to determine the workflow.
    is_no_time_chart = full_chart_object.get("chart_type") == "no_time"

    # 3. Create a map of points for easy lookup. This is always needed.
    points_map = {p['id']: p for p in celestial_points}
    
    if not points_map:
        return []
        
    all_features = []
    
    # 4. Extract higher-order features first, like stelliums.
    all_features.extend(_extract_stelliums(points_map))

    # 5. These placements are time-agnostic and are always extracted.
    all_features.extend(_extract_points_in_signs(points_map))
    all_features.extend(_extract_aspects(aspect_list, points_map))

    # 6. Only extract house-based placements if it is a full chart with time.
    if not is_no_time_chart:
        print("-> Full chart detected. Extracting house-based placements.")
        
        if houses: 
            houses_map = {h['id']: h for h in houses}
            all_features.extend(_extract_signs_on_houses(houses_map))
        
        all_features.extend(_extract_points_in_houses(points_map))
    else:
        print("-> 'No time' chart detected. Skipping all house-based placement extraction.")

    # --- END OF MODIFIED SECTION ---
    
    return all_features

# =============================================================================
# 3. HELPER EXTRACTION FUNCTIONS (UNCHANGED)
# =============================================================================

def _extract_stelliums(points_map: Dict[str, Any]) -> List[Dict]:
    """
    Identifies and extracts stelliums from the chart.
    A stellium is defined as 3 or more planets in the same sign within a specified orb.
    """
    features = []
    planets_by_sign = defaultdict(list)

    for point_id, point_info in points_map.items():
        if point_id in PLANET_IDS:
            sign_id = point_info.get("zodiac_sign", {}).get("id")
            if sign_id:
                planets_by_sign[sign_id].append(point_info)

    # 2. Iterate through each sign that has planets
    for sign_id, planets_in_sign in planets_by_sign.items():
        # 3. Check if the sign meets the minimum planet count for a stellium
        if len(planets_in_sign) >= STELLIUM_PLANET_COUNT:
            # 4. Sort the planets by their longitude to find the first and last
            planets_in_sign.sort(key=lambda p: p['position_longitude'])
            
            first_planet = planets_in_sign[0]
            last_planet = planets_in_sign[-1]
            
            # 5. Calculate the orb between the first and last planet
            orb = last_planet['position_longitude'] - first_planet['position_longitude']
            
            # 6. If the orb is within the allowed range, we have a stellium
            if orb <= STELLIUM_ORB:
                sign_full_name = SIGN_ABBREVIATION_MAP.get(sign_id.lower(), sign_id)
                planet_names = ", ".join(p['name'] for p in planets_in_sign)
                
                # Build the component list for the prompt assembler
                stellium_components = [
                    {"type": "complex_configurations", "id": "stellium"}, # MUST BE PLURAL
                    {"type": "zodiac_sign", "id": sign_full_name}
                ]
                stellium_components.extend([
                    {"type": "planet", "id": p['id']} for p in planets_in_sign
                ])
                features.append({
                    "display": f"Stellium in {sign_full_name.capitalize()} ({planet_names})",
                    "components": stellium_components
                })
                print(f"-> Stellium detected in {sign_full_name.capitalize()} with orb {orb:.2f}")

    return features


def _extract_points_in_signs(points_map: Dict[str, Any]) -> List[Dict]:
    """Extracts all celestial points in signs, using the abbreviation map."""
    features = []
    for point_id, point_info in points_map.items():
        sign_abbr = point_info.get("zodiac_sign", {}).get("id")
        if not sign_abbr:
            continue
            
        sign_full_name = SIGN_ABBREVIATION_MAP.get(sign_abbr.lower())
        if not sign_full_name:
            continue
        
        # Note: 'angle' type will not appear in "no time" charts as they are pre-filtered.
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
    Extracts all celestial points in houses, *excluding angles*.
    This function is now only called for full charts.
    """
    features = []
    for point_id, point_info in points_map.items():
        if point_id in ANGLE_IDS: 
            continue 

        # This check is now a redundant safety measure, but harmless.
        house_info = point_info.get("house")
        if not house_info:
            continue

        house_id = house_info.get("id")
        if not house_id:
            continue

        # e.g., 'fourth_house' -> 'fourth'
        numeric_house_key = house_id.replace('_house', '')
        # e.g., 'fourth' -> '4'
        numeric_house_id = HOUSE_ABBREVIATION_MAP.get(numeric_house_key) 
        
        point_type = "node" if point_id in NODE_IDS else \
                     "asteroid" if point_id in ASTEROID_IDS else \
                     "planet"

        features.append({
            "display": f"{point_info.get('name')} in {house_info.get('name')}",
            "components": [{"type": point_type, "id": point_id}, {"type": "house", "id": numeric_house_id}]
        })
    return features 

def _extract_signs_on_houses(houses_map: Dict[str, Any]) -> List[Dict]:
    """
    Extracts the sign on each house cusp.
    This function is now only called for full charts.
    """
    features = []
    for house_id, house_info in houses_map.items():
        sign_abbr = house_info.get("zodiac_sign", {}).get("id")
        if not sign_abbr:
            continue
        
        sign_full_name = SIGN_ABBREVIATION_MAP.get(sign_abbr.lower())
        if not sign_full_name:
            continue
        
        numeric_house_key = house_id.replace('_house', '')
        numeric_house_id = HOUSE_ABBREVIATION_MAP.get(numeric_house_key)
        
        features.append({
            "display": f"{sign_full_name.capitalize()} on {house_info.get('name')} Cusp",
            "components": [{"type": "zodiac_sign", "id": sign_full_name}, {"type": "house", "id": numeric_house_id}]
        })
    return features

def _extract_aspects(aspect_list: List[Dict[str, Any]], points_map: Dict[str, Any]) -> List[Dict]:
    """Extracts major aspects between points."""
    features = []
    # Note: Aspects to angles are pre-filtered by the calculation service for "no time" charts.
    all_point_ids = PLANET_IDS.union(ASTEROID_IDS)

    for aspect in aspect_list:
        p1_id = aspect.get("point_1_id")
        p2_id = aspect.get("point_2_id")
        aspect_id = aspect.get("aspect_id")

        if not (p1_id and p2_id and aspect_id):
            continue

        # Filter for major aspects and ensure both points are planets or asteroids.
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
