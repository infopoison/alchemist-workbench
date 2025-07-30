# llm_test.py

import httpx
import asyncio
import json
from typing import List, Dict, Any, Optional

# =============================================================================
# 1. CONFIGURATION
# =============================================================================

INTERPRETATION_SERVICE_URL = "http://localhost:8003"
CHART_DATA_FILE = "test_chart_RV.json" # Path to the stored natal chart JSON file

# Define the list of all life areas for testing.
LIFE_AREAS_FOR_SELECTION = [
    "Relationships",
    "Career",
    "Self",
    "Health and Wellness",
    "Creativity",
    "Finance",
    "Family",
    "Spirituality",
    "Communication"
]

# =============================================================================
# 2. HELPER FUNCTIONS
# =============================================================================

def load_birth_data_from_chart_file(filename: str) -> Optional[Dict[str, Any]]:
    """
    Loads a full natal chart from a JSON file and extracts the birth data
    from the 'subject' key, formatting it for API consumption.
    """
    try:
        with open(filename, 'r') as f:
            print(f"-> Loading full natal chart from '{filename}'...")
            full_chart = json.load(f)

        # The API endpoints expect a birth_data object. We extract this from
        # the 'subject' field of the stored chart.
        if 'subject' in full_chart:
            subject_data = full_chart['subject']
            
            # Construct the birth_data payload required by the Interpretation Service.
            # We add default 'name' and 'city' if they aren't in the 'subject' object.
            birth_data = {
                "name": subject_data.get("name", "RV"),
                "city": subject_data.get("city", "Santiago"),
                "date": subject_data.get("date"),
                "time": subject_data.get("time"),
                "latitude": subject_data.get("latitude"),
                "longitude": subject_data.get("longitude"),
                "timezone": subject_data.get("timezone")
            }
            
            # Quick validation to ensure critical fields were found.
            required_keys = ["date", "time", "latitude", "longitude", "timezone"]
            if not all(key in birth_data and birth_data[key] is not None for key in required_keys):
                print(f"❌ ERROR: The 'subject' object in '{filename}' is missing required data.")
                return None
            
            print("✅ SUCCESS: Extracted birth data from the chart file.")
            return birth_data
        else:
            print(f"❌ ERROR: Could not find the 'subject' key in '{filename}'.")
            return None

    except FileNotFoundError:
        print(f"❌ ERROR: The chart data file '{filename}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"❌ ERROR: Failed to parse '{filename}'. Please ensure it is valid JSON.")
        return None
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred while loading the file: {e}")
        return None

def select_life_area_for_test(life_areas: List[str]) -> Optional[str]:
    """Prompts the user to choose a life area for the test."""
    print("\n--- [Test Setup] Please choose a life area for the test run ---")
    for i, area in enumerate(life_areas):
        print(f"  [{i + 1}] {area}")

    while True:
        try:
            choice = input("\nEnter the number of your choice (or 'q' to quit): ").strip().lower()
            if choice == 'q':
                return None
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(life_areas):
                return life_areas[choice_idx]
            else:
                print("   -> Invalid number. Please try again.")
        except ValueError:
            print("   -> Please enter a valid number or 'q'.")

def select_placement_for_analysis(placements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Prompts the user to choose a relevant placement for analysis."""
    print("\n--- Please choose a relevant placement for analysis ---")
    formatted_placements = [p.get("display", "Unknown Placement") for p in placements]
    for i, placement_display in enumerate(formatted_placements):
        print(f"  [{i + 1}] {placement_display}")

    while True:
        try:
            choice = input("\nEnter the number of your choice (or 'q' to quit): ").strip().lower()
            if choice == 'q':
                return None
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(placements):
                return placements[choice_idx]
            else:
                print("   -> Invalid number. Please try again.")
        except ValueError:
            print("   -> Please enter a valid number or 'q'.")

def select_valence_to_continue(valences: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Prompts the user to choose a valence to continue the test."""
    print("\n--- Please choose a valence to continue ---")
    for i, valence in enumerate(valences):
        print(f"  [{i+1}] {valence.get('archetype', 'N/A')}: {valence.get('description', 'No description.')}")
    
    while True:
        try:
            choice = input("\nEnter the number of your choice (or 'q' to quit): ").strip().lower()
            if choice == 'q':
                return None
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(valences):
                return valences[choice_idx]
            else:
                print("   -> Invalid number. Please try again.")
        except ValueError:
            print("   -> Please enter a valid number or 'q'.")

# =============================================================================
# 3. MAIN ASYNCHRONOUS TEST FUNCTION
# =============================================================================

async def main():
    """
    Runs the end-to-end interpretation test using a stored natal chart JSON,
    mirroring the interactive workflow of e2e_test.py.
    """
    print("🚀 Starting Alchemical Workbench Interpretation Test (from stored JSON)...\n")
    
    # STAGE 1: Load Birth Data from the local JSON file.
    # This replaces the call to the Calculation Service.
    print("--- [Stage 1/4] Loading Birth Data from File ---")
    birth_data_for_api = load_birth_data_from_chart_file(CHART_DATA_FILE)
    if not birth_data_for_api:
        print("Test aborted. Could not load valid birth data from the file.")
        return

    # Prompt user to select a life area to test.
    selected_life_area = select_life_area_for_test(LIFE_AREAS_FOR_SELECTION)
    if not selected_life_area:
        print("Test aborted by user.")
        return
    print(f"-> User selected life area for testing: '{selected_life_area}'\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # ---------------------------------------------------------------------
        # STAGE 2: Find relevant placements and get user selection.
        # ---------------------------------------------------------------------
        print(f"--- [Stage 2/4] Finding Relevant Placements for '{selected_life_area}' ---")
        relevant_placements = []
        chosen_placement_for_valence = None
        try:
            print(f"-> Requesting relevant placements from Interpretation Service...")
            
            relevant_placements_response = await client.post(
                f"{INTERPRETATION_SERVICE_URL}/life-areas/find-relevant-placements?life_area={selected_life_area}",
                json=birth_data_for_api  # Use the data loaded from the file
            )
            relevant_placements_response.raise_for_status()
            response_data = relevant_placements_response.json()
            
            relevant_placements = response_data.get('component_placements', [])
            if not relevant_placements:
                print(f"❌ ERROR: No relevant placements were returned for '{selected_life_area}'. Halting.")
                return
            
            # Prompt user to select a placement from the returned list.
            chosen_placement_for_valence = select_placement_for_analysis(relevant_placements)
            if not chosen_placement_for_valence:
                print("Test aborted by user.")
                return
            print(f"   -> User selected placement for analysis: '{chosen_placement_for_valence.get('display')}'")

        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Interpretation Service returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred while finding relevant placements: {e}")
            return
        
        # ---------------------------------------------------------------------
        # STAGE 3: Call Interpretation Service for Valences.
        # ---------------------------------------------------------------------
        print("\n--- [Stage 3/4] Simulating Valence Generation ---")
        valences = []
        try:
            valence_payload = {
                "components": chosen_placement_for_valence.get("components", []), 
                "birth_data": birth_data_for_api 
            }
            
            print(f"-> Sending selected placement to Interpretation Service for valences...")
            valence_response = await client.post(f"{INTERPRETATION_SERVICE_URL}/interpret/valences", json=valence_payload)
            valence_response.raise_for_status()
            
            valences = valence_response.json().get("valences", [])
            if not valences:
                print("❌ ERROR: Response contained no valences to choose from. Halting.")
                return
            print(f"✅ SUCCESS: Interpretation Service (Valence) responded with status {valence_response.status_code}.")

        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Interpretation Service (Valence) returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred during the valence request: {e}")
            return

        # ---------------------------------------------------------------------
        # STAGE 4: Display generated valences and get user selection.
        # ---------------------------------------------------------------------
        print(f"\n--- [Stage 4/4] Displaying Generated Valences & Simulating Selection ---")
        
        chosen_valence = select_valence_to_continue(valences)
        if not chosen_valence:
            print("Test aborted by user.")
            return
        
        print(f"\n-> User selected the following valence to continue: '{chosen_valence.get('archetype')}'")

    print("\n\n✨ Interpretation Test Simulation Complete. ✨")

# =============================================================================
# 4. RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    asyncio.run(main())