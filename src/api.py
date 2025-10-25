#!/usr/bin/env python3
import sys
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
    """
    Albion Online Data Project manager class. The class provides facade interface
    for fetching Albion market data with internal in-memory caching for efficient
    data retrieval and load balancing API requests to evade HTTP 429.
    """

    def __init__(self, database: Database, update_interval_sec: int = 600) -> None:
        """
        Initialize AlbionOnlineDataManager class.

        Args:
            database (Database): global database reference.
            update_interval_sec (int): recache interval in seconds.
        """
        try:
            self._database = database
            self._update_interval_sec = update_interval_sec
            self._cache: list[dict[str, list[dict[str, Any]]]] = [{}, {}, {}]
            # number of items fetched per request.
            self._chunk_size: int = 64
            # async lock that allows to queue incoming requests during caching
            self._lock = Lock()
            self._cached_item_names: list[str] = self.__fill_cached_item_names()
        except (ProgrammingError, OperationalError):
            LOGGER.error("PANIC: No database table `items` found.")
            LOGGER.error(
                "FATAL ERROR: `__fill_cached_item_names()` has failed with an SQL error. This is likely due to a programming error inside the codebase. Please, double check SQL queries and try running the application again."
            )
            sys.exit(1)

    async def lifecycle(self) -> None:
        """
        Manager's lifecycle that runs forever. During the lifecycle
        the manager object updates global data cache.
        """
        while True:
            await self.__update_cache()
            await sleep(self._update_interval_sec)

    async def __update_cache(self) -> None:
        """
        Update global data cache. The update happens in parallel on American, European,
        and Asian servers. For each server async tasks are created, gathered and processed
        to update internal cache with the latest data on Albion Online Data Project server.
        Missing responses are padded with empty placeholders to preserve chunk size consistent.

        The update is thread safe because it's guarded with an internal async lock. This prevents
        concurrent write or read operations.

        Workflow:
            1. Create async fetch tasks for each server via `__create_server_tasks()`.
            2. Await completion of each fetch task with `asyncio.gather()`.
            3. Chain all received responses per server.
            4. Insert data into cache for each item.
            5. Log the performance of caching.

        Note:
            This function is called only and only inside `lifecycle()` method and is not intended
            to be called anywhere else.
        """
        LOGGER.info("Cache update started.")
        start = perf_counter()

        async with self._lock:
            tasks: dict[int, list[Task]] = self.__create_server_tasks()
            for server in range(1, 4):
                responses: list[list[dict[str, Any]]] = await gather(*tasks[server])
                chained_responses: list[dict[str, Any]] = []

                # If no response, add `[{}] * self_chunk_size` padding to keep
                # the data consistent.
                for response in responses:
                    chained_responses.extend(
                        response if response else [{}] * self._chunk_size
                    )

                for response in chained_responses:
                    # the [{}] responses from top
                    if not response:
                        continue
                    # This may be a memory hog because previous responses aren't(?) discarded.
                    elif response["item_id"] not in self._cache[server - 1]:
                        self._cache[server - 1][response["item_id"]] = [response]
                    else:
                        self._cache[server - 1][response["item_id"]].append(response)

        LOGGER.info(
            f"Finished caching. Took: {round(perf_counter() - start, 2)} seconds."
        )

    def __create_server_tasks(self) -> dict[int, list[Task]]:
        """
        For each server create fetch tasks for internal data caching using `AlbionOnlineData`
        object. Each task fetches `self._chunk_size` items.

        Returns:
            dict[int, list[Task]]: A mapping of server ID to a list of fetch tasks.
        """
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
        """
        Get item data by its name and quality on specified server. This method triggers an
        async lock which blocks incoming concurrent write and read requests. If the item is
        cached and its quality is equal to 1, returns the item data from cache, otherwise
        makes an additional API request.

        Args:
            item_name (str): internal item name.
            server (int): 1 for NA, 2 for Europe, and 3 for Asia.
            quality (int): normal to masterpiece quality expressed with an integer.

        Returns:
            Optional[list[dict[str, Any]]]: item data from cache or API, or `None` if the
            request fails.
        """
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
        
    async def get_gold(self, server: int, count: int = 3) -> Optional[list[dict[str, Any]]]:
        """
        Get latest gold prices from Albion Online Data project server.

        Args:
            server (int): 1 for NA, 2 for Europe, and 3 for Asia
            count (int): entries to fetch

        Returns:
            Optional[list[dict[str, Any]]]: list of the latest gold prices or `None`
            if the request fails.
        """
        fetcher = AlbionOnlineData(server)
        return await fetcher.fetch_gold(count)

    def __fill_cached_item_names(self) -> list[str]:
        """
        Select items from `armors`, `weapons`, and `crafting` categories from the items database.

        Returns:
            list[str]: List of cachable item names.
        """
        names: list[str] = []

        with self._database as db:
            db.execute(
                "SELECT * FROM items WHERE shop_category IN (?, ?, ?)",
                ("armors", "weapons", "crafting"),
            )
            items: list[tuple] = db.fetchall()

        # item[0] is an id
        # item[1] is a name
        # See src.db.__init__.py

        # Add enchanted resources and skip other enchanted items.
        for item in items:
            names.append(
                f"{item[1]}@{item[1][-1]}"
                if ItemManager.is_resource(self._database, item[1])
                and item[1][-1] in ("1", "2", "3", "4")
                else item[1]
            )

        return names

    def __is_cached(self, item_name: str) -> bool:
        """Check if item is cachable."""
        return item_name in self._cached_item_names


