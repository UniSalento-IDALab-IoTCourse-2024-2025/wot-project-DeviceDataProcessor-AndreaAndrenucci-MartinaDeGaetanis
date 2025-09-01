from dataclasses import dataclass, field
import config.pollutants_measurement_units as units

@dataclass
class Pollutants:
    
    c6h6_value: float
    co_value: float
    h2s_value: float
    ipa_value: float
    no2_value: float
    o3_value: float
    pm10_value: float
    pm2dot5_value: float
    so2_value: float

    c6h6_unit: str = field(init=False)
    co_unit: str = field(init=False)
    h2s_unit: str = field(init=False)
    ipa_unit: str = field(init=False)
    no2_unit: str = field(init=False)
    o3_unit: str = field(init=False)
    pm10_unit: str = field(init=False)
    pm2dot5_unit: str = field(init=False)
    so2_unit: str = field(init=False)

    def __post_init__(self):
        self.c6h6_unit = units.C6H6_MEASUREMENT_UNIT
        self.co_unit = units.CO_MEASUREMENT_UNIT
        self.h2s_unit = units.H2S_MEASUREMENT_UNIT
        self.ipa_unit = units.IPA_MEASUREMENT_UNIT
        self.no2_unit = units.NO2_MEASUREMENT_UNIT
        self.o3_unit = units.O3_MEASUREMENT_UNIT
        self.pm10_unit = units.PM10_MEASUREMENT_UNIT
        self.pm2dot5_unit = units.PM2DOT5_MEASUREMENT_UNIT
        self.so2_unit = units.SO2_MEASUREMENT_UNIT

    def to_dict(self):
        return {
            "c6h6_value": self.c6h6_value,
            "c6h6_unit": self.c6h6_unit,
            "co_value": self.co_value,
            "co_unit": self.co_unit,
            "h2s_value": self.h2s_value,
            "h2s_unit": self.h2s_unit,
            "ipa_value": self.ipa_value,
            "ipa_unit": self.ipa_unit,
            "no2_value": self.no2_value,
            "no2_unit": self.no2_unit,
            "o3_value": self.o3_value,
            "o3_unit": self.o3_unit,
            "pm10_value": self.pm10_value,
            "pm10_unit": self.pm10_unit,
            "pm2dot5_value": self.pm2dot5_value,
            "pm2dot5_unit": self.pm2dot5_unit,
            "so2_value": self.so2_value,
            "so2_unit": self.so2_unit
        }

    @staticmethod
    def from_dict(data: dict) -> 'Pollutants':
        return Pollutants(
            c6h6_value=data.get("c6h6_value"),
            co_value=data.get("co_value"),
            h2s_value=data.get("h2s_value"),
            ipa_value=data.get("ipa_value"),
            no2_value=data.get("no2_value"),
            o3_value=data.get("o3_value"),
            pm10_value=data.get("pm10_value"),
            pm2dot5_value=data.get("pm2dot5_value"),
            so2_value=data.get("so2_value")
        )
