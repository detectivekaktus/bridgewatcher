#!/usr/bin/env python3
from dotenv import load_dotenv
from enum import Enum
import os

class Servers(Enum):
    AMERICA = 1
    EUROPE  = 2
    ASIA    = 3

load_dotenv()
DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
