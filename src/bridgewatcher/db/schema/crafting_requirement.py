from dataclasses import dataclass
from typing import Any, override

from .mongo_collection_item import MongoCollectionItem


@dataclass
class CraftingRequirement(MongoCollectionItem):
    name: str
    amount: int

    @override
    @classmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> "CraftingRequirement":
        return cls(doc["name"], doc["amount"])

    @override
    def to_mongo(self) -> dict[Any, Any]:
        return {"name": self.name, "amount": self.amount}
