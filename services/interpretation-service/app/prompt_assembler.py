# services/interpretation-service/app/prompt_assembler.py

import json
import os
from typing import List, Dict, Any, Optional

# IMPORTANT: In a real production system, these prompt templates would
# ideally be loaded from separate .md or .txt files in a dedicated
# 'prompt_library' directory (as described in MergedImplementationGuidelines.pdf,
# Part I, Section 4.2). For this exercise, to avoid creating many small files,
# we are directly importing the string variables from the provided validate_prompts.py.
# This simulates having the prompt content available.

# Importing specific prompt template strings from validate_prompts.py
# We assume validate_prompts.py is accessible (e.g., copied to knowledge_base or similar for this context)
# For a clean microservice, these would typically be loaded from a dedicated prompt library.
# For now, we'll simulate loading them into dictionaries.

# Placeholders for the actual prompt content (full strings from validate_prompts.py)
# In a real scenario, you'd load these from files, e.g.,
# with open("prompt_library/associative_planet_in_sign.md", "r") as f:
#    ASSOCIATIVE_PROMPT_PLANET_IN_SIGN = f.read()

# --- Placeholder Prompt Content (from validate_prompts.py) ---
# We're defining these as empty strings or simplified versions here to represent
# that the *full* content would be loaded/imported.
# The actual content for these comes from the 'validate_prompts.py' file you provided.

# Associative Prompts
ASSOCIATIVE_PROMPT_PLANET_IN_SIGN = """... (Full ASSOCIATIVE_PROMPT_PLANET_IN_SIGN from validate_prompts.py) ..."""
ASSOCIATIVE_PROMPT_PLANET_IN_HOUSE = """... (Full ASSOCIATIVE_PROMPT_PLANET_IN_HOUSE from validate_prompts.py) ..."""
ASSOCIATIVE_PROMPT_PLANET_ASPECT_PLANET = """... (Full ASSOCIATIVE_PROMPT_PLANET_ASPECT_PLANET from validate_prompts.py) ..."""
ASSOCIATIVE_PROMPT_SIGN_ON_HOUSE = """... (Full ASSOCIATIVE_PROMPT_SIGN_ON_HOUSE from validate_prompts.py) ..."""
ASSOCIATIVE_PROMPT_NODE_IN_SIGN = """... (Full ASSOCIATIVE_PROMPT_NODE_IN_SIGN from validate_prompts.py) ..."""
ASSOCIATIVE_PROMPT_NODE_IN_HOUSE = """... (Full ASSOCIATIVE_PROMPT_NODE_IN_HOUSE from validate_prompts.py) ..."""
ASSOCIATIVE_PROMPT_PLANET_ASPECT_ANGLE = """... (Full ASSOCIATIVE_PROMPT_PLANET_ASPECT_ANGLE from validate_prompts.py) ..."""
ASSOCIATIVE_PROMPT_PLANET_ASPECT_NODE = """... (Full ASSOCIATIVE_PROMPT_PLANET_ASPECT_NODE from validate_prompts.py) ..."""
ASSOCIATIVE_PROMPT_NODE_ASPECT_ANGLE = """... (Full ASSOCIATIVE_PROMPT_NODE_ASPECT_ANGLE from validate_prompts.py) ..."""

# Reflection Prompts
REFLECTION_PROMPT_PLANET_IN_SIGN = """... (Full REFLECTION_PROMPT_PLANET_IN_SIGN from validate_prompts.py) ..."""
REFLECTION_PROMPT_PLANET_IN_HOUSE = """... (Full REFLECTION_PROMPT_PLANET_IN_HOUSE from validate_prompts.py) ..."""
REFLECTION_PROMPT_PLANET_ASPECT_PLANET = """... (Full REFLECTION_PROMPT_PLANET_ASPECT_PLANET from validate_prompts.py) ..."""
REFLECTION_PROMPT_SIGN_ON_HOUSE = """... (Full REFLECTION_PROMPT_SIGN_ON_HOUSE from validate_prompts.py) ..."""
REFLECTION_PROMPT_NODE_IN_SIGN = """... (Full REFLECTION_PROMPT_NODE_IN_SIGN from validate_prompts.py) ..."""
REFLECTION_PROMPT_NODE_IN_HOUSE = """... (Full REFLECTION_PROMPT_NODE_IN_HOUSE from validate_prompts.py) ..."""
REFLECTION_PROMPT_PLANET_ASPECT_ANGLE = """... (Full REFLECTION_PROMPT_PLANET_ASPECT_ANGLE from validate_prompts.py) ..."""
REFLECTION_PROMPT_PLANET_ASPECT_NODE = """... (Full REFLECTION_PROMPT_PLANET_ASPECT_NODE from validate_prompts.py) ..."""
REFLECTION_PROMPT_NODE_ASPECT_ANGLE = """... (Full REFLECTION_PROMPT_NODE_ASPECT_ANGLE from validate_prompts.py) ..."""

