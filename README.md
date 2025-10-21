String Analyzer Service
A powerful RESTful API service that analyzes strings and stores their computed properties with advanced filtering capabilities.


Features
String Analysis: Compute comprehensive properties including length, palindrome status, character frequency, and more

Flexible Filtering: Filter strings using both query parameters and natural language

SHA256 Hashing: Unique identification for each analyzed string

RESTful API: Clean, well-documented endpoints following REST conventions

No Database Required: In-memory storage for zero-dependency setup


Installation
git clone <repository-url>
cd string-analyzer


Install dependencies:
pip install -r requirements.txt


Run the server:
python run.py

API Endpoints
1. Analyze a String
POST /strings   ----- curl -X POST "http://localhost:8000/strings" \
                            -H "Content-Type: application/json" \
                            -d '{"value": "hello world"}'

2. Get String Analysis
GET /strings/{string_value}  -- curl "http://localhost:8000/strings/hello%20world"

3. Filter Strings
GET /strings?filters
                    # Get all palindromes longer than 5 characters
                    curl "http://localhost:8000/strings?is_palindrome=true&min_length=5"



4. Natural Language Filtering
GET /strings/filter-by-natural-language?query=your_query

curl "http://localhost:8000/strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings"


5. Delete String
DELETE /strings/{string_value}

curl -X DELETE "http://localhost:8000/strings/hello%20world"


String Properties Analyzed
Each analyzed string returns:

Property	                Description
length  	                Number of characters
is_palindrome	            Boolean if string reads same forwards/backwards
unique_characters	        Count of distinct characters
word_count	                Number of words separated by whitespace
sha256_hash	Unique          SHA256 hash identifier
character_frequency_map	    Dictionary mapping characters to occurrence counts
