import Client from discord

import BotLogger from logger

class SuggestionBot(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = BotLogger()

    async def on_ready(self):
        self.logger.debug('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        self.logger.debug('Message from {0.author}: {0.content}'.format(message))
