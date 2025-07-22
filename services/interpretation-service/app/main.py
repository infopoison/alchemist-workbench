# services/interpretation-service/app/main.py

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import httpx # For making calls to other services
import traceback # For detailed error logging
import uuid # For generating UUIDs for SynthesisResponse

# Import Pydantic schemas defined for this service
from .schemas import (
    DeconstructRequest, DeconstructResponse,
    SynthesisRequest, SynthesisResponse,
    ComponentInput, BirthDataInput,
    SynthesisRuleMetadata, EngineMetadata
)

# Import OpenAI client
from openai import OpenAI, OpenAIError

# Import the new PromptAssembler
from .prompt_assembler import PromptAssembler

# Import the new service clients
from .clients import LexiconServiceClient, CalculationServiceClient


# Load environment variables from .env file
load_dotenv()

# --- Custom Exception for Upstream Service Errors ---
class UpstreamServiceError(HTTPException):
    """Custom exception for upstream service failures, to return a 503."""
    def __init__(self, detail: str, status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE):
        super().__init__(status_code=status_code, detail={"error": {"code": "upstream_unavailable", "message": detail}})

class ComponentNotFoundError(HTTPException):
    """Custom exception for when a requested component is not found in Lexicon."""
    def __init__(self, component_id: str, component_type: str):
        detail = f"The requested component '{component_id}' of type '{component_type}' does not exist."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "component_not_found", "message": detail}})

class InvalidBirthDataError(HTTPException):
    """Custom exception for invalid birth data from Calculation Service."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "invalid_birth_data", "message": detail}})

class SynthesisContentError(HTTPException):
    """Custom exception for content policy violations from LLM."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": {"code": "synthesis_content_error", "message": detail}})

