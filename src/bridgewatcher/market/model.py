from dataclasses import dataclass

from bridgewatcher.api.model import Cities, Qualities
from bridgewatcher.db.schema import Item


@dataclass
class MarketFlip:
    buy_price: int
    buy_city: Cities
    sell_price: int
    sell_city: Cities
    quality: Qualities


@dataclass
class CraftingIncome:
    sell_city: Cities
    income: int
    fees: int
    taxes: int

    @property
    def net(self) -> int:
        return self.income - self.fees - self.taxes


@dataclass
class MaterialPurchase:
    item: Item
    buy_city: Cities
    count: int
    cost: int
    fees: int


@dataclass
class MaterialLeftover:
    item: Item
    count: int
    value: int


@dataclass
class Craft:
    item: Item
    count: int
    has_premium: bool
    crafting_city: Cities
    income: CraftingIncome
    purchases: list[MaterialPurchase]
    leftovers: list[MaterialLeftover]

    @property
    def total_cost(self) -> int:
        return sum(purchase.cost + purchase.fees for purchase in self.purchases)

    @property
    def leftovers_value(self) -> int:
        return sum(leftover.value for leftover in self.leftovers)

    @property
    def profit(self) -> int:
        return self.income.net + self.leftovers_value - self.total_cost
