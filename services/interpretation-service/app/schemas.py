# /services/interpretation-service/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import uuid

# =============================================================================
# I. Original Schemas for the Interpretation Service
# =============================================================================

class ComponentInput(BaseModel):
    type: str
    id: str

class BirthDataInput(BaseModel):
    name: str
    city: str
    date: str
    time: Optional[str] = None
    latitude: float
    longitude: float
    timezone: str

class SynthesisRuleMetadata(BaseModel):
    """Documents the astrological rule used for a synthesis, ensuring transparency."""
    name: str = Field(..., example="The Zodiacal Lens", description="The name of the generative framework rule.")
    description: str = Field(..., example="The sign a planet occupies acts as a 'lens'...", description="The verbatim text of the rule's principle.")

class EngineMetadata(BaseModel):
    """Provides versioning and source information for the engines used in a response."""
    calculation_engine: Optional[str] = Field(None, example="AstrologerAPI_v4_RapidAPI", description="The calculation engine used, if any.")
    interpretive_engine: str = Field(..., example="OpenAI_GPT-4o-mini_2024-07-21", description="The interpretive LLM used.")

class DeconstructRequest(BaseModel):
    """Request to get the canonical definition of a single component."""
    component: ComponentInput

class DeconstructResponse(BaseModel):
    """Response containing the canonical definition of a single component."""
    component_id: str
    definition_text: str

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


class ValenceResponse(BaseModel):
    """Response containing the generated valences and all metadata for transparency."""
    synthesis_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    valences: List[Valence]
    synthesis_rule: SynthesisRuleMetadata
    components_used: List[Dict[str, Any]] # Holds full JSON objects from Lexicon
    engine_metadata: EngineMetadata

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
# II. Chart Object Schemas (Copied from Calculation Service Contract)
# =============================================================================

class CalculationEngineMetadata(BaseModel):
    """Metadata specifically from the Calculation Service."""
    calculation_engine: str

class Subject(BaseModel):
    date: str
    time: Optional[str] = None
    latitude: float
    longitude: float
    timezone: str

class ZodiacSign(BaseModel):
    id: str
    name: str

class House(BaseModel):
    id: str
    name: str

class CelestialPoint(BaseModel):
    id: str
    name: str
    position_longitude: float
    absolute_longitude: float
    speed: float
    is_retrograde: bool
    zodiac_sign: ZodiacSign
    house: Optional[House] = None

class HouseCusp(BaseModel):
    id: str
    name: str
    position_longitude: float
    absolute_longitude: float
    zodiac_sign: ZodiacSign

class Aspect(BaseModel):
    point_1_id: str
    point_2_id: str
    aspect_id: str
    aspect_name: str
    orb: float

class CalculatedChart(BaseModel):
    chart_id: uuid.UUID
    engine_metadata: CalculationEngineMetadata
    subject: Subject
    celestial_points: List[CelestialPoint]
    houses: Optional[List[HouseCusp]] = None
    aspects: List[Aspect]
    chart_type: Optional[str] = None