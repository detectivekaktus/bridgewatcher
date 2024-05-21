#!/usr/bin/env python3
from datetime import datetime
from typing import List
from discord.ext.commands import Context
from discord import Embed
from requests import Response
from . import ERROR, SERVER_ERROR, TOO_MANY_REQUESTS


async def notify_if_not_ok(context: Context, response: Response) -> bool:
    if not response.ok:
        if response.status_code == TOO_MANY_REQUESTS:
            await context.send(embed=Embed(title=f":red_circle: {response.status_code}. Too many requests.",
                                           color=ERROR,
                                           description="I've encountered too many requests lately. Please, wait a few minutes and try again."))
            return True
        elif response.status_code == SERVER_ERROR:
            await context.send(embed=Embed(title=f":red_circle: {response.status_code}. Internal server error.",
                                           color=ERROR,
                                           description="The API server I get information from can't handle your request."))
            return True

        await context.send(embed=Embed(title=f":red_circle: {response.status_code}. There was an error handlering your request.",
                                       color=ERROR,
                                       description="I've incountered an error that doesn't allow me to handle your request."))
        return True

    return False


def get_percent_variation(data: List[dict], index: int) -> float:
    return round((data[index]["price"] / data[index + 1]["price"] - 1) * 100, 2)


def convert_api_timestamp(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").strftime("%d %B %Y, %H:%M:%S %p")
