from enum import StrEnum
from json import dumps, loads
from typing import overload

from aiohttp import ClientSession
from dacite import from_dict

from bridgewatcher.api.model import CityPrice
from bridgewatcher.db import redis
from bridgewatcher.db.schema import Item


class AlbionOnlineServers(StrEnum):
    AMERICA = "west"
    EUROPE = "europe"
    ASIA = "east"


class AlbionOnline:
    # This is supposed to be prepended with https:// and the subdomain for
    # the server you want to fetch data from
    base_uri: str = "albion-online-data.com/api/v2/stats/prices"

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
        if redis.exists(key):
            prices = loads(await redis.get(key))  # type: ignore
            return prices

        async with ClientSession() as session:
            url = f"https://{self.server.value}.{self.base_uri}/{id}"
            async with session.get(url) as res:
                if not res.ok:
                    # TODO: Add logger warning
                    return []

                body = await res.json()

        prices = [from_dict(data_class=CityPrice, data=price) for price in body]
        await redis.set(key, dumps(prices), ex=300)
        return prices
