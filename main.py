import os

from dotenv import load_dotenv

from bot import SuggestionBot
 

if __name__ == '__main__':
    load_dotenv()
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    bot = SuggestionBot()
    bot.run(DISCORD_BOT_TOKEN)
