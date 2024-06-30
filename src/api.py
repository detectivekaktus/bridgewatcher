#!/usr/bin/env python3
from abc import ABC
from asyncio import Lock, sleep
from datetime import datetime
from sqlite3 import OperationalError, ProgrammingError
from time import perf_counter
from typing import Any, Final, Optional
from requests import ConnectTimeout, ReadTimeout, Response, get
from src.constants import CITIES, ENCHANTMENTS, NON_CRAFTABLE, NON_SELLABLE_ON_BLACK_MARKET
from src.db import Database
from src.utils import inttostr_server
from src.utils.logging import LOGGER


AOD_SERVER_URLS: Final = {
    1: "west",
    2: "europe",
    3: "east"
}


SBI_SERVER_URLS: Final = {
    1: "gameinfo",
    2: "gameinfo-ams",
    3: "gameinfo-sgp"
}


class AlbionOnlineDataManager:
    def __init__(self, database: Database, update_interval_sec: int = 900) -> None:
        try:
            self.__database = database
            self.__update_interval_sec = update_interval_sec
            self.__cache: list[dict[str, list[dict[str, Any]]]] = [{}, {}, {}]
            self.__lock = Lock()
            self.__cached_item_names: list[str] = self.__fill_cached_item_names()
        except (ProgrammingError, OperationalError):
            LOGGER.error("No database table `items` found.")


    async def lifecycle(self) -> None:
        while True:
            await self.__update_cache()
            await sleep(self.__update_interval_sec)


    async def __update_cache(self) -> None:
        LOGGER.info("Cache update started.")
        start = perf_counter()

        async with self.__lock:
            for server in range(1, 4):
                fetcher: AlbionOnlineData = AlbionOnlineData(server)
                chunk_size: int = 64
                for i in range(0, len(self.__cached_item_names), chunk_size):
                    names: list[str] = self.__cached_item_names[i:i + chunk_size]
                    items: Optional[list[dict[str, Any]]] = await fetcher.fetch_price(",".join(names))
                    if not items:
                        LOGGER.error(f"Couldn't cache {",".join(names)} on {inttostr_server(server)} server.")
                        continue

                    for name in names:
                        for item in range(0, len(items), len(CITIES)):
                            self.__cache[server - 1][name] = items[item:item + len(CITIES)]

        LOGGER.info(f"Finished caching. Took: {round(perf_counter() - start, 2)} seconds.")


    async def get(self, item_name: str, server: int, quality: int = 1) -> Optional[list[dict[str, Any]]]:
        async with self.__lock:
            if not self.__is_cached(item_name) or quality != 1:
                fetcher: AlbionOnlineData = AlbionOnlineData(server)
                return await fetcher.fetch_price(item_name, quality)

            return self.__cache[server - 1].get(item_name.lower(), None)


    def __fill_cached_item_names(self) -> list[str]:
        names: list[str] = []

        with self.__database as db:
            db.execute("SELECT * FROM items WHERE shop_category IN (?, ?, ?, ?, ?, ?)",
                       ("armor", "mainhand", "offhand", "mounts", "artefacts", "resources"))
            items: list[tuple] = db.fetchall()

        for item in items:
            if ItemManager.is_resource(self.__database, item[1]) and item[1][-1] in ("1", "2", "3", "4"):
                names.append(f"{item[1]}@{item[1][-1]}")
            else:
                names.append(item[1])

        return names


    def __is_cached(self, item_name: str) -> bool:
        return item_name.lower() in self.__cached_item_names


class Fetcher(ABC):
    def __init__(self, server: int, timeout: int = 5) -> None:
        self._server = server
        self._timeout = timeout


