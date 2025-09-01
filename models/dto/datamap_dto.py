from typing import Optional
from dataclasses import dataclass
from models.domain import DataMap
import datetime

@dataclass
class DataMapDTO:
    date: str  # <-- resta stringa ISO
    pollutant: str
    url: str
    region: str
    opacity: float
    attribution: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "pollutant": self.pollutant,
            "url": self.url,
            "region": self.region,
            "opacity": self.opacity,
            "attribution": self.attribution
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataMapDTO":
        return cls(
            date=data["date"],
            pollutant=data["pollutant"],
            url=data["url"],
            region=data["region"],
            opacity=data["opacity"],
            attribution=data.get("attribution")
        )

    @classmethod
    def from_domain(cls, domain: DataMap) -> "DataMapDTO":
        return cls(
            date=domain.date.isoformat(),
            pollutant=domain.pollutant,
            url=domain.url,
            region=domain.region,
            opacity=getattr(domain, "opacity", 1.0),  # fallback se non presente
            attribution=getattr(domain, "attribution", None)
        )

    def to_domain(self) -> DataMap:
        return DataMap(
            date=datetime.datetime.fromisoformat(self.date),
            pollutant=self.pollutant,
            url=self.url,
            region=self.region
        )
