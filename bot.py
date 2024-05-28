#!/usr/bin/env python3
from sys import argv
from os import path
from typing import List, cast
from src import DISCORD_TOKEN
from src.client import bot
from src.db.manager import DatabaseManager
import src.commands


def usage() -> None:
    print("Usage: ./bot.py [run | database] [--populate | --upgrade] ")
    print("  run:      run the bot                                   ")
    print("  database: access the bot's items database               ")
    print("    --populate: insert data into database if doesn't exist")
    print("    --upgrade:  update the data in the database           ")


def verify_configuration() -> None:
    if not DISCORD_TOKEN:
        print("ERROR: Your configuration is missing DISCORD_TOKEN environment variable.")
        exit(1)

    if not path.exists("res/items.db"):
        print("ERROR: Your configuration is missing items database.")
        print("Execute ./bot.py database --populate to create one.")
        exit(1)


def crash(msg: str) -> None:
    print(msg)
    usage()
    exit(1)


def main() -> None:
    if len(argv) < 2:
        crash("ERROR: no subcommand specified.")

    cliargs: List[str] = argv[1:]
    i = 0
    match cliargs[i]:
        case "run":
            verify_configuration()

            if len(cliargs) - 1 == i:
                bot.run(cast(str, DISCORD_TOKEN))
                exit(0)
            else:
                crash(f"ERROR: unknown flag {cliargs[i + 1]} specified for the run subcommand.")
        case "database":
            i += 1
            if i == len(cliargs):
                crash("ERROR: no flag specified for the database subcommand.")

            if cliargs[i] == "--populate":
                manager: DatabaseManager = DatabaseManager("res/items.db")
                manager.create_items_table()
                manager.populate_table()
                exit(0)
            elif cliargs[i] == "--upgrade":
                manager: DatabaseManager = DatabaseManager("res/items.db")
                manager.upgrade_database()
                exit(0)
            else:
                crash(f"ERROR: unknown parameter {cliargs[i]} for the database subcommand.")
        case _:
            crash(f"ERROR: unknown subcommand {cliargs[i]}.")


if __name__ == "__main__":
    main()
