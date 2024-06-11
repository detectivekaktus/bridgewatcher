#!/usr/bin/env python3
from os import path, remove
from sqlite3 import Connection, Cursor, connect
from json import dumps, load
from typing import Optional, Tuple


class DatabaseManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path


    def create_items_table(self) -> None:
        conn: Connection = connect(self.db_path)
        curs: Cursor = conn.cursor()
        curs.execute("CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY, name TEXT, shop_category TEXT, shop_subcategory TEXT, crafting_requirements TEXT)")
        conn.commit()
        conn.close()

    def populate_table(self) -> None:
        with open("res/items.json", "r") as f:
            items = load(f)
        categories = ("hideoutitem", "trackingitem", "farmableitem", "simpleitem", "consumableitem", "consumablefrominventoryitem", "equipmentitem", "weapon", "mount", "furnitureitem", "mountskin", "journalitem", "labourercontract", "transformationweapon", "crystalleagueitem", "siegebanner", "killtrophy")

        conn: Connection = connect(self.db_path)
        curs: Cursor = conn.cursor()
        items_added = 0

        for category in categories:
            for item in items["items"][category]:
                if not isinstance(item, dict): continue
                curs.execute("INSERT INTO items (name, shop_category, shop_subcategory, crafting_requirements) VALUES (?, ?, ?, ?)",
                             (item["@uniquename"],
                              item["@shopcategory"] if "@shopcategory" in item else None,
                              item["@shopsubcategory1"] if "@shopsubcategory1" in item else None,
                              dumps(item["craftingrequirements"]) if "craftingrequirements" in item else None
))
                conn.commit()
                items_added += 1

                print(f"Added {item["@uniquename"]} into the database. Items added: {items_added}")

        conn.close()
        print("Finished adding items...")

    def upgrade_database(self) -> None:
        if not path.exists(self.db_path):
            print("ERROR: can't upgrade non existing database.")
            exit(1)

        conn: Connection = connect(self.db_path)
        curs: Cursor = conn.cursor()
        curs.execute("DROP TABLE items")
        conn.commit()
        conn.close()

        self.create_items_table()
        self.populate_table()

    def destroy(self, keep_file: bool = False) -> None:
        if not keep_file:
            remove(self.db_path)
        else:
            conn: Connection = connect(self.db_path)
            curs: Cursor = conn.cursor()
            curs.execute("DROP TABLE items")
            conn.commit()
            conn.close()


    @staticmethod
    def get_item(item_name: str) -> Optional[Tuple]:
        conn: Connection = connect("res/items.db")
        curs: Cursor = conn.cursor()
        curs.execute("SELECT * FROM items WHERE name = ?", (item_name, ))
        item: Optional[Tuple] = curs.fetchone()
        conn.commit()
        conn.close()

        return item
