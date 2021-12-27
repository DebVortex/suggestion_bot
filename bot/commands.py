import tempfile
from csv import writer as CsvWriter
from io import StringIO


from discord import Embed
from discord.ext import commands
from discord import File

from database.models import Suggestion, STATE_NEW, STATE_ACCEPTED, STATE_DECLINED

from .utils import UPVOTE, DOWNVOTE, get_votes

POSSIBLE_STATES = {
    'new': STATE_NEW,
    'accepted': STATE_ACCEPTED,
    'declined': STATE_DECLINED
}

STATE_NAMES = {
    STATE_NEW: 'new',
    STATE_ACCEPTED: 'accepted',
    STATE_DECLINED: 'declined'
}


def sort_weighted_suggestions(msg):
    return msg.votes['total'], msg.votes['up']


async def handle_channel(ctx, channel, state, page):
    selected_state = await get_selected_state(ctx, state)
    suggestions = Suggestion.select().where(
        Suggestion.channel_id == channel.id,
      Suggestion.state == selected_state
    ).order_by(
        Suggestion.up_votes.desc()
    )
    count = suggestions.count()
    if not count:
        await ctx.message.channel.send(f"I was not able to find any saved suggestions for '{channel.name}.' with the state '{state}'.")
        return
        
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

async def get_selected_state(ctx, state):
    selected_state = POSSIBLE_STATES.get(state)
    if selected_state is None:
        ctx.bot.logger.info(f"State '{state}' is not a valid state.")
        await ctx.message.channel.send(f"I'm sorry, '{state}' is not a valid state. Please choose one of: new, accepted, declined")
        return
    return selected_state


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


async def export_channel(ctx, channel, state):
    state_id = POSSIBLE_STATES.get(state)
    query = { "channel_id": channel.id }
    if state_id:
        query['state'] = state_id
    suggestions_to_export = Suggestion.filter(**query)
    if not suggestions_to_export.count():
        ctx.bot.logger.info(f"No suggestions found for channel {channel.name} with state {state} (None = all states)")
        await ctx.message.channel.send(f"I was not able to find any saved suggestions for '{channel.name}' with the state '{state}'.")
        return
    ctx.bot.logger.info(f"Exporting {suggestions_to_export.count()} suggestions for channel {channel.name} with state {state} (None = all states)")
    with tempfile.NamedTemporaryFile(mode="w+", suffix='.csv') as csvFile:
        fieldnames = ['id', 'summary', 'state', 'up_votes', 'down_votes', 'link']
        csv_writer = CsvWriter(csvFile)
        csv_writer.writerow(fieldnames)
        for suggestion in suggestions_to_export:
            csv_writer.writerow([
                suggestion.id,
                suggestion.summary,
                STATE_NAMES[suggestion.state],
                suggestion.up_votes,
                suggestion.down_votes,
                f"https://discordapp.com/channels/{suggestion.guild_id}/{suggestion.channel_id}/{suggestion.discord_id}"
            ])
        csvFile.seek(0)
        if state:
            filename = f"{channel.name}-{state}.csv"
        else:
            filename = f"{channel.name}.csv"
        ctx.bot.logger.info(f"Sending exported suggestions for channel {channel.name} with state {state} (None = all states) to {ctx.message.author}.")
        await ctx.message.channel.send(file=File(StringIO(csvFile.read()), filename=filename))


@commands.command(
    brief="Show suggestions",
    help="Shows a list of suggestions of the specified state. State can be new, accepted or declined. If none is provided, new will be assumed."
)
async def show(ctx, state="new", page=1):
    ctx.bot.logger.info(f"Got 'show' command from {ctx.author} with state '{state}'.")
    channels = [channel for channel in ctx.guild.text_channels if channel.name in ctx.bot.channels]

    for channel in channels:
        await handle_channel(ctx, channel, state, page)
        

@commands.command(
    brief="Show suggestions for a specified channel",
    help="Shows a list of suggestions of the specified state and channel. State can be new, accepted or declined. If none is provided, new will be assumed."
)
async def show_channel(ctx, channel=None, state="new", page=1):
    if not channel:
        await ctx.message.channel.send("Please provide a channel name.")
        return
    ctx.bot.logger.info(f"Got 'show-channel' command from {ctx.author} with state '{state}' for channel '{channel}'.")

    channel_to_handle = None
    for text_channel in ctx.guild.text_channels:
        if text_channel.name == channel:
            channel_to_handle = text_channel
    if channel_to_handle:
        await handle_channel(ctx, channel_to_handle, state, page)
    else:
        await ctx.message.channel.send(f"I'm not watching the '{channel}'. Channels watched are '{ctx.bot.channels}'.")


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


@commands.command(
    brief="Export all suggestions to a CSV file",
    help="Export all suggestions to a CSV file. The file will be send to the user."
)
async def export(ctx, channel=None, state=None):
    ctx.bot.logger.info(f"Got 'export' command from {ctx.author}.")
    channels_to_handle = []
    for chn in ctx.guild.text_channels:
        if chn.name in ctx.bot.channels:
            channels_to_handle.append(chn)

    if channel:
        channels_to_handle = [chn for chn in channels_to_handle if chn.name == channel and chn.name in ctx.bot.channels]
    else:
        channels_to_handle = [chn for chn in ctx.guild.text_channels if chn.name in ctx.bot.channels]

    ctx.bot.logger.info(f"Preparing to export the following channels: {channels_to_handle}.")
    for chn in channels_to_handle:
        await export_channel(ctx, chn, state)


COMMANDS = [show, show_channel, accept, decline, renew, index_channels, update_votes, export]
