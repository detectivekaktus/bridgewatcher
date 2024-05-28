#!/usr/bin/env python3
from os import path
from sqlite3 import Connection, Cursor, connect
from json import load


class DatabaseManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path


    def create_items_table(self) -> None:
        conn: Connection = connect(self.db_path)
        curs: Cursor = conn.cursor()
        curs.execute("CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY, name TEXT, crafting_requirements TEXT)")
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
                curs.execute("INSERT INTO items (name, crafting_requirements) VALUES (?, ?)",
                             (item["@uniquename"], str(item["craftingrequirements"]) if "craftingrequirements" in item else None))
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
