#!/usr/bin/env python3
from typing import Any
from discord import Color, Embed
from src.utils import format_name


class NameErrorEmbed(Embed):
    def __init__(self, name: str) -> None:
        super().__init__(title=f"{format_name(name)} doesn't exist!",
                         description=f"After a quick lookup *{format_name(name)}* was not found. Check the name once more and try again.\n\nYou can [submit an issue](https://github.com/detectivekaktus/bridgewatcher/issues/new) if you think that the bot's behavior is wrong.",
                         color=Color.red())


class ServerErrorEmbed(Embed):
    def __init__(self) -> None:
        super().__init__(title="There was a server error!",
                         description="I can't process your request due to a server error occured. Wait a moment and try again.",
                         color=Color.red())


class InvalidValueErrorEmbed(Embed):
    def __init__(self, value: Any) -> None:
        super().__init__(title="Invalid value found!",
                         description=f"The value *'{str(value)}'* you specified, appears to be invalid. Please, input a new value and try again.",
                         color=Color.red())


class OutdatedDataErrorEmbed(Embed):
    def __init__(self) -> None:
        super().__init__(title="The data on the server is outdated!",
                         description="During the handling of your process, the data you requested, appears to be outdated. Wait a moment and try again.\n\nInstall the [Albion Online Data Project client](https://albion-online-data.com/) to avoid such problems in the future for you and other bot users.",
                         color=Color.red())


class TimedOutErrorEmbed(Embed):
    def __init__(self) -> None:
        super().__init__(title="Your request timed out!",
                         description="You were innactive for a long time so your request timed out and you have to start a new one.",
                         color=Color.red())
