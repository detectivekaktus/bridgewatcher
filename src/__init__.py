#!/usr/bin/env python3
from os import getenv
from typing import Final, Tuple
from dotenv import load_dotenv


ERROR_COLOR:    Final = 0xff1231
GOLD_COLOR:     Final = 0xf5d62a
PRICE_COLOR:    Final = 0x2465ff
CRAFTING_COLOR: Final = 0x32c9b8
SUCCESS_COLOR:  Final = 0x66f542

AMERICA: Final = 1
EUROPE:  Final = 2
ASIA:    Final = 3

CITIES: Final[Tuple[str, ...]] = ("black market", "brecilien", "bridgewatch", "caerleon", "fort sterling", "lymhurst", "thetford")

BONUS_RATE: Final = 28
CRAFTING_BONUSES: Final[dict[str, Tuple]] = {
    "brecilien":     ("cape", "bag", "potion"),
    "bridgewatch":   ("crossbow", "dagger", "cursestaff", "plate_armor", "cloth_shoes"),
    "fort sterling": ("hammer", "spear", "holystaff", "plate_helmet", "cloth_armor"),
    "caerleon":      ("gatherergear", "tools", "knuckles", "shapeshifterstaff"),
    "lymhurst":      ("sword", "bow", "arcanestaff", "leather_helmet", "leather_shoes"),
    "martlock":      ("axe", "quarterstaff", "froststaff", "plate_shoes", "offhand"),
    "thetford":      ("mace", "naturestaff", "firestaff", "leather_armor", "cloth_helmet")
}


load_dotenv()
DISCORD_TOKEN: str | None = getenv("DISCORD_TOKEN")
