from dataclasses import dataclass
from typing import Any, override

from .mongo_collection_item import MongoCollectionItem


@dataclass
class DiscordServer(MongoCollectionItem):
    id: int
    server: str

    @override
    @classmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> MongoCollectionItem:
        return cls(doc["id"], doc["server"])

    @override
    def to_mongo(self) -> dict[Any, Any]:
        return {"id": self.id, "server": self.server}
