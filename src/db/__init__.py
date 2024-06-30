#!/usr/bin/env python3
from os import path, remove
from sqlite3 import Cursor, connect
from json import dumps, load


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    def __enter__(self) -> Cursor:
        self.connection = connect(self.path)
        return self.connection.cursor()

    def __exit__(self, *args) -> None:
        self.connection.commit()
        self.connection.close()


    def create_items_table(self) -> None:
        with self as db:
            db.execute("CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY, name TEXT, shop_category TEXT, shop_subcategory TEXT, crafting_requirements TEXT)")


    def populate_table(self) -> None:
        with open("res/items.json", "r") as f:
            items = load(f)
        categories = ("hideoutitem", "trackingitem", "farmableitem", "simpleitem", "consumableitem", "consumablefrominventoryitem", "equipmentitem", "weapon", "mount", "furnitureitem", "mountskin", "journalitem", "labourercontract", "transformationweapon", "crystalleagueitem", "siegebanner", "killtrophy")

        items_added: int = 0

        for category in categories:
            for item in items["items"][category]:
                if not isinstance(item, dict): continue
                
                with self as db:
                    db.execute("INSERT INTO items (name, shop_category, shop_subcategory, crafting_requirements) VALUES (?, ?, ?, ?)",
                             (item["@uniquename"],
                              item["@shopcategory"] if "@shopcategory" in item else None,
                              item["@shopsubcategory1"] if "@shopsubcategory1" in item else None,
                              dumps(item["craftingrequirements"]) if "craftingrequirements" in item else None))
                items_added += 1
                print(f"Added {item["@uniquename"]} into the database. Items added: {items_added}")

        print("Finished adding items...")


    def upgrade_database(self) -> None:
        if not path.exists(self.path):
            print("ERROR: can't upgrade non existing database.")
            exit(1)

        with self as db:
            db.execute("DROP TABLE items")

        self.create_items_table()
        self.populate_table()


    def destroy(self, keep_file: bool = False) -> None:
        if not path.exists(self.path):
            print("ERROR: can't destroy non existing database.")
            exit(1)

        if not keep_file:
            remove(self.path)
