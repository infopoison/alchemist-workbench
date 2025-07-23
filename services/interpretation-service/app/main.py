# services/interpretation-service/app/main.py

import json
import os
import traceback
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from openai import OpenAI, OpenAIError

# Import refactored Pydantic schemas for the new two-stage flow
from .schemas import (
    DeconstructRequest, DeconstructResponse,
    ValenceRequest, ValenceResponse,
    ManifestationRequest, ManifestationResponse,
    EngineMetadata
)

# Import the refactored PromptAssembler
from .exceptions import UpstreamServiceError, ComponentNotFoundError, InvalidBirthDataError
from .prompt_assembler import PromptAssembler

# Import the service clients
from .clients import LexiconServiceClient, CalculationServiceClient

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# II. APPLICATION LIFESPAN & STATE MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    print("Interpretation Service starting up...")
    
    # Retrieve and validate necessary environment variables
    lexicon_url = os.getenv("LEXICON_SERVICE_URL")
    calc_url = os.getenv("CALCULATION_SERVICE_URL")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not all([lexicon_url, calc_url, openai_key]):
        raise ValueError("Missing one or more required environment variables (LEXICON_SERVICE_URL, CALCULATION_SERVICE_URL, OPENAI_API_KEY).")

    # Initialize clients and the prompt assembler, storing them in app.state
    app.state.lexicon_client = LexiconServiceClient(base_url=lexicon_url)
    app.state.calculation_client = CalculationServiceClient(base_url=calc_url)
    app.state.openai_client = OpenAI(api_key=openai_key)
    app.state.prompt_assembler = PromptAssembler(
        lexicon_client=app.state.lexicon_client,
        calculation_client=app.state.calculation_client
    )
    
    yield
    
    print("Interpretation Service shutting down...")
    # Gracefully close client connections on shutdown
    await app.state.lexicon_client.aclose()
    await app.state.calculation_client.aclose()


# =============================================================================
# III. FASTAPI APPLICATION & EXCEPTION HANDLERS
# =============================================================================

app = FastAPI(
    title="Alchemical Workbench - Interpretation Service",
    description="Orchestrates the two-stage valence and manifestation synthesis process.",
    version="2.0.0", # Version updated to reflect major refactor
    lifespan=lifespan
)

# Define a generic exception handler for unexpected errors
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print("--- An unexpected error occurred in Interpretation Service ---")
    traceback.print_exc()
    print("----------------------------------------------------------")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected internal error occurred."
            }
        },
    )


# =============================================================================
# IV. API ENDPOINTS
# =============================================================================

@app.get("/", tags=["Health Check"])
async def health_check():
    """Provides a simple health check endpoint."""
    return {"status": "Interpretation Service is operational"}

@app.post("/interpret/deconstruct", response_model=DeconstructResponse, tags=["Interpretation"])
async def deconstruct_component(request_data: DeconstructRequest, request: Request):
    """
    Generates a concise, archetypal definition for a single component by
    fetching its canonical data directly from the Lexicon Service.
    This endpoint does NOT call the LLM.
    """
    lexicon_client = request.app.state.lexicon_client
    try:
        component_data = await lexicon_client.get_component_detail(
            request_data.component.type, request_data.component.id
        )
        
        # Construct definition from structured data to ensure consistency
        display_content = component_data.get('display_content', {})
        principle = display_content.get('principle', '')
        core_concept = display_content.get('core_concept', '')
        definition_text = f"Principle: {principle}. Core Concept: {core_concept}".strip()

        return DeconstructResponse(
            component_id=request_data.component.id,
            definition_text=definition_text
        )
    except (ComponentNotFoundError, UpstreamServiceError) as e:
        raise e # Re-raise known exceptions to be handled by FastAPI


@app.post("/interpret/valences", response_model=ValenceResponse, tags=["Interpretation"])
async def get_valences(request_data: ValenceRequest, request: Request):
    """
    **Stage 1 of Synthesis:** Generates a list of potential archetypal expressions
    (valences) for a given astrological signature.
    """
    prompt_assembler = request.app.state.prompt_assembler
    openai_client = request.app.state.openai_client

    try:
        # Assemble the rule-based prompt for valence generation
        prompt_info = await prompt_assembler.assemble_valence_prompt(
            components_input=[c.dict() for c in request_data.components],
            birth_data=request_data.birth_data.dict() if request_data.birth_data else None
        )

        # Call the LLM to generate valences
        llm_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_info["prompt_text"]}],
            response_format={"type": "json_object"}
        )
        
        response_content = llm_response.choices[0].message.content
        valences_data = json.loads(response_content)

        # Construct and return the transparent response object
        return ValenceResponse(
            valences=valences_data.get("valences", []),
            synthesis_rule=prompt_info["synthesis_rule_metadata"],
            components_used=prompt_info["components_used"],
            engine_metadata=EngineMetadata(
                calculation_engine="AstrologerAPI_v1.0", # Example, would be dynamic
                interpretive_engine="OpenAI_GPT-4o-mini_2024-07-22"
            )
        )
    except (ComponentNotFoundError, UpstreamServiceError, ValueError) as e:
        raise e
    except OpenAIError as e:
        # Handle specific OpenAI errors
        if "rate limit" in str(e):
            raise SynthesisRateLimitError("The synthesis engine is experiencing high demand.")
        if "content management policy" in str(e):
            raise SynthesisContentError("The interpretation could not be generated due to a content policy violation.")
        raise UpstreamServiceError(f"An error occurred with the synthesis engine: {e}")
    except json.JSONDecodeError:
        raise BadLLMResponseError("The synthesis engine returned a malformed response.")


@app.post("/interpret/manifestations", response_model=ManifestationResponse, tags=["Interpretation"])
async def get_manifestations(request_data: ManifestationRequest, request: Request):
    """
    **Stage 2 of Synthesis:** Generates detailed manifestations for a chosen valence
    for a single, specified life area.
    """
    prompt_assembler = request.app.state.prompt_assembler
    openai_client = request.app.state.openai_client

    try:
        # Assemble the prompt for the specific life area provided in the request
        prompt = prompt_assembler.assemble_manifestation_prompt(
            components_input=[c.dict() for c in request_data.components],
            chosen_valence=request_data.chosen_valence,
            life_area=request_data.life_area
        )

        # Make a single call to the LLM
        llm_response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        response_content = llm_response.choices[0].message.content
        manifestation_data = json.loads(response_content)

        # The key in the LLM's response will match the requested life_area.
        # We extract the list of patterns from that key.
        manifestations_list = manifestation_data.get(request_data.life_area, [])

        # Return the simplified response object
        return ManifestationResponse(
            manifestations=manifestations_list,
            engine_metadata=EngineMetadata(
                interpretive_engine="OpenAI_GPT-4o-mini_2024-07-22"
            )
        )
    except (ComponentNotFoundError, UpstreamServiceError, ValueError) as e:
        raise e
    except OpenAIError as e:
        if "rate limit" in str(e):
            raise SynthesisRateLimitError("The synthesis engine is experiencing high demand.")
        if "content management policy" in str(e):
            raise SynthesisContentError("The interpretation could not be generated due to a content policy violation.")
        raise UpstreamServiceError(f"An error occurred with the synthesis engine: {e}")
    except json.JSONDecodeError:
        raise BadLLMResponseError("The synthesis engine returned a malformed response.")
    except Exception as e:
        print(f"An unexpected error occurred during manifestation generation: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to generate manifestations.")
