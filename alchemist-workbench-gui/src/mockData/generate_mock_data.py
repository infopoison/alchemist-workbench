# validation/generate_mock_data.py

import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# --- 1. SETUP: Load Environment Variables and API Client ---
# Make sure you have a .env file in the root of your project
# with your OPENAI_API_KEY.
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- CONFIGURATION ---
# Set this to a number (e.g., 2) to test with only the first few features
# Set to None to run for all 64 features.
LIMIT_FEATURES = None 
NUM_VALENCES_PER_FEATURE = 3
LIFE_AREAS = [
    'psychological_patterns',
    'relational_dynamics',
    'occupational_arenas',
    'creative_expression',
    'health_and_wellness',
    'financial_style',
    'leisure_and_hobbies',
]

# --- 2. KNOWLEDGE BASE & PROMPT TEMPLATES ---
# This section contains the necessary data and prompts, adapted from your
# existing service code.

# Load foundational knowledge base files
try:
    with open('./first_order.json', 'r') as f:
        kb = json.load(f)
    with open('./features.json', 'r') as f:
        features_data = json.load(f)
except FileNotFoundError as e:
    print(f"Error: Could not find knowledge base file. Make sure you run this script from the project root.")
    print(f"File not found: {e.filename}")
    exit()

# Pre-process knowledge base for easy lookups
kb_planets = {p['id']: p for p in kb['planets']}
kb_signs = {s['id']: s for s in kb['zodiac_signs']}
kb_houses = {h['id']: h for h in kb['houses']}
kb_dynamics = {d['id']: d for d in kb['dynamics']}
kb_angles = {a['id']: a for a in kb['angles']}
kb_nodes = {n['id']: n for n in kb['nodes']}

# Import prompt templates directly from your prompt_assembler.py
# (In a real app, these would be in a shared library)
from prompt_assembler_templates import (
    VALENCE_PROMPTS,
    MANIFESTATION_PROMPTS,
    ESSENTIAL_DIGNITIES
)

# --- 3. HELPER FUNCTIONS ---

def get_llm_response(prompt_text: str) -> Dict[str, Any]:
    """Sends a prompt to the OpenAI API and returns the parsed JSON response."""
    try:
        # A simple retry mechanism for API calls
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt_text}],
                    response_format={"type": "json_object"},
                    temperature=0.7, # Add some creativity
                )
                content = response.choices[0].message.content
                return json.loads(content)
            except (json.JSONDecodeError, OpenAI.APIError) as e:
                print(f"  - Retrying due to error: {e} (Attempt {attempt + 1})")
                time.sleep(5)
        raise Exception("Failed to get valid JSON response after 3 attempts.")
    except Exception as e:
        print(f"  - CRITICAL ERROR calling OpenAI API: {e}")
        return {}

def _determine_synthesis_type(components: List[Dict[str, str]]) -> str:
    """Determines the astrological pattern type from a list of components."""
    types = [c['type'] for c in components]
    if types == ['planet', 'zodiac_sign']: return 'planet_in_sign'
    if types == ['planet', 'house']: return 'planet_in_house'
    if types == ['node', 'zodiac_sign']: return 'node_in_sign'
    if types == ['node', 'house']: return 'node_in_house'
    if types == ['sign_on_house', 'house']: return 'sign_on_house' # Corrected type
    if types == ['planet', 'dynamic', 'planet']: return 'planet_aspect_planet'
    # Add other types from your prompt_assembler if needed
    # For this script, we'll simplify based on features.json structure
    if components[0]['type'] == 'sign_on_house': return 'sign_on_house'
    if components[0]['type'] == 'planet_aspect_planet': return 'planet_aspect_planet'
    
    # Fallback based on your features.json structure
    feature_type = components[0].get('type', 'planet_in_sign')
    return feature_type


def _get_dignity_status(planet_id: str, sign_id: str) -> str:
    """Determines the essential dignity of a planet in a sign."""
    dignities = ESSENTIAL_DIGNITIES.get(planet_id, {})
    for dignity, sign in dignities.items():
        if isinstance(sign, list) and sign_id in sign:
            return dignity.capitalize()
        if sign_id == sign:
            return dignity.capitalize()
    return "Peregrine"

def build_prompt_string(template: str, replacements: Dict[str, str]) -> str:
    """Replaces placeholders in a template string."""
    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, str(value))
    return prompt

