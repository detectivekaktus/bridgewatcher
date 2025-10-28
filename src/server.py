#!/usr/bin/env python3
from dataclasses import dataclass
from os import path
from sqlite3 import Cursor, connect
from typing import Optional
from discord import Guild
from src.utils.constants import AlbionServer


@dataclass
class ServerConfig:
    """Class for keeping individual server configuration"""
    name: str
    id: int
    owner_id: int
    fetch_server: AlbionServer


class ServerManager:
    def __init__(self, path: str) -> None:
        self._path = path
        self.create_table()

    def __enter__(self) -> Cursor:
        self.connection = connect(self._path)
        return self.connection.cursor()

    def __exit__(self, *args) -> None:
        self.connection.commit()
        self.connection.close()

    def create_table(self) -> None:
        with self as servers:
            servers.execute(
                "CREATE TABLE IF NOT EXISTS servers(name TEXT, id INTEGER PRIMARY KEY, owner_id INTEGER, fetch_server INTEGER)"
            )

    def create_config(self, guild: Guild) -> None:
        self.write_config(guild, 1)

    def update_config(self, guild: Guild, fetch_server: int) -> None:
        if not self.has_config(guild):
            self.create_config(guild)
            return

        self.write_config(guild, fetch_server)

    def write_config(self, guild: Guild, fetch_server: int) -> None:
        with self as servers:
            servers.execute(
                "INSERT OR REPLACE INTO servers (name, id, owner_id, fetch_server) VALUES (?, ?, ?, ?)",
                (guild.name, guild.id, guild.owner_id, fetch_server),
            )

    def get_config(self, guild: Guild) -> ServerConfig:
        if not self.has_config(guild):
            self.create_config(guild)

        with self as servers:
            servers.execute("SELECT * FROM servers WHERE id = ?", (guild.id,))
            res: tuple = servers.fetchone()

        config = ServerConfig(*res)
        return config

    def has_config(self, guild: Guild) -> bool:
        if not path.exists(self._path):
            return False

        with self as servers:
            servers.execute("SELECT * FROM servers WHERE id = ?", (guild.id,))
            server: Optional[tuple] = servers.fetchone()

        if not server:
            return False

        return True
