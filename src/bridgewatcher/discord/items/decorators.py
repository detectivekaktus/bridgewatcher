from functools import wraps
from typing import Callable

from discord import Interaction

from bridgewatcher.discord.embed import (
    InsufficientDataEmbed,
    NoItemFoundEmbed,
    TimeoutEmbed,
    UntrackedItemEmbed,
)
from bridgewatcher.util.exc import (
    InsufficientDataError,
    NoItemFoundError,
    UntrackedItemRequested,
)


def guard_item_errors(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self, interaction: Interaction, *args, **kwargs) -> None:
        try:
            return await func(self, interaction, *args, **kwargs)
        except NoItemFoundError as e:
            await interaction.followup.send(
                embed=NoItemFoundEmbed(e.item_name), ephemeral=True
            )
        except UntrackedItemRequested:
            await interaction.followup.send(embed=UntrackedItemEmbed(), ephemeral=True)
        except TimeoutError:
            await interaction.followup.send(embed=TimeoutEmbed(), ephemeral=True)
        except InsufficientDataError:
            await interaction.followup.send(
                embed=InsufficientDataEmbed(), ephemeral=True
            )

    return wrapper
