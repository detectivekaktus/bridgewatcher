from dataclasses import dataclass
from typing import Any, override

from .crafting_requirement import CraftingRequirement
from .mongo_collection_item import MongoCollectionItem
from bridgewatcher.db.schema import crafting_requirement


@dataclass
class Item(MongoCollectionItem):
    name: str
    shop_category: str
    shop_subcategory: str
    crafting_requirements: list[CraftingRequirement] | None

    @override
    @classmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> "Item":
        requirements = []
        if doc["crafting_requirements"] is not None:
            for requirement in doc["crafting_requirements"]:
                requirements.append(CraftingRequirement.from_mongo(requirement))

        return cls(
            doc["name"],
            doc["shop_category"],
            doc["shop_subcategory"],
            requirements if requirements else None,
        )

    @override
    def to_mongo(self) -> dict[Any, Any]:
        return {
            "name": self.name,
            "shop_category": self.shop_category,
            "shop_subcategory": self.shop_subcategory,
            "crafting_requirements": (
                [req.to_mongo() for req in self.crafting_requirements]
                if self.crafting_requirements
                else None
            ),
        }
