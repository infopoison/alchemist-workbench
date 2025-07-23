# e2e_test.py

import httpx
import asyncio
import json
import random

# =============================================================================
# 1. DEFINE CORE INPUTS FOR THE TEST
# =============================================================================

# Define a sample birth data object, matching the BirthDataInput schema.
SAMPLE_BIRTH_DATA = {
    "name": "Creator",
    "city": "Dallas",
    "date": "1995-05-18",
    "time": "17:41:00",
    "latitude": 32.7791,
    "longitude": -96.7969,
    "timezone": "America/Chicago"
}

# Define the list of all life areas to generate manifestations for.
# This list is derived from the ManifestationRequest schema.
LIFE_AREAS = [
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

def find_first_square_aspect(chart_data: dict):
    """
    Parses the full chart data to find the first 'square' aspect.
    This simulates a user looking at their chart and picking an interesting
    feature to explore.

    Args:
        chart_data: The JSON response from the calculation-service.

    Returns:
        A list of component dictionaries for the valence request, or None.
    """
    # CORRECTION: The calculation-service returns a CalculatedChart object
    # with a top-level 'aspects' key, not nested inside a 'data' key.
    if 'aspects' not in chart_data:
        print("   -> WARNING: 'aspects' key not found in the chart response from calculation-service.")
        print(f"      Available keys are: {list(chart_data.keys())}")
        return None

    aspects = chart_data['aspects']
    for aspect in aspects:
        # CORRECTION: The aspect identifier is 'aspect_id', not 'aspect'.
        if aspect.get("aspect_id") == "square":
            # CORRECTION: The planet identifiers are 'point_1_id' and 'point_2_id'.
            p1_name = aspect.get("point_1_id", "").lower().replace("_", "")
            p2_name = aspect.get("point_2_id", "").lower().replace("_", "")

            # Ensure we are dealing with standard planets for a clean test
            # and avoid complex points like 'mean_lilith' or nodes initially.
            valid_planets = {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"}
            if p1_name in valid_planets and p2_name in valid_planets:
                signature = [
                    {"type": "planet", "id": p1_name},
                    {"type": "dynamic", "id": "square"},
                    {"type": "planet", "id": p2_name}
                ]
                print(f"   -> Found a testable 'square' aspect: {p1_name.capitalize()} square {p2_name.capitalize()}.")
                return signature
    
    print("   -> WARNING: No 'square' aspect between major planets found in the chart data.")
    return None

# =============================================================================
# 3. MAIN ASYNCHRONOUS TEST FUNCTION
# =============================================================================

async def main():
    """
    Runs the end-to-end test simulation for the Alchemical Workbench API.
    """
    print("🚀 Starting Alchemical Workbench End-to-End Test (Corrected Flow)...\n")
    signature_components = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ---------------------------------------------------------------------
        # STAGE 1: Call Calculation Service to get the full natal chart
        # ---------------------------------------------------------------------
        print("--- [Stage 1/5] Simulating Chart Calculation ---")
        try:
            print(f"-> Sending birth data to Calculation Service at {CALCULATION_SERVICE_URL}/chart...")
            calc_response = await client.post(f"{CALCULATION_SERVICE_URL}/chart", json=SAMPLE_BIRTH_DATA)
            calc_response.raise_for_status()
            chart_data = calc_response.json()
            print(f"✅ SUCCESS: Calculation Service responded with status {calc_response.status_code}.")
            
            # -----------------------------------------------------------------
            # STAGE 2: Dynamically find a signature from the chart data
            # -----------------------------------------------------------------
            print("\n--- [Stage 2/5] Simulating User Feature Discovery ---")
            print("-> Parsing the returned chart data to find an interesting aspect to analyze...")
            signature_components = find_first_square_aspect(chart_data)

            if not signature_components:
                print("❌ ERROR: Could not find a suitable aspect in the chart to test. Halting.")
                return

        except httpx.HTTPStatusError as e:
            print(f"❌ ERROR: Calculation Service returned a {e.response.status_code} status.")
            print(f"   Response: {e.response.text}")
            return
        except (httpx.RequestError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: An issue occurred during chart calculation: {e}")
            return

        # ---------------------------------------------------------------------
        # STAGE 3: Call Interpretation Service for Valences
        # ---------------------------------------------------------------------
        print("\n--- [Stage 3/5] Simulating Valence Generation ---")
        valence_payload = {
            "components": signature_components,
            "birth_data": SAMPLE_BIRTH_DATA
        }
        chosen_valence = None
        try:
            print(f"-> Sending dynamically found signature to Interpretation Service at {INTERPRETATION_SERVICE_URL}/interpret/valences...")
            valence_response = await client.post(f"{INTERPRETATION_SERVICE_URL}/interpret/valences", json=valence_payload)
            valence_response.raise_for_status()
            print(f"✅ SUCCESS: Interpretation Service responded with status {valence_response.status_code}.")
            
            valences = valence_response.json().get("valences", [])
            if not valences:
                print("❌ ERROR: Valence response contained no valences to choose from.")
                return
            
            # Programmatically select the first valence to simulate user choice
            chosen_valence = valences[0]
            print(f"\n--- [Stage 4/5] Simulating User Valence Selection ---")
            print(f"-> If the user had selected the first option, they would choose the '{chosen_valence['archetype']}' valence.")
            print(f"   Description: \"{chosen_valence['description']}\"")

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
        if chosen_valence:
            print("\n--- [Stage 5/5] Simulating Manifestation Generation for all Life Areas ---")
            for area in LIFE_AREAS:
                manifestation_payload = {
                    "components": signature_components,
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
                            m_name = manifest.get('pattern_name', manifest.get('dynamic_name', 'Unknown'))
                            m_desc = manifest.get('description', 'No description provided.')
                            print(f"   [{m_type}] {m_name}: {m_desc}")
                    else:
                        print("   -> No manifestations returned for this life area.")

                except httpx.HTTPStatusError as e:
                    print(f"❌ ERROR on '{area}': Service returned {e.response.status_code}.")
                    print(f"   Response: {e.response.text}")
                except (httpx.RequestError, json.JSONDecodeError) as e:
                    print(f"❌ ERROR on '{area}': An issue occurred: {e}")

    print("\n\n✨ End-to-End Test Simulation Complete. ✨")

# =============================================================================
# 4. RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    asyncio.run(main())
