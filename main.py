import os

from dotenv import load_dotenv

from bot import SuggestionBot
from bot.logger import BotLogger


if __name__ == '__main__':
    load_dotenv()
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    logger = BotLogger()
    logger.debug('Before instantiation of SuggestionBot')
    bot = SuggestionBot(logger)
    bot.logger.debug('Starting SuggestionBot bot now')
    bot.run(DISCORD_BOT_TOKEN)
