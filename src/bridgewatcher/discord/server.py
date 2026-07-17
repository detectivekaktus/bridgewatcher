from discord import Guild

from bridgewatcher.api import AlbionOnline, AlbionOnlineServers
from bridgewatcher.db import db
from bridgewatcher.db.schema import DiscordServer


class ServerManager:
    @classmethod
    async def get_albion(cls, guild: Guild) -> AlbionOnline:
        conf = await cls.get_or_create_conf(guild)
        server = AlbionOnlineServers.from_str(conf.fetch_server)
        return AlbionOnline(server)

    @classmethod
    async def create_conf(cls, guild: Guild) -> DiscordServer:
        server = DiscordServer(guild.id, AlbionOnlineServers.AMERICA.value)
        servers = db.get_collection("discord_servers")
        await servers.insert_one(server.to_mongo())
        return server

    @classmethod
    async def get_or_create_conf(cls, guild: Guild) -> DiscordServer:
        servers = db.get_collection("discord_servers")
        server = await servers.find_one({"id": guild.id})
        if server is not None:
            return DiscordServer.from_mongo(server)

        return await cls.create_conf(guild)

    @classmethod
    async def get_or_update_conf(
        cls, guild: Guild, fetch_server: AlbionOnlineServers
    ) -> DiscordServer:
        server = await cls.get_or_create_conf(guild)
        server.fetch_server = fetch_server.value
        servers = db.get_collection("discord_servers")
        await servers.update_one(
            filter={"id": guild.id},
            update={"$set": {"fetch_server": server.fetch_server}},
        )
        return server

    @classmethod
    async def delete_conf(cls, guild: Guild) -> None:
        servers = db.get_collection("discord_servers")
        await servers.delete_one({"id": guild.id})
