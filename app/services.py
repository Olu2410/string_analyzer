import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from app.models import StringAnalysis

class StringAnalyzerService:
    def __init__(self, storage):
        self.storage = storage
        
    def analyze_string(self, text: str) -> Dict[str, any]:
        """Analyze a string and compute all required properties"""
        # Basic validation
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        # Remove extra whitespace but preserve original for analysis
        cleaned_text = text.strip()
        
        # Compute properties
        length = len(cleaned_text)
        
        # Case-insensitive palindrome check
        cleaned_for_palindrome = re.sub(r'[^a-zA-Z0-9]', '', cleaned_text.lower())
        is_palindrome = cleaned_for_palindrome == cleaned_for_palindrome[::-1] if cleaned_for_palindrome else True
        
        # Unique characters count
        unique_characters = len(set(cleaned_text))
        
        # Word count (split by whitespace)
        word_count = len(cleaned_text.split())
        
        # SHA256 hash
        sha256_hash = hashlib.sha256(cleaned_text.encode()).hexdigest()
        
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
            "character_frequency_map": character_frequency_map
        }
    
    def analyze_and_store_string(self, text: str) -> StringAnalysis:
        """Analyze a string and store the results"""
        # Check if string already exists
        existing = self.storage.get_by_value(text)
        if existing:
            raise ValueError(f"String '{text}' already exists in the system")
        
        properties = self.analyze_string(text)
        
        analysis = StringAnalysis(
            id=properties["sha256_hash"],
            value=text,
            properties=properties,
            created_at=datetime.utcnow()
        )
        
        self.storage.store(analysis)
        return analysis
    
    def get_string_analysis(self, text: str) -> StringAnalysis:
        """Get analysis for a specific string"""
        analysis = self.storage.get_by_value(text)
        if not analysis:
            raise ValueError(f"String '{text}' does not exist in the system")
        return analysis
    
    def get_strings_with_filters(self, filters: Dict[str, any]) -> List[StringAnalysis]:
        """Get all strings matching the given filters"""
        all_strings = self.storage.get_all()
        
        filtered_strings = []
        for analysis in all_strings:
            if self._matches_filters(analysis, filters):
                filtered_strings.append(analysis)
        
        return filtered_strings
    
    def _matches_filters(self, analysis: StringAnalysis, filters: Dict[str, any]) -> bool:
        """Check if an analysis matches all given filters"""
        props = analysis.properties
        
        if 'is_palindrome' in filters and props['is_palindrome'] != filters['is_palindrome']:
            return False
            
        if 'min_length' in filters and props['length'] < filters['min_length']:
            return False
            
        if 'max_length' in filters and props['length'] > filters['max_length']:
            return False
            
        if 'word_count' in filters and props['word_count'] != filters['word_count']:
            return False
            
        if 'contains_character' in filters:
            char = filters['contains_character']
            if char not in analysis.value:
                return False
        
        return True
    
    def filter_by_natural_language(self, query: str) -> Tuple[List[StringAnalysis], Dict[str, any]]:
        """Filter strings using natural language queries"""
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
            raise ValueError("Unable to parse natural language query")
        
        # Check for conflicting filters
        if ('min_length' in parsed_filters and 'max_length' in parsed_filters and 
            parsed_filters['min_length'] > parsed_filters['max_length']):
            raise ValueError("Conflicting filters: min_length cannot be greater than max_length")
        
        results = self.get_strings_with_filters(parsed_filters)
        return results, parsed_filters
    
    def delete_string(self, text: str):
        """Delete a string analysis"""
        if not self.storage.get_by_value(text):
            raise ValueError(f"String '{text}' does not exist in the system")
        self.storage.delete_by_value(text)