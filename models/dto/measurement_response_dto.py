from dataclasses import dataclass
from typing import Optional, List
from models.dto import AirQualityMeasurementDTO

@dataclass
class MeasurementResponseDTO:
    response:int
    message:str
    payload:Optional[List[AirQualityMeasurementDTO]] = None

    def to_dict(self):
        return {
            "response":self.response,
            "message":self.message,
            "payload":self.payload.to_dict() if self.payload else None
        }