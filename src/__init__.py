#!/usr/bin/env python3
from os import getenv
from typing import Callable, Final, Tuple, Type
from dotenv import load_dotenv


CITIES: Final[Tuple[str, ...]]                       = ("black market", "brecilien", "bridgewatch", "caerleon", "fort sterling", "lymhurst", "martlock", "thetford")
QUALITIES:     Final[Tuple[str, ...]]                = ("Normal", "Good", "Outstanding", "Excellent", "Masterpiece")
ENCHANTMENTS: Final[Tuple[str, ...]]                 = ("@1", "@2", "@3", "@4")
NON_CRAFTABLE: Final[Tuple[str, ...]]                = ("artefacts", "mounts", "labourers")
NON_SELLABLE_ON_BLACK_MARKET: Final[Tuple[str, ...]] = ("artefacts", "mounts", "consumables", "food", "labourers", "resources")

DEFAULT_RATE: Final[int] = 15
BONUS_RATE: Final[int]   = 28
CRAFTING_BONUSES: Final[dict[str, Tuple]] = {
    "brecilien":     ("cape", "bag", "potion"),
    "bridgewatch":   ("rock", "crossbow", "dagger", "cursestaff", "plate_armor", "cloth_shoes"),
    "fort sterling": ("planks", "hammer", "spear", "holystaff", "plate_helmet", "cloth_armor"),
    "caerleon":      ("gatherergear", "tools", "knuckles", "shapeshifterstaff"),
    "lymhurst":      ("cloth", "sword", "bow", "arcanestaff", "leather_helmet", "leather_shoes"),
    "martlock":      ("leather", "axe", "quarterstaff", "froststaff", "plate_shoes", "offhand"),
    "thetford":      ("metalbar", "mace", "naturestaff", "firestaff", "leather_armor", "cloth_helmet")
}


def overrides(interface_class: Type) -> Callable:
    def overrider(method: Callable) -> Callable:
        assert method.__name__ in dir(interface_class), f"{method.__name__} does not override any method in {interface_class.__name__}"
        return method
    return overrider


load_dotenv()
DISCORD_TOKEN: str | None = getenv("DISCORD_TOKEN")
DEBUG_TOKEN: str | None = getenv("DEBUG_TOKEN")
