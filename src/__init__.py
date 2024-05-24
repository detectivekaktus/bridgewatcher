#!/usr/bin/env python3
from enum import Enum
import os
from typing import Final
from dotenv import load_dotenv

ERROR:   Final = 0xff1231
GOLD:    Final = 0xf5d62a
PRICE:   Final = 0x2465ff
SUCCESS: Final = 0x66f542

class Server(Enum):
    AMERICA = 1
    EUROPE  = 2
    ASIA    = 3

load_dotenv()
DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
