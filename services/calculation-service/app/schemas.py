# /services/calculation-service/app/schemas.py

from pydantic import BaseModel, Field
from typing import List
import uuid

# --- Request & Response Schemas ---

class ChartRequest(BaseModel):
    name: str = Field(..., example="John Doe")
    city: str = Field(..., example="Los Angeles")
    date: str = Field(..., example="1990-10-28")
    time: str = Field(..., example="09:30:00")
    latitude: float = Field(..., example=34.0522)
    longitude: float = Field(..., example=-118.2437)
    timezone: str = Field(..., example="America/Los_Angeles")

class EngineMetadata(BaseModel):
    calculation_engine: str

class Subject(BaseModel):
    date: str
    time: str
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
    house: House

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
    chart_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    engine_metadata: EngineMetadata
    subject: Subject
    celestial_points: List[CelestialPoint]
    houses: List[HouseCusp]
    aspects: List[Aspect]