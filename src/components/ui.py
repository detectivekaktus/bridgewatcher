#!/usr/bin/env python3
from typing import Any, List, Optional
from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Button, Select, View, button
from src import CITIES, QUALITIES


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

    async def callback(self, interaction: Interaction) -> Any:
        self.parent_view.quality = self.values[0]
        await interaction.response.defer()


class CitiesSelect(Select):
    def __init__(self,
                 parent_view: Any,
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
        self.parent_view: Any = parent_view


    async def callback(self, interaction: Interaction) -> Any:
        self.parent_view.cities = self.values
        await interaction.response.defer()


class PriceView(View):
    def __init__(self, *, timeout: Optional[float] = 180) -> None:
        super().__init__(timeout=timeout)
        self.quality: str = "normal"
        self.cities: List[str] = []

        self.quality_select = QualitySelect(self, [SelectOption(label=label) for label in QUALITIES],
                                            placeholder="Select item quality.")
        self.cities_select = CitiesSelect(self, [SelectOption(label=city.capitalize()) for city in CITIES],
                                          placeholder="Select cities.")
        self.add_item(self.quality_select)
        self.add_item(self.cities_select)


    @button(label="Submit", style=ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: Button) -> None:
        self.stop()
        await interaction.response.defer()
