#!/usr/bin/env python3
from abc import ABC
from datetime import datetime
from typing import Any, Final, List, Optional, Tuple
from requests import ReadTimeout, Response, get
from src import CITIES, ENCHANTMENTS, NON_CRAFTABLE, NON_SELLABLE_ON_BLACK_MARKET
from src.client import database


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


class Fetcher(ABC):
    def __init__(self, server: int, timeout: int = 5) -> None:
        self._server = server
        self._timeout = timeout


class AlbionOnlineData(Fetcher):
    def __init__(self, server: int, timeout: int = 5) -> None:
        super().__init__(server=server, timeout=timeout)
        self._server_prefix = AOD_SERVER_URLS[server]


    def fetch_gold(self, count: int = 3) -> Optional[List[dict[str, Any]]]:
        try:
            response: Response = get(f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/gold?count={count}",
                                     timeout=self._timeout)
            if not response.ok:
                return None

            return response.json()
        except ReadTimeout:
            return None

    def fetch_price(self, item_name: str, qualities: int = 1, cities: List[str] = []) -> Optional[List[dict[str, Any]]]:
        try:
            response: Response = get(f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}&locations={",".join(cities)}" if cities else f"https://{self._server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}",
                                         timeout=self._timeout)
            if not response.ok:
                return None

            return response.json()
        except ReadTimeout:
            return None


class SandboxInteractiveInfo(Fetcher):
    def __init__(self, server: int, timeout: int = 5) -> None:
        super().__init__(server=server, timeout=timeout)
        self._server_prefix = SBI_SERVER_URLS[server]


    def find_player(self, name: str) -> Optional[dict[str, Any]]:
        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/search?q={name}")
            if not response.ok:
                return None

            json: dict[str, Any] = response.json()
            if len(json["players"]) == 0:
                return None

            return json["players"][0]
        except ReadTimeout:
            return None


    def find_guild(self, name: str) -> Optional[dict[str, Any]]:
        try:
            response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/search?q={name}")
            if not response.ok:
                return None

            json: dict[str, Any] = response.json()
            if len(json["guilds"]) == 0:
                return None

            return json["guilds"][0]
        except ReadTimeout:
            return None


    def get_player(self, name: str) -> Optional[dict[str, Any]]:
        player: Optional[dict[str, Any]] = self.find_player(name)
        if not player:
            return None

        response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}")
        if not response.ok:
            return None

        return response.json()


    def get_deaths(self, name: str) -> Optional[list[dict[str, Any]]]:
        player: Optional[dict[str, Any]] = self.find_player(name)
        if not player:
            return None

        response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}/deaths")
        if not response.ok:
            return None

        return response.json()

    
    def get_kills(self, name: str) -> Optional[list[dict[str, Any]]]:
        player: Optional[dict[str, Any]] = self.find_player(name)
        if not player:
            return None

        response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/players/{player["Id"]}/kills")
        if not response.ok:
            return None

        return response.json()


    def get_guild(self, name: str) -> Optional[dict[str, Any]]:
        guild: Optional[dict[str, Any]] = self.find_guild(name)
        if not guild:
            return None

        response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/guilds/{guild["Id"]}/data")
        if not response.ok:
            return None

        return response.json()

    
    def get_members(self, name: str) -> Optional[list[dict[str, Any]]]:
        guild: Optional[dict[str, Any]] = self.find_guild(name)
        if not guild:
            return None

        response: Response = get(f"https://{self._server_prefix}.albiononline.com/api/gameinfo/guilds/{guild["Id"]}/members")
        if not response.ok:
            return None

        return response.json()


class ItemManager:
    @staticmethod
    def get_item(item_name: str) -> Optional[Tuple]:
        with database as db:
            db.execute("SELECT * FROM items WHERE name = ?", (item_name, ))
            item: Optional[Tuple] = db.fetchone()
        return item

    @staticmethod
    def exists(item_name: str) -> bool:
        is_enchanted: bool = ItemManager.is_enchanted(item_name)

        try:
            item_name = remove_suffix(item_name, is_enchanted)
        except IndexError:
            return False
        
        if int(item_name[1]) < 4 and is_enchanted and not ItemManager.is_consumable(item_name):
            return False
        
        if is_enchanted and ItemManager.is_artefact(item_name):
            return False

        item: Optional[Tuple] = ItemManager.get_item(item_name)

        return True if item != None else False

    @staticmethod
    def is_craftable(item_name: str) -> bool:
        if ItemManager.is_enchanted(item_name):
            item_name = item_name[:-2]

        item: Optional[Tuple] = ItemManager.get_item(item_name)

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
    def is_resource(item_name: str) -> bool:
        if ItemManager.is_enchanted(item_name):
            item_name = item_name[:-2]

        item: Optional[Tuple] = ItemManager.get_item(item_name)

        if not item:
            return False

        return "resources" in item

    @staticmethod
    def is_artefact(item_name: str) -> bool:
        if ItemManager.is_enchanted(item_name):
            return False

        item: Optional[Tuple] = ItemManager.get_item(item_name)

        if not item:
            return False

        return "artefacts" in item

    @staticmethod
    def is_fractional(item_name: str) -> bool:
        if ItemManager.is_enchanted(item_name):
            return False

        item: Optional[Tuple] = ItemManager.get_item(item_name)

        if not item:
            return False

        return "cityresources" in item

    @staticmethod
    def is_consumable(item_name: str) -> bool:
        item: Optional[Tuple] = ItemManager.get_item(item_name)

        if not item:
            return False

        return "consumables" in item

    @staticmethod
    def is_returnable(item_name: str) -> bool:
        return not ItemManager.is_artefact(item_name) and not ItemManager.is_fractional(item_name)

    @staticmethod
    def is_sellable_on_black_market(item_name: str) -> bool:
        item: Optional[Tuple] = ItemManager.get_item(item_name)

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


def get_percent_variation(data: List[dict], index: int) -> float:
    return round((data[index]["price"] / data[index + 1]["price"] - 1) * 100, 2)


def convert_api_timestamp(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").strftime("%d %B %Y, %H:%M:%S UTC")


def strquality_toint(quality: str) -> int:
    match quality.lower():
        case "normal":
            return 1
        case "good":
            return 2
        case "outstanding":
            return 3
        case "excellent":
            return 4
        case "masterpiece":
            return 5
        case _:
            return 1


def is_valid_city(city: str) -> bool:
    return city.lower() in CITIES


def remove_suffix(item_name: str, is_enchanted: bool) -> str:
    if is_enchanted:
        return item_name[:-9] if ItemManager.is_resource(item_name) else item_name[:-2]
    return item_name