class AlbionOnlineData(Fetcher):
    def __init__(self, server: int, timeout: int = 5) -> None:
        super().__init__(server=server, timeout=timeout)
        self._server_prefix = AOD_SERVER_URLS[server]


    async def fetch_gold(self, count: int = 3) -> Optional[list[dict[str, Any]]]:
        try:
            response: Response = get(f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/gold?count={count}",
                                     timeout=self._timeout)
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during gold fetch on {inttostr_server(self._server)} server.")
                return None

            return response.json()
        except (ReadTimeout, ConnectTimeout):
            LOGGER.error(f"Couldn't read or connect to fetch gold price on {inttostr_server(self._server)} server.")
            return None

    async def fetch_price(self, item_name: str, qualities: int = 1, cities: list[str] = []) -> Optional[list[dict[str, Any]]]:
        try:
            response: Response = get(f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}&locations={",".join(cities)}" if cities else f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}",
                                         timeout=self._timeout)
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during item price fetch on {inttostr_server(self._server)} server.")
                return None

            return response.json()
        except (ReadTimeout, ConnectTimeout):
            LOGGER.error(f"Couldn't read or connect to fetch item price on {inttostr_server(self._server)} server.")
            return None


class SandboxInteractiveInfo(Fetcher):
    def __init__(self, server: int, timeout: int = 5) -> None:
        super().__init__(server=server, timeout=timeout)
        self._server_prefix = SBI_SERVER_URLS[server]


    def find_player(self, name: str) -> Optional[dict[str, Any]]:
        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/search?q={name}")
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during player `{name}` lookup on {inttostr_server(self._server)} server.")
                return None

            json: dict[str, Any] = response.json()
            if len(json["players"]) == 0:
                return None

            return json["players"][0]
        except (ReadTimeout, ConnectTimeout) as e:
            LOGGER.error(f"Couldn't read or connect to find player `{name}` on {inttostr_server(self._server)} server.")
            LOGGER.error(e)
            return None


    def find_guild(self, name: str) -> Optional[dict[str, Any]]:
        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/search?q={name}")
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during guild `{name}` lookup on {inttostr_server(self._server)} server.")
                return None

            json: dict[str, Any] = response.json()
            if len(json["guilds"]) == 0:
                return None

            return json["guilds"][0]
        except (ReadTimeout, ConnectTimeout) as e:
            LOGGER.error(f"Couldn't read or connect to find guild `{name}` on {inttostr_server(self._server)} server.")
            LOGGER.error(e)
            return None


    def get_player(self, name: str) -> Optional[dict[str, Any]]:
        player: Optional[dict[str, Any]] = self.find_player(name)
        if not player:
            return None

        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}")
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during player `{name}` fetch on {inttostr_server(self._server)} server.")
                return None

            return response.json()
        except (ReadTimeout, ConnectTimeout) as e:
            LOGGER.error(f"Couldn't read or connect to get player `{name}` on {inttostr_server(self._server)} server.")
            LOGGER.error(e)
            return None


    def get_deaths(self, name: str) -> Optional[list[dict[str, Any]]]:
        player: Optional[dict[str, Any]] = self.find_player(name)
        if not player:
            return None

        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}/deaths")
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during player `{name}` deaths fetch on {inttostr_server(self._server)} server.")
                return None

            return response.json()
        except (ReadTimeout, ConnectTimeout) as e:
            LOGGER.error(f"Couldn't read or connect to get player `{name}` deaths on {inttostr_server(self._server)} server.")
            LOGGER.error(e)
            return None

    
    def get_kills(self, name: str) -> Optional[list[dict[str, Any]]]:
        player: Optional[dict[str, Any]] = self.find_player(name)
        if not player:
            return None

        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}/kills")
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during player `{name}` kills fetch on {inttostr_server(self._server)} server.")
                return None

            return response.json()
        except (ReadTimeout, ConnectTimeout) as e:
            LOGGER.error(f"Couldn't read or connect to get player `{name}` kills on {inttostr_server(self._server)} server.")
            LOGGER.error(e)
            return None


    def get_guild(self, name: str) -> Optional[dict[str, Any]]:
        guild: Optional[dict[str, Any]] = self.find_guild(name)
        if not guild:
            return None

        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/guilds/{guild["Id"]}/data")
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during guild `{name}` fetch on {inttostr_server(self._server)} server.")
                return None

            return response.json()
        except (ReadTimeout, ConnectTimeout) as e:
            LOGGER.error(f"Couldn't read or connect to get guild `{name}` on {inttostr_server(self._server)} server.")
            LOGGER.error(e)
            return None

    
    def get_members(self, name: str) -> Optional[list[dict[str, Any]]]:
        guild: Optional[dict[str, Any]] = self.find_guild(name)
        if not guild:
            return None

        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/guilds/{guild["Id"]}/members")
            if not response.ok:
                LOGGER.error(f"Got status code {response.status_code} during guild `{name}` members fetch on {inttostr_server(self._server)} server.")
                return None

            return response.json()
        except (ReadTimeout, ConnectTimeout) as e:
            LOGGER.error(f"Couldn't read or connect to get guild `{name}` members on {inttostr_server(self._server)} server.")
            LOGGER.error(e)
            return None


