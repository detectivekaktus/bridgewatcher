from re import IGNORECASE, compile, escape

from discord import Interaction

from bridgewatcher.db import db
from bridgewatcher.db.schema import Item, ItemName
from bridgewatcher.discord.views import ItemPickerView
from bridgewatcher.util.exc import NoItemFoundError, UntrackedItemRequested


class ItemGuesser:
    @staticmethod
    async def guess_item_by_name(
        interaction: Interaction, item_name: str
    ) -> tuple[Item, ItemName]:
        await interaction.response.send_message("Searching...", ephemeral=True)

        names = db.get_collection("item_names")
        regex = compile(f"^.*{escape(item_name)}.*$", IGNORECASE)
        results = await names.find({"name": regex}, limit=5).to_list()

        if not results:
            await interaction.delete_original_response()
            raise NoItemFoundError(f"{item_name} doesn't exist", item_name)
        elif len(results) == 1:
            await interaction.delete_original_response()
            return await ItemGuesser._get_item_by_id_from_list(results, 0)

        names = [ItemName.from_mongo(result) for result in results]
        view = ItemPickerView(names)
        await interaction.edit_original_response(
            content="Please, select the item you're looking for from the options below",
            view=view,
        )

        timed_out = await view.wait()
        if timed_out:
            await interaction.delete_original_response()
            raise TimeoutError("User didn't select an item")
        await interaction.delete_original_response()

        index: int = view.selected_index  # type: ignore
        return await ItemGuesser._get_item_by_id_from_list(results, index)

    @staticmethod
    async def _get_item_by_id_from_list(
        item_names: list[dict], index: int
    ) -> tuple[Item, ItemName]:
        items = db.get_collection("items")

        item_name = ItemName.from_mongo(item_names[index])
        item = await items.find_one({"name": item_name.id})
        # interestingly enough this result may be null cause not all
        # items are stored in the db. if it's not stored it's unimportant
        if item is None:
            raise UntrackedItemRequested(
                f"{item_name.name} is not stored in the database"
            )
        return Item.from_mongo(item), item_name
