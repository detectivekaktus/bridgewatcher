from asyncio import run
from copy import copy
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps, loads
from typing import Any

from aiohttp import ClientSession
from pymongo.collation import Collation

from bridgewatcher.api.model import Cities
from bridgewatcher.db import db
from bridgewatcher.db.schema import Version, Item, CraftingRequirement, ItemName
from bridgewatcher.loggers import LOGGER

ITEMS_URL = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/refs/heads/master/items.json"
ITEM_NAMES_URL = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/refs/heads/master/formatted/items.txt"

NOT_INCLUDED_IN_DATABASE = (
    "@xmlns:xsi",
    "@xsi:noNamespaceSchemaLocation",
    "consumablefrominventoryitem",
    "crystalleagueitem",
    "hideoutitem",
    "journalitem",
    "killtrophy",
    "labourercontract",
    "mountskin",
    "rewardtoken",
    "shopcategories",
    "trashitem",
)

CAN_BE_ENCHANTED = (
    "weapons",
    "transformationweapon",
    "armors",
    "head",
    "shoes",
    # "crafting", for some reason the ao dump does include the enchanted versions of raw and refined materials
)

REFINED_RESOURCES = ("PLANKS", "METALBAR", "LEATHER", "CLOTH", "STONEBLOCK")
RAW_RESOURCES = ("WOOD", "ORE", "HIDE", "FIBER", "ROCK")

# https://wiki.albiononline.com/wiki/Local_Production_Bonus
CITIES_WITH_CRAFTING_BONUSES = {
    Cities.FORT_STERLING: [
        "hammer",
        "holystaff",
        "spear",
        "cloth_armor",
        "plate_helmet",
        "planks",
    ],
    Cities.LYMHURST: [
        "bow",
        "sword",
        "arcanestaff",
        "leather_helmet",
        "leather_shoes",
        "cloth",
    ],
    Cities.BRIDGEWATCH: [
        "crossbow",
        "dagger",
        "cursestaff",
        "plate_armor",
        "cloth_shoes",
        "stoneblock",
    ],
    Cities.MARTLOCK: [
        "axe",
        "quarterstaff",
        "froststaff",
        "plate_shoes",
        "torchtype",
        "shieldtype",
        "booktype",
    ],
    Cities.THETFORD: [
        "mace",
        "naturestaff",
        "firestaff",
        "leather_armor",
        "cloth_helmet",
        "metalbars",
        "leather",
    ],
    Cities.CAERLEON: [
        "ore",
        "fiber",
        "wood",
        "rock",
        "hide",
        "toolkit",
        "knuckles",
        "shapeshifterstaff",
    ],
    Cities.BRECILIEN: ["accessoires_capes_capes", "bags", "potions"],
}


def get_crafting_requirements(
    source_requirements: dict[Any, Any],
) -> list[CraftingRequirement]:
    if source_requirements is None or source_requirements.get("craftresource") is None:
        return []

    resources = source_requirements["craftresource"]
    # dumb fuckers can't do an array with just one object,
    # so I have to make another nested check
    if isinstance(resources, list):
        return [
            CraftingRequirement(requirement["@uniquename"], int(requirement["@count"]))
            for requirement in resources
        ]
    else:
        return [CraftingRequirement(resources["@uniquename"], int(resources["@count"]))]


def get_city_with_crafting_bonus(item: dict[Any, Any]) -> Cities | None:
    subcategory = item.get("@shopsubcategory1")
    subcategory_type = item.get("@shopsubcategory2")
    for city, bonuses in CITIES_WITH_CRAFTING_BONUSES.items():
        for bonus in bonuses:
            if subcategory == bonus or subcategory_type == bonus:
                return city

    return None


def get_enchanted_versions_of_item(item: Item) -> list[Item]:
    if (
        item.shop_category not in CAN_BE_ENCHANTED
        or item.crafting_requirements is None
        or "UNIQUE" in item.name
        or item.name[1] in ("1", "2", "3")  # unenchantable tiers
    ):
        return []

    enchanted_items = []
    for enchantment in range(1, 5):
        enchanted_item_requirements = []
        for requirement in item.crafting_requirements:
            if (
                not any(resource in requirement.name for resource in REFINED_RESOURCES)
                or "ARTEFACT" in requirement.name
            ):
                enchanted_item_requirements.append(requirement)
                continue

            new_requirement = copy(requirement)
            new_requirement.name += f"_LEVEL{enchantment}"
            enchanted_item_requirements.append(new_requirement)

        enchanted_item = copy(item)
        enchanted_item.name = f"{item.name}@{enchantment}"
        enchanted_item.crafting_requirements = enchanted_item_requirements
        enchanted_items.append(enchanted_item)

    return enchanted_items


