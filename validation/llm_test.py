# llm_test.py

import httpx
import asyncio
import json
from typing import List, Dict, Any, Optional

# =============================================================================
# 1. CONFIGURATION
# =============================================================================

INTERPRETATION_SERVICE_URL = "http://localhost:8003"
CHART_DATA_FILE = "test_chart.json"
LIFE_AREAS = [
    "psychological_patterns", "relational_dynamics", "occupational_arenas",
    "creative_expression", "health_and_wellness", "financial_style", "leisure_and_hobbies"
]

# Define which celestial points are planets, nodes, or asteroids for extraction logic
PLANET_IDS = {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"}
NODE_IDS = {"mean_node", "mean_south_node"}
ASTEROID_IDS = {"chiron", "mean_lilith"}

# Map 3-letter sign abbreviations from chart data to full IDs for the API.
SIGN_ABBREVIATION_MAP = {
    "ari": "aries", "tau": "taurus", "gem": "gemini", "can": "cancer",
    "leo": "leo", "vir": "virgo", "lib": "libra", "sco": "scorpio",
    "sag": "sagittarius", "cap": "capricorn", "aqu": "aquarius", "pis": "pisces"
}

# =============================================================================
# 2. DATA EXTRACTION FUNCTIONS
# =============================================================================

def load_full_chart_object(filename: str) -> Optional[Dict[str, Any]]:
    """Loads the entire stored chart object from a JSON file."""
    try:
        with open(filename, 'r') as f:
            print(f"-> Loading stored chart data from '{filename}'...")
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ ERROR: Could not load or parse '{filename}'. Please ensure it exists and is valid JSON.")
        print(f"   Details: {e}")
        return None

def extract_planets_in_signs(chart_data: Dict[str, Any]) -> List[Dict]:
    """Extracts all Planet-in-Sign combinations."""
    features = []
    for planet_id in PLANET_IDS:
        if planet_id in chart_data:
            planet_info = chart_data[planet_id]
            sign_abbr = planet_info.get("sign", "").lower()
            sign_id = SIGN_ABBREVIATION_MAP.get(sign_abbr) # Translate abbreviation
            if sign_id:
                features.append({
                    "display": f"{planet_info.get('name')} in {sign_id.capitalize()}",
                    "components": [
                        {"type": "planet", "id": planet_id},
                        {"type": "zodiac_sign", "id": sign_id}
                    ]
                })
    return features

def extract_planets_in_houses(chart_data: Dict[str, Any]) -> List[Dict]:
    """Extracts all Planet-in-House combinations."""
    features = []
    for planet_id in PLANET_IDS:
        if planet_id in chart_data:
            planet_info = chart_data[planet_id]
            house_name = planet_info.get("house", "")
            if house_name:
                house_id = house_name.lower().replace('_house', '')
                features.append({
                    "display": f"{planet_info.get('name')} in {house_name.replace('_', ' ')}",
                    "components": [
                        {"type": "planet", "id": planet_id},
                        {"type": "house", "id": house_id}
                    ]
                })
    return features

def extract_signs_on_houses(chart_data: Dict[str, Any]) -> List[Dict]:
    """Extracts all Sign-on-House-Cusp combinations."""
    features = []
    for i in range(1, 13):
        house_key = f"{_get_ordinal(i)}_house"
        if house_key in chart_data:
            house_info = chart_data[house_key]
            sign_abbr = house_info.get("sign", "").lower()
            sign_id = SIGN_ABBREVIATION_MAP.get(sign_abbr) # Translate abbreviation
            if sign_id:
                features.append({
                    "display": f"{sign_id.capitalize()} on {house_info.get('name').replace('_', ' ')} Cusp",
                    "components": [
                        {"type": "zodiac_sign", "id": sign_id},
                        {"type": "house", "id": str(i)}
                    ]
                })
    return features

def extract_nodes_in_signs(chart_data: Dict[str, Any]) -> List[Dict]:
    """Extracts all Node-in-Sign combinations."""
    features = []
    for node_id in NODE_IDS:
        if node_id in chart_data:
            node_info = chart_data[node_id]
            sign_abbr = node_info.get("sign", "").lower()
            sign_id = SIGN_ABBREVIATION_MAP.get(sign_abbr) # Translate abbreviation
            if sign_id:
                features.append({
                    "display": f"{node_info.get('name').replace('_', ' ')} in {sign_id.capitalize()}",
                    "components": [
                        {"type": "node", "id": node_id},
                        {"type": "zodiac_sign", "id": sign_id}
                    ]
                })
    return features

def extract_nodes_in_houses(chart_data: Dict[str, Any]) -> List[Dict]:
    """Extracts all Node-in-House combinations."""
    features = []
    for node_id in NODE_IDS:
        if node_id in chart_data:
            node_info = chart_data[node_id]
            house_name = node_info.get("house", "")
            if house_name:
                house_id = house_name.lower().replace('_house', '')
                features.append({
                    "display": f"{node_info.get('name').replace('_', ' ')} in {house_name.replace('_', ' ')}",
                    "components": [
                        {"type": "node", "id": node_id},
                        {"type": "house", "id": house_id}
                    ]
                })
    return features

def extract_asteroids_in_signs(chart_data: Dict[str, Any]) -> List[Dict]:
    """Extracts all Asteroid-in-Sign combinations."""
    features = []
    for asteroid_id in ASTEROID_IDS:
        if asteroid_id in chart_data:
            asteroid_info = chart_data[asteroid_id]
            sign_abbr = asteroid_info.get("sign", "").lower()
            sign_id = SIGN_ABBREVIATION_MAP.get(sign_abbr) # Translate abbreviation
            if sign_id:
                features.append({
                    "display": f"{asteroid_info.get('name').replace('_', ' ').title()} in {sign_id.capitalize()}",
                    "components": [
                        {"type": "asteroid", "id": asteroid_id},
                        {"type": "zodiac_sign", "id": sign_id}
                    ]
                })
    return features

def extract_asteroids_in_houses(chart_data: Dict[str, Any]) -> List[Dict]:
    """Extracts all Asteroid-in-House combinations."""
    features = []
    for asteroid_id in ASTEROID_IDS:
        if asteroid_id in chart_data:
            asteroid_info = chart_data[asteroid_id]
            house_name = asteroid_info.get("house", "")
            if house_name:
                house_id = house_name.lower().replace('_house', '')
                features.append({
                    "display": f"{asteroid_info.get('name').replace('_', ' ').title()} in {house_name.replace('_', ' ')}",
                    "components": [
                        {"type": "asteroid", "id": asteroid_id},
                        {"type": "house", "id": house_id}
                    ]
                })
    return features

def extract_aspects(aspect_list: List[Dict[str, Any]]) -> List[Dict]:
    """Formats aspects for the selection menu, now including asteroids."""
    features = []
    all_points = PLANET_IDS.union(ASTEROID_IDS)
    
    for aspect in aspect_list:
        p1_name = aspect.get("p1_name", "N/A").lower().replace("_", "")
        p2_name = aspect.get("p2_name", "N/A").lower().replace("_", "")
        aspect_id = aspect.get("aspect", "N/A").lower()
        
        if aspect_id in {"conjunction", "square", "trine", "opposition", "sextile"}:
            if p1_name in all_points and p2_name in all_points:
                p1_type = "asteroid" if p1_name in ASTEROID_IDS else "planet"
                p2_type = "asteroid" if p2_name in ASTEROID_IDS else "planet"

                features.append({
                    "display": f"{p1_name.capitalize()} {aspect_id.capitalize()} {p2_name.capitalize()}",
                    "components": [
                        {"type": p1_type, "id": p1_name},
                        {"type": "dynamic", "id": aspect_id},
                        {"type": p2_type, "id": p2_name}
                    ]
                })
    return features

def _get_ordinal(n):
    """Helper to convert number to ordinal string (e.g., 1 -> first)."""
    ordinals = ["", "first", "second", "third", "fourth", "fifth", "sixth", 
                "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]
    return ordinals[n] if 0 < n < len(ordinals) else str(n)


# =============================================================================
# 3. INTERACTIVE MENU FUNCTIONS
# =============================================================================

def select_feature(chart_data: Dict[str, Any], aspect_list: List[Dict[str, Any]]) -> Optional[Dict]:
    """Displays a categorized menu of all testable features and prompts user selection."""
    print("\n--- [Step 1/3] Please select a feature to generate an interpretation for ---")
    
    feature_categories = {
        "Planets in Signs": extract_planets_in_signs(chart_data),
        "Planets in Houses": extract_planets_in_houses(chart_data),
        "Signs on House Cusps": extract_signs_on_houses(chart_data),
        "Nodes in Signs": extract_nodes_in_signs(chart_data),
        "Nodes in Houses": extract_nodes_in_houses(chart_data),
        "Asteroids in Signs": extract_asteroids_in_signs(chart_data),
        "Asteroids in Houses": extract_asteroids_in_houses(chart_data),
        "Notable Aspects": extract_aspects(aspect_list)
    }

    master_list = []
    for category, features in feature_categories.items():
        if features:
            print(f"\n--- {category} ---")
            for feature in features:
                master_list.append(feature)
                print(f"  [{len(master_list)}] {feature['display']}")

    if not master_list:
        print("❌ ERROR: No features could be extracted from the chart data.")
        return None

    while True:
        try:
            choice = int(input("\nEnter the number of your choice: "))
            if 1 <= choice <= len(master_list):
                return master_list[choice - 1]
            else:
                print("   -> Invalid number. Please try again.")
        except ValueError:
            print("   -> Please enter a valid number.")

def select_valence(valences: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Displays a list of generated valences and prompts the user to select one."""
    print("\n--- [Step 2/3] Please select a valence to explore further ---")
    if not valences:
        print("   -> No valences were returned from the service.")
        return None

    for i, valence in enumerate(valences):
        archetype = valence.get('archetype', 'No Archetype')
        description = valence.get('description', 'No description.')
        print(f"  [{i + 1}] {archetype}: \"{description}\"")

    while True:
        try:
            choice = int(input("\nEnter the number of your choice: "))
            if 1 <= choice <= len(valences):
                return valences[choice - 1]
            else:
                print("   -> Invalid number. Please try again.")
        except ValueError:
            print("   -> Please enter a valid number.")

# =============================================================================
# 4. MAIN ASYNCHRONOUS TEST FUNCTION
# =============================================================================

async def main():
    """Runs the interactive test for the interpretation service's LLM capabilities."""
    print("🚀 Starting Alchemical Workbench LLM Interpretation Test...\n")

    full_chart_object = load_full_chart_object(CHART_DATA_FILE)
    if not full_chart_object:
        return

    chart_data = full_chart_object.get("data", {})
    aspect_list = full_chart_object.get("aspects", [])

    if not chart_data:
        print("❌ ERROR: 'data' key not found in the chart JSON. Cannot proceed.")
        return

    selected_feature = select_feature(chart_data, aspect_list)
    if not selected_feature:
        return
        
    signature_components = selected_feature["components"]
    
    birth_data = {
        "name": chart_data.get("name"),
        "city": chart_data.get("city"),
        "date": f"{chart_data.get('year')}-{chart_data.get('month'):02d}-{chart_data.get('day'):02d}",
        "time": f"{chart_data.get('hour'):02d}:{chart_data.get('minute'):02d}:00",
        "latitude": chart_data.get("lat"),
        "longitude": chart_data.get("lng"),
        "timezone": chart_data.get("tz_str")
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        valence_payload = {"components": signature_components, "birth_data": birth_data}
        try:
            print(f"\n-> Requesting valences for '{selected_feature['display']}'...")
            valence_response = await client.post(f"{INTERPRETATION_SERVICE_URL}/interpret/valences", json=valence_payload)
            valence_response.raise_for_status()
            valences = valence_response.json().get("valences", [])
            print("✅ SUCCESS: Received valences.")
        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Interpretation Service returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred while requesting valences: {e}")
            return

        chosen_valence = select_valence(valences)
        if not chosen_valence:
            return

        print("\n--- [Step 3/3] Generating manifestations for all life areas ---")
        for area in LIFE_AREAS:
            manifestation_payload = {
                "components": signature_components,
                "chosen_valence": chosen_valence,
                "life_area": area,
                "birth_data": birth_data
            }
            try:
                print(f"\n-> Generating manifestations for life area: '{area}'...")
                manifest_response = await client.post(f"{INTERPRETATION_SERVICE_URL}/interpret/manifestations", json=manifestation_payload)
                manifest_response.raise_for_status()
                print(f"✅ SUCCESS: Received manifestations for '{area}'.")
                
                manifestations = manifest_response.json().get('manifestations', [])
                if manifestations:
                    for manifest in manifestations:
                        m_type = manifest.get('type', 'N/A').upper()
                        
                        # CORRECTION: Check all possible name keys before defaulting to "Unknown".
                        name_keys = [
                            'pattern_name', 'dynamic_name', 'arena_name', 
                            'expression_name', 'manifestation_name', 
                            'style_name', 'activity_name'
                        ]
                        m_name = 'Unknown'
                        for key in name_keys:
                            if key in manifest:
                                m_name = manifest[key]
                                break
                        
                        m_desc = manifest.get('description', 'No description provided.')
                        print(f"   [{m_type}] {m_name}: {m_desc}")
                else:
                    print("   -> No manifestations returned for this life area.")

            except httpx.HTTPStatusError as e:
                print(f"❌ ERROR on '{area}': Service returned {e.response.status_code}.")
            except (httpx.RequestError, json.JSONDecodeError) as e:
                print(f"❌ ERROR on '{area}': An issue occurred: {e}")

    print("\n\n✨ LLM Interpretation Test Complete. ✨")

# =============================================================================
# 5. RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    asyncio.run(main())
