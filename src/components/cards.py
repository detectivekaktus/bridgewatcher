#!/usr/bin/env python3
from typing import Any, Optional, cast
from discord import ButtonStyle, Color, Embed, Interaction, Message
from discord.ui import Button, View, button


class PlayerDeathCard(View):
    def __init__(self, interaction: Interaction, data: list[dict[str, Any]], *, timeout: Optional[float] = 180) -> None:
        super().__init__(timeout=timeout)
        self._interaction: Interaction = interaction
        self._data: list[dict[str, Any]] = data
        self._current: int = 0
        self.message: Message | None = None


    async def handle_message(self, edit: bool = False) -> None:
        if not self.message and edit:
            return

        embed: Embed = Embed(title=f"{self._data[self._current]["Victim"]["Name"]}'s death against {self._data[self._current]["Killer"]["Name"]}",
                             color=Color.yellow())
        try:
            embed.add_field(name="Killer's weapon", value=f"**{self._data[self._current]["Killer"]["Equipment"]["MainHand"]["Type"]}**")
            embed.add_field(name="Killer's average IP", value=f"**{int(self._data[self._current]["Killer"]["AverageItemPower"]):,}**")
            embed.add_field(name="Fame gained", value=f"**{self._data[self._current]["TotalVictimKillFame"]:,}**")
            embed.add_field(name="Victim's weapon", value=f"**{self._data[self._current]["Victim"]["Equipment"]["MainHand"]["Type"]}**")
            embed.add_field(name="Victim's average IP", value=f"**{int(self._data[self._current]["Victim"]["AverageItemPower"]):,}**")
            if (partecipants := len(self._data[self._current]["Participants"])) != 1:
                embed.add_field(name="Killed in a group of", value=f"**{partecipants}**")
        except Exception:
            await self._interaction.followup.send("Failed to load the log. You won't see the data related to it, but you can continue exploring other results.", ephemeral=True)
            return

        if edit:
            message: Message = cast(Message, self.message)
            await message.edit(view=self, embed=embed)
        else:
            await self._interaction.response.send_message(view=self, embed=embed)


    @button(label="<", style=ButtonStyle.blurple, disabled=True)
    async def prev_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self._current -= 1
        button.disabled = True if self._current == 0 else False
        self.next_button.disabled = True if self._current == len(self._data) - 1 else False
        await self.handle_message(edit=True)

    @button(label=">", style=ButtonStyle.blurple)
    async def next_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self._current += 1
        button.disabled = True if self._current == len(self._data) - 1 else False
        self.prev_button.disabled = True if self._current == 0 else False
        await self.handle_message(edit=True)
