import os

from dotenv import load_dotenv
from discord import Intents

from bot import SuggestionBot
from logger import BotLogger
from bot.commands import COMMANDS


if __name__ == '__main__':
    load_dotenv()
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    logger = BotLogger()
    logger.debug('Before instantiation of SuggestionBot')
    bot = SuggestionBot(logger, command_prefix="/")
    bot.logger.debug('Starting SuggestionBot bot now')
    [bot.add_command(command) for command in COMMANDS]
    bot.run(DISCORD_BOT_TOKEN)
