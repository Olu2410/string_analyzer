import os
from fastapi import FastAPI, HTTPException, Query, status
from typing import Optional, List, Dict, Any
import re
from datetime import datetime
import hashlib



app = FastAPI(title="String Analyzer Service", version="1.0.0")

# In-memory storage
storage = {}

def analyze_string(text: str) -> Dict[str, Any]:
    """
    Analyze a string and compute the following:
    - length: number of characters
    - is_palindrome: case-insensitive check ignoring spaces/special chars
    - unique_characters: count of distinct characters
    - word_count: words separated by whitespace
    - sha256_hash: hash for unique identification
    - character_frequency_map: dict mapping each character to its count
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")

    # Remove leading/trailing whitespace but keep internal spaces
    cleaned_text = text.strip()

    # Compute properties
    length = len(cleaned_text)

    # Palindrome check (case-insensitive, ignore non-alphanumeric)
    cleaned_for_palindrome = re.sub(r'[^a-zA-Z0-9]', '', cleaned_text.lower())
    is_palindrome = cleaned_for_palindrome == cleaned_for_palindrome[::-1] if cleaned_for_palindrome else False

    # Unique characters
    unique_characters = len(set(cleaned_text))

    # Word count (split by any whitespace)
    word_count = len(cleaned_text.split())

    # SHA-256 hash
    sha256_hash = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()

    # Character frequency map
    character_frequency_map = {}
    for char in cleaned_text:
        character_frequency_map[char] = character_frequency_map.get(char, 0) + 1

    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha256_hash,
        "character_frequency_map": character_frequency_map,
    }



@app.post("/strings", status_code=status.HTTP_201_CREATED)
async def create_analyze_string(request: dict):
    """
    Create and analyze a new string
    """
    # Validate request body exists and has 'value' field
    if not request or "value" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body or missing 'value' field"
        )
    
    value = request["value"]
    
    # Validate data type
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Invalid data type for 'value' (must be string)"
        )
    
    # Validate value is not empty string
    if not value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body or missing 'value' field"
        )
    
    # Check if string already exists
    if value in storage:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="String already exists in the system"
        )
    
    # Analyze string
    properties = analyze_string(value)
    
    # Store result
    result = {
        "id": properties["sha256_hash"],
        "value": value,
        "properties": properties,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    storage[value] = result
    
    return result


@app.get("/strings/{string_value}", status_code=status.HTTP_200_OK)
async def get_string(string_value: str):
    """
    Get analysis for a specific string
    """
    if string_value not in storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="String does not exist in the system"
        )
    
    return storage[string_value]



@app.get("/strings", status_code=status.HTTP_200_OK)
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
        # Validate query parameters
        errors = []
        
        # Validate min_length and max_length relationship
        if min_length is not None and max_length is not None:
            if min_length > max_length:
                errors.append("min_length cannot be greater than max_length")
        
        # Validate contains_character is a single character
        if contains_character is not None:
            if len(contains_character) != 1:
                errors.append("contains_character must be a single character")
            elif not contains_character.isprintable():
                errors.append("contains_character must be a printable character")
        
        # Validate word_count is reasonable
        if word_count is not None and word_count > 1000:  # Arbitrary large limit
            errors.append("word_count value is too large")
        
        # Validate length parameters are reasonable
        if min_length is not None and min_length > 10000:  # Arbitrary large limit
            errors.append("min_length value is too large")
        
        if max_length is not None and max_length > 10000:  # Arbitrary large limit
            errors.append("max_length value is too large")
        
        # If there are validation errors, raise 400
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid query parameter values or types"
            )
        
        # Build filters dictionary
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
        
        # Apply filters
        filtered_strings = []
        
        for analysis in storage.values():
            matches = True
            props = analysis["properties"]
            
            if 'is_palindrome' in filters and props['is_palindrome'] != filters['is_palindrome']:
                matches = False
                
            if 'min_length' in filters and props['length'] < filters['min_length']:
                matches = False
                
            if 'max_length' in filters and props['length'] > filters['max_length']:
                matches = False
                
            if 'word_count' in filters and props['word_count'] != filters['word_count']:
                matches = False
                
            if 'contains_character' in filters:
                char = filters['contains_character']
                if char not in analysis["value"]:
                    matches = False
            
            if matches:
                filtered_strings.append(analysis)
        
        return {
            "data": filtered_strings,
            "count": len(filtered_strings),
            "filters_applied": filters
        }
        
    except ValueError as e:
        # This will catch any FastAPI validation errors for query parameters
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid query parameter values or types"
        )


@app.get("/strings/filter-by-natural-language", status_code=status.HTTP_200_OK)
async def filter_by_natural_language(query: str = Query(..., description="Natural language query")):
    """
    Filter strings using natural language queries
    """
    query_lower = query.lower()
    parsed_filters = {}
    
    # Parse natural language query
    if "palindromic" in query_lower or "palindrome" in query_lower:
        parsed_filters['is_palindrome'] = True
    
    # Word count patterns
    word_count_match = re.search(r'single\s+word|one\s+word|word\s+count\s*[=:]?\s*1', query_lower)
    if word_count_match:
        parsed_filters['word_count'] = 1
    
    # Length patterns
    longer_match = re.search(r'longer\s+than\s+(\d+)', query_lower)
    if longer_match:
        parsed_filters['min_length'] = int(longer_match.group(1)) + 1
    
    shorter_match = re.search(r'shorter\s+than\s+(\d+)', query_lower)
    if shorter_match:
        parsed_filters['max_length'] = int(shorter_match.group(1)) - 1
    
    exact_length_match = re.search(r'length\s+(\d+)|(\d+)\s+characters', query_lower)
    if exact_length_match:
        length = int(exact_length_match.group(1) or exact_length_match.group(2))
        parsed_filters['min_length'] = length
        parsed_filters['max_length'] = length
    
    # Character containment patterns
    char_match = re.search(r'contain(?:s|ing)?\s+(?:the\s+)?(?:letter\s+)?([a-zA-Z])', query_lower)
    if char_match:
        parsed_filters['contains_character'] = char_match.group(1).lower()
    
    vowel_match = re.search(r'vowel', query_lower)
    if vowel_match and 'contains_character' not in parsed_filters:
        # Default to 'a' as the first vowel
        parsed_filters['contains_character'] = 'a'
    
    # Validate that we could parse something
    if not parsed_filters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse natural language query"
        )
    
    # Check for conflicting filters
    if ('min_length' in parsed_filters and 'max_length' in parsed_filters and 
        parsed_filters['min_length'] > parsed_filters['max_length']):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parsed but resulted in conflicting filters"
        )
    
    # Apply filters
    filtered_strings = []
    for analysis in storage.values():
        matches = True
        props = analysis["properties"]
        
        if 'is_palindrome' in parsed_filters and props['is_palindrome'] != parsed_filters['is_palindrome']:
            matches = False
            
        if 'min_length' in parsed_filters and props['length'] < parsed_filters['min_length']:
            matches = False
            
        if 'max_length' in parsed_filters and props['length'] > parsed_filters['max_length']:
            matches = False
            
        if 'word_count' in parsed_filters and props['word_count'] != parsed_filters['word_count']:
            matches = False
            
        if 'contains_character' in parsed_filters:
            char = parsed_filters['contains_character']
            if char not in analysis["value"]:
                matches = False
        
        if matches:
            filtered_strings.append(analysis)
    
    return {
        "data": filtered_strings,
        "count": len(filtered_strings),
        "interpreted_query": {
            "original": query,
            "parsed_filters": parsed_filters
        }
    }

@app.delete("/strings/{string_value}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_string(string_value: str):
    """
    Delete a string analysis
    """
    if string_value not in storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="String does not exist in the system"
        )
    
    del storage[string_value]

# @app.get("/")
# async def root():
#     return {"message": "String Analyzer Service is running"}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)