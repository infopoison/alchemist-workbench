# /services/calculation-service/app/main.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import traceback  

from .schemas import ChartRequest, CalculatedChart
from .astrologer_api import AstrologerAPIClient, UpstreamServiceError

load_dotenv()

"""
Removes all time-dependent data from a CalculatedChart object.
This function modifies the chart in-place to:
1.  Remove the entire `houses` list (house cusps).
2.  Filter out the four angles (Ascendant, Descendant, MC, IC) from the celestial points list.
3.  Remove the `house` placement data from all remaining celestial points.
4.  Filter out any aspects that involve one of the removed angles.
5.  Add a `chart_type` flag to indicate the data has been modified.

Args:
    chart: The CalculatedChart object to be pruned.

Returns:
    The modified CalculatedChart object.
"""
def _prune_chart_for_no_time(chart: CalculatedChart) -> CalculatedChart:
    print("-> Pruning chart for 'no time' scenario.")

    # Define the IDs of the angles to be removed
    ANGLE_IDS: Set[str] = {"ascendant", "descendant", "medium_coeli", "imum_coeli"}

    # 1. Remove house cusps by setting the field to None
    chart.houses = None

    # 2. Filter out angles from the list of celestial points
    chart.celestial_points = [
        point for point in chart.celestial_points if point.id not in ANGLE_IDS
    ]

    # 3. Remove house placement from all remaining celestial points
    for point in chart.celestial_points:
        point.house = None

    # 4. Filter out any aspects that involve one of the angles
    if chart.aspects:
        chart.aspects = [
            aspect for aspect in chart.aspects 
            if aspect.point_1_id not in ANGLE_IDS and aspect.point_2_id not in ANGLE_IDS
        ]

    # 5. Add the 'no_time' flag to mark this chart as time-agnostic
    chart.chart_type = "no_time"

    print("-> Pruning complete.")
    return chart

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
    """
    Creates a natal chart. If no birth time is provided, the service returns
    a chart with all time-dependent data (houses, angles) removed.
    """
    api_client: AstrologerAPIClient = request.app.state.api_client

    is_no_time_request = chart_request.time is None
    if is_no_time_request:
        print("Received a 'no birth time' request. A default time of noon will be used for the external API call.")

    # The API client will handle using a default time if chart_request.time is None.
    try:
        calculated_chart = await api_client.get_natal_chart(chart_request)
    except Exception as e:
        print(f"Error calling get_natal_chart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chart from upstream API: {str(e)}")

    if is_no_time_request and calculated_chart:
        calculated_chart = _prune_chart_for_no_time(calculated_chart)


    if calculated_chart is None:
        print("calculated_chart is None! This is why a validation error might occur.")
        raise HTTPException(status_code=500, detail="Calculation service returned no data.")

    return calculated_chart


@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "Calculation Service is operational"}