from dataclasses import dataclass
from typing import Any, override

from bridgewatcher.api.model import Cities

from .crafting_requirement import CraftingRequirement
from .mongo_collection_item import MongoCollectionItem


@dataclass
class Item(MongoCollectionItem):
    name: str
    shop_category: str
    shop_subcategory: str
    shop_subcategory_type: str | None
    city_with_bonus: Cities | None
    crafting_requirements: list[CraftingRequirement] | None

    @override
    @classmethod
    def from_mongo(cls, doc: dict[Any, Any]) -> "Item":
        requirements = []
        if doc["crafting_requirements"] is not None:
            for requirement in doc["crafting_requirements"]:
                requirements.append(CraftingRequirement.from_mongo(requirement))

        city_with_bonus = doc["city_with_bonus"]
        city = Cities.from_str(city_with_bonus) if city_with_bonus is not None else None

        return cls(
            doc["name"],
            doc["shop_category"],
            doc["shop_subcategory"],
            doc["shop_subcategory_type"],
            city,
            requirements if requirements else None,
        )

    @override
    def to_mongo(self) -> dict[Any, Any]:
        return {
            "name": self.name,
            "shop_category": self.shop_category,
            "shop_subcategory": self.shop_subcategory,
            "shop_subcategory_type": self.shop_subcategory_type,
            "city_with_bonus": (
                self.city_with_bonus.value if self.city_with_bonus is not None else None
            ),
            "crafting_requirements": (
                [req.to_mongo() for req in self.crafting_requirements]
                if self.crafting_requirements
                else None
            ),
        }
