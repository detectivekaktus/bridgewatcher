#!/usr/bin/env python3
from os import getenv
from typing import Final
from dotenv import load_dotenv


ERROR_COLOR:   Final = 0xff1231
GOLD_COLOR:    Final = 0xf5d62a
PRICE_COLOR:   Final = 0x2465ff
SUCCESS_COLOR: Final = 0x66f542

AMERICA: Final = 1
EUROPE:  Final = 2
ASIA:    Final = 3


load_dotenv()
DISCORD_TOKEN: str | None = getenv("DISCORD_TOKEN")
