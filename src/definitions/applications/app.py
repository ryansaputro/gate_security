"""
AppContext - Central dependency container (mirrors basecode-golang AppContext).
"""

from dataclasses import dataclass
from pymongo.database import Database


@dataclass
class AppContext:
    mongo: Database
