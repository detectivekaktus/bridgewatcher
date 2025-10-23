#!/usr/bin/env python3
from typing import Final


CITIES: Final[list[str]]  = ["black market", "brecilien", "bridgewatch", "caerleon", "fort sterling", "lymhurst", "martlock", "thetford"]

QUALITIES:     Final[tuple[str, ...]]                = ("Normal", "Good", "Outstanding", "Excellent", "Masterpiece")
ENCHANTMENTS: Final[tuple[str, ...]]                 = ("@1", "@2", "@3", "@4")


NON_CRAFTABLE: Final[tuple[str, ...]]                = ("artefacts", "mounts", "labourers")
NON_SELLABLE_ON_BLACK_MARKET: Final[tuple[str, ...]] = ("artefacts", "mounts", "consumables", "food", "labourers", "resources")


DEFAULT_RATE: Final[int] = 15
BONUS_RATE: Final[int]   = 28


CRAFTING_BONUSES: Final[dict[str, tuple]] = {
    "brecilien":     ("capes", "bags", "potions"),
    "bridgewatch":   ("stoneblock", "crossbow", "dagger", "cursestaff", "plate_armor", "cloth_shoes"),
    "fort sterling": ("planks", "hammer", "spear", "holystaff", "plate_helmet", "cloth_armor"),
    "caerleon":      ("gatherergear", "tools", "knuckles", "shapeshifterstaff"),
    "lymhurst":      ("cloth", "sword", "bow", "arcanestaff", "leather_helmet", "leather_shoes"),
    "martlock":      ("leather", "axe", "quarterstaff", "froststaff", "plate_shoes", "offhand"),
    "thetford":      ("metalbar", "mace", "naturestaff", "firestaff", "leather_armor", "cloth_helmet")
}

