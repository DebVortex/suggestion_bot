from discord import Client

class SuggestionBot(Client):

    def __init__(self, logger, *args, **kwargs):
        logger.debug('Start SuggestionBot.__init__')
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.logger.debug('Finished SuggestionBot.__init__')

    async def on_ready(self):
        self.logger.info('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if self.user == message.author:
            return
        # check message.cannel if in correct channel
        # check message.content if correct structure

        # if WRONG structure:
        text = message.content
        author = message.author
        await message.delete()
        dm_channel = await author.create_dm()
        await dm_channel.send("Here is your message: {0}".format(text))
        self.logger.info('Message from {0.author} in {0.channel}: {0.content}'.format(message))
