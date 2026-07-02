from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from .mongo_collection_item import MongoCollectionItem


@dataclass
class Version(MongoCollectionItem):
    hash: str
    last_time_updated: datetime

    @classmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> "Version":
        return cls(doc["hash"], doc["last_time_updated"])

    @override
    def to_mongo(self) -> dict[Any, Any]:
        return {"hash": self.hash, "last_time_updated": self.last_time_updated}
