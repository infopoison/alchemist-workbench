# /validation/validate_calculation_engine.py

import httpx
import json
from deepdiff import DeepDiff
import asyncio

# --- Configuration ---
CALCULATION_SERVICE_URL = "http://localhost:8002/chart"
# Using a simple, free benchmark API for this validation test.
# NOTE: In a real production scenario, we'd use a paid, high-precision service like Astro-Seek's API.
BENCHMARK_API_URL = "https://json.astrologyapi.com/v1/western_chart"
GOLDEN_DATASET_FILE = "golden_birth_data.json"

# Load API key for benchmark service if needed (update if your benchmark requires one)
# from dotenv import load_dotenv
# import os
# load_dotenv(dotenv_path='../services/calculation-service/.env')
# BENCHMARK_API_KEY = os.getenv("ASTROLOGER_API_KEY")


def load_golden_dataset():
    """Loads the golden dataset from the JSON file."""
    try:
        with open(GOLDEN_DATASET_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Golden dataset file not found at '{GOLDEN_DATASET_FILE}'")
        return []

async def get_alchemical_workbench_chart(client, birth_data):
    """Gets a chart from our local Calculation Service."""
    try:
        response = await client.post(CALCULATION_SERVICE_URL, json=birth_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"\nERROR calling Alchemical Workbench service: {e}")
        return None

async def get_benchmark_chart(client, birth_data):
    """Gets a chart from the external benchmark API."""
    # This function needs to be adapted to the specific benchmark API's request format.
    # The astrologyapi.com format is used here as an example.
    api_payload = {
        "day": int(birth_data["date"].split('-')[2]),
        "month": int(birth_data["date"].split('-')[1]),
        "year": int(birth_data["date"].split('-')[0]),
        "hour": int(birth_data["time"].split(':')[0]),
        "min": int(birth_data["time"].split(':')[1]),
        "lat": birth_data["latitude"],
        "lon": birth_data["longitude"],
        "tzone": 5.5 # Example, this API uses a numeric timezone offset
    }
    try:
        # Update auth if your benchmark requires it
        # auth = (BENCHMARK_API_KEY.split(':')[0], BENCHMARK_API_KEY.split(':')[1])
        response = await client.post(BENCHMARK_API_URL, json=api_payload, timeout=30) # auth=auth
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"\nERROR calling Benchmark API: {e}")
        return None

def compare_charts(aw_chart, benchmark_chart):
    """
    Compares the absolute longitude of planets between the two charts.
    Returns a dictionary of discrepancies.
    """
    discrepancies = {}
    
    # Extract planet positions from our service
    aw_planets = {p['id']: p['absolute_longitude'] for p in aw_chart.get('celestial_points', [])}
    
    # Extract planet positions from benchmark service (structure might differ)
    benchmark_planets = {p['name'].lower(): p['fullDegree'] for p in benchmark_chart.get('planets', [])}

    all_planet_ids = set(aw_planets.keys()) | set(benchmark_planets.keys())

    for planet_id in sorted(list(all_planet_ids)):
        aw_pos = aw_planets.get(planet_id)
        bench_pos = benchmark_planets.get(planet_id)

        if aw_pos is None or bench_pos is None:
            discrepancies[planet_id] = f"Present in one chart but not the other (AW: {aw_pos}, Benchmark: {bench_pos})"
            continue

        # Compare positions with a tolerance for minor floating point differences
        if abs(aw_pos - bench_pos) > 0.1: # Allowing a 0.1 degree tolerance
            discrepancies[planet_id] = {
                "alchemical_workbench": aw_pos,
                "benchmark": bench_pos,
                "difference": abs(aw_pos - bench_pos)
            }
            
    return discrepancies

async def main():
    print("--- Starting Calculation Engine Audit ---")
    golden_dataset = load_golden_dataset()
    
    if not golden_dataset:
        return

    async with httpx.AsyncClient() as client:
        for i, birth_data in enumerate(golden_dataset):
            print(f"\n=> Processing Test Case {i+1}/{len(golden_dataset)}: {birth_data['name']}")
            
            # Run requests in parallel
            aw_chart_task = get_alchemical_workbench_chart(client, birth_data)
            benchmark_chart_task = get_benchmark_chart(client, birth_data)
            
            aw_chart, benchmark_chart = await asyncio.gather(aw_chart_task, benchmark_chart_task)

            if not aw_chart or not benchmark_chart:
                print("   Skipping comparison due to an error fetching data.")
                continue

            print("   Comparing planetary positions...")
            discrepancies = compare_charts(aw_chart, benchmark_chart)

            if not discrepancies:
                print("   ✅ PASS: No significant discrepancies found.")
            else:
                print("   ❌ FAIL: Discrepancies found!")
                for planet, diff in discrepancies.items():
                    print(f"     - {planet.capitalize()}: {diff}")

    print("\n--- Audit Complete ---")

if __name__ == "__main__":
    asyncio.run(main())