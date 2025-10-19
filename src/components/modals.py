#!/usr/bin/env python3
from json import loads
from random import choice
from typing import Any, Optional
from discord import Interaction
from discord.ui import Modal, TextInput
from src import ITEM_NAMES
from src.api import remove_suffix
from src.client import DATABASE
from src.utils.formatting import api_name_to_readable_name
from src.utils.annotations import overrides


class ResourcesModal(Modal):
    def __init__(self, view: Any, *, title: str = "Resources", timeout: Optional[float] = None, custom_id: str = "resources") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.view = view

        item_name: str = remove_suffix(DATABASE, self.view.item_name, self.view.is_enchanted)
        with DATABASE as db:
            db.execute("SELECT * FROM items WHERE name = ?", (item_name, ))
            item: list[dict[str, Any]] | dict[str, Any] = loads(db.fetchone()[4])

        if isinstance(item, list):
            item = item[0]

        requirements: list[dict[str, Any]] = [item["craftresource"]] if isinstance(item["craftresource"], dict) else item["craftresource"]
        self.txt_inputs: list[TextInput] = []
        
        for requirement in requirements:
            txt_input = TextInput(label=api_name_to_readable_name(ITEM_NAMES, requirement["@uniquename"]), placeholder=choice(["Eg. 100", "Eg. 3350", "Eg. 305", "Eg. 5000"]))
            self.txt_inputs.append(txt_input)
            self.add_item(txt_input)


    @overrides(Modal)
    async def on_submit(self, interaction: Interaction) -> None:
        for txt_input in self.txt_inputs:
            try:
                value = int(txt_input.value)
                self.view.resources[ITEM_NAMES[txt_input.label]] = value
            except ValueError:
                await interaction.response.send_message("Some of your resource values are not valid.",
                                                        ephemeral=True,
                                                        delete_after=5)
                return

        await interaction.response.defer()


class ReturnModal(Modal):
    def __init__(self, view: Any, *, title: str = "Return rate", timeout: Optional[float] = None, custom_id: str = "rrate") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.view = view
        self.return_rate: TextInput = TextInput(label=title, placeholder="Eg. 15 or 25.5")
        self.add_item(self.return_rate)


    @overrides(Modal)
    async def on_submit(self, interaction: Interaction) -> None:
        try:
            return_rate: float = float(self.return_rate.value)
            if return_rate >= 100 or return_rate < 0:
                raise ValueError("Return rate can't be more than 99 percent and can't be below 0 percent.")
            self.view.return_rate = return_rate
            await interaction.response.defer()
        except ValueError:
            await interaction.response.send_message(f"{self.return_rate.value} is not a valid return rate.",
                                                    ephemeral=True,
                                                    delete_after=5)
            return
