#!/usr/bin/env python3
from json import loads
from random import choice
from typing import Any, List, Optional
from discord import Interaction
from discord.ui import Modal, TextInput
from src import overrides
from src.api import ItemManager, remove_suffix
from src.client import database


class ResourcesModal(Modal):
    def __init__(self, view: Any, *, title: str = "Resources", timeout: Optional[float] = None, custom_id: str = "resources") -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        self.view = view

        item_name: str = remove_suffix(self.view.item_name, self.view.is_enchanted)
        with database as db:
            db.execute("SELECT * FROM items WHERE name = ?", (item_name, ))
            item: List[dict[str, Any]] | dict[str, Any] = loads(db.fetchone()[4])

        if isinstance(item, list):
            item = item[0]

        if isinstance(item["craftresource"], dict):
            requirements: List[dict[str, Any]] = [item["craftresource"]]
        else:
            requirements: List[dict[str, Any]] = item["craftresource"]
        
        self.txt_inputs: List[TextInput] = []
        placeholders = ("Eg. 100", "Eg. 3350", "Eg. 305", "Eg. 777")
        
        for requirement in requirements:
            if self.view.is_enchanted and int(requirement["@uniquename"][1]) > 3:
                if not ItemManager.is_resource(requirement["@uniquename"]) and not ItemManager.is_artefact(requirement["@uniquename"]):
                    requirement["@uniquename"] = f"{requirement["@uniquename"]}{view.item_name[-2:]}" 
                elif ItemManager.is_resource(requirement["@uniquename"]):
                    requirement["@uniquename"] = f"{requirement["@uniquename"]}_LEVEL{view.item_name[-1]}@{view.item_name[-1]}"

            self.view.crafting_requirements[requirement["@uniquename"]] = int(requirement["@count"])
            txt_input = TextInput(label=requirement["@uniquename"], placeholder=choice(placeholders))
            self.txt_inputs.append(txt_input)
            self.add_item(txt_input)


    @overrides(Modal)
    async def on_submit(self, interaction: Interaction) -> None:
        for txt_input in self.txt_inputs:
            try:
                value = int(txt_input.value)
                self.view.resources[txt_input.label] = value
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
            await interaction.response.send_message(f"{self.return_rate.value} is not a valid return rate.")
            return
