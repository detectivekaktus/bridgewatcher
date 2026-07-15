from discord import Color, Embed, Guild, Interaction
from discord.app_commands import check, command, guild_only
from discord.ext.commands import Bot, Cog

from bridgewatcher.discord.util import ServerManager, md
from bridgewatcher.discord.util.embed import BridgewatcherEmbed
from bridgewatcher.discord.util.text import format_number, readable_timestamp


class MarketCog(Cog):
    MONTHLY_PREMIUM = 3750
    QUARTER_PREMIUM = 10500
    SEMIANNUAL_PREMIUM = 19500
    ANNUAL_PREMIUM = 36000

    @command(name="gold", description="Shows gold prices up to 12 hours prior")
    @guild_only()
    @check(lambda ctx: ctx.guild is not None)
    async def show_gold_prices(self, interaction: Interaction) -> None:
        guild: Guild = interaction.guild  # type: ignore
        albion = await ServerManager.get_albion(guild)
        prices = await albion.get_gold_prices()

        entries = [
            f"{md.italic(readable_timestamp(price.timestamp))} - {md.bold(format_number(price.price))}"
            for price in prices
        ]
        embed = BridgewatcherEmbed(
            interaction,
            title="Gold prices",
            color=Color.gold(),
            description="\n".join(entries),
        )

        await interaction.response.send_message(embed=embed)

    @command(name="premium", description="Shows current premium prices")
    @guild_only()
    @check(lambda ctx: ctx.guild is not None)
    async def show_premium_prices(self, interaction: Interaction) -> None:
        guild: Guild = interaction.guild  # type: ignore
        albion = await ServerManager.get_albion(guild)
        prices = await albion.get_gold_prices()
        current_price = prices[0]

        entries = [
            f"{md.bold("1 month")}: {format_number(current_price.price * self.MONTHLY_PREMIUM)} silver",
            f"{md.bold("3 months")}: {format_number(current_price.price * self.QUARTER_PREMIUM)} silver",
            f"{md.bold("6 months")}: {format_number(current_price.price * self.SEMIANNUAL_PREMIUM)} silver",
            f"{md.bold("12 months")}: {format_number(current_price.price * self.ANNUAL_PREMIUM)} silver",
        ]
        embed = BridgewatcherEmbed(
            interaction,
            title="Premium prices",
            color=Color.dark_red(),
            description="\n".join(entries),
        )
        embed.set_footer(
            text=f"Last time updated: {readable_timestamp(current_price.timestamp)}"
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(MarketCog())
