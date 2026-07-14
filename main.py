from os import getenv
from sys import stderr

from dotenv import load_dotenv

from bridgewatcher.discord import bot
from bridgewatcher.loggers import load_logging_config


def main() -> None:
    load_logging_config()
    load_dotenv()

    MAIN_TOKEN = getenv("DISCORD_TOKEN")
    DEBUG_TOKEN = getenv("DEBUG_TOKEN")
    debug = getenv("DEBUG", "false").lower() in ("true", "1")
    token = DEBUG_TOKEN if debug else MAIN_TOKEN
    if token is None:
        print(f"FATAL: Currently chosen token is null. {debug=!r}", file=stderr)
        exit(1)

    bot.run(token)


if __name__ == "__main__":
    main()
