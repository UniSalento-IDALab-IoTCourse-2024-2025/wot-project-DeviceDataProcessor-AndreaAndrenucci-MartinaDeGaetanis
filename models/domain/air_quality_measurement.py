from dataclasses import dataclass
from typing import Optional
from models.domain.pollutants import Pollutants
from datetime import datetime


@dataclass
class AirQualityMeasurement:
    
    misuration_date: datetime
    denomination: str
    municipality: str
    province: str
    latitude: float
    longitude: float
    quality_index: int
    quality_class: str
    area_type: str
    pollutants: Optional[Pollutants] = None

    def to_dict(self):
        return {
            "misuration_date": self.misuration_date,
            "denomination": self.denomination,
            "municipality": self.municipality,
            "province": self.province,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "quality_index": self.quality_index,
            "quality_class": self.quality_class,
            "area_type": self.area_type,
            "Pollutants": self.pollutants.to_dict() if self.pollutants else None
        }

    @staticmethod
    def from_dict(data: dict) -> 'AirQualityMeasurement':
        raw_date = data.get("misuration_date")

        if isinstance(raw_date, datetime):
            misuration_date = raw_date
        elif isinstance(raw_date, str):
            misuration_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        else:
            misuration_date = None  

        return AirQualityMeasurement(
            misuration_date=misuration_date,
            denomination=data.get("denomination"),
            municipality=data.get("municipality"),
            province=data.get("province"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            quality_index=data.get("quality_index"),
            quality_class=data.get("quality_class"),
            area_type=data.get("area_type"),
            pollutants=Pollutants.from_dict(data["Pollutants"]) if data.get("Pollutants") else None
        )
