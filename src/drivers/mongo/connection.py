"""
MongoDB driver (mirrors basecode-golang drivers/mongo).
"""

import os
from pymongo import MongoClient
from pymongo.database import Database


class Mongo:
    def __init__(self):
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DB", "gate_security")
        self._client = MongoClient(uri)
        self._db = self._client[db_name]

    def get_db(self) -> Database:
        return self._db

    def close(self):
        self._client.close()
