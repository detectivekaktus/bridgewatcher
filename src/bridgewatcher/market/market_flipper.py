from math import ceil

from bridgewatcher.api.model import Cities
from bridgewatcher.market import MarketHelper, MarketQuery
from bridgewatcher.market.consts import ORDER_FEE, ORDINARY_TAX, PREMIUM_TAX
from bridgewatcher.market.model import MarketFlip
from bridgewatcher.util.exc import InsufficientDataError


class MarketFlipper(MarketHelper):
    async def flip(self, query: MarketQuery, has_premium: bool = True) -> MarketFlip:
        buy_query = (
            query
            if not query.include_black_market
            else MarketQuery.with_black_market_excluded(query.item_or_id, query.quality)
        )

        buy_price = await self.get_cheapest_item_buy_price(buy_query)
        if buy_price.sell_price_min == 0:
            raise InsufficientDataError(f"No fresh prices on {query.item_or_id}")

        sell_price = await self.get_expensive_item_sell_price(query)
        if sell_price.sell_price_min == 0:
            raise InsufficientDataError(f"No fresh prices on {query.item_or_id}")

        applied_tax = PREMIUM_TAX if has_premium else ORDINARY_TAX
        taxes = ceil(sell_price.sell_price_min * applied_tax)

        buy_fee = ceil(buy_price.sell_price_min * ORDER_FEE)
        sell_fee = ceil(sell_price.sell_price_min * ORDER_FEE)
        fees = buy_fee + sell_fee

        return MarketFlip(
            buy_price=buy_price.sell_price_min,
            buy_city=Cities.from_str(buy_price.city),
            sell_price=sell_price.sell_price_min,
            sell_city=Cities.from_str(sell_price.city),
            quality=query.quality,
            taxes=taxes,
            fees=fees,
        )
