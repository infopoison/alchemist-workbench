# llm_test.py

import httpx
import asyncio
import json
from typing import List, Dict, Any, Optional

# =============================================================================
# 1. CONFIGURATION
# =============================================================================

INTERPRETATION_SERVICE_URL = "http://localhost:8003"
CHART_DATA_FILE = "test_chart_RV.json" # This file contains the full natal chart data from Calculation Service

# Define a mock BirthDataInput for requests to the Interpretation Service
MOCK_BIRTH_DATA = {
    "name": "Test User",
    "city": "Los Angeles",
    "date": "1990-10-28",
    "time": "09:30:00",
    "latitude": 34.0522,
    "longitude": -118.2437,
    "timezone": "America/Los_Angeles"
}

# Life areas for the user to choose from in the CLI
LIFE_AREAS_FOR_SELECTION = [
    "Relationships", "Career", "Self", "Health and Wellness", 
    "Creativity", "Finance", "Family", "Spirituality", "Communication"
]

# Life areas for manifestations (these map to schemas' Literal types)
MANIFESTATION_LIFE_AREAS = [
    "psychological_patterns", "relational_dynamics", "occupational_arenas",
    "creative_expression", "health_and_wellness", "financial_style", "leisure_and_hobbies"
]


# =============================================================================
# 2. DATA EXTRACTION FUNCTIONS (Used internally for providing chart context to LLM)
# These functions help format the `test_chart_RV.json` data for the prompt
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

