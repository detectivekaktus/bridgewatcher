from bridgewatcher.api.model import Cities
from bridgewatcher.market import MarketHelper, MarketQuery
from bridgewatcher.market.model import MarketFlip
from bridgewatcher.util.exc import InsufficientDataError


class MarketFlipper(MarketHelper):
    async def flip(self, query: MarketQuery) -> MarketFlip:
        buy_price = await self.get_cheapest_item_buy_price(query)
        if buy_price.buy_price_max == 0:
            raise InsufficientDataError(f"No fresh prices on {query.item_or_id}")

        sell_price = await self.get_expensive_item_sell_price(query)
        if sell_price.sell_price_min == 0:
            raise InsufficientDataError(f"No fresh prices on {query.item_or_id}")

        return MarketFlip(
            buy_price=buy_price.buy_price_max,
            buy_city=Cities.from_str(buy_price.city),
            sell_price=sell_price.sell_price_min,
            sell_city=Cities.from_str(sell_price.city),
            quality=query.quality,
        )
