from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class StringProperties(BaseModel):
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: Dict[str, int]

class StringAnalysisResponse(BaseModel):
    id: str
    value: str
    properties: StringProperties
    created_at: datetime

class StringCreateRequest(BaseModel):
    value: str = Field(..., min_length=1, description="String to analyze")

class StringListResponse(BaseModel):
    data: List[StringAnalysisResponse]
    count: int
    filters_applied: Dict[str, Any]

class NaturalLanguageFilterResponse(BaseModel):
    data: List[StringAnalysisResponse]
    count: int
    interpreted_query: Dict[str, Any]