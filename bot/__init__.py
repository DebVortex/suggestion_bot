import sys
import os
import re

from discord.ext.commands import Bot

from database.models import Suggestion

SUMMARY_REGEX = r'.*\[(?P<summary>.*)\].*'


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

    def decline_message(self):
        ...

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
                channel_name=message.channel.name,
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
        if message.channel.type.value == 1:
            await super().on_message(message)
            return

        self.logger.info(f'Got message from {message.author} in {message.channel}')
        if message.channel.name not in self.channels:
            self.logger.info(f'Ignoring message, as its not in a channel to watch.')
            return

        match = self.check.match(message.content)
        decline_reason = self.get_decline_reason(match)
        if not decline_reason:
            self.logger.info(f'Message from {message.author} accepted.')
            self.accept_message(message, match)
            return

        orig_message = message.content
        author = message.author
        await message.delete()
        dm_channel = await author.create_dm()
        await dm_channel.send(
            self.message_template.format(
                channel=message.channel,
                max_length=self.max_length,
                orig_message=orig_message,
                reason=decline_reason
            )
        )
        self.logger.info('Message from {0.author} in {0.channel}: {0.content}'.format(message))
