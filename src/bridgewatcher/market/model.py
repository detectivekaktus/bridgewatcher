from dataclasses import dataclass

from bridgewatcher.api.model import Cities, Qualities
from bridgewatcher.db.schema import Item


@dataclass
class MarketFlip:
    quality: Qualities
    buy_price: int
    buy_city: Cities
    sell_price: int
    sell_city: Cities
    taxes: int
    fees: int

    @property
    def profit(self) -> int:
        return self.sell_price - self.buy_price - self.fees - self.taxes


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
    unit_price: int
    cost: int
    fees: int


@dataclass
class MaterialLeftover:
    item: Item
    count: int
    unit_price: int
    value: int


@dataclass
class Craft:
    item: Item
    count: int
    has_premium: bool
    _crafting_city: Cities | None
    return_rate: float
    income: CraftingIncome
    purchases: list[MaterialPurchase]
    leftovers: list[MaterialLeftover]

    @property
    def crafting_city(self) -> str:
        return (
            self._crafting_city.value if self._crafting_city is not None else "Any city"
        )

    @property
    def total_cost(self) -> int:
        return sum(purchase.cost + purchase.fees for purchase in self.purchases)

    @property
    def total_fees(self) -> int:
        return self.income.fees + sum(purchase.fees for purchase in self.purchases)

    @property
    def leftovers_value(self) -> int:
        return sum(leftover.value for leftover in self.leftovers)

    @property
    def profit(self) -> int:
        return self.income.net + self.leftovers_value - self.total_cost