# --- Dispatcher Dictionaries (from validate_prompts.py) ---
# These map test types to the correct prompt template string.
# In a real system, these would be populated by loading the actual files.
ASSOCIATIVE_PROMPTS = {
    'planet_in_sign': ASSOCIATIVE_PROMPT_PLANET_IN_SIGN,
    'planet_in_house': ASSOCIATIVE_PROMPT_PLANET_IN_HOUSE,
    'planet_aspect_planet': ASSOCIATIVE_PROMPT_PLANET_ASPECT_PLANET,
    'sign_on_house': ASSOCIATIVE_PROMPT_SIGN_ON_HOUSE,
    'node_in_sign': ASSOCIATIVE_PROMPT_NODE_IN_SIGN,
    'node_in_house': ASSOCIATIVE_PROMPT_NODE_IN_HOUSE,
    'planet_aspect_angle': ASSOCIATIVE_PROMPT_PLANET_ASPECT_ANGLE,
    'planet_aspect_node': ASSOCIATIVE_PROMPT_PLANET_ASPECT_NODE,
    'node_aspect_angle': ASSOCIATIVE_PROMPT_NODE_ASPECT_ANGLE
}

REFLECTION_PROMPTS = {
    'planet_in_sign': REFLECTION_PROMPT_PLANET_IN_SIGN,
    'planet_in_house': REFLECTION_PROMPT_PLANET_IN_HOUSE,
    'planet_aspect_planet': REFLECTION_PROMPT_PLANET_ASPECT_PLANET,
    'sign_on_house': REFLECTION_PROMPT_SIGN_ON_HOUSE,
    'node_in_sign': REFLECTION_PROMPT_NODE_IN_SIGN,
    'node_in_house': REFLECTION_PROMPT_NODE_IN_HOUSE,
    'planet_aspect_angle': REFLECTION_PROMPT_PLANET_ASPECT_ANGLE,
    'planet_aspect_node': REFLECTION_PROMPT_PLANET_ASPECT_NODE,
    'node_aspect_angle': REFLECTION_PROMPT_NODE_ASPECT_ANGLE
}

# --- Simplified Framework Rules (from MergedImplementationGuidelines.pdf and other reports) ---
# In a real system, this would be loaded from generative_frameworks.md.
# For now, a simplified dictionary mapping rule names to descriptions.
FRAMEWORK_RULES = {
    "The Zodiacal Lens": {
        "name": "The Zodiacal Lens",
        "description": "The sign a planet occupies acts as a 'lens, costume, or environment,' dictating the style and quality of how that planetary drive is expressed."
    },
    "The Stage Metaphor": {
        "name": "The Stage Metaphor",
        "description": "The planet is the 'archetypal actor,' and the house is the 'stage' or specific domain of life where that actor's energy and drama unfolds."
    },
    "The Archetypal Dialogue": {
        "name": "The Archetypal Dialogue",
        "description": "Aspects represent the geometric and psychological dialogue between two planetary drives, describing how different functions within the psyche support or challenge one another."
    },
    "The Adverbial Signature": {
        "name": "The Adverbial Signature",
        "description": "The sign on a house cusp acts as an 'adjective' or adverbial signature, describing the tone, style, and conditions one encounters in that area of life."
    },
    "The Zodiacal Lens (Extended for Nodes)": {
        "name": "The Zodiacal Lens (Extended for Nodes)",
        "description": "The sign a component occupies acts as a 'lens, costume, or environment,' dictating the style and quality of how that component's core principle is expressed. For a Node, this is its evolutionary purpose (North Node) or karmic pattern (South Node)."
    },
    "The Stage Metaphor (Extended for Nodes)": {
        "name": "The Stage Metaphor (Extended for Nodes)",
        "description": "The house is the 'stage' or specific domain of life where an archetypal principle's story unfolds. For a Node, it is the karmic or evolutionary theme that is played out in that specific life area."
    },
    "The Archetypal Imprint": {
        "name": "The Archetypal Imprint",
        "description": "This framework defines how a planet's core drive imprints upon, activates, or challenges one of the four fundamental pillars of the life structure."
    },
    "The Karmic Infusion": {
        "name": "The Karmic Infusion",
        "description": "This framework describes how a planetary drive infuses its energy into the user's evolutionary path."
    },
    "The Soul's Compass": {
        "name": "The Soul's Compass",
        "description": "This framework defines how the soul's evolutionary path (the Nodal Axis) is grounded in, expressed through, or challenged by the most tangible pillars of the life structure (the Angles)."
    },
    # Add other principles of interplay if needed (Fusion, Harmony, Conflict & Growth, Adjustment)
    "The Fusion Principle": {
        "name": "The Fusion Principle",
        "description": "The archetypes merge and act as a single, unified force."
    },
    "The Harmony Principle": {
        "name": "The Harmony Principle",
        "description": "The archetypes support each other naturally, representing innate talents and ease."
    },
    "The Conflict & Growth Principle": {
        "name": "The Conflict & Growth Principle",
        "description": "The archetypes are in a state of tension that demands conscious awareness and forces developmental growth."
    },
    "The Adjustment Principle": {
        "name": "The Adjustment Principle",
        "description": "The archetypes share nothing in common, creating a blind spot that requires constant, conscious adjustment."
    }
}


