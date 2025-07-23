# services/interpretation-service/app/clients.py

import httpx
import asyncio
from typing import Dict, Any, List, Optional

# Import custom exceptions from main.py (assuming they are defined in app/main.py or a shared exceptions.py)
# For simplicity, we'll import them directly from main for now.
# In a larger project, these would typically be in a shared 'app/exceptions.py' file.
from .main import UpstreamServiceError, ComponentNotFoundError, InvalidBirthDataError

# Import schemas from the Calculation Service for type hinting/validation of incoming chart data
# In a real monorepo, these would be imported from a shared package.
# For now, we'll assume the structure matches the Calculation Service's output.
# If we were to define them locally, it would look like this (simplified):
# class CalculatedChartStub(BaseModel):
#     chart_id: str
#     engine_metadata: Dict[str, Any]
#     subject: Dict[str, Any]
#     celestial_points: List[Dict[str, Any]]
#     houses: List[Dict[str, Any]]
#     aspects: List[Dict[str, Any]]


class LexiconServiceClient:
    """
    Client for interacting with the Lexicon Service.
    Encapsulates HTTP calls and basic error handling for Lexicon-specific responses.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        # Add a timeout to the client
        self._client = httpx.AsyncClient(base_url=base_url, timeout=5.0)


    async def get_component_detail(self, component_type: str, component_id: str) -> Dict[str, Any]:
            """Fetches detailed data for a single component from the Lexicon Service with a retry mechanism."""
            # Fix the pluralization for zodiac_signs
            plural_component_types = {
                "planet": "planets",
                "zodiac_sign": "zodiac_signs",
                "node": "nodes", # Add other component types as needed
                "house": "houses", 
                "dynamic": "dynamics",
                "angle": "angles"

            }
            component_type_for_request = plural_component_types.get(component_type, component_type)


            url = f"/components/{component_type_for_request}/{component_id}"
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await self._client.get(url)
                    response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
                    return response.json()
                except httpx.HTTPStatusError as e:
                    # This block handles 4xx/5xx responses, so no retry is needed.
                    # The server responded, but with an error status.
                    try:
                        error_detail = e.response.json()
                    except json.JSONDecodeError:
                        error_detail = {"error": {"message": e.response.text}}

                    if error_detail.get("error", {}).get("code") == "component_not_found":
                        raise ComponentNotFoundError(f"Component '{component_id}' of type '{component_type}' not found.") from e
                    else:
                        raise UpstreamServiceError(f"Lexicon Service returned an error: {e.response.status_code} - {error_detail.get('error', {}).get('message')}") from e

                except httpx.RequestError as e:
                    # This block handles network-level errors, where a retry is appropriate.
                    if attempt < max_retries - 1:
                        print(f"⚠️ Attempt {attempt + 1} failed for {url}. Retrying...")
                        await asyncio.sleep(1) # Wait for 1 second before retrying
                    else:
                        raise UpstreamServiceError(f"Network error contacting Lexicon Service: {e}") from e
                except Exception as e:
                    # Catch any other unexpected errors
                    raise UpstreamServiceError(f"An unexpected error occurred in LexiconServiceClient: {e}") from e

class CalculationServiceClient:
    """
    Client for interacting with the Calculation Service.
    Encapsulates HTTP calls and basic error handling for Calculation-specific responses.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)

    async def get_natal_chart(self, chart_request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches a natal chart from the Calculation Service.
        chart_request_payload should match Calculation Service's ChartRequest schema.
        Returns the raw JSON response (CalculatedChart object).
        """
        try:
            response = await self._client.post("/chart", json=chart_request_payload)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            calculated_chart_data = response.json()

            # Basic validation of calculated_chart_data structure
            if not calculated_chart_data or not isinstance(calculated_chart_data, dict):
                raise InvalidBirthDataError("Calculation service returned invalid or no chart data.")

            return calculated_chart_data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                # Specific error for invalid birth data
                raise InvalidBirthDataError(f"Invalid birth data provided to Calculation Service: {e.response.text}") from e
            elif e.response.status_code == 500 and "Calculation service returned no data" in e.response.text:
                # Catch the specific error from Calculation Service if it returns None
                raise InvalidBirthDataError(f"Calculation service returned no data for provided birth details: {e.response.text}") from e
            # For other HTTP errors from Calculation Service, raise a generic UpstreamServiceError
            raise UpstreamServiceError(f"Calculation Service returned an error: {e.response.status_code} - {e.response.text}") from e
        except httpx.RequestError as e:
            # Network-level errors (DNS, connection refused, timeout)
            raise UpstreamServiceError(f"Network error contacting Calculation Service: {e}") from e
        except Exception as e:
            # Catch any other unexpected errors
            raise UpstreamServiceError(f"An unexpected error occurred in CalculationServiceClient: {e}") from e

    async def aclose(self):
        """Closes the underlying httpx client session."""
        await self._client.aclose()

