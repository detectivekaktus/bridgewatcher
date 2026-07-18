from discord import ButtonStyle
from discord.ui import Button, View


class HelpView(View):
    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.add_item(
            Button(
                label="Add me to your server",
                style=ButtonStyle.link,
                url="https://discord.com/oauth2/authorize?client_id=1241428288195526796",
            )
        )
        self.add_item(
            Button(
                label="Donate",
                style=ButtonStyle.link,
                url="https://paypal.me/ArtiomAstashonak",
            )
        )
