from discord import Embed
from discord.ext import commands
from peewee import DoesNotExist

from database.models import Suggestion, STATE_NEW, STATE_ACCEPTED, STATE_DECLINED


POSSIBLE_STATES = {
    'new': STATE_NEW,
    'accepted': STATE_ACCEPTED,
    'declined': STATE_DECLINED
}


@commands.command(
    brief="Show suggestions",
    help="Shows a list of suggestions of the specified state. State can be new, accepted or declined. If none is provided, new will be assumed."
)
async def show(ctx, state="new"):
    ctx.bot.logger.info(f"Got 'show' command from {ctx.author} with state '{state}'.")
    selected_state = POSSIBLE_STATES.get(state)
    if selected_state is None:
        ctx.bot.logger.info(f"State '{state}' is not a valid state.")
        await ctx.message.channel.send(f"I'm sorry, '{state}' is not a valid state. Please choose one of: new, accepted, declined")
        return
    suggestions = Suggestion.filter(state=selected_state)
    if suggestions.count():
        embed = Embed(
            title=f"All '{state}' suggestions",
            description=f"Here you find all {state} suggestions, sorted by votes.",
            color=0x03C6AB
        )
        for suggestion in suggestions:
            embed.add_field(
                name=f"[{suggestion.id}] {suggestion.summary}",
                value=f"[Jump to suggestion](https://discordapp.com/channels/{suggestion.guild_id}/{suggestion.channel_id}/{suggestion.discord_id})",
                inline=False
            )
        await ctx.message.channel.send(embed=embed)
    else:
        await ctx.message.channel.send(f"I was not able to find any saved suggestions for '{state}'")


@commands.command(
    brief="Accept suggestions",
    help="Accept suggestions. Suggestions are selected via the provided IDs."
)
async def accept(ctx, *ids):
    # TODO: Combine accept, decline and renew
    suggestions = Suggestion.select().where(Suggestion.id.in_(ids))
    updated = []
    for suggestion in suggestions:
        suggestion.accept()
        updated.append(suggestion.id)
    message = f"No suggestions found for the IDs: {ids}."
    if updated:
        message = f"Added {updated} to the accepted list."
    await ctx.message.channel.send(message)


@commands.command(
    brief="Decline suggestions",
    help="Decline suggestions. Suggestions are selected via the provided IDs."
)
async def decline(ctx, *ids):
    # TODO: Combine accept, decline and renew
    suggestions = Suggestion.select().where(Suggestion.id.in_(ids))
    updated = []
    for suggestion in suggestions:
        suggestion.decline()
        updated.append(suggestion.id)
    message = f"No suggestions found for the IDs: {ids}."
    if updated:
        message = f"Added {updated} to the declined list."
    await ctx.message.channel.send(message)


@commands.command(
    brief="Set state of suggestions back to new",
    help="Set the state of suggestions back to new. Suggestions are selected via the provided IDs."
)
async def renew(ctx, *ids):
    # TODO: Combine accept, decline and renew
    suggestions = Suggestion.select().where(Suggestion.id.in_(ids))
    updated = []
    for suggestion in suggestions:
        suggestion.renew()
        updated.append(suggestion.id)
    message = f"No suggestions found for the IDs: {ids}."
    if updated:
        message = f"Added {updated} to the new list."
    await ctx.message.channel.send(message)


COMMANDS = [show, accept, decline, renew]
