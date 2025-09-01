from dataclasses import dataclass
from typing import Optional, List
from models.dto.datamap_dto import DataMapDTO

@dataclass
class DataMapResponseDTO:
    response:int
    message:str
    payload:Optional[List[DataMapDTO]] = None

    def to_dict(self):
        return {
            "response":self.response,
            "payload": [dto.to_dict() for dto in self.payload] if self.payload else None,
            "message":self.message
        }