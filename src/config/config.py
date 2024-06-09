#!/usr/bin/env pytnon3
from os import makedirs, path
from sqlite3 import Connection, Cursor, connect
from typing import Any, Tuple
from discord import Guild


def create_server_config(guild: Guild) -> None:
    if not path.exists("servers/"):
        makedirs("servers/")

    conn: Connection = connect("servers/servers.db")
    curs: Cursor = conn.cursor()
    curs.execute("CREATE TABLE IF NOT EXISTS servers(name TEXT, id INTEGER PRIMARY KEY, owner_id INTEGER, fetch_server INTEGER)")
    conn.commit()
    conn.close()

    write_config(guild, 1)


def get_server_config(guild: Guild) -> dict[str, Any]:
    if not has_config(guild):
        create_server_config(guild)

    conn: Connection = connect("servers/servers.db")
    curs: Cursor = conn.cursor()
    curs.execute("SELECT * FROM servers WHERE id = ?", (guild.id, ))
    res: Tuple = curs.fetchone()
    conn.commit()
    conn.close()

    return {
        "name": res[0],
        "id": res[1],
        "owner_id": res[2],
        "fetch_server": res[3]
    }


def update_server_config(guild: Guild, fetch_server: int) -> None:
    if not has_config(guild):
        create_server_config(guild)
        return
    write_config(guild, fetch_server)


def write_config(guild: Guild, fetch_server: int) -> None:
    conn: Connection = connect("servers/servers.db")
    curs: Cursor = conn.cursor()
    curs.execute("INSERT OR REPLACE INTO servers (name, id, owner_id, fetch_server) VALUES (?, ?, ?, ?)",
                 (guild.name, guild.id, guild.owner_id, fetch_server))
    conn.commit()
    conn.close()

def has_config(guild: Guild) -> bool:
    if not path.exists(f"servers/"):
        return False

    conn: Connection = connect("servers/servers.db")
    curs: Cursor = conn.cursor()
    curs.execute("SELECT * FROM servers WHERE id = ?", (guild.id, ))
    res: Tuple = curs.fetchone()
    conn.commit()
    conn.close()

    if not res:
        return False

    return True
