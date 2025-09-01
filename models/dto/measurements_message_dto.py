from dataclasses import dataclass
from typing import Optional
from models.dto import AirQualityMeasurementDTO

@dataclass
class MeasurementsMessageDTO:
    measurements: Optional[AirQualityMeasurementDTO] = None
    
    def to_dict(self)->dict:
        return{
            "measurements": self.measurements if self.measurements else None
        }
    
@staticmethod
def from_dict(data: dict) -> "MeasurementsMessageDTO":
    measurements_data = data.get("measurements", [])
    measurements = [
        AirQualityMeasurementDTO(m) for m in measurements_data
    ] if isinstance(measurements_data, list) else []

    return MeasurementsMessageDTO(measurements=measurements)