class Fetcher(ABC):
    """
    Abstract `Fetcher` class. This class is meant to be inherited by any
    class that makes third-party API requests. The class provides internal
    abstract `_fetch(self, url: str)` method for hiding internal logic.
    """

    def __init__(self, server: int, timeout: int = 5) -> None:
        self._server = server
        self._timeout = timeout

    @abstractmethod
    async def _fetch(self, url: str) -> Any:
        pass


class AlbionOnlineData(Fetcher):
    """
    Albion Online Data Project fetcher. This class is not meant to be used directly,
    please, use `AlbionOnlineDataManager` instead.
    """

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
        """
        Get latest gold prices from Albion Online Data project server.

        Returns:
            Optional[list[dict[str, Any]]]: list of the latest gold prices or `None`
            if the request fails.
        """
        return await self._fetch(
            f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/gold?count={count}"
        )

    async def fetch_price(
        self, item_name: str, qualities: int = 1, cities: list[str] = []
    ) -> Optional[list[dict[str, Any]]]:
        """
        Get latest item prices from Albion Online Data project server.

        Returns:
            Optional[list[dict[str, Any]]]: list of the latest item prices in each city
            or `None` if the request fails.
        """
        return await self._fetch(
            f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}&locations={",".join(cities)}"
            if cities
            else f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}"
        )


class SandboxInteractiveInfo(Fetcher):
    """
    Sandbox Interactive API fetcher. This class uses the official reverse-engineered
    Sandbox Interactive API. It can fetch player and guild data.
    """

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

    async def _find_player(self, name: str) -> Optional[dict[str, Any]]:
        """
        Get the player's details by their name. If there are multiple players matching
        the name criteria, the first one is returned.

        Args:
            name (str): in-game player's name.

        Returns:
            Optional[dict[str, Any]]: general player info, or None if the request fails
            or there's no player with the given name.
        """
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

    async def _find_guild(self, name: str) -> Optional[dict[str, Any]]:
        """
        Get the guild's details by its name. If there are multiple guilds matching
        the name criteria, the first one is returned.

        Args:
            name (str): in-game guild's name.

        Returns:
            Optional[dict[str, Any]]: general guild info, or None if the request fails
            or there's no guild with the given name.
        """
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
        """
        Get detailed player data by their name. If there are multilple players
        matching the name criteria, the first one is returned.

        Args:
            name (str): player's name.

        Returns:
            Optional[dict[str, Any]]: detailed player info, or None if the request fails
            or there's no player with the given name.
        """
        player: Optional[dict[str, Any]] = await self._find_player(name)
        if not player:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}"
        )

    async def get_deaths(self, name: str) -> Optional[list[dict[str, Any]]]:
        """
        Get detailed log of recent player's deaths by their name. If there are multilple players
        matching the name criteria, the first one is returned.

        Args:
            name (str): player's name.

        Returns:
            Optional[list[dict[str, Any]]]: detailed log of player's deaths, or None if the request
            fails or there's no player with the given name.
        """
        player: Optional[dict[str, Any]] = await self._find_player(name)
        if not player:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}/deaths"
        )

    async def get_kills(self, name: str) -> Optional[list[dict[str, Any]]]:
        """
        Get detailed log of recent player's kills by their name. If there are multilple players
        matching the name criteria, the first one is returned.

        Args:
            name (str): player's name.

        Returns:
            Optional[list[dict[str, Any]]]: detailed log of player's kills, or None if the request
            fails or there's no player with the given name.
        """
        player: Optional[dict[str, Any]] = await self._find_player(name)
        if not player:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}/kills"
        )

    async def get_guild(self, name: str) -> Optional[dict[str, Any]]:
        """
        Get detailed guild data by its name. If there are multilple guilds
        matching the name criteria, the first one is returned.

        Args:
            name (str): guild's name.

        Returns:
            Optional[dict[str, Any]]: detailed guild info, or None if the request fails
            or there's no guild with the given name.
        """
        guild: Optional[dict[str, Any]] = await self._find_guild(name)
        if not guild:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/guilds/{guild["Id"]}/data"
        )

    async def get_members(self, name: str) -> Optional[list[dict[str, Any]]]:
        """
        Get detailed list of guild members by its name. If there are multilple guilds
        matching the name criteria, the first one is returned.

        Args:
            name (str): guild's name.

        Returns:
            Optional[dict[str, Any]]: detailed list of guild members, or None if the request fails
            or there's no guild with the given name.
        """
        guild: Optional[dict[str, Any]] = await self._find_guild(name)
        if not guild:
            return None

        return await self._fetch(
            f"https://{self._server_prefix}.albiononline.com/api/gameinfo/guilds/{guild["Id"]}/members"
        )


