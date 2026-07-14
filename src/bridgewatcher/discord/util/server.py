from discord import Guild

from bridgewatcher.api import AlbionOnlineServers
from bridgewatcher.db import db
from bridgewatcher.db.schema import DiscordServer


class ServerManager:
    @staticmethod
    async def create_conf(guild: Guild) -> DiscordServer:
        server = DiscordServer(guild.id, AlbionOnlineServers.AMERICA.value)
        servers = db.get_collection("discord_servers")
        await servers.insert_one(server.to_mongo())
        return server

    @staticmethod
    async def get_or_create_conf(guild: Guild) -> DiscordServer:
        servers = db.get_collection("discord_servers")
        server = await servers.find_one({"id": guild.id})
        if server is not None:
            return DiscordServer.from_mongo(server)

        return await ServerManager.create_conf(guild)

    @staticmethod
    async def get_or_update_conf(
        guild: Guild, fetch_server: AlbionOnlineServers
    ) -> DiscordServer:
        server = await ServerManager.get_or_create_conf(guild)
        server.fetch_server = fetch_server
        servers = db.get_collection("discord_servers")
        await servers.update_one(
            filter={"id": guild.id},
            update={"$set": {"fetch_server": server.fetch_server}},
        )
        return server

    @staticmethod
    async def delete_conf(guild: Guild) -> None:
        servers = db.get_collection("discord_servers")
        await servers.delete_one({"id": guild.id})
