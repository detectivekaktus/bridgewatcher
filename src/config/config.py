#!/usr/bin/env pytnon3
from json import load
from os import makedirs, path
from typing import Any
from discord import Guild


def create_server_config(guild: Guild) -> None:
    if not guild: return
    if not path.exists("servers/"):
        makedirs("servers/")
    write_config(guild, 1)


def get_server_config(guild: Guild) -> dict[str, Any]:
    if not has_config(guild):
        create_server_config(guild)

    with open(f"servers/{guild.id}.json", "r") as fconf:
        cfg = load(fconf)
    return cfg


def update_server_config(guild: Guild, fetch_server: int) -> None:
    if not guild: return
    if not has_config(guild):
        create_server_config(guild)
        return
    write_config(guild, fetch_server)


def write_config(guild: Guild, fetch_server: int) -> None:
    with open(f"servers/{guild.id}.json", "w") as config:
        config.write("{\n")
        config.write(f"  \"name\": \"{guild.name}\",\n")
        config.write(f"  \"owner_id\": {guild.owner_id},\n")
        config.write(f"  \"fetch_server\": {fetch_server}\n")
        config.write("}\n")


def has_config(guild: Guild) -> bool:
    if not guild: return False
    if not path.exists(f"servers/{guild.id}.json") or not path.exists("servers/"): return False
    return True
