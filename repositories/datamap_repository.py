from typing import List
from models.domain import DataMap
from modules.singleton import singleton
from pymongo import MongoClient
from datetime import datetime
import os

@singleton
class DatamapRepository:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
        self.collection = MongoClient(mongo_uri)["air_quality_db"]["datamaps"]

    def find_by_date(self) -> List[DataMap]:
        results = self.collection.find()
        return [DataMap.from_dict(doc) for doc in results]

    def save(self, measurement: DataMap):
        self.collection.insert_one(measurement.to_dict())

    def find_latest_measurement(self, pollutant) -> DataMap | None:
        doc = self.collection.find_one(
            filter={"pollutant": pollutant},
            sort=[("date", -1)]
        )
        return DataMap.from_dict(doc) if doc else None


    def find_by_exact_date(self, date) -> DataMap:
        dt = datetime.fromisoformat(date) if isinstance(date, str) else date
        doc = self.collection.find_one({"date": dt})
        return DataMap.from_dict(doc)
