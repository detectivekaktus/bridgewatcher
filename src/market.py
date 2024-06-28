#!/usr/bin/env python3
from math import floor
from typing import Any, Final, Optional, cast
from src import ITEM_NAMES
from src.constants import CRAFTING_BONUSES
from src.api import ItemManager, remove_suffix
from src.client import DATABASE
from src.utils import api_name_to_readable_name, format_name


PREMIUM_TAX: Final[int] = 4
NON_PREMIUM_TAX: Final[int] = 8


class Crafter:
    def __init__(self, resource_prices: dict[str, int], resources: dict[str, int], requirements: dict[str, int], bonus: float, has_premium: bool) -> None:
        self._resource_prices: dict[str, int] = resource_prices
        self._resources: dict[str, int] = resources
        self._requirements: dict[str, int] = requirements
        self._bonus = bonus
        self._has_premium = has_premium


    def printable(self, item: dict[str, Any]) -> dict[str, Any]:
        raw_cost: int = self._get_raw_cost()
        returned_resources: dict[str, int] = self._get_returned_resources()
        total_resources: dict[str, int] = {}
        for resource in self._resources.keys():
            total_resources[resource] = self._resources[resource] + returned_resources[resource]
        items_crafted: int = self._get_items_crafted(total_resources) if self._resources != self._requirements else 1
        unused_material: dict[str, int] = self._get_unused_material(total_resources, items_crafted)
        unused_resources_price = self._get_unused_resources_price(unused_material)
        tax: int = int((item["sell_price_min"] * items_crafted) * (PREMIUM_TAX if self._has_premium else NON_PREMIUM_TAX) / 100)
        profit: int = self._get_profit(item, raw_cost, items_crafted, unused_resources_price, tax)

        return {
            "sell_price": (item["sell_price_min"] * items_crafted),
            "tax": tax,
            "raw_cost": raw_cost,
            "unused_resources_price": unused_resources_price,
            "profit": profit,
            "fields": [
                {
                    "title": "🔄 Return rate",
                    "value": f"{float(self._bonus)}%"
                },
                {
                    "title": "📦 Items crafted",
                    "value": items_crafted
                },
            ],
            "unused_materials": [ {"name": f"Remainder of {format_name(api_name_to_readable_name(ITEM_NAMES, name))}",
                                   "value": value} for name, value in unused_material.items() ]
        }


    def _get_raw_cost(self) -> int:
        res: int = 0

        for resource in self._resources.keys():
            res += self._resources[resource] * self._resource_prices[resource]

        return res

    def _get_returned_resources(self) -> dict[str, int]:
        res: dict[str, int] = {}

        for key, value in self._resources.items():
            if not ItemManager.is_returnable(DATABASE, key):
                res[key] = 0
                continue

            source: int = value
            res[key] = 0
            returned: int = 1
            while source != 0:
                source = floor(source * self._bonus / 100)
                returned += source
                res[key] += source

        return res

    def _get_items_crafted(self, total_resources: dict[str, int]) -> int:
        res: float = float("inf")

        for resource in total_resources.keys():
            res = min(res, total_resources[resource] // self._requirements[resource])

        return int(res)

    def _get_unused_material(self, total_resources: dict[str, int], items_crafted: int) -> dict[str, int]:
        res: dict[str, int] = {}

        for resource in total_resources.keys():
            res[resource] = total_resources[resource] - int(self._requirements[resource]) * items_crafted

        return res

    def _get_unused_resources_price(self, unused_resources: dict[str, int]) -> int:
        res: int = 0

        for resource in unused_resources.keys():
            res += unused_resources[resource] * self._resource_prices[resource]

        return res

    def _get_profit(self, item: dict[str, Any], raw_cost: int, items_crafted: int, unused_resources_price: int, tax: int) -> int:
        return (item["sell_price_min"] * items_crafted) - tax - raw_cost + unused_resources_price


def find_crafting_bonus_city(item_name: str) -> Optional[str]:
    item_name = remove_suffix(DATABASE, item_name, ItemManager.is_enchanted(item_name))

    with DATABASE as db:
        db.execute("SELECT * FROM items WHERE name = ?", (item_name, ))
        item: Optional[tuple] = db.fetchone()

    if not item:
        return None

    for key, values in CRAFTING_BONUSES.items():
        for value in values:
            if value in item:
                return key

    return None


def find_least_expensive_city(data: list[dict[str, Any]], include_black_market: bool = True) -> str:
    curr_city: Optional[str] = None
    curr_price: Optional[int] = None
    index: int = 0

    for index in range(len(data)):
        if (data[index]["city"].lower() == "black market") and (not include_black_market):
            continue

        if not curr_price or data[index]["sell_price_min"] < curr_price:
            curr_price = data[index]["sell_price_min"]
            curr_city = data[index]["city"]

    return cast(str, curr_city)


def find_most_expensive_city(data: list[dict[str, Any]], include_black_market: bool = True) -> str:
    curr_city: Optional[str] = None
    curr_price: Optional[int] = None
    index: int = 0

    for index in range(len(data)):
        if (data[index]["city"].lower() == "black market") and (not include_black_market):
            continue

        if not curr_price or data[index]["sell_price_min"] > curr_price:
            curr_price = data[index]["sell_price_min"]
            curr_city = data[index]["city"]

    return cast(str, curr_city)
