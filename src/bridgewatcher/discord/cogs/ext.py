from datetime import datetime, timezone

from discord.app_commands import command
from discord.ext.commands import Bot, Cog
from discord import Interaction


class Ext(Cog):
    def __init__(self) -> None:
        super().__init__()

    @command(name="utc", description="Shows current UTC time")
    async def show_utc(self, interaction: Interaction) -> None:
        now = datetime.now(timezone.utc)
        await interaction.response.send_message(
            f"Currently it's {now.hour}:{now.minute} in Albion Online"
        )


async def setup(bot: Bot) -> None:
    await bot.add_cog(Ext())
