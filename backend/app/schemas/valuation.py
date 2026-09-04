from typing import Optional

from pydantic import BaseModel, Field


class PropertyValuationRequest(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    neighborhood: str = Field(min_length=1, max_length=150)
    area: float = Field(gt=0, le=5000)
    building_age: int = Field(default=0, ge=0, le=200)
    rooms: Optional[int] = Field(default=None, ge=0, le=20)
    floor: Optional[int] = Field(default=None, ge=-5, le=200)
    elevator: bool = False
    parking: bool = False
    storage: bool = False
    property_condition: str = Field(default="good", min_length=1, max_length=40)


class PropertyValuationResponse(BaseModel):
    estimation_type: str
    city: str
    neighborhood: str
    area: float
    estimated_total_price: float
    estimated_price_per_sqm: float
    price_range_min: float
    price_range_max: float
    confidence: float
    confidence_label: str
    market_samples_used: int
    model_name: str
    influential_factors: list[str]
    explanation: str
    model_note: str


class ProjectValuationRequest(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    neighborhood: str = Field(min_length=1, max_length=150)
    total_units: int = Field(gt=0, le=100000)
    average_unit_area: float = Field(gt=0, le=5000)
    total_area: Optional[float] = Field(default=None, gt=0, le=500000000)
    building_type: str = Field(default="standard", min_length=1, max_length=60)


class ProjectValuationResponse(BaseModel):
    estimation_type: str
    city: str
    neighborhood: str
    total_units: int
    average_unit_area: float
    total_area: float
    estimated_total_project_value: float
    estimated_value_per_unit: float
    estimated_price_per_sqm: float
    price_range_min: float
    price_range_max: float
    confidence: float
    confidence_label: str
    market_samples_used: int
    model_name: str
    influential_factors: list[str]
    explanation: str
    model_note: str