def assemble_valence_prompt(feature: Dict[str, Any]) -> str:
    """Assembles the prompt for generating valences for a single feature."""
    synthesis_type = feature['type']
    template = VALENCE_PROMPTS.get(synthesis_type)
    if not template:
        raise ValueError(f"No valence prompt template for type: {synthesis_type}")

    # Simplified data fetching for script
    components_data = []
    component_map = {}
    p_count = 1
    for comp_id in feature['components']:
        if comp_id in kb_planets: 
            data = kb_planets[comp_id]
            key = f"[PLANET_{p_count}_DATA]" if p_count > 1 else "[PLANET_DATA]"
            component_map[key] = json.dumps(data, indent=2)
            p_count += 1
        elif comp_id in kb_signs: component_map['[SIGN_DATA]'] = json.dumps(kb_signs[comp_id], indent=2)
        elif comp_id in kb_houses: component_map['[HOUSE_DATA]'] = json.dumps(kb_houses[comp_id], indent=2)
        elif comp_id in kb_nodes: component_map['[NODE_DATA]'] = json.dumps(kb_nodes[comp_id], indent=2)
        elif comp_id in kb_dynamics: component_map['[ASPECT_DATA]'] = json.dumps(kb_dynamics[comp_id], indent=2)

    # Simplified dignity/quality logic for script
    if synthesis_type == 'planet_in_sign':
        planet_id = feature['components'][0]
        sign_id = feature['components'][1]
        component_map['[DIGNITY_STATUS]'] = _get_dignity_status(planet_id, sign_id)
    else:
        component_map['[DIGNITY_STATUS]'] = "N/A"

    if synthesis_type == 'planet_in_house':
        house_id = feature['components'][1]
        component_map['[QUALITY_DATA]'] = kb_houses[house_id].get('quality', 'N/A').capitalize()
    else:
        component_map['[QUALITY_DATA]'] = "N/A"


    # Replace the number of valences to generate
    template = template.replace(
        'a list of 3-5 distinct "expression archetypes"',
        f'a list of exactly {NUM_VALENCES_PER_FEATURE} distinct "expression archetypes"'
    )

    return build_prompt_string(template, component_map)


def assemble_manifestation_prompt(feature_name: str, valence: Dict[str, Any], life_area: str) -> str:
    """Assembles the prompt for generating a single manifestation."""
    template = MANIFESTATION_PROMPTS.get(life_area)
    if not template:
        raise ValueError(f"No manifestation prompt template for life area: {life_area}")

    # The manifestation prompt is simpler
    replacements = {
        '[SIGNATURE_DATA]': feature_name,
        '[VALENCE_DATA]': json.dumps(valence, indent=2)
    }
    
    # Modify prompt to ask for only ONE manifestation
    template = template.replace(
        "Generate 2-3 detailed",
        "Generate exactly one detailed"
    )
    
    return build_prompt_string(template, replacements)


# --- 4. MAIN EXECUTION ---
def main():
    """Main script execution function."""
    print("🚀 Starting mock data generation...")
    
    # This will be the final dictionary we write to a file.
    # It will be keyed by the feature ID, e.g., "sun_in_taurus".
    final_interpretations = {}
    
    all_features = [feature for category in features_data for feature in category['features']]
    
    features_to_process = all_features[:LIMIT_FEATURES] if LIMIT_FEATURES is not None else all_features
    total_features = len(features_to_process)

    for i, feature in enumerate(features_to_process):
        feature_id = feature['id']
        feature_name = feature['name']
        print(f"\n[{i+1}/{total_features}] Processing Feature: {feature_name}")
        
        # --- Step 1: Generate Valences for the Feature ---
        print(f"  -> Generating {NUM_VALENCES_PER_FEATURE} valences...")
        valence_prompt = assemble_valence_prompt(feature)
        valence_response = get_llm_response(valence_prompt)
        valences = valence_response.get('valences', [])

        if not valences:
            print(f"  - ⚠️ WARNING: No valences returned for {feature_name}. Skipping.")
            continue
        
        processed_valences = []
        for v_idx, valence in enumerate(valences[:NUM_VALENCES_PER_FEATURE]):
            print(f"    -> Processing Valence {v_idx+1}/{NUM_VALENCES_PER_FEATURE}: '{valence.get('archetype')}'")
            
            valence['manifestations'] = {}
            
            # --- Step 2: Generate Manifestations for each Life Area ---
            for area in LIFE_AREAS:
                print(f"      - Generating manifestation for '{area}'...")
                manifestation_prompt = assemble_manifestation_prompt(feature_name, valence, area)
                manifestation_response = get_llm_response(manifestation_prompt)
                
                # The key in the response matches the life area
                manifestation_list = manifestation_response.get(area, [])
                
                # We only asked for one, so we take the first if it exists
                if manifestation_list:
                    valence['manifestations'][area] = manifestation_list[0]
                else:
                    print(f"      - ⚠️ WARNING: No manifestation returned for {area}.")
                    valence['manifestations'][area] = {} # Add empty object on failure
                
                time.sleep(1) # Be kind to the API

            processed_valences.append(valence)

        final_interpretations[feature_id] = {
            "featureName": feature_name,
            "valences": processed_valences
        }

    # --- Step 3: Write the final data to a JSON file ---
    output_path = 'client/src/mockData/interpretations.json'
    print(f"\n✅ Generation complete. Writing all data to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(final_interpretations, f, indent=2)
    
    print("✨ Done!")

if __name__ == "__main__":
    # This is a helper file to contain the large prompt strings
    # to keep the main script cleaner.
    with open('prompt_assembler_templates.py', 'w') as f:
        f.write('from prompt_assembler import VALENCE_PROMPTS, MANIFESTATION_PROMPTS, ESSENTIAL_DIGNITIES')

    main()

