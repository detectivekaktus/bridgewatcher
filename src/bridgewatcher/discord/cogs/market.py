from datetime import datetime, timezone

from discord import Color, Guild, Interaction
from discord.app_commands import Choice, check, choices, command, describe, guild_only
from discord.ext.commands import Bot, Cog

from bridgewatcher.api.model import Qualities
from bridgewatcher.discord.embed import BridgewatcherEmbed
from bridgewatcher.discord.formatting import md, format_number, readable_timestamp
from bridgewatcher.discord.formatting.text import get_datetime_from_timestamp
from bridgewatcher.discord.items import ItemGuesser, get_item_icon, guard_item_errors
from bridgewatcher.discord.server import ServerManager
from bridgewatcher.market import Crafter, MarketFlipper, MarketQuery


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

    @command(name="price", description="Get latest prices for an item")
    @describe(
        item_name="Name of item you want to get prices for",
        quality="Quality of the item",
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
    async def get_item_prices(
        self, interaction: Interaction, item_name: str, quality: Choice[int]
    ) -> None:
        item, name = await ItemGuesser.guess_item_by_name(interaction, item_name)

        guild: Guild = interaction.guild  # type: ignore
        albion = await ServerManager.get_albion(guild)
        prices = await albion.get_item_prices(item)
        filtered = [price for price in prices if price.quality == quality.value]

        entries = []
        for price in filtered:
            city_price = (
                f"{md.bold(format_number(price.sell_price_min))} silver"
                if price.sell_price_min != 0
                else "No data"
            )
            entry = f"{price.city.title()}: {city_price}"

            time = get_datetime_from_timestamp(price.sell_price_min_date)
            timediff = datetime.now(timezone.utc) - time
            if price.sell_price_min != 0 and timediff.seconds >= 60 * 60 * 2:
                entry += f" {md.italic("outdated")}"

            entries.append(entry)

        embed = await BridgewatcherEmbed.from_interaction(
            interaction,
            title=f"💵Prices for {name.name}",
            color=Color.green(),
            description="\n".join(entries),
        )
        embed.set_thumbnail(
            url=get_item_icon(item.name, Qualities.from_int(quality.value))
        )

        await interaction.followup.send(embed=embed)

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
                f"quality from {md.bold(flip.buy_city.title())} to {md.bold(flip.sell_city.title())} "
                f"is {md.bold(format_number(flip.profit))} silver, given by:\n"
                f"* +{format_number(flip.sell_price)} sell price\n"
                f"* -{format_number(flip.buy_price)} buy price\n"
                f"* -{format_number(flip.taxes)} sale tax\n"
                f"* -{format_number(flip.fees)} buying and selling order fees"
            ),
        )
        embed.set_thumbnail(url=get_item_icon(name.id, flip.quality))
        embed.add_field(name="🌆Buy city", value=md.bold(flip.buy_city.title()))
        embed.add_field(
            name="💲Buy price", value=md.bold(format_number(flip.buy_price))
        )
        embed.add_field(name="🏙️Sell city", value=md.bold(flip.sell_city.title()))
        embed.add_field(
            name="💲Sell price", value=md.bold(format_number(flip.sell_price))
        )

        await interaction.followup.send(embed=embed)

    @command(name="craft", description="Calculate the profit from crafting an item")
    @describe(
        item_name="Name of the item you want to craft",
        has_premium="Your premium subscription status",
        count="Number of items you want to craft",
        using_focus="Use of focus during crafting",
    )
    @guild_only()
    @check(lambda ctx: ctx.guild is not None)
    @guard_item_errors
    async def craft_item(
        self,
        interaction: Interaction,
        item_name: str,
        has_premium: bool,
        count: int = 1,
        using_focus: bool = True,
    ) -> None:
        item, name = await ItemGuesser.guess_item_by_name(interaction, item_name)

        guild: Guild = interaction.guild  # type: ignore
        albion = await ServerManager.get_albion(guild)
        crafter = Crafter(albion)
        craft = await crafter.craft(item, count, has_premium, using_focus)

        embed = await BridgewatcherEmbed.from_interaction(
            interaction,
            title=f"⚒️ Crafting {name.name}",
            color=Color.blurple(),
            description=(
                f"This is a brief summary of crafting {name.name} in {craft.crafting_city.title()} "
                f"with the sell destination in {md.bold(craft.income.sell_city.title())}. "
                f"Your profit is expected to be {format_number(craft.profit)} silver, given by:\n"
                f"* +{format_number(craft.income.income)} income\n"
                f"* -{format_number(craft.income.taxes)} taxes\n"
                f"* -{format_number(craft.total_fees)} fees\n"
                f"* -{format_number(craft.total_cost)} materials\n"
                f"* +{format_number(craft.leftovers_value)} leftovers"
            ),
        )
        embed.set_thumbnail(url=get_item_icon(name.id))
        embed.add_field(
            name="🔄Return rate", value=f"{md.bold(round(craft.return_rate * 100, 2))}%"
        )
        embed.add_field(
            name="🏭Crafting city", value=md.bold(craft.crafting_city.title())
        )
        embed.add_field(
            name="🏪Selling city", value=md.bold(craft.income.sell_city.title())
        )
        embed.add_field(name="📦Items crafted", value=md.bold(craft.count))
        embed.add_field(
            name="💲Taxes", value=md.bold(format_number(craft.income.taxes))
        )
        embed.add_field(name="💲Fees", value=md.bold(format_number(craft.total_fees)))
        embed.add_field(name="🔍Focus", value=md.bold("Yes" if using_focus else "No"))
        embed.add_field(name="👑Premium", value=md.bold("Yes" if has_premium else "No"))

        await interaction.followup.send(embed=embed)


async def setup(bot: Bot) -> None:
    await bot.add_cog(MarketCog())
