from dataclasses import dataclass
from typing import Optional
from models.dto.pollutants_dto import PollutantsDTO
from models.domain import AirQualityMeasurement
from datetime import datetime

@dataclass
class AirQualityMeasurementDTO:
    misuration_date: str
    denomination: str
    municipality: str
    province: str
    latitude: float
    longitude: float
    quality_index: int
    quality_class: str  # es. "buona", "pessima"
    area_type: str      # es. "urbana", "suburbana"
    pollutantsDTO: Optional[PollutantsDTO] = None

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
            "Pollutants": self.pollutantsDTO.to_dict() if self.pollutantsDTO else None
        }

    @staticmethod
    def from_dict(data: dict) -> 'AirQualityMeasurementDTO':
        return AirQualityMeasurementDTO(
            misuration_date=data.get("misuration_date"),
            denomination=data.get("denomination"),
            municipality=data.get("municipality"),
            province=data.get("province"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            quality_index=data.get("quality_index"),
            quality_class=data.get("quality_class"),
            area_type=data.get("area_type"),
            pollutantsDTO=PollutantsDTO.from_dict(data["pollutants"]) if data.get("pollutants") else None
        )
        
    def to_domain(self) -> AirQualityMeasurement:
        return AirQualityMeasurement(
            misuration_date=datetime.fromisoformat(self.misuration_date),
            denomination=self.denomination,
            municipality=self.municipality,
            province=self.province,
            latitude=self.latitude,
            longitude=self.longitude,
            quality_index=self.quality_index,
            quality_class=self.quality_class,
            area_type=self.area_type,
            pollutants=self.pollutantsDTO.to_domain() if self.pollutantsDTO else None
        )

    @staticmethod
    def from_domain(domain: AirQualityMeasurement) -> 'AirQualityMeasurementDTO':
        return AirQualityMeasurementDTO(
            misuration_date=domain.misuration_date.isoformat(),
            denomination=domain.denomination,
            municipality=domain.municipality,
            province=domain.province,
            latitude=domain.latitude,
            longitude=domain.longitude,
            quality_index=domain.quality_index,
            quality_class=domain.quality_class,
            area_type=domain.area_type,
            pollutantsDTO=PollutantsDTO.from_domain(domain.pollutants) if domain.pollutants else None
        )