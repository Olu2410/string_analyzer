import os
import json
from fastapi import FastAPI, HTTPException, Query, status, Response
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import re
from pathlib import Path

# Configuration for File Persistence
STORAGE_FILE = "strings_storage.json"
STORAGE_PATH = Path(__file__).parent / STORAGE_FILE

app = FastAPI(title="String Analyzer Service", version="1.0.0")
storage: Dict[str, Dict[str, Any]] = {}


# Persistence Functions

def load_data_from_file() -> Dict[str, Dict[str, Any]]:
    """Loads data from the JSON file on startup."""
    if STORAGE_PATH.exists():
        try:
            with open(STORAGE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {STORAGE_FILE} is corrupted. Starting with empty storage.")
            return {}
    return {}

def save_data_to_file():
    """Saves the current storage dictionary to the JSON file."""
    with open(STORAGE_PATH, 'w') as f:
        json.dump(storage, f, indent=4)


# Load data when the application starts
storage = load_data_from_file()


# Analysis Function

def analyze_string(text: str) -> Dict[str, Any]:
    """Analyze a string and compute all required properties"""
    cleaned_text = text.strip()
    length = len(cleaned_text)

    # Case-insensitive palindrome check (ignore non-alphanumeric)
    cleaned_for_palindrome = re.sub(r'[^a-zA-Z0-9]', '', cleaned_text.lower())
    is_palindrome = cleaned_for_palindrome == cleaned_for_palindrome[::-1]

    unique_characters = len(set(cleaned_text))
    word_count = len(cleaned_text.split())
    sha256_hash = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()

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


# Endpoints (Modified to include save_data_to_file)

@app.post("/strings", status_code=status.HTTP_201_CREATED)
async def create_analyze_string(request: Dict[str, Any]):
    
    if not request or "value" not in request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body or missing 'value' field")

    value = request["value"]

    if not isinstance(value, str):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid data type for 'value' (must be string)")

    if not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body or missing 'value' field")

    if value in storage:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="String already exists in the system")

    properties = analyze_string(value)
    result = {
        "id": properties["sha256_hash"],
        "value": value,
        "properties": properties,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    storage[value] = result
    save_data_to_file()  # Save data after creation
    return result


@app.get("/strings/{string_value}", status_code=status.HTTP_200_OK)
async def get_string(string_value: str):
    if string_value not in storage:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    return storage[string_value]


@app.get("/strings", status_code=status.HTTP_200_OK)
async def get_all_strings(
    is_palindrome: Optional[bool] = Query(None),
    min_length: Optional[int] = Query(None, ge=0),
    max_length: Optional[int] = Query(None, ge=0),
    word_count: Optional[int] = Query(None, ge=0),
    contains_character: Optional[str] = Query(None, max_length=1)
):
    # Validation
    if min_length and max_length and min_length > max_length:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid query parameter values or types")
    
    # (case-insensitive search)
    filters = {
        "is_palindrome": is_palindrome, "min_length": min_length, "max_length": max_length,
        "word_count": word_count, "contains_character": contains_character
    }

    filtered = []
    for item in storage.values():
        props = item["properties"]
        match = True

        if is_palindrome is not None and props["is_palindrome"] != is_palindrome:
            match = False
        if min_length is not None and props["length"] < min_length:
            match = False
        if max_length is not None and props["length"] > max_length:
            match = False
        if word_count is not None and props["word_count"] != word_count:
            match = False
        
        # Case-insensitive check
        if contains_character and contains_character.lower() not in item["value"].lower():
            match = False

        if match:
            filtered.append(item)

    return {
        "data": filtered,
        "count": len(filtered),
        "filters_applied": {k: v for k, v in filters.items() if v is not None}
    }


@app.get("/strings/filter-by-natural-language", status_code=status.HTTP_200_OK)
async def filter_by_natural_language(query: str):

    q = query.lower()
    parsed_filters = {}

    if "palindrome" in q:
        parsed_filters["is_palindrome"] = True
    if "single word" in q or "one word" in q:
        parsed_filters["word_count"] = 1
    if "longer than" in q:
        m = re.search(r"longer than (\d+)", q)
        if m:
            parsed_filters["min_length"] = int(m.group(1)) + 1
    if "shorter than" in q:
        m = re.search(r"shorter than (\d+)", q)
        if m:
            parsed_filters["max_length"] = int(m.group(1)) - 1
    if "contain" in q:
        m = re.search(r"letter (\w)", q)
        if m:
            parsed_filters["contains_character"] = m.group(1)
    if "vowel" in q and "contains_character" not in parsed_filters:
        parsed_filters["contains_character"] = "a"

    if not parsed_filters:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to parse natural language query")

    if ("min_length" in parsed_filters and "max_length" in parsed_filters and
            parsed_filters["min_length"] > parsed_filters["max_length"]):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Query parsed but resulted in conflicting filters")

    filtered = []
    for item in storage.values():
        props = item["properties"]
        match = True
        if "is_palindrome" in parsed_filters and props["is_palindrome"] != parsed_filters["is_palindrome"]:
            match = False
        if "min_length" in parsed_filters and props["length"] < parsed_filters["min_length"]:
            match = False
        if "max_length" in parsed_filters and props["length"] > parsed_filters["max_length"]:
            match = False
        if "word_count" in parsed_filters and props["word_count"] != parsed_filters["word_count"]:
            match = False
        
        # Case-insensitive check
        if "contains_character" in parsed_filters and parsed_filters["contains_character"].lower() not in item["value"].lower():
            match = False

        if match:
            filtered.append(item)

    return {
        "data": filtered,
        "count": len(filtered),
        "interpreted_query": {
            "original": query,
            "parsed_filters": parsed_filters
        }
    }


@app.delete("/strings/{string_value}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_string(string_value: str):
    if string_value not in storage:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    del storage[string_value]
    save_data_to_file() # Save data after deletion
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)