class ItemManager:
    @staticmethod
    def get_item(database: Database, item_name: str) -> Optional[tuple]:
        with database as db:
            db.execute("SELECT * FROM items WHERE name = ?", (item_name, ))
            item: Optional[tuple] = db.fetchone()
        return item

    @staticmethod
    def is_craftable(database: Database, item_name: str) -> bool:
        if ItemManager.is_enchanted(item_name):
            item_name = item_name[:-2]

        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        if not item[4]:
            return False

        for type in NON_CRAFTABLE:
            if type in item:
                return False

        return True

    @staticmethod
    def is_enchanted(item_name: str) -> bool:
        return item_name[-2:] in ENCHANTMENTS

    @staticmethod
    def is_resource(database: Database, item_name: str) -> bool:
        if ItemManager.is_enchanted(item_name):
            item_name = item_name[:-2]

        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        return "resources" in item

    @staticmethod
    def is_artefact(database: Database, item_name: str) -> bool:
        if ItemManager.is_enchanted(item_name):
            return False

        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        return "artefacts" in item

    @staticmethod
    def is_fractional(database: Database, item_name: str) -> bool:
        if ItemManager.is_enchanted(item_name):
            return False

        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        return "cityresources" in item

    @staticmethod
    def is_consumable(database: Database, item_name: str) -> bool:
        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        return "consumables" in item

    @staticmethod
    def is_returnable(database: Database, item_name: str) -> bool:
        return not ItemManager.is_artefact(database, item_name) and not ItemManager.is_fractional(database, item_name)

    @staticmethod
    def is_sellable_on_black_market(database: Database, item_name: str) -> bool:
        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        for type in NON_SELLABLE_ON_BLACK_MARKET:
            if type in item:
                return False

        return True


class SandboxInteractiveRenderer:
    @staticmethod
    def fetch_item(identifier: str, quality: int = 1) -> str:
        return f"https://render.albiononline.com/v1/item/{identifier}.png?quality={quality}"

    @staticmethod
    def fetch_spell(identifier: str) -> str:
        return f"https://render.albiononline.com/v1/spell/{identifier}.png"

    @staticmethod
    def fetch_wardrobe(identifier: str) -> str:
        return f"https://render.albiononline.com/v1/wardrobe/{identifier}.png" 


def get_percent_variation(data: list[dict], index: int) -> float:
    return round((data[index]["price"] / data[index + 1]["price"] - 1) * 100, 2)


def convert_api_timestamp(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").strftime("%d %B %Y, %H:%M:%S UTC")


def remove_suffix(database: Database, item_name: str, is_enchanted: bool) -> str:
    if is_enchanted:
        return item_name[:-9] if ItemManager.is_resource(database, item_name) else item_name[:-2]
    return item_name

