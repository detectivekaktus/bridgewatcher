#!/usr/bin/env python3
from math import floor
from typing import Any, Final, Optional
from src import ITEM_NAMES
from src.constants import CRAFTING_BONUSES
from src.api import ItemManager, remove_suffix
from src.client import DATABASE
from src.utils.formatting import api_name_to_readable_name, format_name


PREMIUM_TAX: Final[int] = 4
NON_PREMIUM_TAX: Final[int] = 8


class Crafter:
    """Helper class for evaluating crafting outcome."""

    def __init__(
        self,
        resource_prices: dict[str, int],
        resources: dict[str, int],
        requirements: dict[str, int],
        return_rate: float,
        has_premium: bool,
    ) -> None:
        """
        Initialize a `Crafter` class.

        Args:
            resource_prices (dict[str, int]): name-price dictionary of primary resource prices.
            resources (dict[str, int]): available resources for crafting.
            requirements (dict[str, int]): crafting requirements.
            return_rate (float): return rate applied to crafting.
            has_premium (bool): premium status.
        """
        self._resource_prices: dict[str, int] = resource_prices
        self._resources: dict[str, int] = resources
        self._requirements: dict[str, int] = requirements
        self._return_rate = return_rate
        self._has_premium = has_premium

    def printable(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Get API-like response with crafting cost, profit, unused materials details.
        Designed to be used with Albion Online Data Project item data.

        Args:
            item (dict[str, Any]): City-specific item data from the Albion Online Data project API.
                Expected to contain at least:
                    - "sell_price_min" (int): Minimum market sell price.

        Returns:
            dict[str, Any]: A dictionary containing crafting outcome details:
                - "sell_price" (int): Total sell price.
                - "tax" (int): Market tax to be payed.
                - "raw_cost" (int): Total cost of raw materials used.
                - "unused_resources_price" (int): Total value of unused materials, including
                the returned ones.
                - "profit" (int): Net profit of sell and unused materials after costs and taxes.
                - "fields" (list[dict[str, str | int]]): Display-friendly fields.
                - "unused_materials" (list[dict[str, str | int]]): Details of leftover materials,
                including name and their value.
        """
        raw_cost: int = self._get_raw_cost()
        returned_resources: dict[str, int] = self._get_returned_resources()
        total_resources: dict[str, int] = {}
        for resource in self._resources.keys():
            total_resources[resource] = (
                self._resources[resource] + returned_resources[resource]
            )
        items_crafted: int = (
            self._get_items_crafted(total_resources)
            if self._resources != self._requirements
            else 1
        )
        unused_material: dict[str, int] = self._get_unused_material(
            total_resources, items_crafted
        )
        unused_resources_price = self._get_unused_resources_price(unused_material)
        tax: int = int(
            (item["sell_price_min"] * items_crafted)
            * (PREMIUM_TAX if self._has_premium else NON_PREMIUM_TAX)
            / 100
        )
        profit: int = self._get_profit(
            item, raw_cost, items_crafted, unused_resources_price, tax
        )

        return {
            "sell_price": (item["sell_price_min"] * items_crafted),
            "tax": tax,
            "raw_cost": raw_cost,
            "unused_resources_price": unused_resources_price,
            "profit": profit,
            "fields": [
                {"title": "🔄 Return rate", "value": f"{float(self._return_rate)}%"},
                {"title": "📦 Items crafted", "value": items_crafted},
            ],
            "unused_materials": [
                {
                    "name": f"Remainder of {format_name(api_name_to_readable_name(ITEM_NAMES, name))}",
                    "value": value,
                }
                for name, value in unused_material.items()
            ],
        }

    def _get_raw_cost(self) -> int:
        """Get total cost of the raw materials by iterating over resources."""
        cost: int = 0

        for resource in self._resources.keys():
            cost += self._resources[resource] * self._resource_prices[resource]

        return cost

    def _get_returned_resources(self) -> dict[str, int]:
        """
        Get dictionary with returned resources by their name. Non-returnable
        resources are associated with number 0.

        Returns:
            dict[str, int]: A mapping of resource names to the total return amount.
        """
        res: dict[str, int] = {}

        for key, value in self._resources.items():
            if not ItemManager.is_returnable(DATABASE, key):
                res[key] = 0
                continue

            source: int = value
            res[key] = 0
            while source != 0:
                source = floor(source * self._return_rate / 100)
                res[key] += source

        return res

    def _get_items_crafted(self, total_resources: dict[str, int]) -> int:
        """
        Get maximum number of items crafted by selecting the minimum craftable number of
        items for each resource involved into crafting.

        Args:
            total_resources (dict[str, int]): user-given and returned resources combined in a
                single dictionary, keyed by resource name.

        Returns:
            int: total number of items crafted.
        """
        items_number: float = float("inf")

        for resource in total_resources.keys():
            items_number = min(
                items_number, total_resources[resource] // self._requirements[resource]
            )

        return int(items_number)

    def _get_unused_material(
        self, total_resources: dict[str, int], items_crafted: int
    ) -> dict[str, int]:
        """
        Get dictionary, keyed by resource name, with material leftovers after crafting.

        Args:
            total_resources (dict[str, int]): user-given and returned resources combined
                in a single dictionary, keyed by resource name.
            items_crafted (int): number of crafted items.

        Returns:
            dict[str, int]: A mapping of resource names and their leftovers.
        """
        materials: dict[str, int] = {}

        for resource in total_resources.keys():
            materials[resource] = (
                total_resources[resource]
                - int(self._requirements[resource]) * items_crafted
            )

        return materials

    def _get_unused_resources_price(self, unused_resources: dict[str, int]) -> int:
        """
        Get total unused resources market value by iterating the collection of unused resources.

        Args:
            unused_resources (dict[str, int]): A mapping of unused resources by their name.

        Returns:
            int: total price of unused resources.
        """
        price: int = 0

        for resource in unused_resources.keys():
            price += unused_resources[resource] * self._resource_prices[resource]

        return price

    def _get_profit(
        self,
        item: dict[str, Any],
        raw_cost: int,
        items_crafted: int,
        unused_resources_price: int,
        tax: int,
    ) -> int:
        return (
            (item["sell_price_min"] * items_crafted)
            - tax
            - raw_cost
            + unused_resources_price
        )


def find_crafting_bonus_city(item_name: str) -> Optional[str]:
    """
    Get city name with crafting bonus for the selected item.

    Args:
        item_name (str): internal item name.

    Returns:
        Optional[str]: city name with crafting bonus for the selected item
            or `None` if failed to find any.

    Example:
        >>> find_crafting_bonus_city("T4_METALBAR")
        "thetford"

        >>> find_crafting_bonus_city("T4_MOUNT_HORSE")
        None
    """
    item_name = remove_suffix(DATABASE, item_name, ItemManager.is_enchanted(item_name))

    with DATABASE as db:
        db.execute("SELECT * FROM items WHERE name = ?", (item_name,))
        item: Optional[tuple] = db.fetchone()

    if not item:
        return None

    for key, values in CRAFTING_BONUSES.items():
        for value in values:
            if value in item:
                return key

    return None


def find_least_expensive_city(
    data: list[dict[str, Any]], include_black_market: bool = True
) -> Optional[str]:
    """
    Get city with the least expensive price for selected item, passed via `data`
    argument. The `data` argument is Albion Online Data Project API response
    for an item. Passing multilple items data may result in unexpected behavior.

    Args:
        data (list[dict[str, Any]]): Albion Online Data Project API item data.
        include_black_market (bool): consider black market prices.

    Returns:
        Optional[str]: city with the least expensive price for the item or `None` if
            not found any.
    """
    curr_city: Optional[str] = None
    curr_price: Optional[int] = None
    index: int = 0

    for index in range(len(data)):
        if (data[index]["city"].lower() == "black market") and (
            not include_black_market
        ):
            continue

        if not curr_price or data[index]["sell_price_min"] < curr_price:
            curr_price = data[index]["sell_price_min"]
            curr_city = data[index]["city"]

    return curr_city


def find_most_expensive_city(
    data: list[dict[str, Any]], include_black_market: bool = True
) -> Optional[str]:
    """
    Get city with the most expensive price for selected item, passed via `data`
    argument. The `data` argument is Albion Online Data Project API response
    for an item. Passing multilple items data may result in unexpected behavior.

    Args:
        data (list[dict[str, Any]]): Albion Online Data Project API item data.
        include_black_market (bool): consider black market prices.

    Returns:
        Optional[str]: city with the most expensive price for the item or `None` if
            not found any.
    """
    curr_city: Optional[str] = None
    curr_price: Optional[int] = None
    index: int = 0

    for index in range(len(data)):
        if (data[index]["city"].lower() == "black market") and (
            not include_black_market
        ):
            continue

        if not curr_price or data[index]["sell_price_min"] > curr_price:
            curr_price = data[index]["sell_price_min"]
            curr_city = data[index]["city"]

    return curr_city