# It may be tricky to understand what this function is all about without seeing what
# the Albion Online dumps look like. Here's a simplified version of what it looks like:
# {
#   "items": {
#       "category": [
#           {
#               "@uniquename": "...",
#               "@shopcategory": "...",
#               "@shopsubcategory1": "...",
#               "craftingrequirements": {
#                   "craftresource": [
#                       {
#                           "@uniquename": "...",
#                           "@count": "999"
#                       }
#                   ]
#               }
#           }
#       ]
#   }
# }
#
# There's a lot of ambiguity with this schema, for example craftresource may be not an array
# but a map if there's only one craft resource. Or it can also be absent if there's no
# crafting requirements instead of having a null value
async def seed_items_collection() -> None:
    async with ClientSession() as session:
        async with session.get(ITEMS_URL) as res:
            if not res.ok:
                raise ValueError("Unsatisfied response gotten from items dump")
            dump_items: dict[str, Any] = loads(await res.text())["items"]

    items_collection = db.get_collection("items")
    await items_collection.drop()
    await items_collection.create_index("name")

    dump_items = {
        k: v for k, v in dump_items.items() if k not in NOT_INCLUDED_IN_DATABASE
    }
    for category_items in dump_items.values():
        items = []
        for category_item in category_items:
            # this is the most stupid shit ive ever done, messing up with the types
            # of the variable but hey, python allows me to write shitty code, why not
            # to get used to it ;)
            source_requirements = category_item.get("craftingrequirements")
            if isinstance(source_requirements, list):
                source_requirements = source_requirements[0]

            requirements = get_crafting_requirements(source_requirements)
            city_with_bonus = get_city_with_crafting_bonus(category_item)

            item = Item(
                category_item["@uniquename"],
                category_item["@shopcategory"],
                category_item["@shopsubcategory1"],
                category_item.get("@shopsubcategory2"),
                city_with_bonus,
                requirements if requirements else None,
            )
            items.append(item.to_mongo())

            enchanted_items = map(Item.to_mongo, get_enchanted_versions_of_item(item))
            items.extend(enchanted_items)

        await items_collection.insert_many(items)


# This file is formatted differently but easily understandable. Here's an example:
# 1: ITEM_UNIQUE_NAME                   : Item Readable Name
# 2: MUCH_LONGER_ITEM_UNIQUE_NAME       : Much Longer Item Readable Name
# 3: ITEM_WITH_MISSING_READABLE_NAME
async def seed_item_names_collection() -> None:
    async with ClientSession() as session:
        async with session.get(ITEM_NAMES_URL) as res:
            if not res.ok:
                raise ValueError("Unsatisfied response gotten from item names dump")
            content = await res.text()

    names_collection = db.get_collection("item_names")
    await names_collection.drop()

    names_collection = await db.create_collection(
        "item_names", collation=Collation(locale="en_US", strength=2)
    )
    await names_collection.create_index("id")
    await names_collection.create_index("name")

    names = []
    lines = content.split("\n")
    for line in lines:
        items = line.split(":")
        if len(items) < 3:
            continue

        id = items[1].strip()
        name = items[2].strip()
        # for some unknowngly stupid reason the naming for materials in items.txt
        # is different from items.json, so we have to convert it
        if any(
            enchantment in id
            for enchantment in ("LEVEL1", "LEVEL2", "LEVEL3", "LEVEL4")
        ):
            id = id[:-2]

        names.append(ItemName(id, name).to_mongo())
    await names_collection.insert_many(names)


async def add_needed_constraints() -> None:
    servers = db.get_collection("discord_servers")
    await servers.create_index("id", unique=True)


async def seed() -> None:
    await add_needed_constraints()
    await seed_items_collection()
    await seed_item_names_collection()


async def get_current_hash() -> str:
    async with ClientSession() as session:
        async with session.get(ITEMS_URL) as res:
            if not res.ok:
                raise ValueError("Unsatisfied response gotten from items dump")
            json = loads(await res.text())
            content = dumps(json, separators=(":", ","))
    return sha256(content.encode("utf-8")).hexdigest()


async def update_hash(hash: str) -> None:
    version_collection = db.get_collection("version")
    await version_collection.drop()

    version = Version(hash, datetime.now(timezone.utc))
    await version_collection.insert_one(version.to_mongo())


async def seed_if_needed(forced: bool = False) -> None:
    current_hash = await get_current_hash()

    if not forced:
        version_doc = await db.get_collection("version").find_one()
        if version_doc is not None:
            version = Version.from_mongo(version_doc)
            if version.hash == current_hash:
                LOGGER.info("Hashes match. No seeding will run")
                return
    else:
        LOGGER.info("Forced seeding detected")

    LOGGER.info("Seeding the database")
    await seed()
    await update_hash(current_hash)


def seed_if_needed_sync(forced: bool = False) -> None:
    run(seed_if_needed(forced))


if __name__ == "__main__":
    seed_if_needed_sync(True)
