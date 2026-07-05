from enum import StrEnum
from json import dumps, loads
from typing import overload

from aiohttp import ClientSession, ClientTimeout
from dacite import from_dict

from bridgewatcher.api.model import CityPrice, GoldPrice
from bridgewatcher.db import redis
from bridgewatcher.db.schema import Item
from bridgewatcher.loggers import LOGGER


class AlbionOnlineServers(StrEnum):
    AMERICA = "west"
    EUROPE = "europe"
    ASIA = "east"


class AlbionOnline:
    MAX_GOLD_PRICE_COUNT = 24

    ITEM_CACHE_EXPIRATION_PERIOD = 60 * 5
    GOLD_CACHE_EXPIRATION_PERIOD = 60 * 60

    # This is supposed to be prepended with https:// and the subdomain for
    # the server you want to fetch data from
    base_uri: str = "albion-online-data.com/api/v2/stats"

    def __init__(self, server: AlbionOnlineServers) -> None:
        self.server = server

    @overload
    async def get_item_prices(self, item_or_id: Item) -> list[CityPrice]: ...

    @overload
    async def get_item_prices(self, item_or_id: str) -> list[CityPrice]: ...

    async def get_item_prices(self, item_or_id: Item | str) -> list[CityPrice]:
        id = item_or_id.name if isinstance(item_or_id, Item) else item_or_id

        # items are stored as item_id:server
        key = f"{id}:{self.server.value}"
        if await redis.exists(key):
            raw_prices = loads(await redis.get(key))  # type: ignore
            prices = [CityPrice(**raw_price) for raw_price in raw_prices]
            return prices

        async with ClientSession(timeout=ClientTimeout(total=5)) as session:
            url = f"https://{self.server.value}.{self.base_uri}/prices/{id}"
            async with session.get(url) as res:
                if not res.ok:
                    LOGGER.warning(
                        f"{res.status}: Couldn't fetch item prices for {id}."
                    )
                    return []

                body = await res.json()

        prices = [from_dict(data_class=CityPrice, data=price) for price in body]
        await redis.set(key, dumps(body), ex=self.ITEM_CACHE_EXPIRATION_PERIOD)
        return prices

    async def get_gold_prices(self) -> list[GoldPrice]:
        key = f"gold:{self.server.value}"
        if await redis.exists(key):
            raw_prices = loads(await redis.get(key))  # type: ignore
            prices = [GoldPrice(**raw_price) for raw_price in raw_prices]
            return prices

        async with ClientSession(timeout=ClientTimeout(total=5)) as session:
            url = f"https://{self.server.value}.{self.base_uri}/gold?count={self.MAX_GOLD_PRICE_COUNT}"
            async with session.get(url) as res:
                if not res.ok:
                    LOGGER.warning(f"{res.status}: Couldn't fetch gold prices.")
                    return []

                body = await res.json()

        prices = [from_dict(data_class=GoldPrice, data=price) for price in body]
        await redis.set(key, dumps(body), ex=self.GOLD_CACHE_EXPIRATION_PERIOD)
        return prices
