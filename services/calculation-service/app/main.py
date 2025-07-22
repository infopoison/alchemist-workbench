# /services/calculation-service/app/main.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import traceback  

from .schemas import ChartRequest, CalculatedChart
from .astrologer_api import AstrologerAPIClient, UpstreamServiceError

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Calculation Service starting up...")
    app.state.api_client = AstrologerAPIClient()
    yield
    print("Calculation Service shutting down...")

app = FastAPI(
    title="Alchemical Workbench - Calculation Service",
    description="Provides accurate astrological calculations via a strategic firewall.",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(UpstreamServiceError)
async def upstream_service_unavailable_handler(request: Request, exc: UpstreamServiceError):
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "upstream_unavailable", "message": str(exc)}},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # --- CHANGE: PRINT THE FULL TRACEBACK TO THE CONSOLE ---
    print("--- An unexpected error occurred ---")
    traceback.print_exc()
    print("------------------------------------")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected internal error occurred in the Calculation Service."
            }
        },
    )

@app.post("/chart", response_model=CalculatedChart, tags=["Calculation"])
async def create_chart(chart_request: ChartRequest, request: Request):
    api_client: AstrologerAPIClient = request.app.state.api_client
    
    print(f"Calling get_natal_chart with: {chart_request.dict()}") # Debugging input
    
    calculated_chart = None # Initialize to None for safety in case of exception before assignment
    try:
        calculated_chart = await api_client.get_natal_chart(chart_request)
        print(f"Result from get_natal_chart: {calculated_chart}") # THIS IS KEY
    except Exception as e:
        print(f"Error calling get_natal_chart: {e}")
        # Depending on your desired error handling, you might re-raise,
        # return an error response, etc. For now, let's just observe.

    # After the print, if `calculated_chart` is None, this is your problem source.
    if calculated_chart is None:
        print("calculated_chart is None! This is why the ResponseValidationError occurs.")
        # You would typically return an HTTPException here for a real API
        raise HTTPException(status_code=500, detail="Calculation service returned no data.")

    return calculated_chart


@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "Calculation Service is operational"}