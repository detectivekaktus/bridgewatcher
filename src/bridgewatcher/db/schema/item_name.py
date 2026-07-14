from dataclasses import dataclass
from typing import Any, override

from .mongo_collection_item import MongoCollectionItem


@dataclass
class ItemName(MongoCollectionItem):
    id: str
    name: str

    @override
    @classmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> MongoCollectionItem:
        return cls(doc["id"], doc["name"])

    @override
    def to_mongo(self) -> dict[Any, Any]:
        return {"id": self.id, "name": self.name}
