from discord import Color, Embed, Interaction


class BridgewatcherEmbed(Embed):
    def __init__(
        self,
        interaction: Interaction,
        title: str | None = None,
        color: int | Color | None = None,
        description: str | None = None,
    ):
        super().__init__(title=title, color=color, description=description)
        self.set_author(
            name=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar,
        )


class NoItemFoundEmbed(Embed):
    def __init__(self, item_name: str):
        super().__init__(color=Color.red(), title=f"{item_name} does not exist")


class UntrackedItemEmbed(Embed):
    def __init__(self, item_name: str):
        super().__init__(
            color=Color.red(), title=f"{item_name} is not tracked by Bridgewatcher"
        )


class TimeoutEmbed(Embed):
    def __init__(self):
        super().__init__(color=Color.red(), title=f"Your time has run out")
