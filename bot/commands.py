from discord import Embed
from discord.ext import commands
from peewee import DoesNotExist

from database.models import Suggestion, STATE_NEW, STATE_ACCEPTED, STATE_DECLINED

UPVOTE = '👍'
DOWNVOTE = '👎'

POSSIBLE_STATES = {
    'new': STATE_NEW,
    'accepted': STATE_ACCEPTED,
    'declined': STATE_DECLINED
}


def sort_weighted_suggestions(msg):
    return msg.votes['total'], msg.votes['up']


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
    sug = suggestions[0]
    channel = ctx.guild.get_channel(int(sug.channel_id))
    if suggestions.count():
        channel_ids = set([s.channel_id for s in suggestions])
        channels = {}
        for channel_id in channel_ids:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                channels[channel.id] = {
                    'channel': channel,
                    'embed': Embed(
                        title=f"All '{state}' suggestions from #{channel.name}",
                        description=f"Here you find all {state} suggestions, sorted by votes. Taken from the #{channel} channel.",
                        color=0x03C6AB
                    )
                }

        channels_with_weighted_suggestions = {}
        for suggestion in suggestions:
            suggestion.votes = { 'up': 0, 'down': 0, 'total': 0}
            channel = channels.get(suggestion.channel_id, {}).get('channel')
            if channel:
                message = await channel.fetch_message(suggestion.discord_id)
                if not channel.name in channels_with_weighted_suggestions:
                    channels_with_weighted_suggestions[channel.name] = []
                for reaction in message.reactions:
                    if reaction.emoji == UPVOTE:
                        suggestion.votes['up'] += reaction.count
                        suggestion.votes['total'] += reaction.count
                    if reaction.emoji == DOWNVOTE:
                        suggestion.votes['down'] += reaction.count
                        suggestion.votes['total'] += reaction.count
                channels_with_weighted_suggestions[channel.name].append(suggestion)

        for suggestions in channels_with_weighted_suggestions.values():
            sorted_suggestions = sorted(suggestions, key=sort_weighted_suggestions, reverse=True)
            for suggestion in sorted_suggestions:
                channels[suggestion.channel_id]['embed'].add_field(
                    name=f"[{suggestion.id}] {suggestion.summary} | **{suggestion.votes['up']}x{UPVOTE}** | **{suggestion.votes['down']}x{DOWNVOTE}**",
                    value=f"[Jump to suggestion](https://discordapp.com/channels/{suggestion.guild_id}/{suggestion.channel_id}/{suggestion.discord_id})",
                    inline=False
                )
        for channel in channels.values():
            await ctx.message.channel.send(embed=channel['embed'])
    else:
        await ctx.message.channel.send(f"I was not able to find any saved suggestions for '{state}'")


async def change_state(ctx, new_state, *ids):
    suggestions = Suggestion.select().where(Suggestion.id.in_(ids))
    updated = []
    ctx.bot.logger.info(f"Found {suggestions.count()} suggestions, for IDs {ids}.")
    for suggestion in suggestions:
        getattr(suggestion, new_state)()
        ctx.bot.logger.info(f"Updated {suggestion.id} and set state to {new_state}.")
        updated.append(suggestion.id)
    message = f"No suggestions found for the IDs: {ids}."
    if updated:
        message = f"Added {updated} to the {new_state} list."
    await ctx.message.channel.send(message)


@commands.command(
    brief="Accept suggestions",
    help="Accept suggestions. Suggestions are selected via the provided IDs."
)
async def accept(ctx, *ids):
    ctx.bot.logger.info(f"Got 'accept' command from {ctx.author} for IDs '{ids}'.")
    await change_state(ctx, 'accept', *ids)


@commands.command(
    brief="Decline suggestions",
    help="Decline suggestions. Suggestions are selected via the provided IDs."
)
async def decline(ctx, *ids):
    ctx.bot.logger.info(f"Got 'decline' command from {ctx.author} for IDs '{ids}'.")
    await change_state(ctx, 'decline', *ids)


@commands.command(
    brief="Set state of suggestions back to new",
    help="Set the state of suggestions back to new. Suggestions are selected via the provided IDs."
)
async def renew(ctx, *ids):
    ctx.bot.logger.info(f"Got 'renew' command from {ctx.author} for IDs '{ids}'.")
    await change_state(ctx, 'renew', *ids)


COMMANDS = [show, accept, decline, renew]
