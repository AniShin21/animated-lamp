import logging

from .screenshotbot import ScreenShotBot
from .config import Config

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if Config.DEBUG else logging.INFO,
    )
    logging.getLogger("pyrogram").setLevel(
        logging.DEBUG if Config.DEBUG else logging.WARNING
    )

    # Initialize and run the bot
    try:
        bot = ScreenShotBot()
        bot.run()
    except Exception as e:
        logging.error(f"Failed to start the bot: {e}", exc_info=True)
