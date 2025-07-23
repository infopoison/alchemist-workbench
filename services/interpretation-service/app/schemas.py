# services/interpretation-service/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import uuid

# =============================================================================
# I. CORE & SHARED SCHEMAS
# =============================================================================
# These are the foundational building blocks used across multiple requests.

class ComponentInput(BaseModel):
    """Identifies a single astrological component for analysis."""
    type: str = Field(..., example="planet", description="The category of the component (e.g., 'planet', 'zodiac_sign').")
    id: str = Field(..., example="mars", description="The unique identifier for the component (e.g., 'mars', 'aries').")

class BirthDataInput(BaseModel):
    """Represents the necessary data to calculate a natal chart."""
    name: Optional[str] = Field("User", example="John Doe", description="Optional name for the subject.")
    city: str = Field(..., example="Los Angeles", description="The city of birth.")
    date: str = Field(..., example="1990-10-28", description="The birth date in YYYY-MM-DD format.")
    time: str = Field(..., example="09:30:00", description="The birth time in 24-hour HH:MM:SS format.")
    latitude: float = Field(..., example=34.0522, description="The geographical latitude.")
    longitude: float = Field(..., example=-118.2437, description="The geographical longitude.")
    timezone: str = Field(..., example="America/Los_Angeles", description="The IANA timezone name.")

class SynthesisRuleMetadata(BaseModel):
    """Documents the astrological rule used for a synthesis, ensuring transparency."""
    name: str = Field(..., example="The Zodiacal Lens", description="The name of the generative framework rule.")
    description: str = Field(..., example="The sign a planet occupies acts as a 'lens'...", description="The verbatim text of the rule's principle.")

class EngineMetadata(BaseModel):
    """Provides versioning and source information for the engines used in a response."""
    calculation_engine: Optional[str] = Field(None, example="AstrologerAPI_v4_RapidAPI", description="The calculation engine used, if any.")
    interpretive_engine: str = Field(..., example="OpenAI_GPT-4o-mini_2024-07-21", description="The interpretive LLM used.")


# =============================================================================
# II. DECONSTRUCTION ENDPOINT (/interpret/deconstruct)
# =============================================================================
# Schemas for the simple, single-component definition lookup. This flow is unchanged.

class DeconstructRequest(BaseModel):
    """Request to get the canonical definition of a single component."""
    component: ComponentInput

class DeconstructResponse(BaseModel):
    """Response containing the canonical definition of a single component."""
    component_id: str
    definition_text: str


# =============================================================================
# III. STAGE 1: VALENCE GENERATION ENDPOINT (/interpret/valences)
# =============================================================================
# Schemas for the first step of the synthesis process: generating potential valences.

class Valence(BaseModel):
    """Represents a single potential archetypal expression (a 'valence')."""
    archetype: str = Field(..., example="The Spiritual Warrior", description="The evocative name of the valence.")
    description: str = Field(..., example="A brief, one-sentence explanation of the expression.", description="A concise description of the valence.")

class ValenceRequest(BaseModel):
    """Request to generate a list of valences for a given astrological signature."""
    components: List[ComponentInput]
    birth_data: Optional[BirthDataInput] = None

class ValenceResponse(BaseModel):
    """Response containing the generated valences and all metadata for transparency."""
    synthesis_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    valences: List[Valence]
    synthesis_rule: SynthesisRuleMetadata
    components_used: List[Dict[str, Any]] # Holds full JSON objects from Lexicon
    engine_metadata: EngineMetadata


# =============================================================================
# IV. STAGE 2: MANIFESTATION GENERATION ENDPOINT (/interpret/manifestations)
# =============================================================================
# Schemas for the second step: elaborating a chosen valence across life areas.

class ManifestationRequest(BaseModel):
    """Request to generate detailed life-area manifestations for a chosen valence."""
    components: List[ComponentInput]
    chosen_valence: Valence
    life_area: Literal[
        "psychological_patterns", "relational_dynamics", "occupational_arenas",
        "creative_expression", "health_and_wellness", "financial_style", "leisure_and_hobbies"
    ] = Field(..., description="The specific life area to generate manifestations for.")
    birth_data: Optional[BirthDataInput] = None

class ManifestationResponse(BaseModel):
    """A response containing a list of manifestations for a single life area."""
    manifestations: List[Dict[str, Any]]
    engine_metadata: EngineMetadata


# =============================================================================
# V. DEPRECATED SCHEMAS
# =============================================================================
# The original SynthesisRequest and SynthesisResponse are now deprecated and
# replaced by the more specific ValenceRequest/Response and
# ManifestationRequest/Response schemas to support the new two-stage flow.
# They are left here commented out for historical reference during transition.
#
# class SynthesisRequest(BaseModel):
#     components: List[ComponentInput]
#     birth_data: Optional[BirthDataInput] = None
#
# class SynthesisResponse(BaseModel):
#     synthesis_id: uuid.UUID = Field(default_factory=uuid.uuid4)
#     interpretation_text: str
#     synthesis_rule: SynthesisRuleMetadata
#     components_used: List[Dict[str, Any]]
#     engine_metadata: EngineMetadata
