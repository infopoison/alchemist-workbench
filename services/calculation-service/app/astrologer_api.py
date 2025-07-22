# /services/calculation-service/app/astrologer_api.py

import httpx
import os
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import uuid # Make sure uuid is imported here
from .schemas import ChartRequest, CalculatedChart, EngineMetadata, Subject, CelestialPoint, HouseCusp, Aspect, ZodiacSign, House


class UpstreamServiceError(Exception):
    """Custom exception for upstream service failures."""
    pass


class AstrologerAPIClient:
    """
    A client for the RapidAPI version of the AstrologerAPI service.
    Acts as the anti-corruption layer, translating external responses
    into our immutable internal CalculatedChart contract.
    """

    def __init__(self):
        self.base_url = os.getenv("ASTROLOGER_API_BASE_URL")
        self.api_key = os.getenv("ASTROLOGER_API_KEY")
        if not self.api_key or not self.base_url:
            raise ValueError("ASTROLOGER_API_KEY and ASTROLOGER_API_BASE_URL must be set.")

        self.headers = {
            'X-RapidAPI-Host': self.base_url.replace("https://", ""),
            'X-RapidAPI-Key': self.api_key,
            'Content-Type': 'application/json'
        }

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    async def get_natal_chart(self, request_data: ChartRequest) -> CalculatedChart:
        """
        Fetches the natal chart from the external API and maps it to our internal schema.
        """
        date_parts = request_data.date.split('-')
        time_parts = request_data.time.split(':')

        api_payload = {
            "subject": {
                "name": request_data.name,
                "city": request_data.city,
                "year": int(date_parts[0]),
                "month": int(date_parts[1]),
                "day": int(date_parts[2]),
                "hour": int(time_parts[0]),
                "minute": int(time_parts[1]),
                "latitude": request_data.latitude,
                "longitude": request_data.longitude,
                "timezone": request_data.timezone
            }
        }

        natal_chart_endpoint = "/api/v4/birth-chart"

        async with httpx.AsyncClient() as client:
            try:
                print(f"[{self.__class__.__name__}] Sending payload to external API: {json.dumps(api_payload, indent=2)}")
                print(f"[{self.__class__.__name__}] Full URL being requested: {self.base_url + natal_chart_endpoint}") # ADD THIS LINE
                response = await client.post(
                    self.base_url + natal_chart_endpoint,
                    json=api_payload,
                    headers=self.headers,
                    timeout=30.0
                )

                response.raise_for_status()

                raw_api_data = response.json()
                print(f"[{self.__class__.__name__}] Received raw data from external API: {json.dumps(raw_api_data, indent=2)}")

                calculated_chart_instance = self._map_to_internal_schema(raw_api_data, request_data)

                return calculated_chart_instance

            except httpx.HTTPStatusError as e:
                print(f"[{self.__class__.__name__}] HTTP error from upstream service: {e.response.status_code} - {e.response.text}")
                raise UpstreamServiceError(f"Upstream service returned error: {e.response.status_code} - {e.response.text}") from e
            except httpx.RequestError as e:
                print(f"[{self.__class__.__name__}] Network error contacting upstream service: {e}")
                raise UpstreamServiceError(f"Network error contacting upstream service: {e}") from e
            except json.JSONDecodeError as e:
                print(f"[{self.__class__.__name__}] Error decoding JSON response from upstream service: {e}")
                print(f"[{self.__class__.__name__}] Raw response text (if available): {getattr(response, 'text', 'N/A')}")
                raise UpstreamServiceError(f"Invalid JSON response from upstream service: {e}") from e
            except Exception as e:
                print(f"[{self.__class__.__name__}] An unexpected error occurred during chart calculation: {e}")
                raise UpstreamServiceError(f"Unexpected error in chart calculation: {e}") from e

    def _map_to_internal_schema(self, data: dict, req: ChartRequest) -> CalculatedChart:
        """
        Maps the external API response to our internal schema.
        """
        # Extract the main 'data' block from the API response
        subject_and_points_data = data.get('data', {})

        # Subject mapping - Ensure it pulls from the API's 'data' section
        mapped_subject = Subject(
            name=subject_and_points_data.get('name', req.name),
            city=subject_and_points_data.get('city', req.city),
            date=req.date, # Keeping original request date/time, as API provides ISO formatted string
            time=req.time,
            latitude=subject_and_points_data.get('lat', req.latitude), # API uses 'lat'
            longitude=subject_and_points_data.get('lng', req.longitude), # API uses 'lng'
            timezone=subject_and_points_data.get('tz_str', req.timezone) # API uses 'tz_str'
        )

        celestial_points = []
        # The API response lists planet/axial cusp names in 'planets_names_list' and 'axial_cusps_names_list'
        # Then, each planet/cusp's data is a direct key in the 'data' object.
        all_point_keys = subject_and_points_data.get('planets_names_list', []) + \
                         subject_and_points_data.get('axial_cusps_names_list', [])

        for point_key_raw in all_point_keys:
            # The API uses lower_case for keys, but sometimes Title_Case for values
            point_key = point_key_raw.lower() # Ensure key lookup is lowercase
            point_data = subject_and_points_data.get(point_key, {})

            if not point_data:
                print(f"Warning: No data found for point '{point_key}'")
                continue # Skip if data for this point is missing

            # Clean name from API (e.g., "Mean_Node" -> "Mean Node")
            clean_name = point_data.get('name', point_key_raw).replace("_", " ").title()

            try:
                celestial_points.append(CelestialPoint(
                    id=point_key,
                    name=clean_name,
                    position_longitude=point_data['position'],
                    absolute_longitude=point_data['abs_pos'],
                    speed=point_data.get('speed', 0.0),
                    is_retrograde=point_data.get('retrograde', False),
                    zodiac_sign=ZodiacSign(
                        id=point_data['sign'].lower(),
                        name=point_data['sign']
                    ),
                    # The 'house' field from API is a string like "Eleventh_House"
                    house=House(
                        id=point_data['house'].lower(),
                        name=point_data['house'].replace("_", " ") # e.g., "Eleventh House"
                    )
                ))
            except KeyError as e:
                print(f"Error mapping CelestialPoint for '{point_key_raw}': Missing key {e}. Data: {point_data}")
            except Exception as e:
                print(f"Unexpected error mapping CelestialPoint for '{point_key_raw}': {e}. Data: {point_data}")


        house_cusps = []
        house_name_map = {
            "first_house": 1, "second_house": 2, "third_house": 3, "fourth_house": 4,
            "fifth_house": 5, "sixth_house": 6, "seventh_house": 7, "eighth_house": 8,
            "ninth_house": 9, "tenth_house": 10, "eleventh_house": 11, "twelfth_house": 12
        }

        for house_key_raw in subject_and_points_data.get('houses_names_list', []):
            # Convert the key from 'First_House' (from list) to 'first_house' (actual dict key)
            normalized_house_key = house_key_raw.lower() # <--- NEW LINE
            house_data = subject_and_points_data.get(normalized_house_key, {}) # <--- CHANGED HERE
            
            if not house_data:
                # This warning should now disappear!
                print(f"Warning: No data found for house '{house_key_raw}' (after normalization: '{normalized_house_key}')")
                continue

            house_num = house_name_map.get(normalized_house_key, 0) # Use normalized key here too

            suffix = "th"
            if 10 <= house_num % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(house_num % 10, "th")

            try:
                house_cusps.append(HouseCusp(
                    id=normalized_house_key, # Use the normalized key for ID
                    name=f"{house_num}{suffix} House",
                    position_longitude=house_data['position'],
                    absolute_longitude=house_data['abs_pos'],
                    zodiac_sign=ZodiacSign(id=house_data['sign'].lower(), name=house_data['sign'])
                ))
            except KeyError as e:
                print(f"Error mapping HouseCusp for '{house_key_raw}': Missing key {e}. Data: {house_data}")
            except Exception as e:
                print(f"Unexpected error mapping HouseCusp for '{house_key_raw}': {e}. Data: {house_data}")

        aspects = []
        # Aspects are directly under the root of the API response, not under 'data'
        for aspect_data in data.get('aspects', []):
            try:
                aspects.append(Aspect(
                    point_1_id=aspect_data['p1_name'].lower(),
                    point_2_id=aspect_data['p2_name'].lower(),
                    aspect_id=aspect_data['aspect'].lower().replace(" ", "_"),
                    aspect_name=aspect_data['aspect'],
                    orb=aspect_data['orbit']
                ))
            except KeyError as e:
                print(f"Error mapping Aspect: Missing key {e}. Data: {aspect_data}")
            except Exception as e:
                print(f"Unexpected error mapping Aspect: {e}. Data: {aspect_data}")


        return CalculatedChart(
            chart_id=uuid.uuid4(),
            engine_metadata=EngineMetadata(calculation_engine="AstrologerAPI_v4_RapidAPI"),
            subject=mapped_subject,
            celestial_points=celestial_points,
            houses=house_cusps,
            aspects=aspects
        )