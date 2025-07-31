# llm_test.py

import httpx
import asyncio
import json
from typing import List, Dict, Any, Optional

# =============================================================================
# 1. CONFIGURATION
# =============================================================================

INTERPRETATION_SERVICE_URL = "http://localhost:8003"
CHART_DATA_FILE = "test_chart_creator.json" # Path to the stored natal chart JSON file

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

def load_full_chart_from_file(filename: str) -> Optional[Dict[str, Any]]:
    """
    Loads a full natal chart object from a JSON file.
    """
    try:
        with open(filename, 'r') as f:
            print(f"-> Loading full natal chart from '{filename}'...")
            full_chart = json.load(f)
        print("✅ SUCCESS: Loaded full chart object.")
        return full_chart
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
    print("--- [Stage 1/4] Loading Full Chart Data from File ---")
    full_chart_for_api = load_full_chart_from_file(CHART_DATA_FILE)
    if not full_chart_for_api:
        print("Test aborted. Could not load chart from file.")
        return

    selected_life_area = select_life_area_for_test(LIFE_AREAS_FOR_SELECTION)
    if not selected_life_area:
        print("Test aborted by user.")
        return
    print(f"-> User selected life area for testing: '{selected_life_area}'\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # ---------------------------------------------------------------------
        # STAGE 2: Find relevant placements.
        # ---------------------------------------------------------------------
        print(f"--- [Stage 2/4] Finding Relevant Placements for '{selected_life_area}' ---")
        try:
            print(f"-> Sending full chart object to Interpretation Service...")
            
            # --- CHANGED: Send the full chart object, not just birth data ---
            relevant_placements_response = await client.post(
                f"{INTERPRETATION_SERVICE_URL}/life-areas/find-relevant-placements?life_area={selected_life_area}",
                json=full_chart_for_api
            )
            relevant_placements_response.raise_for_status()
            response_data = relevant_placements_response.json()
            
            relevant_placements = response_data.get('component_placements', [])
            if not relevant_placements:
                print(f"❌ ERROR: No relevant placements were returned. Halting.")
                return
            
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
        try:
            # --- CHANGED: Extract the 'subject' from the full chart for this specific payload ---
            subject_data = full_chart_for_api.get("subject")
            birth_data_for_valence = {
                "name": "Anonymous", 
                "city": "Unknown", 
                "date": subject_data.get("date"),
                "time": subject_data.get("time"),
                "latitude": subject_data.get("latitude"),
                "longitude": subject_data.get("longitude"),
                "timezone": subject_data.get("timezone")
            }

            valence_payload = {
                "components": chosen_placement_for_valence.get("components", []), 
                "birth_data": birth_data_for_valence
            }
            
            print(f"-> Sending selected placement to Interpretation Service for valences...")
            valence_response = await client.post(f"{INTERPRETATION_SERVICE_URL}/interpret/valences", json=valence_payload)
            valence_response.raise_for_status()
            
            valences = valence_response.json().get("valences", [])
            if not valences:
                print("❌ ERROR: Response contained no valences. Halting.")
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