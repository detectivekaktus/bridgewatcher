from discord import Color, Guild, Interaction
from discord.app_commands import Choice, check, choices, command, describe, guild_only
from discord.ext.commands import Bot, Cog

from bridgewatcher.api.model import Qualities
from bridgewatcher.discord.embed import BridgewatcherEmbed
from bridgewatcher.discord.formatting import md
from bridgewatcher.discord.server import ServerManager
from bridgewatcher.discord.items.decorators import guard_item_errors
from bridgewatcher.discord.formatting import format_number, readable_timestamp
from bridgewatcher.discord.items import ItemGuesser, get_item_icon
from bridgewatcher.market import MarketFlipper, MarketQuery


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
            f"{readable_timestamp(price.timestamp)}: {md.bold(format_number(price.price))} silver"
            for price in prices
        ]
        embed = await BridgewatcherEmbed.from_interaction(
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
            f"Last time updated: {readable_timestamp(current_price.timestamp)}",
        ]
        embed = await BridgewatcherEmbed.from_interaction(
            interaction,
            title="Premium prices",
            color=Color.dark_red(),
            description="\n".join(entries),
        )

        await interaction.response.send_message(embed=embed)

    @command(name="flip", description="Calculate the profit from flipping an item")
    @describe(
        item_name="Name of the item you want to flip",
        quality="Quality of the item you want to flip",
        has_premium="Your premium subscription status",
    )
    @choices(
        quality=[
            Choice(name=quality.name.lower(), value=quality.value)
            for quality in Qualities
        ]
    )
    @guild_only()
    @check(lambda ctx: ctx.guild is not None)
    @guard_item_errors
    async def flip_item(
        self,
        interaction: Interaction,
        item_name: str,
        quality: Choice[int],
        has_premium: bool,
    ) -> None:
        item, name = await ItemGuesser.guess_item_by_name(interaction, item_name)

        guild: Guild = interaction.guild  # type: ignore
        albion = await ServerManager.get_albion(guild)
        flipper = MarketFlipper(albion)
        flip = await flipper.flip(
            MarketQuery.with_black_market_included(
                item, Qualities.from_int(quality.value)
            ),
            has_premium,
        )

        embed = await BridgewatcherEmbed.from_interaction(
            interaction,
            title=f"📦 Flipping {name.name}",
            color=Color.orange(),
            description=(
                f"The expected profit from flipping {name.name} of {md.bold(flip.quality.name.lower())} "
                f"quality from {md.bold(flip.buy_city.capitalize())} to {md.bold(flip.sell_city.capitalize())} "
                f"is {md.bold(format_number(flip.profit))} silver, given by:\n"
                f"* +{format_number(flip.sell_price)} sell price\n"
                f"* -{format_number(flip.buy_price)} buy price\n"
                f"* -{format_number(flip.taxes)} sale tax\n"
                f"* -{format_number(flip.fees)} buying and selling order fees"
            ),
        )
        embed.add_field(name="🌆Buy city", value=md.bold(flip.buy_city.capitalize()))
        embed.add_field(
            name="💲Buy price", value=md.bold(format_number(flip.buy_price))
        )
        embed.add_field(name="🏙️Sell city", value=md.bold(flip.sell_city.capitalize()))
        embed.add_field(
            name="💲Sell price", value=md.bold(format_number(flip.sell_price))
        )
        embed.set_thumbnail(url=get_item_icon(name.id, flip.quality))

        await interaction.followup.send(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(MarketCog())
