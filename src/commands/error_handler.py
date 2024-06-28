#!/usr/bin/env python3
from sys import stderr
from typing import Any, Final
from discord.ext.commands import BadArgument, Bot, Cog, CommandNotFound, Context, DisabledCommand, NoPrivateMessage


IGNORED: Final[tuple[Any]] = (CommandNotFound, )


class CommandErrorHandler(Cog):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot


    @Cog.listener()
    async def on_command_error(self, context: Context, error: Any) -> None:
        if hasattr(context.command, "on_error"):
            return

        error = getattr(error, "original", error)
        if isinstance(error, IGNORED):
            return
        elif isinstance(error, DisabledCommand):
            await context.send(f"{context.command} has been disabled.")
        elif isinstance(error, NoPrivateMessage):
            await context.author.send(f"{context.command} cannot be used in private messages.")
        elif isinstance(error, BadArgument):
            await context.send(f"You've entered a wrong argument to the {context.command} command.")
        else:
            print(f"Encountered unexpected exception: {error} in command {context.command}.", file=stderr)


async def setup(bot: Bot) -> None:
    await bot.add_cog(CommandErrorHandler(bot))
