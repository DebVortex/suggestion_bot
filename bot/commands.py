from discord.ext import commands


@commands.command(
    brief="Show new suggestions",
    help="Shows a list of all suggestions which has neither been accepted nor declined."
)
async def show_new(ctx, *args):
    ...


@commands.command(brief="Show accepted suggestions")
async def show_accepted(ctx, *args):
    ...


@commands.command(brief="Show declined suggestions")
async def show_declined(ctx, *args):
    ...


@commands.command(brief="Accept a suggestion")
async def accept(ctx, id):
    ...


@commands.command(brief="Decline a suggestion")
async def decline(ctx, id):
    ...


@commands.command(brief="Set state of a suggestion back to new")
async def renew(ctx, id):
    ...


COMMANDS = [show_new, show_accepted, show_declined, accept, decline, renew]
