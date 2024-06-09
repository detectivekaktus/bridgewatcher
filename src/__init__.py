#!/usr/bin/env python3
from os import getenv
from typing import Final, Tuple
from dotenv import load_dotenv


WHITE:          Final = 0xffffff
ERROR_COLOR:    Final = 0xff1231
GOLD_COLOR:     Final = 0xf5d62a
PRICE_COLOR:    Final = 0x2465ff
CRAFTING_COLOR: Final = 0x32c9b8
SUCCESS_COLOR:  Final = 0x66f542

CITIES: Final[Tuple[str, ...]]        = ("black market", "brecilien", "bridgewatch", "caerleon", "fort sterling", "lymhurst", "martlock", "thetford")
ENCHANTMENTS: Final[Tuple[str, ...]]  = ("@1", "@2", "@3", "@4")
NON_CRAFTABLE: Final[Tuple[str, ...]] = ("artefacts", "mounts")

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


load_dotenv()
DISCORD_TOKEN: str | None = getenv("DISCORD_TOKEN")
