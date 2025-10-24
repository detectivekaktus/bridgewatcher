#!/usr/bin/env python3
from abc import ABC, abstractmethod
from aiohttp import ClientSession, ClientTimeout
from asyncio import Lock, Task, create_task, gather, sleep
from datetime import datetime
from sqlite3 import OperationalError, ProgrammingError
from time import perf_counter
from typing import Any, Final, Optional
from src.constants import ENCHANTMENTS, NON_CRAFTABLE, NON_SELLABLE_ON_BLACK_MARKET
from src.db import Database
from src.utils.formatting import inttostr_server
from src.utils.logging import LOGGER


AOD_SERVER_URLS: Final = {1: "west", 2: "europe", 3: "east"}


SBI_SERVER_URLS: Final = {1: "gameinfo", 2: "gameinfo-ams", 3: "gameinfo-sgp"}


class AlbionOnlineDataManager:
    def __init__(self, database: Database, update_interval_sec: int = 600) -> None:
        try:
            self._database = database
            self._update_interval_sec = update_interval_sec
            self._cache: list[dict[str, list[dict[str, Any]]]] = [{}, {}, {}]
            self._chunk_size: int = 64
            self._lock = Lock()
            self._cached_item_names: list[str] = self.__fill_cached_item_names()
        except (ProgrammingError, OperationalError):
            LOGGER.error("No database table `items` found.")

    async def lifecycle(self) -> None:
        while True:
            await self.__update_cache()
            await sleep(self._update_interval_sec)

    async def __update_cache(self) -> None:
        LOGGER.info("Cache update started.")
        start = perf_counter()

        async with self._lock:
            tasks: dict[int, list[Task]] = self.__create_server_tasks()
            for server in range(1, 4):
                responses: list[list[dict[str, Any]]] = await gather(*tasks[server])
                chained_responses: list[dict[str, Any]] = []
                for response in responses:
                    chained_responses.extend(
                        response if response else [{}] * self._chunk_size
                    )

                for response in chained_responses:
                    if not response:
                        continue
                    elif response["item_id"] not in self._cache[server - 1]:
                        self._cache[server - 1][response["item_id"]] = [response]
                    else:
                        self._cache[server - 1][response["item_id"]].append(response)

        LOGGER.info(
            f"Finished caching. Took: {round(perf_counter() - start, 2)} seconds."
        )

    def __create_server_tasks(self) -> dict[int, list[Task]]:
        tasks: dict[int, list[Task]] = {}

        for server in range(1, 4):
            fetcher: AlbionOnlineData = AlbionOnlineData(server)
            tasks[server] = [
                create_task(
                    fetcher.fetch_price(
                        ",".join(self._cached_item_names[i : i + self._chunk_size])
                    )
                )
                for i in range(0, len(self._cached_item_names), self._chunk_size)
            ]

        return tasks

    async def get(
        self, item_name: str, server: int, quality: int = 1
    ) -> Optional[list[dict[str, Any]]]:
        async with self._lock:
            item: Optional[list[dict[str, Any]]] = self._cache[server - 1].get(
                item_name, None
            )
            if not self.__is_cached(item_name) or quality != 1 or not item:
                LOGGER.debug(f"Getting {item_name} {quality} from API.")
                fetcher: AlbionOnlineData = AlbionOnlineData(server)
                return await fetcher.fetch_price(item_name, quality)

            LOGGER.debug(f"Getting {item_name} {quality} from cache.")
            return item

    def __fill_cached_item_names(self) -> list[str]:
        names: list[str] = []

        with self._database as db:
            db.execute(
                "SELECT * FROM items WHERE shop_category IN (?, ?, ?)",
                ("armors", "weapons", "crafting"),
            )
            items: list[tuple] = db.fetchall()

        for item in items:
            names.append(
                f"{item[1]}@{item[1][-1]}"
                if ItemManager.is_resource(self._database, item[1])
                and item[1][-1] in ("1", "2", "3", "4")
                else item[1]
            )

        return names

    def __is_cached(self, item_name: str) -> bool:
        return item_name in self._cached_item_names


class Fetcher(ABC):
    def __init__(self, server: int, timeout: int = 5) -> None:
        self._server = server
        self._timeout = timeout

    @abstractmethod
    async def _fetch(self, url: str) -> Any:
        pass


