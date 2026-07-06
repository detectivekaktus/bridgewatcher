from dataclasses import dataclass
from typing import Any, override

from bridgewatcher.api import AlbionOnline, AlbionOnlineServers
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

    def get_albion(self) -> AlbionOnline:
        server = AlbionOnlineServers.from_str(self.server)
        return AlbionOnline(server)
