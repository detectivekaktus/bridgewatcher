from dataclasses import dataclass

from bridgewatcher.api.model import Cities, Qualities
from bridgewatcher.calc import MarketHelper, MarketQuery


class MarketFlipper(MarketHelper):
    @dataclass
    class Response:
        buy_price: int
        buy_city: Cities
        sell_price: int
        sell_city: Cities
        quality: Qualities

    async def flip(self, query: MarketQuery) -> Response:
        buy_price = await self.get_cheapest_item_buy_price(query)
        sell_price = await self.get_expensive_item_sell_price(query)
        return self.Response(
            buy_price=buy_price.buy_price_max,
            buy_city=Cities.from_str(buy_price.city),
            sell_price=sell_price.sell_price_min,
            sell_city=Cities.from_str(sell_price.city),
            quality=query.quality,
        )
