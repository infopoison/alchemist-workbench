from fastapi import HTTPException, status

# =============================================================================
# I. CUSTOM EXCEPTION CLASSES
# =============================================================================
# These provide standardized error responses as per the API contract.

class UpstreamServiceError(HTTPException):
    """Custom exception for upstream service failures, returns a 503."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": {"code": "upstream_unavailable", "message": detail}})

class ComponentNotFoundError(HTTPException):
    """Custom exception for when a component is not found in the Lexicon Service."""
    def __init__(self, component_id: str, component_type: str):
        detail = f"The requested component '{component_id}' of type '{component_type}' does not exist."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "component_not_found", "message": detail}})

class InvalidBirthDataError(HTTPException):
    """Custom exception for invalid birth data processed by the Calculation Service."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": {"code": "invalid_birth_data", "message": detail}})

class SynthesisContentError(HTTPException):
    """Custom exception for content policy violations from the LLM."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": {"code": "synthesis_content_error", "message": detail}})

class SynthesisRateLimitError(HTTPException):
    """Custom exception for LLM rate limit errors."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={"error": {"code": "synthesis_rate_limited", "message": detail}})

class BadLLMResponseError(HTTPException):
    """Custom exception for when the LLM returns a malformed response."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": {"code": "bad_llm_response", "message": detail}})