def extract_all_natal_placements_for_llm_prompt(chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts and formats all relevant natal chart placements (planets, houses, aspects, nodes, angles)
    from the calculation service response into a list suitable for the LLM prompt's
    'User's Natal Chart Placements' section.
    This provides the LLM with the context of the user's full chart.
    """
    all_placements = []

    # Planets in Signs
    if 'planets' in chart_data:
        for p_id, p_info in chart_data['planets'].items():
            all_placements.append({
                "type": "planet_in_sign",
                "id": p_id,
                "label": f"{p_info.get('name')} in {p_info.get('sign_name')}"
            })
            # Also add planet in house if available
            if p_info.get('house_number'):
                all_placements.append({
                    "type": "planet_in_house",
                    "id": p_id, # Re-using planet id for simplicity, could be more complex
                    "label": f"{p_info.get('name')} in House {p_info.get('house_number')}"
                })

    # House Cusps (Signs on Houses)
    if 'houses' in chart_data:
        for h_num, h_info in chart_data['houses'].items():
            all_placements.append({
                "type": "sign_on_house",
                "id": f"house_{h_num}",
                "label": f"House {h_num} with {h_info.get('sign_name')} on Cusp"
            })

    # Aspects
    if 'aspects' in chart_data:
        for aspect_category in chart_data['aspects'].values(): # Iterate through categories like 'planet_aspect_planet', etc.
            for aspect in aspect_category:
                p1_name = aspect.get('point_1_name')
                p2_name = aspect.get('point_2_name')
                aspect_name = aspect.get('aspect_name')
                # A robust solution would derive the 'type' and 'id' from aspect components
                # For this demo, we'll simplify how we present it to the LLM.
                all_placements.append({
                    "type": "aspect",
                    "id": f"{p1_name.lower()}_{aspect_name.lower()}_{p2_name.lower()}",
                    "label": f"{p1_name} {aspect_name} {p2_name}"
                })

    # Lunar Nodes
    if 'lunar_nodes' in chart_data:
        for node in chart_data['lunar_nodes']:
            all_placements.append({
                "type": "node_in_sign",
                "id": node['id'],
                "label": f"{node['name']} in {node['sign_name']}"
            })
            if node.get('house_number'):
                all_placements.append({
                    "type": "node_in_house",
                    "id": node['id'],
                    "label": f"{node['name']} in House {node['house_number']}"
                })
    
    # Angles (Ascendant, Midheaven, etc.)
    if 'angles' in chart_data:
        for angle in chart_data['angles']:
            all_placements.append({
                "type": "angle_in_sign",
                "id": angle['id'],
                "label": f"{angle['name']} in {angle['sign_name']}"
            })

    return all_placements


# =============================================================================
# 3. INTERACTIVE MENU FUNCTIONS (Updated for new workflow)
# =============================================================================

def select_life_area(life_areas: List[str]) -> Optional[str]:
    """Prompts the user to choose a life area."""
    print("\n--- [Step 1/4] Please choose a life area to reflect on ---")
    for i, area in enumerate(life_areas):
        print(f"  [{i + 1}] {area}")

    while True:
        try:
            choice = int(input("\nEnter the number of your choice: "))
            if 1 <= choice <= len(life_areas):
                return life_areas[choice - 1]
            else:
                print("   -> Invalid number. Please try again.")
        except ValueError:
            print("   -> Please enter a valid number.")

def select_placement_from_relevant(placements: List[Dict[str, Any]]) -> Optional[Dict]:
    """
    Displays a list of relevant astrological placements identified by the LLM
    and prompts the user to select one.
    """
    print("\n--- [Step 2/4] Here are the most relevant placements. Please choose one to explore: ---")
    if not placements:
        print("   -> No relevant placements were returned from the service.")
        return None

    # Format for display: e.g., "planet:venus", "house:house_7"
    display_placements = [f"{p['type'].replace('_', ' ').title()}: {p['id'].replace('_', ' ').title()}" for p in placements]

    for i, display_text in enumerate(display_placements):
        print(f"  [{i + 1}] {display_text}")

    while True:
        try:
            choice = int(input("\nEnter the number of your choice: "))
            if 1 <= choice <= len(placements):
                return placements[choice - 1]
            else:
                print("   -> Invalid number. Please try again.")
        except ValueError:
            print("   -> Please enter a valid number.")

def select_valence(valences: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Displays a list of generated valences and prompts the user to select one."""
    print("\n--- [Step 3/4] How is this energy expressing itself today? ---")
    if not valences:
        print("   -> No valences were returned from the service.")
        return None

    for i, valence in enumerate(valences):
        archetype = valence.get('archetype', 'No Archetype')
        description = valence.get('description', 'No description.')
        print(f"  [{i + 1}] {archetype}: \"{description}\"")

    while True:
        try:
            choice = int(input("\nPlease select the valence that feels most true right now (1-{}): ".format(len(valences))))
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
    print("🚀 Starting Alchemical Workbench LLM Interpretation Test (New Workflow)...\n")

    full_chart_response = load_full_chart_object(CHART_DATA_FILE)
    if not full_chart_response:
        return

    # Extract birth data from the loaded chart, or use MOCK_BIRTH_DATA if the file doesn't have it
    birth_data = full_chart_response.get("birth_data", MOCK_BIRTH_DATA)
    # Ensure birth_data has all required fields for the API call (even if mocked)
    birth_data_api_format = {
        "name": birth_data.get("name", "User"),
        "city": birth_data.get("city", "Los Angeles"),
        "date": birth_data.get("date", "1990-10-28"),
        "time": birth_data.get("time", "09:30:00"),
        "latitude": birth_data.get("latitude", 34.0522),
        "longitude": birth_data.get("longitude", -118.2437),
        "timezone": birth_data.get("timezone", "America/Los_Angeles")
    }

    # Extract all chart placements to pass to the /find-relevant-placements endpoint
    natal_chart_placements_for_llm = extract_all_natal_placements_for_llm_prompt(full_chart_response)
    if not natal_chart_placements_for_llm:
        print("❌ ERROR: No astrological placements could be extracted from the chart data to provide context to the LLM.")
        return

    async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout for LLM calls
        # Step 1: User selects a life area
        chosen_life_area = select_life_area(LIFE_AREAS_FOR_SELECTION)
        if not chosen_life_area:
            return

        # Step 2: Call /life-areas/find-relevant-placements
        relevant_placements_for_selection = []
        try:
            print(f"\n-> Requesting relevant placements for '{chosen_life_area}' from Interpretation Service...")
            
            # Note: The 'life_area' parameter is a query parameter, 'birth_data' is in the body.
            # The LLM receives the full 'natal_chart_placements_for_llm' as context within the prompt
            # generated by prompt_assembler.
            find_placements_payload = birth_data_api_format # Send the birth data directly as the body
            
            find_placements_response = await client.post(
                f"{INTERPRETATION_SERVICE_URL}/life-areas/find-relevant-placements?life_area={chosen_life_area}",
                json=find_placements_payload
            )
            find_placements_response.raise_for_status()
            relevant_placements_for_selection = find_placements_response.json()
            print(f"✅ SUCCESS: Received {len(relevant_placements_for_selection)} relevant placements.")
        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Service returned a {e.response.status_code} status for relevant placements.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred while finding relevant placements: {e}")
            return

        # Step 3: User chooses a specific placement from the relevant list
        chosen_placement_for_valence = select_placement_from_relevant(relevant_placements_for_selection)
        if not chosen_placement_for_valence:
            return
        
        # Step 4: Call /interpret/valences for the chosen placement
        valence_payload = {
            "components": [chosen_placement_for_valence], # This must be a list of ComponentInput
            "birth_data": birth_data_api_format # Use the properly formatted birth data
        }
        valences = []
        try:
            print(f"\n-> Requesting valences for '{chosen_placement_for_valence['id']}'...")
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

        # Step 5: User selects a valence
        chosen_valence = select_valence(valences)
        if not chosen_valence:
            return

        # Step 6: Generate manifestations for all specified life areas
        print("\n--- [Step 4/4] Generating manifestations for all life areas ---")
        for area in MANIFESTATION_LIFE_AREAS:
            manifestation_payload = {
                "components": [chosen_placement_for_valence],
                "chosen_valence": chosen_valence,
                "life_area": area,
                "birth_data": birth_data_api_format
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
                        
                        # Check all possible name keys before defaulting to "Unknown".
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