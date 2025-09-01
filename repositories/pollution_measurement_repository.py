from typing import List
from models.domain import AirQualityMeasurement
from modules.singleton import singleton
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone, timedelta
import os

@singleton
class PollutionMeasurementsRepository:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
        self.collection = MongoClient(mongo_uri)["air_quality_db"]["measurements"]

    def find_all_measurements(self) -> List[AirQualityMeasurement]:
        results = self.collection.find()
        return [AirQualityMeasurement.from_dict(doc) for doc in results]

    def save(self, measurement: AirQualityMeasurement):
        self.collection.insert_one(measurement.to_dict())
    
    def save_all(self, measurements:List[AirQualityMeasurement]):
        dicts = [m.to_dict() for m in measurements]
        self.collection.insert_many(dicts)


    def find_latest_measurement(self) -> AirQualityMeasurement | None:
        doc = self.collection.find_one(
            sort=[("misuration_date", -1)]
        )
        return AirQualityMeasurement.from_dict(doc) if doc else None

    def find_by_exact_date(self, date: str) -> List[AirQualityMeasurement]:
        results = self.collection.find({
            "misuration_date": datetime.fromisoformat(date).replace(tzinfo=timezone.utc) if isinstance(date, str) else date
        })
        return [AirQualityMeasurement.from_dict(doc) for doc in results]

    def find_between_dates(self, start_date: str, end_date: str) -> List[AirQualityMeasurement]:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        results = self.collection.find({
            "misuration_date": {
                "$gte": start,
                "$lte": end
            }
        }).sort("misuration_date", ASCENDING)
        return [AirQualityMeasurement.from_dict(doc) for doc in results]
 
    
    def find_unique_coords_closest_to_today(self) -> List[List[float]]:

        closest_doc = self.collection.find_one(
            {}, 
            sort=[("misuration_date", -1)]
        )

        if not closest_doc:
            return []

        closest_date = closest_doc["misuration_date"]
        day_start = closest_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        results = self.collection.find({
            "misuration_date": {
                "$gte": day_start,
                "$lt": day_end
            }
        })

        unique_coords_set = {(doc["longitude"], doc["latitude"]) for doc in results}
        unique_coords = [list(coord) for coord in unique_coords_set]
        return unique_coords