class AlbionOnlineData(Fetcher):
    def __init__(self, server: int, timeout: int = 5) -> None:
        super().__init__(server=server, timeout=timeout)
        self._server_prefix = AOD_SERVER_URLS[server]

    async def _fetch(self, url: str) -> Any:
        try:
            async with ClientSession(
                timeout=ClientTimeout(total=self._timeout)
            ) as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        return await r.json()
                    LOGGER.error(f"Got status code {r.status} on fetch {url}")
                    return None
        except TimeoutError:
            LOGGER.error(f"Timed out on {url} fetch.")
            return None

    async def fetch_gold(self, count: int = 3) -> Optional[list[dict[str, Any]]]:
        return await self._fetch(
            f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/gold?count={count}"
        )

    async def fetch_price(
        self, item_name: str, qualities: int = 1, cities: list[str] = []
    ) -> Optional[list[dict[str, Any]]]:
        return await self._fetch(
            f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}&locations={",".join(cities)}"
            if cities
            else f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}"
        )


class SandboxInteractiveInfo(Fetcher):
    def __init__(self, server: int, timeout: int = 5) -> None:
        super().__init__(server=server, timeout=timeout)
        self._server_prefix = SBI_SERVER_URLS[server]

    async def _fetch(self, url: str) -> Any:
        try:
            async with ClientSession(
                timeout=ClientTimeout(total=self._timeout)
            ) as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        return await r.json()
                    LOGGER.error(f"Got status code {r.status} on fetch {url}")
                    return None
        except TimeoutError:
            LOGGER.error(f"Timed out on {url} fetch.")
            return None

    async def find_player(self, name: str) -> Optional[dict[str, Any]]:
        try:
            async with ClientSession(
                timeout=ClientTimeout(total=self._timeout)
            ) as session:
                async with session.get(
                    f"https://{self._server_prefix}.albiononline.com/api/gameinfo/search?q={name}"
                ) as r:
                    if r.status == 200:
                        json = await r.json()
                        if len(json["players"]) == 0:
                            return None

                        return json["players"][0]
                    else:
                        LOGGER.error(
                            f"Got status code {r.status} during player `{name}` lookup on {inttostr_server(self._server)} server."
                        )
                        return None
        except TimeoutError:
            LOGGER.error(
                f"Couldn't read or connect to find player `{name}` on {inttostr_server(self._server)} server."
            )
            return None

    async def find_guild(self, name: str) -> Optional[dict[str, Any]]:
        try:
            async with ClientSession(
                timeout=ClientTimeout(total=self._timeout)
            ) as session:
                async with session.get(
                    f"https://{self._server_prefix}.albiononline.com/api/gameinfo/search?q={name}"
                ) as r:
                    if r.status == 200:
                        json = await r.json()
                        if len(json["guilds"]) == 0:
                            return None

                        return json["guilds"][0]
                    else:
                        LOGGER.error(
                            f"Got status code {r.status} during guild `{name}` lookup on {inttostr_server(self._server)} server."
                        )
                        return None
        except TimeoutError:
            LOGGER.error(
                f"Couldn't read or connect to find guild `{name}` on {inttostr_server(self._server)} server."
            )
            return None

    async def get_player(self, name: str) -> Optional[dict[str, Any]]:
        player: Optional[dict[str, Any]] = await self.find_player(name)
        if not player:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}"
        )

    async def get_deaths(self, name: str) -> Optional[list[dict[str, Any]]]:
        player: Optional[dict[str, Any]] = await self.find_player(name)
        if not player:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}/deaths"
        )

    async def get_kills(self, name: str) -> Optional[list[dict[str, Any]]]:
        player: Optional[dict[str, Any]] = await self.find_player(name)
        if not player:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}/kills"
        )

    async def get_guild(self, name: str) -> Optional[dict[str, Any]]:
        guild: Optional[dict[str, Any]] = await self.find_guild(name)
        if not guild:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/guilds/{guild["Id"]}/data"
        )

    async def get_members(self, name: str) -> Optional[list[dict[str, Any]]]:
        guild: Optional[dict[str, Any]] = await self.find_guild(name)
        if not guild:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/guilds/{guild["Id"]}/members"
        )


class ItemManager:
    @staticmethod
    def get_item(database: Database, item_name: str) -> Optional[tuple]:
        with database as db:
            db.execute("SELECT * FROM items WHERE name = ?", (item_name,))
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
        return not ItemManager.is_artefact(
            database, item_name
        ) and not ItemManager.is_fractional(database, item_name)

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
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").strftime(
        "%d %B %Y, %H:%M:%S UTC"
    )


def remove_suffix(database: Database, item_name: str, is_enchanted: bool) -> str:
    if is_enchanted:
        return (
            item_name[:-9]
            if ItemManager.is_resource(database, item_name)
            else item_name[:-2]
        )
    return item_name
