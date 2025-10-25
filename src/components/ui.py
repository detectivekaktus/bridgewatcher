#!/usr/bin/env python3
from json import loads
from typing import Any, Optional
from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Button, Select, View, button
from src.utils.constants import CITIES, DEFAULT_RATE, QUALITIES
from src.api import ItemManager, remove_suffix
from src.client import DATABASE
from src.components.modals import ReturnModal, ResourcesModal
from src.utils.annotations import overrides


class QualitySelect(Select):
    def __init__(
        self,
        parent_view: Any,
        options: list[SelectOption],
        *,
        custom_id: str = "qualset",
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
            row=row,
        )
        self.parent_view: Any = parent_view

    @overrides(Select)
    async def callback(self, interaction: Interaction) -> Any:
        self.parent_view.quality = self.values[0]
        await interaction.response.defer()


class CitiesSelect(Select):
    def __init__(
        self,
        cities_holder: list[str],
        options: list[SelectOption],
        *,
        custom_id: str = "citsel",
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = len(CITIES),
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
            row=row,
        )
        self.cities_holder = cities_holder

    @overrides(Select)
    async def callback(self, interaction: Interaction) -> Any:
        self.cities_holder.extend(self.values)
        await interaction.response.defer()


class PriceView(View):
    def __init__(self, *, timeout: Optional[float] = 180) -> None:
        super().__init__(timeout=timeout)
        self.quality: str = "normal"

        self.quality_select = QualitySelect(
            self,
            [SelectOption(label=label) for label in QUALITIES],
            placeholder="Select item quality.",
        )
        self.add_item(self.quality_select)

    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        self.stop()
        await interaction.response.defer()


class CraftingView(View):
    def __init__(
        self, item_name: str, is_enchated: bool, timeout: Optional[float] = 180
    ):
        super().__init__(timeout=timeout)
        self.item_name: str = remove_suffix(DATABASE, item_name, is_enchated)
        self.is_enchanted: bool = is_enchated
        self.craft_city: list[str] = []
        self.sell_city: list[str] = []
        self.resources: dict[str, int] = {}
        self.return_rate: float = DEFAULT_RATE

        with DATABASE as db:
            db.execute("SELECT * FROM items WHERE name = ?", (self.item_name,))
            item: list[dict[str, Any]] | dict[str, Any] = loads(db.fetchone()[4])

        if isinstance(item, list):
            item = item[0]

        requirements: list[dict[str, Any]] = (
            [item["craftresource"]]
            if isinstance(item["craftresource"], dict)
            else item["craftresource"]
        )
        self.crafting_requirements: dict[str, Any] = {}
        for requirement in requirements:
            if self.is_enchanted and int(requirement["@uniquename"][1]) > 3:
                if not ItemManager.is_resource(
                    DATABASE, requirement["@uniquename"]
                ) and not ItemManager.is_artefact(DATABASE, requirement["@uniquename"]):
                    requirement["@uniquename"] = (
                        f"{requirement["@uniquename"]}{item_name[-2:]}"
                    )
                elif ItemManager.is_resource(DATABASE, requirement["@uniquename"]):
                    requirement["@uniquename"] = (
                        f"{requirement["@uniquename"]}_LEVEL{item_name[-1]}@{item_name[-1]}"
                    )
            self.crafting_requirements[requirement["@uniquename"]] = int(
                requirement["@count"]
            )

        self.craft_city_select = CitiesSelect(
            self.craft_city,
            options=[
                SelectOption(label=label.capitalize())
                for label in CITIES
                if label != "black market"
            ],
            placeholder="Enter crafting city.",
            custom_id="craftcit",
            max_values=1,
        )
        self.sell_city_select = CitiesSelect(
            self.sell_city,
            options=[SelectOption(label=label.capitalize()) for label in CITIES],
            placeholder="Enter selling city.",
            custom_id="sellcit",
            max_values=1,
        )
        self.add_item(self.craft_city_select)
        self.add_item(self.sell_city_select)

    @button(label="Resources", style=ButtonStyle.blurple)
    async def resources_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(ResourcesModal(self))

    @button(label="Return rate", style=ButtonStyle.blurple)
    async def return_rate_button(
        self, interaction: Interaction, button: Button
    ) -> None:
        await interaction.response.send_modal(ReturnModal(self))

    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self.stop()


class FlipView(View):
    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.quality: str = "normal"
        self.cities: list[str] = []

        self.quality_select = QualitySelect(
            self,
            [SelectOption(label=label) for label in QUALITIES],
            placeholder="Enter item quality.",
        )
        self.cities_select = CitiesSelect(
            self.cities,
            [
                SelectOption(label=label.capitalize())
                for label in CITIES
                if label != "black market"
            ],
            placeholder="Enter start city.",
            max_values=1,
        )
        self.add_item(self.quality_select)
        self.add_item(self.cities_select)

    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self.stop()
