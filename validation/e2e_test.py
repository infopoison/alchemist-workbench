# e2e_test.py

import httpx
import asyncio
import json
from typing import List, Dict, Any, Optional


# =============================================================================
# 1. DEFINE CORE INPUTS FOR THE TEST
# =============================================================================

# Define a sample birth data object, matching the BirthDataInput schema.
SAMPLE_BIRTH_DATA = {
    "name": "RV",
    "city": "Santiago",
    "date": "1970-08-06",
    "time": "17:41:00",
    "latitude": 32.779,
    "longitude": -96.808,
    "timezone": "America/Chicago"
}

SAMPLE_BIRTH_DATA = {
    "name": "Creator",
    "city": "Dallas",
    "date": "1995-05-18",
    "time": "00:00:00",
    "latitude": -33.447,
    "longitude": -70.673,
    "timezone": "America/Santiago"
}

# Define the list of all life areas for testing the new endpoint.
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

# Define base URLs for the running services.
CALCULATION_SERVICE_URL = "http://localhost:8002"
INTERPRETATION_SERVICE_URL = "http://localhost:8003"


# =============================================================================
# 2. HELPER FUNCTIONS FOR USER SELECTION
# =============================================================================

def select_life_area_for_e2e_test(life_areas: List[str]) -> Optional[str]:
    """Prompts the user to choose a life area for the E2E test."""
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
    Runs the end-to-end test simulation for the Alchemical Workbench API,
    now incorporating user selection for placements and valences.
    """
    print("🚀 Starting Alchemical Workbench End-to-End Test (Interactive Workflow)...\n")
    
    selected_life_area = select_life_area_for_e2e_test(LIFE_AREAS_FOR_SELECTION)
    if not selected_life_area:
        print("Test aborted by user.")
        return
    print(f"-> User selected life area for testing: '{selected_life_area}'\n")

    natal_chart_for_placements = None
    relevant_placements = []
    chosen_placement_for_valence = None
    chosen_valence = None
    valences = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        # ---------------------------------------------------------------------
        # STAGE 1: Call Calculation Service to get the full natal chart
        # ---------------------------------------------------------------------
        print("--- [Stage 1/6] Simulating Chart Calculation ---")
        try:
            print(f"-> Sending birth data to Calculation Service at {CALCULATION_SERVICE_URL}/chart...")
            calc_response = await client.post(f"{CALCULATION_SERVICE_URL}/chart", json=SAMPLE_BIRTH_DATA)
            calc_response.raise_for_status()
            natal_chart_for_placements = calc_response.json()
            print('Natal Chart', natal_chart_for_placements)
            print(f"✅ SUCCESS: Calculation Service responded with status {calc_response.status_code}.")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Calculation Service returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred during chart calculation: {e}")
            return

        # ---------------------------------------------------------------------
        # STAGE 2: Find relevant placements and get user selection
        # ---------------------------------------------------------------------
        print(f"\n--- [Stage 2/6] Finding Relevant Placements for '{selected_life_area}' ---")
        try:
            print(f"-> Requesting relevant placements from Interpretation Service at {INTERPRETATION_SERVICE_URL}/life-areas/find-relevant-placements...")
            
            relevant_placements_response = await client.post(
                f"{INTERPRETATION_SERVICE_URL}/life-areas/find-relevant-placements?life_area={selected_life_area}",
                json=SAMPLE_BIRTH_DATA
            )
            relevant_placements_response.raise_for_status()
            response_data = relevant_placements_response.json()
            
            print(f"--- RAW RESPONSE FROM LLM ---\n{json.dumps(response_data, indent=2)}\n-----------------------------")
            
            relevant_placements = response_data.get('component_placements', [])
            if not relevant_placements:
                print(f"❌ ERROR: No relevant placements returned for '{selected_life_area}'. Halting.")
                return
            
            # NEW: Prompt user to select a placement
            chosen_placement_for_valence = select_placement_for_analysis(relevant_placements)
            if not chosen_placement_for_valence:
                print("Test aborted by user.")
                return
            print(f"   -> User selected placement for further analysis: '{chosen_placement_for_valence.get('display')}'")

        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Interpretation Service (/life-areas) returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred while finding relevant placements: {e}")
            return
        
        # ---------------------------------------------------------------------
        # STAGE 3: Call Interpretation Service for Valences
        # ---------------------------------------------------------------------
        print("\n--- [Stage 3/6] Simulating Valence Generation ---")
        print(f"   -> Using the selected placement for valence generation: '{chosen_placement_for_valence.get('display')}'")

        chosen_placement_components = chosen_placement_for_valence.get("components", [])
        valence_payload = {
            "components": chosen_placement_components, 
            "birth_data": SAMPLE_BIRTH_DATA 
        }
        
        try:
            print(f"-> Sending selected placement to Interpretation Service at {INTERPRETATION_SERVICE_URL}/interpret/valences...")
            valence_response = await client.post(f"{INTERPRETATION_SERVICE_URL}/interpret/valences", json=valence_payload)
            valence_response.raise_for_status()
            print(f"✅ SUCCESS: Interpretation Service (Valence) responded with status {valence_response.status_code}.")
            
            valences = valence_response.json().get("valences", [])
            if not valences:
                print("❌ ERROR: Valence response contained no valences to choose from. Halting.")
                return
            
        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Interpretation Service (Valence) returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred while processing the valence request: {e}")
            return

        # ---------------------------------------------------------------------
        # STAGE 4: Display all generated valences and get user selection
        # ---------------------------------------------------------------------
        print(f"\n--- [Stage 4/6] Displaying All Generated Valences & Simulating Selection ---")
        
        # NEW: Prompt user to select a valence
        chosen_valence = select_valence_to_continue(valences)
        if not chosen_valence:
            print("Test aborted by user.")
            return
        
        print(f"\n-> User selected the following valence to continue: '{chosen_valence.get('archetype')}'")

    print("\n\n✨ End-to-End Test Simulation Complete. ✨")

# =============================================================================
# 4. RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    asyncio.run(main())
