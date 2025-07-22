# services/interpretation-service/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

# --- Incoming Request Schemas ---

class ComponentInput(BaseModel):
    type: str = Field(..., example="planet")
    id: str = Field(..., example="mars")

class BirthDataInput(BaseModel):
    # Added name and city as per user request for better UX
    name: Optional[str] = Field("User", example="John Doe") # Optional, with a default placeholder
    city: str = Field(..., example="Los Angeles") # Required, as users typically know this
    date: str = Field(..., example="1990-10-28")
    time: str = Field(..., example="09:30:00")
    latitude: float = Field(..., example=34.0522)
    longitude: float = Field(..., example=-118.2437)
    timezone: str = Field(..., example="America/Los_Angeles")

class DeconstructRequest(BaseModel):
    component: ComponentInput

class SynthesisRequest(BaseModel):
    components: List[ComponentInput]
    birth_data: Optional[BirthDataInput] = None # Optional, as not all syntheses need chart data

# --- Outgoing Response Schemas (for /interpret/deconstruct) ---

class DeconstructResponse(BaseModel):
    component_id: str
    definition_text: str

# --- Outgoing Response Schemas (for /interpret/synthesis) ---
# These mirror the structure from MergedImplementationGuidelines.pdf
# Note: Full canonical data for components_used will be injected here,
# so we'll use a flexible type for now.

class SynthesisRuleMetadata(BaseModel):
    name: str
    description: str

class EngineMetadata(BaseModel):
    # Note: calculation_engine is from Calculation Service, interpretive_engine is for OpenAI
    calculation_engine: str
    interpretive_engine: str

class SynthesisResponse(BaseModel):
    synthesis_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    interpretation_text: str
    synthesis_rule: SynthesisRuleMetadata
    components_used: List[Dict[str, Any]] # Will hold full JSON objects from Lexicon
    engine_metadata: EngineMetadata

