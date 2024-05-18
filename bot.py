#!/usr/bin/env python3
from src import DISCORD_TOKEN
from src.client import bot

def main() -> int:
    if not DISCORD_TOKEN:
        raise KeyError("Your configuration is missing DISCORD_TOKEN environment variable.")

    bot.run(DISCORD_TOKEN)
    return 0


if __name__ == "__main__":
    exit(main())
