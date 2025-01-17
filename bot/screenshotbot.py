import logging
import time
import string
import random
import asyncio
from contextlib import contextmanager
from collections import defaultdict
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import Config
from bot.workers import Worker
from bot.utils.broadcast import Broadcast
from aiohttp import web  # Importing aiohttp for the dummy server

log = logging.getLogger(__name__)

class ScreenShotBot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            plugins={
                "root": "plugins"
            },
            bot_token=Config.BOT_TOKEN
        )
        self.process_pool = Worker()
        self.CHAT_FLOOD = defaultdict(
            lambda: int(time.time()) - Config.SLOW_SPEED_DELAY - 1
        )
        self.broadcast_ids = {}
        self.app = web.Application()  # Create aiohttp application

    async def start(self):
        await super().start()
        await self.process_pool.start()
        me = await self.get_me()
        print(f"New session started for {me.first_name} (@{me.username})")

        # Set up the dummy server to keep the bot alive
        self.app.router.add_get('/', self.handle_dummy_request)
        
        # Start the aiohttp server asynchronously
        asyncio.create_task(self.run_server())

    async def stop(self):
        await self.process_pool.stop()
        await super().stop()
        print("Session stopped. Bye!!")

    async def handle_dummy_request(self, request):
        """
        This is a dummy HTTP handler to keep the bot alive.
        It simply responds with a 200 OK status.
        """
        return web.Response(text="Bot is running!")

    async def run_server(self):
        """
        Run the aiohttp server within the same event loop.
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        print("Dummy server started on port 8080")

    @contextmanager
    def track_broadcast(self, handler):
        """
        Context manager to track broadcasts and generate unique broadcast IDs.
        """
        broadcast_id = ""
        while True:
            broadcast_id = "".join(
                random.choice(string.ascii_letters) for _ in range(6)  # Increased ID length
            )
            if broadcast_id not in self.broadcast_ids:
                break

        self.broadcast_ids[broadcast_id] = handler
        try:
            yield broadcast_id
        finally:
            self.broadcast_ids.pop(broadcast_id, None)

    async def start_broadcast(self, broadcast_message, admin_id):
        """
        Method to start the broadcast asynchronously.
        """
        asyncio.create_task(self._start_broadcast(broadcast_message, admin_id))

    async def _start_broadcast(self, broadcast_message, admin_id):
        """
        Handle the broadcast sending process.
        """
        try:
            broadcast_handler = Broadcast(
                client=self, broadcast_message=broadcast_message
            )
            with self.track_broadcast(broadcast_handler) as broadcast_id:
                # Send an initial message with buttons for progress and cancellation
                reply_message = await self.send_message(
                    chat_id=admin_id,
                    text="Broadcast started. Use the buttons to check the progress or to cancel the broadcast.",
                    reply_to_message_id=broadcast_message.message_id,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text="Check Progress",
                            callback_data=f"sts_bdct+{broadcast_id}",
                        ),
                        InlineKeyboardButton(
                            text="Cancel!",
                            callback_data=f"cncl_bdct+{broadcast_id}",
                        ),
                    ]]),
                )

                # Start the broadcast process
                await broadcast_handler.start()

                # Edit the message after broadcast completion
                await reply_message.edit_text("Broadcast completed")

        except Exception as e:
            log.error(f"Error during broadcast: {e}", exc_info=True)
            # Send an error message to admin if something goes wrong
            await self.send_message(
                chat_id=admin_id,
                text="An error occurred during the broadcast. Please try again later.",
            )
