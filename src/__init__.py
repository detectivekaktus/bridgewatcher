#!/usr/bin/env python3
from os import getenv
from typing import Final
from dotenv import load_dotenv


def map_readable_item_names() -> dict[str, str]:
    with open("res/items.txt", "r") as items:
        lines = items.readlines()

    map: dict[str, str] = {}
    for line in lines:
        item = line.split()
        if (name := " ".join(item[3:]).lower()) in map.keys():
            map[f"{name} {item[1][-1]}"] = item[1]
        else:
            map[" ".join(item[3:]).lower()] = item[1]

    return map


load_dotenv()
DISCORD_TOKEN: str | None = getenv("DISCORD_TOKEN")
DEBUG_TOKEN: str | None = getenv("DEBUG_TOKEN")
ITEM_NAMES: Final[dict[str, str]] = map_readable_item_names()
