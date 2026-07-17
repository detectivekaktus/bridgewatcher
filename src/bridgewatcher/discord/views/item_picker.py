from discord import Interaction
from discord.ui import Button, View

from bridgewatcher.db.schema import ItemName


class ItemPickerView(View):
    def __init__(self, items: list[ItemName]):
        super().__init__(timeout=180)
        self.items = items
        self.selected_index: int | None = None

        for i, item in enumerate(items):
            level = item.id[-2:]
            display_name = (
                item.name
                if level not in ("@1", "@2", "@3", "@4")
                else f"{item.name} (level {level[-1]})"
            )

            button = Button(label=display_name, custom_id=item.id)
            button.callback = self._make_callback(i)
            self.add_item(button)

    def _make_callback(self, index: int):
        async def callback(interaction: Interaction) -> None:
            self.selected_index = index
            await interaction.response.defer()
            self.stop()

        return callback
