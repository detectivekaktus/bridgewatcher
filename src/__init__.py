#!/usr/bin/env python3
from dotenv import load_dotenv
from typing import Final
import os

ERROR:   Final   = 0xff1231
GOLD:    Final   = 0xf5d62a
SUCCESS: Final   = 0x66f542

load_dotenv()
DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
