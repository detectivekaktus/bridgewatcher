#!/usr/bin/env python3
from datetime import datetime
from typing import Any, Final, List
from requests import ReadTimeout, Response, get
from . import Server


SERVER_URLS_PREFIX: Final = {
    Server.AMERICA: "west",
    Server.ASIA:    "east",
    Server.EUROPE:  "europe"
}


class AODFetcher:
    def __init__(self, server: Server, timeout: int = 5) -> None:
        self.__server_prefix: str | None = SERVER_URLS_PREFIX.get(server)
        self.__timeout: int = timeout


    def fetch_gold(self, count: int = 3) -> List[dict[str, Any]] | None:
        try:
            response: Response = get(f"https://{self.__server_prefix}.albion-online-data.com/api/v2/stats/gold?count={count}", timeout=self.__timeout)
            if not response.ok: return None
            return response.json()
        except ReadTimeout:
            return None

    def fetch_price(self, item_name: str, qualities: int = 1, cities: List[str] = []) -> List[dict[str, Any]] | None:
        try:
            if cities:
                response: Response = get(f"https://{self.__server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}&locations={",".join(cities)}", timeout=self.__timeout)
            else:
                response: Response = get(f"https://{self.__server_prefix}.albion-online-data.com/api/v2/stats/prices/{item_name}.json?qualities={qualities}", timeout=self.__timeout)
            if not response.ok: return None
            return response.json()
        except ReadTimeout:
            return None
    

class SBIRenderFetcher:
    def fetch_item(self, identifier: str, quality: int = 1) -> str:
        return f"https://render.albiononline.com/v1/item/{identifier}.png?quality={quality}"

    def fetch_spell(self, identifier: str) -> str:
        return f"https://render.albiononline.com/v1/spell/{identifier}.png"

    def fetch_wardrobe(self, identifier: str) -> str:
        return f"https://render.albiononline.com/v1/wardrobe/{identifier}.png" 


def get_percent_variation(data: List[dict], index: int) -> float:
    return round((data[index]["price"] / data[index + 1]["price"] - 1) * 100, 2)


def convert_api_timestamp(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").strftime("%d %B %Y, %H:%M:%S UTC")


def is_valid_city(city: str) -> bool:
    return city.lower() in ("black market", "brecilien", "bridgewatch", "caerleon", "fort sterling", "lymhurst", "martlock", "thetford")
