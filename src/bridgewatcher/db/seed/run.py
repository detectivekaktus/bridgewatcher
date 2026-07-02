from asyncio import run
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps, loads
from typing import Any

from aiohttp import ClientSession

from bridgewatcher.db import db
from bridgewatcher.db.schema import Version, Item, CraftingRequirement, ItemName

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

    dump_items = {
        k: v for k, v in dump_items.items() if k not in NOT_INCLUDED_IN_DATABASE
    }

    items_collection = db.get_collection("items")
    await items_collection.drop()
    await items_collection.create_index("name")

    for category_items in dump_items.values():
        items = []
        for category_item in category_items:
            print(f"Attempting to insert {category_item["@uniquename"]}")

            requirements: list[CraftingRequirement] = []

            # for now let's ignore multiple recipes
            source_requirements = category_item.get("craftingrequirements")
            if isinstance(source_requirements, list):
                continue

            if (
                source_requirements is not None
                and source_requirements.get("craftresource") is not None
            ):
                resources = source_requirements["craftresource"]
                # dumb fuckers can't do an array with just one object,
                # so I have to make another nested check
                if isinstance(resources, list):
                    for requirement in resources:
                        requirement = CraftingRequirement(
                            requirement["@uniquename"], int(requirement["@count"])
                        )
                        requirements.append(requirement)
                else:
                    requirement = CraftingRequirement(
                        resources["@uniquename"], resources["@count"]
                    )
                    requirements.append(requirement)

            item = Item(
                category_item["@uniquename"],
                category_item["@shopcategory"],
                category_item["@shopsubcategory1"],
                requirements if requirements else None,
            )
            items.append(item.to_mongo())

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
    await names_collection.create_index("identifier")
    await names_collection.create_index("name")

    names = []
    lines = content.split("\n")
    for line in lines:
        items = line.split(":")
        if len(items) < 3:
            continue

        name = ItemName(items[1].strip(), items[2].strip())
        names.append(name.to_mongo())
    await names_collection.insert_many(names)


async def seed() -> None:
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
                print("Hashes match. No seeding will run")
                return
    else:
        print("Forced seeding detected")

    print("Seeding the database")
    await seed()
    await update_hash(current_hash)
    print("Seeding complete")


def seed_if_needed_sync(forced: bool = False) -> None:
    run(seed_if_needed(forced))


if __name__ == "__main__":
    seed_if_needed_sync(True)