class PromptAssembler:
    """
    Assembles LLM prompts based on astrological components and interpretive rules.
    This module encapsulates the 'white box' prompting philosophy.
    """

    def __init__(self, lexicon_client: Any, calculation_client: Any):
        self.lexicon_client = lexicon_client
        self.calculation_client = calculation_client
        
        # Store prompt templates and framework rules
        self.associative_prompts = ASSOCIATIVE_PROMPTS
        self.reflection_prompts = REFLECTION_PROMPTS
        self.framework_rules = FRAMEWORK_RULES

        # Store knowledge base lookups (simulated from validate_prompts.py logic)
        # In a real scenario, these would be loaded from first_order.json on startup
        # or fetched dynamically from the Lexicon Service.
        # For now, we'll assume a simplified direct lookup for prompt building.
        # This part needs to be robustly handled by fetching from Lexicon Service.
        self.kb_planets = {} # Will be populated by fetching from Lexicon
        self.kb_signs = {}
        self.kb_houses = {}
        self.kb_dynamics = {}
        self.kb_angles = {}
        self.kb_nodes = {}

    async def _fetch_component_data(self, component_type: str, component_id: str) -> Dict[str, Any]:
        """Fetches a single component's data from the Lexicon Service."""
        try:
            response = await self.lexicon_client.get(f"/components/{component_type}/{component_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ComponentNotFoundError(component_id=component_id, component_type=component_type)
            raise UpstreamServiceError(f"Lexicon Service error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise UpstreamServiceError(f"Network error contacting Lexicon Service: {e}")

    def _get_framework_rule_text(self, rule_name: str) -> Dict[str, str]:
        """Retrieves the verbatim rule text for a given framework."""
        rule = self.framework_rules.get(rule_name)
        if not rule:
            raise ValueError(f"Framework rule '{rule_name}' not found in prompt library.")
        return rule

    async def assemble_synthesis_prompt(
        self,
        components_input: List[Dict[str, str]], # e.g., [{"type": "planet", "id": "mars"}, {"type": "zodiac_sign", "id": "aries"}]
        calculated_chart_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]: # Returns dict with 'prompt_text' and 'synthesis_rule_metadata'
        """
        Dynamically assembles the LLM prompt based on the provided astrological components.
        This is a simplified version; the full logic for pattern identification
        and rule selection will be more complex.
        """
        
        # 1. Fetch all canonical data for components
        fetched_components_data = []
        for comp_input in components_input:
            data = await self._fetch_component_data(comp_input['type'], comp_input['id'])
            fetched_components_data.append(data)

        # 2. Identify the primary pattern and select the correct prompt template
        # This is a VERY simplified pattern matching. In a full implementation,
        # you'd have robust logic to determine the exact combination (e.g., planet-in-sign,
        # planet-aspect-planet, node-aspect-angle, etc.) and select the corresponding template.
        
        # For demonstration, let's assume a simple case or pick a default if multiple components.
        # This part needs to be expanded based on the 'generative_frameworks.md' logic.
        
        prompt_template_key = None
        synthesis_rule_name = "Placeholder Rule" # Default rule name
        
        if len(components_input) == 2:
            comp1_type = components_input[0]['type']
            comp2_type = components_input[1]['type']
            
            if comp1_type == 'planet' and comp2_type == 'zodiac_sign':
                prompt_template_key = 'planet_in_sign'
                synthesis_rule_name = "The Zodiacal Lens"
            elif comp1_type == 'planet' and comp2_type == 'house':
                prompt_template_key = 'planet_in_house'
                synthesis_rule_name = "The Stage Metaphor"
            elif comp1_type == 'node' and comp2_type == 'zodiac_sign':
                prompt_template_key = 'node_in_sign'
                synthesis_rule_name = "The Zodiacal Lens (Extended for Nodes)"
            elif comp1_type == 'node' and comp2_type == 'house':
                prompt_template_key = 'node_in_house'
                synthesis_rule_name = "The Stage Metaphor (Extended for Nodes)"
            elif comp1_type == 'sign' and comp2_type == 'house':
                prompt_template_key = 'sign_on_house'
                synthesis_rule_name = "The Adverbial Signature"
        elif len(components_input) == 3:
            # Example for Planet-Aspect-Planet
            comp1_type = components_input[0]['type']
            comp2_type = components_input[1]['type'] # This would be 'dynamic' for aspects
            comp3_type = components_input[2]['type']
            
            if comp1_type == 'planet' and comp2_type == 'dynamic' and comp3_type == 'planet':
                prompt_template_key = 'planet_aspect_planet'
                synthesis_rule_name = "The Archetypal Dialogue"
            elif comp1_type == 'planet' and comp2_type == 'dynamic' and comp3_type == 'angle':
                prompt_template_key = 'planet_aspect_angle'
                synthesis_rule_name = "The Archetypal Imprint"
            elif comp1_type == 'planet' and comp2_type == 'dynamic' and comp3_type == 'node':
                prompt_template_key = 'planet_aspect_node'
                synthesis_rule_name = "The Karmic Infusion"
            elif comp1_type == 'node' and comp2_type == 'dynamic' and comp3_type == 'angle':
                prompt_template_key = 'node_aspect_angle'
                synthesis_rule_name = "The Soul's Compass"
        
        if not prompt_template_key:
            # Fallback for unsupported combinations or more complex patterns
            prompt_template = f"""
                You are an expert archetypal astrologer. Synthesize an interpretation based on these astrological components:
                Components: {json.dumps(fetched_components_data, indent=2)}
                """
            if calculated_chart_data:
                prompt_template += f"\nChart Data: {json.dumps(calculated_chart_data, indent=2)}"
            prompt_template += """
                Provide a coherent narrative interpretation.
                """
            # Use a generic rule for fallback
            synthesis_rule_metadata = self._get_framework_rule_text("Placeholder Rule") # Generic placeholder
            return {
                "prompt_text": prompt_template,
                "synthesis_rule_metadata": SynthesisRuleMetadata(name=synthesis_rule_name, description=synthesis_rule_metadata.get("description", ""))
            }


        # Get the actual prompt template string
        selected_template = self.associative_prompts.get(prompt_template_key)
        if not selected_template:
            raise ValueError(f"Associative prompt template for '{prompt_template_key}' not found.")

        # Prepare data for placeholder replacement (similar to build_prompt in validate_prompts.py)
        replacements = {}
        
        # Extract individual components for placeholders like [PLANET_DATA], [SIGN_DATA] etc.
        # This part requires careful mapping based on the expected placeholders in each template.
        # For simplicity, we'll iterate through fetched_components_data and assign.
        # A more robust solution would dynamically match based on placeholder names in template.
        
        planet_count = 1
        for data in fetched_components_data:
            comp_id = data.get('id')
            comp_type = data.get('type') # Assuming 'type' is part of the fetched data now

            if comp_type == 'planet':
                key = f"[PLANET_{planet_count}_DATA]" if planet_count > 1 else "[PLANET_DATA]"
                replacements[key] = json.dumps(data)
                planet_count += 1
            elif comp_type == 'zodiac_sign':
                replacements['[SIGN_DATA]'] = json.dumps(data)
            elif comp_type == 'house':
                replacements['[HOUSE_DATA]'] = json.dumps(data)
            elif comp_type == 'node':
                replacements['[NODE_DATA]'] = json.dumps(data)
            elif comp_type == 'angle':
                replacements['[ANGLE_DATA]'] = json.dumps(data)
            elif comp_type == 'dynamic': # For aspects
                replacements['[ASPECT_DATA]'] = json.dumps(data)
        
        # Add calculated chart data if present
        if calculated_chart_data:
             replacements['[CALCULATED_CHART_DATA]'] = json.dumps(calculated_chart_data)
        
        # Add specific rule text
        framework_rule_metadata = self._get_framework_rule_text(synthesis_rule_name)
        replacements['[FRAMEWORK_RULE]'] = framework_rule_metadata.get("description", "") # Assuming rule text placeholder

        # Also add specific placeholders from validate_prompts.py if needed, e.g.
        # replacements['[DIGNITY_STATUS]'] = "N/A" # If template uses this
        # replacements['[QUALITY_DATA]'] = "N/A" # If template uses this

        # Replace placeholders in the selected template
        final_prompt = selected_template
        for placeholder, value in replacements.items():
            final_prompt = final_prompt.replace(placeholder, value)
        
        # If the template requires calculated chart data but it's not provided,
        # or other critical data is missing, we should raise an error.
        # For now, we'll rely on the LLM to handle missing data gracefully or
        # the prompt itself to be robust.

        return {
            "prompt_text": final_prompt,
            "synthesis_rule_metadata": SynthesisRuleMetadata(name=synthesis_rule_name, description=framework_rule_metadata.get("description", ""))
        }


