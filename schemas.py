"""
Database Schemas for Diabetes Health Management App

Each Pydantic model maps to a MongoDB collection whose name is the lowercase
of the class name (e.g., GlucoseReading -> "glucosereading").

These schemas are used for validating request bodies before storing them.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# Core domain schemas

class GlucoseReading(BaseModel):
    timestamp: datetime = Field(..., description="When the reading was taken (ISO8601)")
    value_mgdl: float = Field(..., ge=20, le=600, description="Glucose value in mg/dL")
    mode: Literal["manual", "cgm"] = Field("manual", description="Reading source")
    note: Optional[str] = Field(None, description="Optional note about context")
    meal_context: Optional[Literal["pre", "post", "none"]] = Field(
        None, description="Relation to a meal if known"
    )

class Meal(BaseModel):
    timestamp: datetime = Field(..., description="When the meal was consumed")
    name: str = Field(..., description="Short name, e.g., 'Dal Khichdi, 2 bowls'")
    carbs_g: Optional[float] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)
    fat_g: Optional[float] = Field(None, ge=0)
    calories: Optional[float] = Field(None, ge=0)
    note: Optional[str] = None

class MedicationLog(BaseModel):
    timestamp: datetime = Field(..., description="When the dose was taken")
    type: Literal["oral", "insulin", "mixed"] = Field(...)
    brand: Optional[str] = None
    dose_units: Optional[float] = Field(None, ge=0, description="Units for insulin or mg for oral")
    frequency: Optional[str] = Field(None, description="e.g., once daily, with meals")
    note: Optional[str] = None

class Activity(BaseModel):
    timestamp: datetime = Field(...)
    kind: Literal["walk", "run", "cycle", "gym", "other"] = Field("walk")
    duration_min: float = Field(..., ge=0)
    calories: Optional[float] = Field(None, ge=0)
    note: Optional[str] = None

class Reminder(BaseModel):
    label: str
    time_local: str = Field(..., description="HH:MM 24h format in user's local time")
    type: Literal["glucose", "meal", "medication", "activity"]
    enabled: bool = True

# Lightweight request model for insights windows
class InsightsWindow(BaseModel):
    days: int = Field(14, ge=1, le=90)
"""
# Notes:
# - Collections will be named: 'glucosereading', 'meal', 'medicationlog', 'activity', 'reminder'
# - Timestamps are stored as UTC datetimes by database helpers with created_at/updated_at
"""
