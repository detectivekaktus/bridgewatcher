#!/usr/bin/env python3
from sys import argv
from os import path
from typing import List, cast
from src import DEBUG_TOKEN, DISCORD_TOKEN
from src.client import bot, DATABASE


def usage() -> None:
    print("Usage: ./bot.py [run | database] [--populate | --upgrade]   ")
    print("  run:      run the bot                                     ")
    print("    Use --debug to run the debug version of the bot, instead")
    print("    of running the main application.                        ")
    print("  database: access the bot's items database                 ")
    print("    --populate: insert data into database if doesn't exist  ")
    print("    --upgrade:  update the data in the database             ")
    print("    --destroy:  delete the entire bot's database            ")
    print("    Use --entire to delete the database file from the disk. ")


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
            else:
                if cliargs[i + 1] == "--debug":
                    i += 1
                    if len(cliargs) - 1 != i:
                        crash("ERROR: Got too many arguments for the run subcommand.")

                    if not DEBUG_TOKEN:
                        crash("ERROR: Your configuration is missing DEBUG_TOKEN environment variable.")

                    bot.run(cast(str, DEBUG_TOKEN))
                else:
                    crash(f"ERROR: unexpected flag {cliargs[i + 1]} specified for the run subcommand.")
        case "database":
            i += 1
            if len(cliargs) == i:
                crash("ERROR: no flag specified for the database subcommand.")

            if cliargs[i] == "--populate":
                DATABASE.create_items_table()
                DATABASE.populate_table()
                exit(0)
            elif cliargs[i] == "--upgrade":
                DATABASE.upgrade_database()
                exit(0)
            elif cliargs[i] == "--destroy":
                i += 1
                if len(cliargs) == i:
                    DATABASE.destroy(True)
                elif cliargs[i] == "--entire":
                    DATABASE.destroy()
                else:
                    crash(f"ERROR: Unexpected flag {cliargs[i]} in sequence of `database` and `destroy` commands.")
                exit(0)
            else:
                crash(f"ERROR: unknown flag {cliargs[i]} for the database subcommand.")
        case _:
            crash(f"ERROR: unknown subcommand {cliargs[i]}.")


if __name__ == "__main__":
    main()
