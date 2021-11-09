from discord import Embed
from discord.ext import commands
from peewee import DoesNotExist

from database.models import Suggestion, STATE_NEW, STATE_ACCEPTED, STATE_DECLINED

from .utils import UPVOTE, DOWNVOTE, get_votes

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
async def show(ctx, state="new", page=1):
    ctx.bot.logger.info(f"Got 'show' command from {ctx.author} with state '{state}'.")
    selected_state = POSSIBLE_STATES.get(state)
    if selected_state is None:
        ctx.bot.logger.info(f"State '{state}' is not a valid state.")
        await ctx.message.channel.send(f"I'm sorry, '{state}' is not a valid state. Please choose one of: new, accepted, declined")
        return

    channels = [channel for channel in ctx.guild.text_channels if channel.name in ctx.bot.channels]

    for channel in channels:
        suggestions = Suggestion.select().where(
            Suggestion.channel_id == channel.id,
            Suggestion.state == selected_state
        ).order_by(
            Suggestion.up_votes.desc()
        )
        count = suggestions.count()
        if not count:
            await ctx.message.channel.send(f"I was not able to find any saved suggestions for '{channel.name}.' with the state '{state}'.")
            continue
        
        startEntry = ((page - 1) * 5) + 1
        endEntry = page * 5
        embed = Embed(
            title=f"Showing suggestions for #{channel.name}",
            description=f"Here you the '{state}' suggestions {startEntry}-{endEntry} of {count}, sorted by up votes. Taken from the #{channel} channel.",
            color=0x03C6AB
        )
        for suggestion in suggestions.paginate(page, 5):
            embed.add_field(
                name=f"[{suggestion.id}] {suggestion.summary} | **{suggestion.up_votes}x{UPVOTE}** | **{suggestion.down_votes}x{DOWNVOTE}**",
                value=f"[Jump to suggestion](https://discordapp.com/channels/{suggestion.guild_id}/{suggestion.channel_id}/{suggestion.discord_id})",
                inline=False
            )
        await ctx.message.channel.send(embed=embed)


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


@commands.command(
    brief="Update the vote counts of existing suggestions",
    help="If the bot was offline for any reason, you can run update_votes to correct the votes int the database."
)
async def update_votes(ctx):
    ctx.bot.logger.info(f"Got the 'update_votes' command from {ctx.author}.")
    await ctx.message.channel.send(f"Ok Human. I'll update all the votes, of all suggestions... *sigh*")
    for suggestion in Suggestion.filter():
        channel = ctx.guild.get_channel(int(suggestion.channel_id))
        if channel:
            message = await channel.fetch_message(suggestion.discord_id)
            up_votes = get_votes(message.reactions, UPVOTE)
            down_votes = get_votes(message.reactions, DOWNVOTE)
            if suggestion.up_votes == up_votes and suggestion.down_votes == down_votes:
                ctx.bot.logger.info(f'No change in votes for message {suggestion.discord_id}')
                continue
            suggestion.set_votes(up_votes, down_votes)
            ctx.bot.logger.info(f'Updated votes for message {suggestion.discord_id}: {up_votes}x{UPVOTE} and {down_votes}x{DOWNVOTE}')
    await ctx.message.channel.send(f"There you go. All votes should be up to date.")

async def index_channel(ctx, channel):
    ctx.bot.logger.info(f"Indexing channel '{channel}'.")
    async for message in channel.history(limit=None):
        if message.author == ctx.bot.user:
            continue

        match = ctx.bot.check.match(message.content)
        decline_reason = ctx.bot.get_decline_reason(match)
        if not decline_reason:
            ctx.bot.logger.info(f'Message from {message.author} in correct format.')
            suggestions = Suggestion.filter(Suggestion.discord_id == message.id)
            if suggestions.count():
                ctx.bot.logger.info(f'Found suggestion for message with ID {message.id}.')
                continue
            ctx.bot.logger.info(f'Creating suggestion for message with ID {message.id}.')
            summary = match.group('summary')
            up_votes = get_votes(message.reactions, UPVOTE)
            down_votes = get_votes(message.reactions, DOWNVOTE)
            suggestion = Suggestion.create(
                guild_id=ctx.guild.id,
                channel_id=channel.id,
                discord_id=message.id,
                up_votes=up_votes,
                down_votes=down_votes,
                summary=summary,
                state=STATE_NEW
            )
            ctx.bot.logger.info(f"Created suggestion {suggestion.id} for message {message.id} in channel {channel.name}.")
        
@commands.command(
    brief="Index all messages in all WATCH_CHANNELS",
    help="Index all messages in all WATCH_CHANNELS. This might take some time. All messages not already saved will be added to the database."
)
async def index_channels(ctx):
    ctx.bot.logger.info(f"Got 'index' command from {ctx.author}.")
    await ctx.message.channel.send(f"Human wants me to work, eh? This will take some time, please be patient...")
    old_count = Suggestion.select().count()
    for channel in ctx.guild.channels:
        if channel.name in ctx.bot.channels: 
            if channel:
                await index_channel(ctx, channel)
    await ctx.message.channel.send(f"Done! I had {old_count} suggestions in my DB and now I have {Suggestion.filter().count()}")


COMMANDS = [show, accept, decline, renew, index_channels, update_votes]
