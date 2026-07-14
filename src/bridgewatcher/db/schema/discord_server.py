from dataclasses import dataclass
from typing import Any, override

from .mongo_collection_item import MongoCollectionItem


@dataclass
class DiscordServer(MongoCollectionItem):
    id: int
    fetch_server: str

    @override
    @classmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> "DiscordServer":
        return cls(doc["id"], doc["fetch_server"])

    @override
    def to_mongo(self) -> dict[Any, Any]:
        return {"id": self.id, "fetch_server": self.fetch_server}
