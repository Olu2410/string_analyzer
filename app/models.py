from dataclasses import dataclass
from datetime import datetime
from typing import Dict

@dataclass
class StringAnalysis:
    id: str  # SHA256 hash
    value: str
    properties: Dict[str, any]
    created_at: datetime
    
    def to_dict(self):
        return {
            "id": self.id,
            "value": self.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }