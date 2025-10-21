from typing import Dict, List, Optional
from app.models import StringAnalysis

class InMemoryStringStorage:
    def __init__(self):
        self._storage_by_hash: Dict[str, StringAnalysis] = {}
        self._storage_by_value: Dict[str, StringAnalysis] = {}
    
    def store(self, analysis: StringAnalysis):
        """Store a string analysis"""
        self._storage_by_hash[analysis.id] = analysis
        self._storage_by_value[analysis.value] = analysis
    
    def get_by_hash(self, hash_id: str) -> Optional[StringAnalysis]:
        """Get analysis by SHA256 hash"""
        return self._storage_by_hash.get(hash_id)
    
    def get_by_value(self, value: str) -> Optional[StringAnalysis]:
        """Get analysis by string value"""
        return self._storage_by_value.get(value)
    
    def get_all(self) -> List[StringAnalysis]:
        """Get all stored analyses"""
        return list(self._storage_by_value.values())
    
    def delete_by_value(self, value: str):
        """Delete analysis by string value"""
        analysis = self._storage_by_value.get(value)
        if analysis:
            del self._storage_by_value[value]
            del self._storage_by_hash[analysis.id]