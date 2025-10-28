#!/usr/bin/env python3
from enum import IntEnum, StrEnum
from typing import Final


class City(StrEnum):
    BLACK_MARKET = "black market"
    BRECILIEN = "brecilien"
    BRIDGEWATCH = "bridgewatch"
    CAERLEON = "caerleon"
    FORT_STERLING = "fort sterling"
    LYMHURST = "lymhurst"
    MARTLOCK = "martlock"
    THETFORD = "thetford"


class AlbionServer(IntEnum):
    WEST = 1
    EUROPE = 2
    EAST = 3


class Quality(StrEnum):
    NORMAL = "normal"
    GOOD = "good"
    OUTSTANDING = "outstanding"
    EXCELLENT = "excellent"
    MASTERPIECE = "masterpiece"


class Enchantment(StrEnum):
    LEVEL_1 = "@1"
    LEVEL_2 = "@2"
    LEVEL_3 = "@3"
    LEVEL_4 = "@4"


NON_CRAFTABLE: Final[tuple[str, ...]] = ("artefacts", "mounts", "labourers")
NON_SELLABLE_ON_BLACK_MARKET: Final[tuple[str, ...]] = (
    "artefacts",
    "mounts",
    "consumables",
    "food",
    "labourers",
    "resources",
)


DEFAULT_RATE: Final[int] = 15
BONUS_RATE: Final[int] = 28


CRAFTING_BONUSES: Final[dict[str, tuple]] = {
    "brecilien": ("capes", "bags", "potions"),
    "bridgewatch": (
        "stoneblock",
        "crossbow",
        "dagger",
        "cursestaff",
        "plate_armor",
        "cloth_shoes",
    ),
    "fort sterling": (
        "planks",
        "hammer",
        "spear",
        "holystaff",
        "plate_helmet",
        "cloth_armor",
    ),
    "caerleon": ("gatherergear", "tools", "knuckles", "shapeshifterstaff"),
    "lymhurst": (
        "cloth",
        "sword",
        "bow",
        "arcanestaff",
        "leather_helmet",
        "leather_shoes",
    ),
    "martlock": (
        "leather",
        "axe",
        "quarterstaff",
        "froststaff",
        "plate_shoes",
        "offhand",
    ),
    "thetford": (
        "metalbar",
        "mace",
        "naturestaff",
        "firestaff",
        "leather_armor",
        "cloth_helmet",
    ),
}
