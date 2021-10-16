from discord.ext import commands


@commands.command()
async def show_new(ctx, *args):
    ...


@commands.command()
async def show_accepted(ctx, *args):
    ...


@commands.command()
async def show_declined(ctx, *args):
    ...


@commands.command()
async def accept(ctx, id):
    ...


@commands.command()
async def decline(ctx, id):
    ...


COMMANDS = [show_new, show_accepted, show_declined, accept, decline]
