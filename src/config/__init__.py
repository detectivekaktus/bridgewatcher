#!/usr/bin/env python3
from os import makedirs, path
from sqlite3 import Cursor, connect
from typing import Any, Optional, Tuple
from discord import Guild


class Servers:
    def __init__(self, path: str) -> None:
        self.path = path
        self.create_table()


    def __enter__(self) -> Cursor:
        self.connection = connect(self.path)
        return self.connection.cursor()


    def __exit__(self, *args) -> None:
        self.connection.commit()
        self.connection.close()


    def create_table(self) -> None:
        with self as servers:
            servers.execute("CREATE TABLE IF NOT EXISTS servers(name TEXT, id INTEGER PRIMARY KEY, owner_id INTEGER, fetch_server INTEGER)")


    def create_config(self, guild: Guild) -> None:
        if not path.exists("servers/"):
            makedirs("servers/")

        self.write_config(guild, 1)


    def update_config(self, guild: Guild, fetch_server: int) -> None:
        if not self.has_config(guild):
            self.create_config(guild)
            return
        
        self.write_config(guild, fetch_server)


    def write_config(self, guild: Guild, fetch_server: int) -> None:
        with self as servers:
            servers.execute("INSERT OR REPLACE INTO servers (name, id, owner_id, fetch_server) VALUES (?, ?, ?, ?)",
                 (guild.name, guild.id, guild.owner_id, fetch_server))


    def get_config(self, guild: Guild) -> dict[str, Any]:
        if not self.has_config(guild):
            self.create_config(guild)

        with self as servers:
            servers.execute("SELECT * FROM servers WHERE id = ?", (guild.id, ))
            res: Tuple = servers.fetchone()

        return {
            "name": res[0],
            "id": res[1],
            "owner_id": res[2],
            "fetch_server": res[3]
        }


    def has_config(self, guild: Guild) -> bool:
        if not path.exists("servers/servers.db"):
            return False

        with self as servers:
            servers.execute("SELECT * FROM servers WHERE id = ?", (guild.id, ))
            server: Optional[Tuple] = servers.fetchone()

        if not server:
            return False

        return True