class ItemManager:
    """
    ItemManager class. This class is meant to judge and identify item attributes using
    the internal items database or the input name. It's not instanciatable.
    """

    @staticmethod
    def get_item(database: Database, item_name: str) -> Optional[tuple]:
        """Get item by its name from `items` database."""
        with database as db:
            db.execute("SELECT * FROM items WHERE name = ?", (item_name,))
            item: Optional[tuple] = db.fetchone()
        return item

    @staticmethod
    def is_craftable(database: Database, item_name: str) -> bool:
        """
        Check if item is craftable using the `items` database.

        Returns:
            bool: False if 1. Item name is invalid, 2. Item's got no crafting requirements.
                3. Item's inside NON_CRAFTABLE category, True otherwise.
        
        """
        if ItemManager.is_enchanted(item_name):
            item_name = item_name[:-2]

        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        # If no crafting_requirements field
        if not item[4]:
            return False

        for type in NON_CRAFTABLE:
            if type in item:
                return False

        return True

    @staticmethod
    def is_enchanted(item_name: str) -> bool:
        """
        Check if the last two characters inside item's name are in (@1, @2, @3, @4).
        """
        return item_name[-2:] in ENCHANTMENTS

    @staticmethod
    def is_resource(database: Database, item_name: str) -> bool:
        """
        Check if `shop_category` of item is equal to `crafting`. 
        """
        if ItemManager.is_enchanted(item_name):
            item_name = item_name[:-2]

        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        return "crafting" in item

    @staticmethod
    def is_artefact(database: Database, item_name: str) -> bool:
        """
        Check if `shop_category` of item is equal to `artefacts`. 
        """
        if ItemManager.is_enchanted(item_name):
            return False

        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        return "artefacts" in item

    @staticmethod
    def is_fractional(database: Database, item_name: str) -> bool:
        """
        Check if `shop_category` of item is equal to `cityresources`. 
        """
        if ItemManager.is_enchanted(item_name):
            return False

        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        return "cityresources" in item

    @staticmethod
    def is_consumable(database: Database, item_name: str) -> bool:
        """
        Check if `shop_category` of item is equal to `consumables`. 
        """
        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        return "consumables" in item

    @staticmethod
    def is_returnable(database: Database, item_name: str) -> bool:
        """
        Check if item is returnable during crafting.

        Returns:
            True if item's not an artefact nor a fractional item, False otherwise.
        """
        return not ItemManager.is_artefact(
            database, item_name
        ) and not ItemManager.is_fractional(database, item_name)

    @staticmethod
    def is_sellable_on_black_market(database: Database, item_name: str) -> bool:
        """
        Check if item's category is inside `NON_SELLABLE_ON_BLACK_MARKET`.
        """
        item: Optional[tuple] = ItemManager.get_item(database, item_name)

        if not item:
            return False

        for type in NON_SELLABLE_ON_BLACK_MARKET:
            if type in item:
                return False

        return True


class SandboxInteractiveRenderer:
    """
    Sandbox Interactive API fetcher. This class uses the official reverse-engineered
    Sandbox Interactive API. It can fetch item, spell and wardrobe icons. This class
    is not meant to be instanciated.
    """

    @staticmethod
    def fetch_item(identifier: str, quality: int = 1) -> str:
        """
        Get item icon url by its name and quality.
        
        Args:
            identifier (str): internal item name
            quality (int): normal to masterpiece quality in integer form.

        Returns:
            str: icon url for the item.
        """
        return f"https://render.albiononline.com/v1/item/{identifier}.png?quality={quality}"

    @staticmethod
    def fetch_spell(identifier: str) -> str:
        """
        Get spell icon url by its name.
        
        Args:
            identifier (str): internal spell name

        Returns:
            str: icon url for the spell.
        """
        return f"https://render.albiononline.com/v1/spell/{identifier}.png"

    @staticmethod
    def fetch_wardrobe(identifier: str) -> str:
        """
        Get wardrobe icon url by its name.
        
        Args:
            identifier (str): internal wardrobe name

        Returns:
            str: icon url for the wardrobe.
        """
        return f"https://render.albiononline.com/v1/wardrobe/{identifier}.png"


def get_percent_variation(data: list[dict], index: int) -> float:
    return round((data[index]["price"] / data[index + 1]["price"] - 1) * 100, 2)


def convert_api_timestamp(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").strftime(
        "%d %B %Y, %H:%M:%S UTC"
    )


def remove_suffix(database: Database, item_name: str, is_enchanted: bool) -> str:
    """
    Remove items' enchantment suffix. A normal enchanted item is written like
    T4_MAIN_CURSEDSTAFF@1, while resources are written like T4_METALBAR_LEVEL1@1.

    Returns:
        str: item name without enchantment suffix.

    Example:
        >>> remove_suffix("T4_MAIN_CURSEDSTAFF@1")
        "T4_MAIN_CURSEDSTAFF"
        >>> remove_suffix("T4_METALBAR_LEVEL1@1")
        "T4_METALBAR"
    """
    if is_enchanted:
        return (
            item_name[:-9]
            if ItemManager.is_resource(database, item_name)
            else item_name[:-2]
        )
    return item_name
