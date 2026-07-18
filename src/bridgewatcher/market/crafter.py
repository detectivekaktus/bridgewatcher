from math import ceil

from bridgewatcher.api.model import Cities, Qualities
from bridgewatcher.db import db
from bridgewatcher.db.schema import Item
from bridgewatcher.market import MarketHelper, MarketQuery
from bridgewatcher.market.consts import ORDER_FEE, ORDINARY_TAX, PREMIUM_TAX
from bridgewatcher.market.model import (
    Craft,
    CraftingIncome,
    MaterialLeftover,
    MaterialPurchase,
)
from bridgewatcher.util.exc import (
    InsufficientDataError,
    NoItemFoundError,
    UncraftableItemCraftedError,
)


class Crafter(MarketHelper):
    # https://wiki.albiononline.com/wiki/Resource_return_rate
    RETURN_RATES = {
        True: {  # refining
            # base rate, bonus rate
            True: (0.367, 0.539),  # with focus
            False: (0.153, 0.435),  # without focus
        },
        False: {  # crafting
            # base rate, bonus rate
            True: (0.248, 0.479),  # with focus
            False: (0.153, 0.435),  # without focus
        },
    }
    NON_RETURNABLES = ("artefacts", "cityresources")

    async def _get_item_from_item_or_id(self, item_or_id: Item | str) -> Item:
        if isinstance(item_or_id, Item):
            return item_or_id

        items_collection = db.get_collection("items")
        mongo_item = await items_collection.find_one({"name": item_or_id})

        if mongo_item is None:
            raise NoItemFoundError(f"No such item with id {item_or_id}", item_or_id)

        return Item.from_mongo(mongo_item)

    async def _get_income(
        self, item: Item, count: int, has_premium: bool
    ) -> CraftingIncome:
        query = MarketQuery.with_black_market_included(item, Qualities.NORMAL)
        sell_price = await self.get_expensive_item_sell_price(query)
        if sell_price.sell_price_min == 0:
            raise InsufficientDataError(f"No fresh data on {item.name}")

        income = sell_price.sell_price_min * count
        applied_tax = PREMIUM_TAX if has_premium else ORDINARY_TAX
        taxes = ceil(income * applied_tax)
        return CraftingIncome(
            Cities.from_str(sell_price.city),
            income,
            taxes,
        )

    async def _get_purchases(self, item: Item, count: int) -> list[MaterialPurchase]:
        purchases = []
        for requirement in item.crafting_requirements:  # type: ignore
            query = MarketQuery.with_black_market_excluded(
                requirement.name, Qualities.NORMAL
            )
            price = await self.get_cheapest_item_buy_price(query)
            if price.sell_price_min == 0:
                raise InsufficientDataError(f"No fresh data on {requirement.name}")

            requirement_item = await self._get_item_from_item_or_id(requirement.name)
            requirement_count = requirement.amount * count
            purchases.append(
                MaterialPurchase(
                    requirement_item,
                    Cities.from_str(price.city),
                    requirement_count,
                    price.sell_price_min,
                )
            )
        return purchases

    async def _get_leftovers(
        self, item: Item, purchases: list[MaterialPurchase], using_focus: bool
    ) -> tuple[list[MaterialLeftover], float]:
        is_refining = item.shop_subcategory == "refinedresources"
        base_rate, bonus_rate = self.RETURN_RATES[is_refining][using_focus]
        return_rate = bonus_rate if item.city_with_bonus is not None else base_rate

        leftovers = []
        for purchase in purchases:
            if (
                purchase.item.shop_category in self.NON_RETURNABLES
                or purchase.item.shop_subcategory in self.NON_RETURNABLES
            ):
                continue

            returned = ceil(purchase.count * return_rate)
            value = purchase.unit_price * returned
            leftovers.append(
                MaterialLeftover(purchase.item, returned, purchase.unit_price, value)
            )

        return leftovers, return_rate

    async def craft(
        self,
        item_or_id: Item | str,
        count: int = 1,
        has_premium: bool = True,
        using_focus: bool = False,
    ) -> Craft:
        if count <= 0:
            raise ValueError("Count cannot be negative")

        item = await self._get_item_from_item_or_id(item_or_id)
        if item.crafting_requirements is None:
            raise UncraftableItemCraftedError(f"{item.name} is uncraftable")

        income = await self._get_income(item, count, has_premium)
        purchases = await self._get_purchases(item, count)
        leftovers, return_rate = await self._get_leftovers(item, purchases, using_focus)

        return Craft(
            item=item,
            count=count,
            has_premium=has_premium,
            _crafting_city=item.city_with_bonus,
            return_rate=return_rate,
            income=income,
            purchases=purchases,
            leftovers=leftovers,
        )
