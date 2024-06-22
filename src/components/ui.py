#!/usr/bin/env python3
from typing import Any, List, Optional
from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Button, Select, View, button
from src import CITIES, DEFAULT_RATE, QUALITIES
from src.components.modals import ReturnModal, ResourcesModal
from src.utils import overrides


class QualitySelect(Select):
    def __init__(self,
                 parent_view: Any,
                 options: List[SelectOption], *,
                 custom_id: str = "qualset",
                 placeholder: Optional[str] = None,
                 min_values: int = 1,
                 max_values: int = 1,
                 disabled: bool = False,
                 row: Optional[int] = None) -> None:
        super().__init__(custom_id=custom_id,
                         placeholder=placeholder,
                         min_values=min_values,
                         max_values=max_values,
                         options=options,
                         disabled=disabled,
                         row=row)
        self.parent_view: Any = parent_view


    @overrides(Select)
    async def callback(self, interaction: Interaction) -> Any:
        self.parent_view.quality = self.values[0]
        await interaction.response.defer()


class CitiesSelect(Select):
    def __init__(self,
                 cities_holder: List[str],
                 options: List[SelectOption], *,
                 custom_id: str = "citsel",
                 placeholder: Optional[str] = None,
                 min_values: int = 1,
                 max_values: int = len(CITIES),
                 disabled: bool = False,
                 row: Optional[int] = None) -> None:
        super().__init__(custom_id=custom_id,
                         placeholder=placeholder,
                         min_values=min_values,
                         max_values=max_values,
                         options=options,
                         disabled=disabled,
                         row=row)
        self.cities_holder = cities_holder


    @overrides(Select)
    async def callback(self, interaction: Interaction) -> Any:
        self.cities_holder.extend(self.values)
        await interaction.response.defer()


class PriceView(View):
    def __init__(self, *, timeout: Optional[float] = 180) -> None:
        super().__init__(timeout=timeout)
        self.quality: str = "normal"
        self.cities: List[str] = []

        self.quality_select = QualitySelect(self, [SelectOption(label=label) for label in QUALITIES],
                                            placeholder="Select item quality.")
        self.cities_select = CitiesSelect(self.cities, [SelectOption(label=city.capitalize()) for city in CITIES],
                                          placeholder="Select cities.")
        self.add_item(self.quality_select)
        self.add_item(self.cities_select)


    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        self.stop()
        await interaction.response.defer()


class CraftingView(View):
    def __init__(self, item_name: str, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.item_name: str = item_name
        self.is_enchanted: bool = False
        self.craft_city: List[str] = []
        self.sell_city: List[str] = []
        self.resources: dict[str, int] = {}
        self.crafting_requirements: dict[str, int] = {}
        self.return_rate: float = DEFAULT_RATE

        self.craft_city_select = CitiesSelect(self.craft_city,
                                              options=[SelectOption(label=label.capitalize()) for label in CITIES if label != "black market"],
                                              placeholder="Enter crafting city.",
                                              custom_id="craftcit",
                                              max_values=1)
        self.sell_city_select = CitiesSelect(self.sell_city,
                                             options=[SelectOption(label=label.capitalize()) for label in CITIES],
                                             placeholder="Enter selling city.",
                                             custom_id="sellcit",
                                             max_values=1)
        self.add_item(self.craft_city_select)
        self.add_item(self.sell_city_select)


    @button(label="Resources", style=ButtonStyle.blurple)
    async def resources_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(ResourcesModal(self))

    @button(label="Return rate", style=ButtonStyle.blurple)
    async def return_rate_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.send_modal(ReturnModal(self))

    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self.stop()


class FlipView(View):
    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.quality: str = "normal"
        self.cities: List[str] = []

        self.quality_select = QualitySelect(self,
                                            [SelectOption(label=label) for label in QUALITIES],
                                            placeholder="Enter item quality.")
        self.cities_select = CitiesSelect(self.cities,
                                              [SelectOption(label=label.capitalize()) for label in CITIES if label != "black market"],
                                              placeholder="Enter start city.",
                                              max_values=1)
        self.add_item(self.quality_select)
        self.add_item(self.cities_select)


    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self.stop()
