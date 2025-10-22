#!/usr/bin/env python3
import os
import sqlite3
from src.db import Database


def main() -> None:
  assert os.getenv("MODE") == "CONTAINER", "Cannot seed database outside a container."

  items_db = Database("/data/items.db")
  try:
    with items_db as db:
      db.execute("SELECT * FROM items LIMIT 1")
    print("Database already exists. Skipping seeding...")
  except sqlite3.OperationalError:
    print("No database found. Seeding...")
    items_db.create_items_table()
    items_db.seed()


if __name__ == "__main__":
  main()