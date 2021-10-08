import sys
import os

from discord import Client

class SuggestionBot(Client):

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

        self.logger.debug('Loading SUBJECT_MAX_LENGTH.')
        max_length = os.getenv('SUBJECT_MAX_LENGTH')
        if not max_length:
            self.logger.warning('No SUBJECT_MAX_LENGTH defined, falling back to default.')
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


    async def on_ready(self):
        self.logger.info('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if self.user == message.author:
            return
        # check message.cannel if in correct channel
        # check message.content if correct structure

        # if WRONG structure:
        orig_message = message.content
        author = message.author
        await message.delete()
        dm_channel = await author.create_dm()
        await dm_channel.send(
            self.message_template.format(
                channel=message.channel,
                max_length=self.max_length,
                orig_message=orig_message
            )
        )
        self.logger.info('Message from {0.author} in {0.channel}: {0.content}'.format(message))
