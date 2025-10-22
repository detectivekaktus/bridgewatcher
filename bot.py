#!/usr/bin/env python3
from sys import argv
from src import DEBUG_TOKEN, DISCORD_TOKEN
from src.client import bot
from src.utils.logging import LOGGER


def main() -> None:
  if "--debug" in argv:
    if not DEBUG_TOKEN:
      print("ERROR: Your configuration is missing DEBUG_TOKEN environment variable.")
      exit(1)

    LOGGER.info("Debug version is starting up.")
    bot.run(DEBUG_TOKEN)
  elif len(argv) == 1:
    if not DISCORD_TOKEN:
      print("ERROR: Your configuration is missing DISCORD_TOKEN environment variable.")
      exit(1)

    LOGGER.info("Production version is starting up.")
    bot.run(DISCORD_TOKEN)
  else:
    print("ERROR: Unknown flags specified. For debugging the application use --debug flag.")
    exit(1)


if __name__ == "__main__":
    main()
