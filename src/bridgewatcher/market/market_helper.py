from dataclasses import dataclass

from bridgewatcher.api import AlbionOnline
from bridgewatcher.api.model import Cities, CityPrice, Qualities
from bridgewatcher.db.schema import Item


@dataclass
class MarketQuery:
    item_or_id: Item | str
    quality: Qualities
    include_black_market: bool

    @staticmethod
    def with_black_market_included(
        item_or_id: Item | str, quality: Qualities
    ) -> "MarketQuery":
        return MarketQuery(item_or_id, quality, True)

    @staticmethod
    def with_black_market_excluded(
        item_or_id: Item | str, quality: Qualities
    ) -> "MarketQuery":
        return MarketQuery(item_or_id, quality, False)


# The fields for cheapest buy and sell price on CityPrice object
# may seem off but I believe they are the right ones for the job.
# See the definition of CityPrice for more detailed information
class MarketHelper:
    def __init__(self, albion: AlbionOnline) -> None:
        self.albion = albion

    def _get_prices_for_quality(
        self,
        prices: list[CityPrice],
        quality: Qualities,
        include_black_market: bool = True,
    ) -> list[CityPrice]:
        return [
            price
            for price in prices
            if price.quality == quality.value
            and (include_black_market or price.city.lower() != Cities.BLACK_MARKET)
        ]

    async def get_cheapest_item_buy_price(self, query: MarketQuery) -> CityPrice:
        prices = await self.albion.get_item_prices(query.item_or_id)
        return self._find_cheapest_buy_price(
            prices, query.quality, query.include_black_market
        )

    def _find_cheapest_buy_price(
        self,
        prices: list[CityPrice],
        quality: Qualities,
        include_black_market: bool = True,
    ) -> CityPrice:
        filtered = self._get_prices_for_quality(prices, quality, include_black_market)
        non_zero = [price for price in filtered if price.buy_price_max > 0]
        return min(non_zero if non_zero else filtered, key=lambda p: p.buy_price_max)

    async def get_expensive_item_sell_price(self, query: MarketQuery) -> CityPrice:
        prices = await self.albion.get_item_prices(query.item_or_id)
        return self._find_expensive_sell_price(
            prices, query.quality, query.include_black_market
        )

    def _find_expensive_sell_price(
        self,
        prices: list[CityPrice],
        quality: Qualities,
        include_black_market: bool = True,
    ) -> CityPrice:
        filtered = self._get_prices_for_quality(prices, quality, include_black_market)
        non_zero = [price for price in filtered if price.sell_price_min > 0]
        return max(non_zero if non_zero else filtered, key=lambda p: p.sell_price_min)
