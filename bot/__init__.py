import sys
import os
import re

from discord.ext.commands import Bot

from database.models import Suggestion

SUMMARY_REGEX = r'.*\[(?P<summary>.*)\].*'

from .utils import get_votes, UPVOTE, DOWNVOTE


class SuggestionBot(Bot):

    def __init__(self, logger, *args, **kwargs):
        logger.debug('Start SuggestionBot.__init__')
        super().__init__(*args, **kwargs)
        self.logger = logger

        self.logger.debug('Loading DELETION_MESSAGE template.')
        message_template_path = os.getenv('DELETION_MESSAGE')
        if not message_template_path:
            self.logger.warning('No DELETION_MESSAGE defined, falling back to default.')
            message_template_path = 'deletion_message.txt'

        try:
            with open(message_template_path, 'r') as message_template_file:
                self.message_template = message_template_file.read()
            self.logger.info('Loaded DELETION_MESSAGE template.')
        except Exception as e:
            self.logger.critical(f'Could not load message_template {message_template_path}')
            self.logger.critical(f'Got following error: {e}')
            self.logger.critical(f'Exiting.')
            sys.exit(1)

        self.logger.debug('Loading SUMMARY_MAX_LENGTH.')
        max_length = os.getenv('SUMMARY_MAX_LENGTH')
        if not max_length:
            self.logger.warning('No SUMMARY_MAX_LENGTH defined, falling back to default.')
            max_length = 200
        self.logger.info(f'Setting summary max length to {max_length}')
        self.max_length = max_length

        self.logger.debug('Loading WATCH_CHANNELS.')
        channels = os.getenv('WATCH_CHANNELS')
        if not channels:
            self.logger.warning('No WATCH_CHANNELS defined, falling back to default.')
            channels = 'suggestion'
        self.logger.info(f'Setting channels to watch to {channels}')
        self.channels = channels.split(';')

        self.logger.debug('Loading SUMMARY_CHANNEL')
        self.SUMMARY_CHANNEL = os.getenv('SUMMARY_CHANNEL')
        self.logger.info(f"Set SUMMARY_CHANNEL to '{self.SUMMARY_CHANNEL}'")

        self.logger.debug('Compiling RegEx')
        self.check = re.compile(SUMMARY_REGEX)
        self.logger.info('Setup of RegEx complete.')

        self.logger.debug('Finished SuggestionBot.__init__')

    def get_decline_reason(self, match):
        if not match:
            return 'Incorrect message format.'
        summary = match.group('summary')
        if len(summary) > self.max_length:
            return 'Summary is to long.'

    async def decline_message(self, message, decline_reason):
        await message.delete()
        dm_channel = await message.author.create_dm()
        await dm_channel.send(
            self.message_template.format(
                channel=message.channel,
                max_length=self.max_length,
                orig_message=message.content,
                reason=decline_reason
            )
        )
        self.logger.info(f'Message from {message.author} in {message.channel}: {message.content}')

    async def on_raw_reaction_add(self, payload):
        await self.handle_reaction_change(payload)

    async def on_raw_reaction_remove(self, payload):
        await self.handle_reaction_change(payload)

    async def on_raw_reaction_clear(self, payload):
        await self.handle_reaction_change(payload)

    async def handle_reaction_change(self, payload):
        self.logger.info(f'Got reaction change for message {payload.message_id}')
        try:
            suggestion = Suggestion.get(Suggestion.discord_id == payload.message_id)
            channel = await self.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            up_votes = get_votes(message.reactions, UPVOTE)
            down_votes = get_votes(message.reactions, DOWNVOTE)
            if suggestion.up_votes == up_votes and suggestion.down_votes == down_votes:
                self.logger.info(f'No change in votes for message {payload.message_id}')
                return
            suggestion.set_votes(up_votes, down_votes)
            self.logger.info(f'Updated votes for message {payload.message_id}: {up_votes}x{UPVOTE} and {down_votes}x{DOWNVOTE}')
        except Suggestion.DoesNotExist:
            self.logger.info(f'Message {payload.message_id} not in database.')


    def add_command(self, command):
        if command.name != 'help':
            self.logger.info(f'Loading command: {command.name}')
        super().add_command(command)

    def accept_message(self, message, match):
        if not Suggestion.filter(discord_id=message.id).count():
            summary = match.group('summary')
            Suggestion.create(
                discord_id=message.id,
                channel_id=message.channel.id,
                guild_id=message.guild.id,
                summary=summary
            )
            self.logger.info(f'Saved message with ID {message.id} in database.')
            return
        self.logger.info(f'Message with ID {message.id} already in database.')

    async def on_ready(self):
        self.logger.info(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if self.user == message.author:
            # Do not react to messages of the bot
            return
        if message.channel.name == self.SUMMARY_CHANNEL:
            await super().on_message(message)
            return

        self.logger.info(f'Got message from {message.author} in {message.channel}')
        if message.channel.name not in self.channels:
            self.logger.info('Ignoring message, as its not in a channel to watch.')
            return

        match = self.check.match(message.content)
        decline_reason = self.get_decline_reason(match)
        if not decline_reason or message.type == 18:
            self.logger.info(f'Message from {message.author} accepted.')
            self.accept_message(message, match)
            return

        await self.decline_message(message, decline_reason)
