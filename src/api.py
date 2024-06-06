#!/usr/bin/env python3
from datetime import datetime
from typing import Any, Final, List, Optional, Tuple
from sqlite3 import Connection, Cursor, connect
from requests import ReadTimeout, Response, get
from src import CITIES, ENCHANTMENTS


SERVER_URLS: Final = {
    1: "west",
    2: "europe",
    3: "east"
}


class AODFetcher:
    def __init__(self, server: int, timeout: int = 5) -> None:
        self.__server_prefix: str | None = SERVER_URLS.get(server)
        self.__timeout: int = timeout


    def fetch_gold(self, count: int = 3) -> Optional[List[dict[str, Any]]]:
        try:
            response: Response = get(f"https://{self.__server_prefix}.albion-online-data.com/api/v2/stats/gold?count={count}",
                                     timeout=self.__timeout)
            if not response.ok: return None
            return response.json()
        except ReadTimeout:
            return None

    def fetch_price(self, item_name: str, qualities: int = 1, cities: List[str] = []) -> Optional[List[dict[str, Any]]]:
        try:
            if cities:
                response: Response = get(f"https://{self.__server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}&locations={",".join(cities)}",
                                         timeout=self.__timeout)
            else:
                response: Response = get(f"https://{self.__server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}",
                                         timeout=self.__timeout)
            if not response.ok: return None
            return response.json()
        except ReadTimeout:
            return None

    @staticmethod
    def exists(item_name: str) -> bool:
        if item_name[-2:] in ("@1", "@2", "@3", "@4"):
            item_name = item_name[:-2]
        conn: Connection = connect("res/items.db")
        curs: Cursor = conn.cursor()
        curs.execute("SELECT * FROM items WHERE name = ?", (item_name, ))
        res: Tuple = curs.fetchone()
        conn.commit()
        conn.close()
        return True if res != None else False

    @staticmethod
    def is_craftable(item_name: str) -> bool:
        conn: Connection = connect("res/items.db")
        curs: Cursor = conn.cursor()
        curs.execute("SELECT * FROM items WHERE name = ?", (item_name, ))
        item: Tuple = curs.fetchone()
        conn.commit()
        conn.close()

        return all([item[4] != None, item[2] != "artefacts"])

    @staticmethod
    def is_enchanted(item_name: str) -> bool:
        return item_name[-2:] in ENCHANTMENTS


class SBIRenderFetcher:
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


def parse_cities(cities: str) -> List[str]:
    cities = cities.strip()
    opened_quote = False
    res: List[str] = []
    word: str = ""

    i = 0
    while i < len(cities):
        if cities[i] == '"':
            opened_quote = not opened_quote
        elif cities[i] == " ":
            if not opened_quote:
                res.append(word)
                word = ""
            else:
                word += cities[i]
        else:
            word += cities[i]
        i += 1
    res.append(word)

    return res


def is_valid_city(city: str) -> bool:
    return city.lower() in CITIES

def are_valid_cities(cities: List[str]) -> bool:
    for city in cities:
        if not is_valid_city(city):
            return False

    return True
