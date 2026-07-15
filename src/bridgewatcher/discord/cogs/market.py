from re import IGNORECASE, compile

from discord import Color, Guild, Interaction
from discord.app_commands import check, command, describe, guild_only
from discord.ext.commands import Bot, Cog

from bridgewatcher.db import db
from bridgewatcher.db.schema import Item, ItemName
from bridgewatcher.discord.embed import (
    BridgewatcherEmbed,
    NoItemFoundEmbed,
    TimeoutEmbed,
    UntrackedItemEmbed,
)
from bridgewatcher.discord.util import ServerManager, md
from bridgewatcher.discord.util.text import format_number, readable_timestamp
from bridgewatcher.discord.views import ItemPickerView
from bridgewatcher.util.exc import NoItemFoundError, UntrackedItemRequested


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

    async def _get_item_by_id_from_list(
        self, item_names: list[dict], index: int
    ) -> Item:
        items = db.get_collection("items")

        item_name = ItemName.from_mongo(item_names[index])
        item = await items.find_one({"name": item_name.id})
        # interestingly enough this result may be null cause not all
        # items are stored in the db. if it's not stored it's unimportant
        if item is None:
            raise UntrackedItemRequested(
                f"{item_name.name} is not stored in the database"
            )
        return Item.from_mongo(item)

    async def _guess_item_by_name(self, interaction: Interaction, name: str) -> Item:
        names = db.get_collection("item_names")
        regex = compile(f"^.*{name}.*$", IGNORECASE)
        results = await names.find({"name": regex}, limit=5).to_list()

        if not results:
            raise NoItemFoundError(f"{name} doesn't exist")
        elif len(results) == 1:
            return await self._get_item_by_id_from_list(results, 0)

        names = [ItemName.from_mongo(result) for result in results]
        view = ItemPickerView(names)
        await interaction.response.send_message(
            "Found multiple items matching the query...", view=view, ephemeral=True
        )

        timed_out = await view.wait()
        if timed_out:
            raise TimeoutError("User didn't select an item")
        index: int = view.selected_index  # type: ignore
        return await self._get_item_by_id_from_list(results, index)

    @command(name="flip", description="Calculate the profit from flipping an item")
    @describe(
        item_name="Name of the item you want to flip",
        has_premium="Your premium subscription status",
    )
    @guild_only()
    @check(lambda ctx: ctx.guild is not None)
    async def flip_item(
        self, interaction: Interaction, item_name: str, has_premium: bool
    ) -> None:
        try:
            item = await self._guess_item_by_name(interaction, item_name)
        except NoItemFoundError:
            await interaction.followup.send(
                embed=NoItemFoundEmbed(item_name), ephemeral=True
            )
            return
        except UntrackedItemRequested:
            await interaction.followup.send(
                embed=UntrackedItemEmbed(item_name), ephemeral=True
            )
            return
        except TimeoutError:
            await interaction.followup.send(embed=TimeoutEmbed(), ephemeral=True)
            return

        print(item.name)


async def setup(bot: Bot) -> None:
    await bot.add_cog(MarketCog())
