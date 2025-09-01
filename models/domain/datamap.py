from dataclasses import dataclass
from datetime import datetime

@dataclass
class DataMap:
    date: datetime
    pollutant: str
    url: str
    region:str

    def to_dict(self) -> dict:
        return {
            "date": self.date,  
            "pollutant": self.pollutant,
            "url": self.url,
            "region": self.region
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataMap":
        return cls(
            date=datetime.fromisoformat(data["date"]) if isinstance(data["date"], str) else data["date"],  # <-- parsing ISO
            pollutant=data["pollutant"],
            url=data["url"],
            region=data["region"]
        )
