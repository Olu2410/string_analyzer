import os
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Dict, Any
import re

from app import schemas, services, storage

app = FastAPI(title="String Analyzer Service", version="1.0.0")

# Initialize storage
string_storage = storage.InMemoryStringStorage()
string_service = services.StringAnalyzerService(string_storage)

@app.post("/strings", response_model=schemas.StringAnalysisResponse, status_code=201)
async def create_analyze_string(request: schemas.StringCreateRequest):
    """
    Create and analyze a new string
    """
    try:
        result = string_service.analyze_and_store_string(request.value)
        return result
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/strings/{string_value}", response_model=schemas.StringAnalysisResponse)
async def get_string(string_value: str):
    """
    Get analysis for a specific string
    """
    try:
        result = string_service.get_string_analysis(string_value)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/strings", response_model=schemas.StringListResponse)
async def get_all_strings(
    is_palindrome: Optional[bool] = Query(None, description="Filter by palindrome status"),
    min_length: Optional[int] = Query(None, ge=0, description="Minimum string length"),
    max_length: Optional[int] = Query(None, ge=0, description="Maximum string length"),
    word_count: Optional[int] = Query(None, ge=0, description="Exact word count"),
    contains_character: Optional[str] = Query(None, max_length=1, description="Single character to search for")
):
    """
    Get all strings with optional filtering
    """
    try:
        filters = {}
        if is_palindrome is not None:
            filters['is_palindrome'] = is_palindrome
        if min_length is not None:
            filters['min_length'] = min_length
        if max_length is not None:
            filters['max_length'] = max_length
        if word_count is not None:
            filters['word_count'] = word_count
        if contains_character is not None:
            filters['contains_character'] = contains_character
            
        results = string_service.get_strings_with_filters(filters)
        
        return schemas.StringListResponse(
            data=results,
            count=len(results),
            filters_applied=filters
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/strings/filter-by-natural-language", response_model=schemas.NaturalLanguageFilterResponse)
async def filter_by_natural_language(query: str = Query(..., description="Natural language query")):
    """
    Filter strings using natural language queries
    """
    try:
        results, parsed_filters = string_service.filter_by_natural_language(query)
        
        return schemas.NaturalLanguageFilterResponse(
            data=results,
            count=len(results),
            interpreted_query={
                "original": query,
                "parsed_filters": parsed_filters
            }
        )
    except ValueError as e:
        if "Unable to parse" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        elif "conflicting" in str(e):
            raise HTTPException(status_code=422, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/strings/{string_value}", status_code=204)
async def delete_string(string_value: str):
    """
    Delete a string analysis
    """
    try:
        string_service.delete_string(string_value)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/")
async def root():
    return {"message": "String Analyzer Service is running"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)