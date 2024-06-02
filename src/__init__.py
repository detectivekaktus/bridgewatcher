#!/usr/bin/env python3
from os import getenv
from typing import Final
from dotenv import load_dotenv


ERROR:   Final = 0xff1231
GOLD:    Final = 0xf5d62a
PRICE:   Final = 0x2465ff
SUCCESS: Final = 0x66f542

AMERICA: Final = 1
EUROPE:  Final = 2
ASIA:    Final = 3


load_dotenv()
DISCORD_TOKEN: str | None = getenv("DISCORD_TOKEN")
