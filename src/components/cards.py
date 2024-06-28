#!/usr/bin/env python3
from abc import ABC, abstractmethod
from typing import Any, Optional, cast
from discord import ButtonStyle, Color, Embed, Guild, Interaction, Message
from discord.ui import Button, View, button
from src import ITEM_NAMES
from src.client import SERVERS
from src.utils import api_name_to_readable_name, format_name, inttoemoji_server, overrides
from src.utils.logging import LOGGER


class Card(ABC):
    def __init__(self, interaction: Interaction, data: list) -> None:
        super().__init__()
        self._interaction = interaction
        self._data = data
        self._current: int = 0
        self.message: Message | None = None

    @abstractmethod
    async def handle_message(self, edit: bool = False) -> None:
        pass


    @abstractmethod
    def update_buttons(self) -> None:
        pass


    @button(label="<", style=ButtonStyle.blurple)
    @abstractmethod
    async def prev_button(self, interaction: Interaction, button: Button) -> None:
        pass

    @button(label=">", style=ButtonStyle.blurple)
    @abstractmethod
    async def next_button(self, interaction: Interaction, button: Button) -> None:
        pass



class PlayerCard(View, Card):
    def __init__(self, interaction: Interaction, data: list[dict[str, Any]], *, is_kill: bool = False, timeout: Optional[float] = 180) -> None:
        View.__init__(self, timeout=timeout)
        Card.__init__(self, interaction, data)
        self._is_kill = is_kill


    @overrides(Card)
    async def handle_message(self, edit: bool = False) -> None:
        if not self.message and edit:
            return

        embed: Embed = Embed(title=f"{self._data[self._current]["Killer"]["Name"]} 🔪 killed {self._data[self._current]["Victim"]["Name"]}" if self._is_kill else f"{self._data[self._current]["Victim"]["Name"]}'s 💀 death against {self._data[self._current]["Killer"]["Name"]}",
                             color=Color.yellow())
        try:
            embed.add_field(name="🔪 Killer's weapon", value=f"**{format_name(api_name_to_readable_name(ITEM_NAMES, self._data[self._current]["Killer"]["Equipment"]["MainHand"]["Type"]))}**", inline=False)
            embed.add_field(name="💯 Killer's average IP", value=f"**{int(self._data[self._current]["Killer"]["AverageItemPower"]):,}**", inline=False)
            embed.add_field(name="📚 Fame gained", value=f"**{self._data[self._current]["TotalVictimKillFame"]:,}**", inline=False)
            embed.add_field(name="🩸 Victim's weapon", value=f"**{format_name(api_name_to_readable_name(ITEM_NAMES, self._data[self._current]["Victim"]["Equipment"]["MainHand"]["Type"]))}**", inline=False)
            embed.add_field(name="💯 Victim's average IP", value=f"**{int(self._data[self._current]["Victim"]["AverageItemPower"]):,}**", inline=False)
            embed.set_author(name=f"Requested by {self._interaction.user.name}", icon_url=self._interaction.user.avatar)
            embed.set_footer(text=f"The data is provided by Sandbox Interactive GmbH. | {inttoemoji_server(SERVERS.get_config(cast(Guild, self._interaction.guild))["fetch_server"])} server")
            if (partecipants := len(self._data[self._current]["Participants"])) != 1:
                embed.add_field(name="🏘️ Killed in group of", value=f"**{partecipants} members**")
        except Exception:
            LOGGER.error("Failed to load the log of kill/deaths. Probaly killer or victim haven't had a weapon equipped.")
            await self._interaction.followup.send("Failed to load the log. You won't see the data related to it, but you can continue exploring other results.", ephemeral=True)
            return

        if edit:
            message: Message = cast(Message, self.message)
            await message.edit(view=self, embed=embed)
        else:
            await self._interaction.response.send_message(view=self, embed=embed)


    @overrides(Card)
    def update_buttons(self) -> None:
        self.prev_button.disabled = True if self._current == 0 else False
        self.next_button.disabled = True if self._current == len(self._data) - 1 else False


    @overrides(Card)
    @button(label="<", style=ButtonStyle.blurple, disabled=True)
    async def prev_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self._current -= 1
        self.update_buttons()
        await self.handle_message(edit=True)

    @overrides(Card)
    @button(label=">", style=ButtonStyle.blurple)
    async def next_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self._current += 1
        self.update_buttons()
        await self.handle_message(edit=True)


class MembersCard(View, Card):
    def __init__(self, interaction: Interaction, data: list[dict[str, Any]], *, delimiter: int = 10, timeout: Optional[float] = 180):
        View.__init__(self, timeout=timeout)
        Card.__init__(self, interaction, data)
        self._page: int = 1
        self._delimiter = delimiter
        self._compute_curr_prev()

    def _compute_curr_prev(self) -> None:
        self._current = self._delimiter * self._page if self._delimiter < len(self._data) else len(self._data)
        self._previous: int = self._current - self._delimiter


    @overrides(Card)
    async def handle_message(self, edit: bool = False) -> None:
        if (not self.message) and edit:
            return

        description: list[str] = ["**Members**:"]
        description.extend([f"`{member["Name"]}`: *{(member["KillFame"] + member["LifetimeStatistics"]["PvE"]["Total"] + member["LifetimeStatistics"]["Gathering"]["All"]["Total"] + member["LifetimeStatistics"]["Crafting"]["Total"] + member["LifetimeStatistics"]["FishingFame"] + member["LifetimeStatistics"]["FarmingFame"]):,} total fame*" for member in self._data[self._previous:self._current]])
        embed: Embed = Embed(title=f"Members of 🛡️ {self._data[0]["GuildName"]}",
                             description="\n".join(description))
        embed.set_author(name=f"Requested by {self._interaction.user.name} | Page {self._page}", icon_url=self._interaction.user.avatar)
        embed.set_footer(text=f"The data is provided by Sandbox Interactive GmbH. | {inttoemoji_server(SERVERS.get_config(cast(Guild, self._interaction.guild))["fetch_server"])} server")

        if edit:
            message: Message = cast(Message, self.message)
            await message.edit(view=self, embed=embed)
        else:
            await self._interaction.response.send_message(view=self, embed=embed)


    @overrides(Card)
    def update_buttons(self) -> None:
        self.prev_button.disabled = True if self._page == 1 else False
        self.next_button.disabled = True if self._current >= len(self._data) else False


    @overrides(Card)
    @button(label="<", style=ButtonStyle.blurple, disabled=True)
    async def prev_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self._page -= 1
        self._compute_curr_prev()
        self.update_buttons()
        await self.handle_message(edit=True)

    @overrides(Card)
    @button(label=">", style=ButtonStyle.blurple)
    async def next_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self._page += 1
        self._compute_curr_prev()
        self.update_buttons()
        await self.handle_message(edit=True)
