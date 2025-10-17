from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TreeData(BaseModel):
    id: Optional[int] = None
    species_id: int
    scientific_name: str
    common_name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    height: float = Field(..., gt=0, le=200)
    width: float = Field(..., gt=0, le=50)
    carbon_seq: float
    oxygen_prod: Optional[float] = None
    estimated_age: Optional[int] = None
    location: str
    date: str
    time: str
    notes: Optional[str] = ""
    created_at: Optional[datetime] = None

class TreeDataUpload(BaseModel):
    trees: List[TreeData]

class AnalysisRequest(BaseModel):
    location: str

class ReportRequest(BaseModel):
    location: str
    format: str = "pdf"

class StatisticsResponse(BaseModel):
    total_trees: int
    total_carbon: float
    total_oxygen: float
    avg_height: float
    avg_width: float
    total_locations: int
    total_species: int
    most_common_species: str
    most_carbon_efficient: str