class SynthesisRateLimitError(HTTPException):
    """Custom exception for LLM rate limit errors."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={"error": {"code": "synthesis_rate_limited", "message": detail}})


# --- Lifespan Events (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Interpretation Service starting up...")
    
    # Retrieve service URLs and API key from environment variables
    lexicon_service_url = os.getenv("LEXICON_SERVICE_URL")
    calculation_service_url = os.getenv("CALCULATION_SERVICE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Validate environment variables
    if not lexicon_service_url:
        raise ValueError("LEXICON_SERVICE_URL must be set for the Interpretation Service.")
    if not calculation_service_url:
        raise ValueError("CALCULATION_SERVICE_URL must be set for the Interpretation Service.")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY must be set for the Interpretation Service.")

    # Initialize service clients and store them in app.state
    app.state.lexicon_client = LexiconServiceClient(base_url=lexicon_service_url)
    app.state.calculation_client = CalculationServiceClient(base_url=calculation_service_url)
    app.state.openai_client = OpenAI(api_key=openai_api_key)

    # Initialize PromptAssembler, passing the clients it needs
    app.state.prompt_assembler = PromptAssembler(
        lexicon_client=app.state.lexicon_client,
        calculation_client=app.state.calculation_client
    )

    yield
    print("Interpretation Service shutting down...")
    
    # Close HTTP clients gracefully during shutdown
    await app.state.lexicon_client.aclose()
    await app.state.calculation_client.aclose()
    # OpenAI client doesn't typically need explicit closing

# --- FastAPI Application Instance ---
app = FastAPI(
    title="Alchemical Workbench - Interpretation Service",
    description="Orchestrates astrological interpretation synthesis.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Global Exception Handlers (as defined in MergedImplementationGuidelines.pdf) ---
# These handlers catch custom HTTPExceptions and return standardized JSON responses.
@app.exception_handler(UpstreamServiceError)
async def upstream_service_unavailable_handler(request: Request, exc: UpstreamServiceError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )

@app.exception_handler(ComponentNotFoundError)
async def component_not_found_handler(request: Request, exc: ComponentNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )

@app.exception_handler(InvalidBirthDataError)
async def invalid_birth_data_handler(request: Request, exc: InvalidBirthDataError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )

@app.exception_handler(SynthesisContentError)
async def synthesis_content_error_handler(request: Request, exc: SynthesisContentError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )

@app.exception_handler(SynthesisRateLimitError)
async def synthesis_rate_limit_error_handler(request: Request, exc: SynthesisRateLimitError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print("--- An unexpected error occurred in Interpretation Service ---")
    traceback.print_exc() # Print full traceback for debugging
    print("----------------------------------------------------------")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected internal error occurred in the Interpretation Service."
            }
        },
    )


# --- Health Check Endpoint ---
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "Interpretation Service is operational"}

# --- Endpoint: POST /interpret/deconstruct ---
# Defined in MergedImplementationGuidelines.pdf, Section 10.0, page 12
@app.post("/interpret/deconstruct", response_model=DeconstructResponse, tags=["Interpretation"])
async def deconstruct_component(request_data: DeconstructRequest, request: Request):
    """
    Generates a concise, archetypal definition for a single astrological component.
    This method directly retrieves static definitions from the Lexicon Service
    without involving the LLM, aligning with the 'white box' philosophy for
    first-order definitions.
    """
    lexicon_client = request.app.state.lexicon_client # Get client from app.state

    component_type = request_data.component.type
    component_id = request_data.component.id

    try:
        # 1. Call Lexicon Service to get canonical data for the component using the client
        component_data = await lexicon_client.get_component_detail(component_type, component_id)

        # 2. Directly construct the definition text from the Lexicon data
        # This removes the LLM call for static first-order definitions.
        # Fields are accessed using .get() with a default empty string to prevent KeyError if data is missing.
        principle = component_data.get('display_content', {}).get('principle', '')
        core_concept = component_data.get('display_content', {}).get('core_concept', '')
        archetype = component_data.get('archetype', '')

        # Concatenate the available information into a coherent definition string
        definition_parts = []
        if archetype:
            definition_parts.append(f"Archetype: {archetype}.")
        if principle:
            definition_parts.append(f"Principle: {principle}.")
        if core_concept:
            definition_parts.append(f"Core Concept: {core_concept}.")
        
        # If no specific parts found, use a generic fallback
        if not definition_parts:
            definition_text = f"Definition for {component_id} not available."
        else:
            definition_text = " ".join(definition_parts).strip()


        return DeconstructResponse(
            component_id=component_id,
            definition_text=definition_text
        )

    except (UpstreamServiceError, ComponentNotFoundError, InvalidBirthDataError, SynthesisContentError, SynthesisRateLimitError) as e:
        # Re-raise our custom HTTPExceptions directly, as their handlers are defined globally
        raise e
    except Exception as e:
        # Catch any other unexpected errors and raise a generic 500
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


# --- Endpoint: POST /interpret/synthesis ---
# Defined in MergedImplementationGuidelines.pdf, Section 10.0, page 13
@app.post("/interpret/synthesis", response_model=SynthesisResponse, tags=["Interpretation"])
async def synthesize_interpretation(request_data: SynthesisRequest, request: Request):
    """
    Generates a complex, multi-part synthesis interpretation based on astrological components.
    """
    # Get initialized clients and prompt assembler from app.state
    openai_client = request.app.state.openai_client
    prompt_assembler = request.app.state.prompt_assembler

    # Initialize variables for data collection
    all_components_data = [] # This will be populated by PromptAssembler's internal calls now
    calculated_chart_data = None
    
    try:
        # 1. Fetch Calculated Chart Data from Calculation Service if birth_data is provided
        # This is now handled by the CalculationServiceClient via prompt_assembler.
        # We need to ensure prompt_assembler can pass birth_data.
        # The prompt_assembler's assemble_synthesis_prompt method will now handle fetching
        # both canonical and calculated data.
        
        # The all_components_data will be returned by the prompt_assembler now.
        # We'll adjust the prompt_assembler's return to include this.
        
        # For now, we'll keep this loop to satisfy the `components_used` in the response model.
        # In a more optimized version, PromptAssembler would return this list directly.
        for component_input in request_data.components:
            # This is a temporary direct call to Lexicon to populate all_components_data for the response.
            # In a fully refactored PromptAssembler, it would return this list.
            component_data = await request.app.state.lexicon_client.get_component_detail(
                component_input.type, component_input.id
            )
            all_components_data.append(component_data)


        # 2. Build the LLM Prompt using the PromptAssembler
        # The PromptAssembler is responsible for fetching all necessary data (canonical and calculated)
        # and selecting the correct prompt template.
        assembled_prompt_info = await prompt_assembler.assemble_synthesis_prompt(
            components_input=[c.dict() for c in request_data.components], # Pass as dicts
            calculated_chart_data=request_data.birth_data.dict() if request_data.birth_data else None
        )
        prompt_content = assembled_prompt_info["prompt_text"]
        synthesis_rule_metadata = assembled_prompt_info["synthesis_rule_metadata"]

        # 3. Call OpenAI API
        llm_response = await openai_client.chat.completions.create(
            model="gpt-4o-mini", # As recommended in MergedImplementationGuidelines.pdf
            messages=[{"role": "user", "content": prompt_content}],
            temperature=0.7, # Allow some creativity for synthesis
            max_tokens=500,
            response_format={"type": "text"} # Synthesis is text, not JSON
        )
        interpretation_text = llm_response.choices[0].message.content.strip()

        # 4. Package the response with actual metadata from PromptAssembler
        return SynthesisResponse(
            synthesis_id=uuid.uuid4(),
            interpretation_text=interpretation_text,
            synthesis_rule=synthesis_rule_metadata, # Use metadata from assembler
            components_used=all_components_data, # Pass the full data of components used
            engine_metadata=EngineMetadata(
                calculation_engine="AstrologerAPI_v4_RapidAPI", # From Calculation Service (fixed for MVP)
                interpretive_engine="OpenAI_GPT-4o-mini_2024-07-21" # Current LLM version (fixed for now)
            )
        )

    except (UpstreamServiceError, ComponentNotFoundError, InvalidBirthDataError, SynthesisContentError, SynthesisRateLimitError, ValueError) as e:
        # Re-raise our custom HTTPExceptions and ValueErrors from PromptAssembler directly
        raise e
    except Exception as e:
        # Catch any other unexpected errors and raise a generic 500
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
