from abc import ABC, abstractmethod
from typing import Any


class MongoCollectionItem(ABC):
    @classmethod
    @abstractmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> "MongoCollectionItem":
        pass

    @abstractmethod
    def to_mongo(self) -> dict[Any, Any]:
        pass
