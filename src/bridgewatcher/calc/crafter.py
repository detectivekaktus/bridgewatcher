from dataclasses import dataclass

from bridgewatcher.calc import MarketHelper
from bridgewatcher.db import db
from bridgewatcher.db.schema import Item


class Crafter(MarketHelper):
    ORDER_FEE = 0.025
    PREMIUM_TAX = 0.04
    ORDINARY_TAX = 0.08

    # https://wiki.albiononline.com/wiki/Resource_return_rate
    BASE_REFINING_RETURN_RATE = 0.153
    BASE_REFINING_RETURN_RATE_WITH_FOCUS = 0.435
    BONUS_REFINING_RETURN_RATE = 0.367
    BONUS_REFINING_RETURN_RATE_WITH_FOCUS = 0.539

    BASE_CRAFTING_RETURN_RATE = 0.153
    BASE_CRAFTING_RETURN_RATE_WITH_FOCUS = 0.435
    BONUS_CRAFTING_RETURN_RATE = 0.248
    BONUS_CRAFTING_RETURN_RATE_WITH_FOCUS = 0.479

    @dataclass
    class Response: ...

    async def _get_item_from_item_or_id(self, item_or_id: Item | str) -> Item:
        if isinstance(item_or_id, Item):
            return item_or_id

        items_collection = db.get_collection("items")
        mongo_item = await items_collection.find_one({"name": item_or_id})

        if mongo_item is None:
            raise ValueError(f"No such item with id {item_or_id}")

        return Item.from_mongo(mongo_item)

    async def craft(
        self, item_or_id: Item | str, count: int = 1, has_premium: bool = True
    ) -> Response:
        item = await self._get_item_from_item_or_id(item_or_id)
        # WIP
        return self.Response()
