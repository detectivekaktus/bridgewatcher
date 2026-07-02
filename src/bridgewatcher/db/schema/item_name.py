from dataclasses import dataclass
from typing import Any, override

from .mongo_collection_item import MongoCollectionItem


@dataclass
class ItemName(MongoCollectionItem):
    identifier: str
    name: str

    @override
    @classmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> MongoCollectionItem:
        return cls(doc["identifier"], doc["name"])

    @override
    def to_mongo(self) -> dict[Any, Any]:
        return {"identifier": self.identifier, "name": self.name}
