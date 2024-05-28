#!/usr/bin/env python3
from sys import argv
from typing import List
from src import DISCORD_TOKEN
from src.client import bot
import src.commands


def usage() -> None:
    print("Usage: ./bot.py [run | database] [--populate | --upgrade] ")
    print("  run:      run the bot                                   ")
    print("  database: access the bot's items database               ")
    print("    --populate: insert data into database if doesn't exist")
    print("    --upgrade:  update the data in the database           ")


def crash(msg: str) -> None:
    print(msg)
    usage()
    exit(1)


def main() -> None:
    if not DISCORD_TOKEN:
        raise KeyError("Your configuration is missing DISCORD_TOKEN environment variable.")

    if len(argv) < 2:
        crash("ERROR: no subcommand specified.")

    cliargs: List[str] = argv[1:]
    i = 0
    match cliargs[i]:
        case "run":
            if len(cliargs) - 1 == i:
                bot.run(DISCORD_TOKEN)
                exit(0)
            else:
                crash(f"ERROR: unknown flag {cliargs[i + 1]} specified for the run subcommand.")
        case "database":
            i += 1
            if i == len(cliargs):
                crash("ERROR: no flag specified for the database subcommand.")

            if cliargs[i] == "--populate":
                raise NotImplementedError()
            elif cliargs[i] == "--upgrade":
                raise NotImplementedError()
            else:
                crash(f"ERROR: unknown parameter {cliargs[i]} for the database subcommand.")
        case _:
            crash(f"ERROR: unknown subcommand {cliargs[i]}.")


if __name__ == "__main__":
    main()
