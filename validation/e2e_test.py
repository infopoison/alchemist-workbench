# e2e_test.py

import httpx
import asyncio
import json
import random # Still useful for other potential randomization if needed, but not for initial life area selection
from typing import List, Dict, Any, Optional 


# =============================================================================
# 1. DEFINE CORE INPUTS FOR THE TEST
# =============================================================================

# Define a sample birth data object, matching the BirthDataInput schema.
SAMPLE_BIRTH_DATA = {
    "name": "RV",
    "city": "Santiago",
    "date": "1970-08-06",
    "time": "00:00:00",
    "latitude": -33.447,
    "longitude": -70.673,
    "timezone": "America/Santiago"
}

# Define the list of all life areas for testing the new endpoint.
LIFE_AREAS_FOR_SELECTION = [ # Renamed for clarity, implies user selection
    "Relationships",
    "Career",
    "Self",
    "Health and Wellness",
    "Creativity",
    "Finance",
    "Family",
    "Spirituality", # Added for more options
    "Communication" # Added for more options
]

# Define the list of all life areas to generate manifestations for.
# This list is derived from the ManifestationRequest schema.
MANIFESTATION_LIFE_AREAS = [
    "psychological_patterns",
    "relational_dynamics",
    "occupational_arenas",
    "creative_expression",
    "health_and_wellness",
    "financial_style",
    "leisure_and_hobbies"
]

# Define base URLs for the running services.
CALCULATION_SERVICE_URL = "http://localhost:8002"
INTERPRETATION_SERVICE_URL = "http://localhost:8003"


# =============================================================================
# 2. HELPER FUNCTIONS
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


# =============================================================================
# 3. MAIN ASYNCHRONOUS TEST FUNCTION
# =============================================================================

async def main():
    """
    Runs the end-to-end test simulation for the Alchemical Workbench API,
    now incorporating the /life-areas/find-relevant-placements endpoint and user selection.
    """
    print("🚀 Starting Alchemical Workbench End-to-End Test (New Workflow)...\n")
    
    selected_life_area = select_life_area_for_e2e_test(LIFE_AREAS_FOR_SELECTION)
    if not selected_life_area:
        print("Test aborted by user.")
        return
    print(f"-> User selected life area for testing: '{selected_life_area}'\n")

    natal_chart_for_placements = None
    relevant_placements = []
    chosen_placement_for_valence = None
    chosen_valence = None

    async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout for LLM calls
        # ---------------------------------------------------------------------
        # STAGE 1: Call Calculation Service to get the full natal chart
        # This chart is needed to pass to the /life-areas/find-relevant-placements endpoint
        # ---------------------------------------------------------------------
        print("--- [Stage 1/6] Simulating Chart Calculation ---")
        try:
            print(f"-> Sending birth data to Calculation Service at {CALCULATION_SERVICE_URL}/chart...")
            calc_response = await client.post(f"{CALCULATION_SERVICE_URL}/chart", json=SAMPLE_BIRTH_DATA)
            calc_response.raise_for_status()
            natal_chart_for_placements = calc_response.json()
            print(f"✅ SUCCESS: Calculation Service responded with status {calc_response.status_code}.")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Calculation Service returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred during chart calculation: {e}")
            return

        # ---------------------------------------------------------------------
        # STAGE 2: Call Interpretation Service to find relevant placements for a life area
        # This is the new endpoint being tested.
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
            relevant_placements = response_data.get('component_placements', [])

            #print(f"✅ SUCCESS: Interpretation Service responded with status {relevant_placements_response.status_code}.")
            print(f"--- RAW RESPONSE FROM LLM ---\n{response_data}\n-----------------------------")
            if not relevant_placements:
                print(f"❌ ERROR: No relevant placements returned for '{selected_life_area}'. Halting.")
                return
            
            formatted_placements = [p.get("display", "Unknown Placement") for p in relevant_placements]
            print(f"   -> LLM suggested relevant placements: {formatted_placements}")

            # For the purpose of this automated test, we'll just pick the first one.
            chosen_placement_for_valence = relevant_placements[0]
            print(f"   -> Automatically selected the first relevant placement for further analysis: '{chosen_placement_for_valence.get('display')}'")

        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Interpretation Service (/life-areas/find-relevant-placements) returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            print(f"   Error Details: {e.response.text}") # Added for more detail
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred while finding relevant placements: {e}")
            return
        
        # ---------------------------------------------------------------------
        # STAGE 3: Call Interpretation Service for Valences (using the chosen relevant placement)
        # ---------------------------------------------------------------------
        print("\n--- [Stage 3/6] Simulating Valence Generation ---")
        print(f"   -> Using the automatically selected placement for valence generation: '{chosen_placement_for_valence.get('display')}'")

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
            
            # Programmatically select the first valence to simulate user choice
            chosen_valence = valences[0]
            print(f"\n--- [Stage 4/6] Displaying All Generated Valences & Simulating Selection ---")
            print("-> All valences received from the interpretation service:")
            for i, valence in enumerate(valences):
                print(f"  [{i+1}] {valence.get('archetype', 'N/A')}: {valence.get('description', 'No description.')}")

            # The script will still proceed by automatically selecting the first valence
            print(f"\n-> Automatically selecting the first valence to continue: '{chosen_valence.get('archetype')}'")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Interpretation Service (Valence) returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred while processing the valence request: {e}")
            return

        # ---------------------------------------------------------------------
        # STAGE 5: Loop and Call for Manifestations for the chosen valence
        # ---------------------------------------------------------------------
        """
        if chosen_valence and chosen_placement_for_valence:
            print("\n--- [Stage 5/6] Simulating Manifestation Generation for all Life Areas ---")
            for area in MANIFESTATION_LIFE_AREAS: # Use the specific list for manifestations
                manifestation_payload = {
                    "components": [chosen_placement_for_valence],
                    "chosen_valence": chosen_valence,
                    "life_area": area,
                    "birth_data": SAMPLE_BIRTH_DATA
                }
                try:
                    print(f"\n-> Generating manifestations for life area: '{area}'...")
                    manifest_response = await client.post(
                        f"{INTERPRETATION_SERVICE_URL}/interpret/manifestations", 
                        json=manifestation_payload
                    )
                    manifest_response.raise_for_status()
                    print(f"✅ SUCCESS: Received manifestations for '{area}' (Status: {manifest_response.status_code}).")
                    
                    # Print the results in a user-friendly format
                    manifestations = manifest_response.json().get('manifestations', [])
                    if manifestations:
                        for i, manifest in enumerate(manifestations):
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
                    print(f"   Response: {e.response.text}")
                except (httpx.RequestError, json.JSONDecodeError) as e:
                    print(f"❌ ERROR on '{area}': An issue occurred: {e}")
        """

    print("\n\n✨ End-to-End Test Simulation Complete. ✨")

# =============================================================================
# 4. RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    asyncio.run(main())