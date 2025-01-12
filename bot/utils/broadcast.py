import traceback
import datetime
import logging
import asyncio
import time
import io

from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    UserIsBlocked,
    PeerIdInvalid,
)

from bot.database import Database
from bot.config import Config

log = logging.getLogger(__name__)
db = Database()


class Broadcast:
    def __init__(self, client, broadcast_message):
        self.client = client
        self.broadcast_message = broadcast_message
        self.cancelled = False
        self.progress = dict(total=0, current=0, failed=0, success=0)

    def get_progress(self) -> dict:
        """Return the current broadcast progress."""
        return self.progress

    def cancel(self):
        """Cancel the ongoing broadcast."""
        self.cancelled = True

    async def _send_msg(self, user_id: int, max_retries: int = 5) -> tuple[int, str | None]:
        """
        Send a broadcast message to a user.

        Args:
            user_id: The user ID to send the message to.
            max_retries: Maximum retries for handling FloodWait.

        Returns:
            Tuple containing the status code and an optional error message.
        """
        retries = 0
        while retries < max_retries:
            try:
                await self.broadcast_message.copy(chat_id=user_id)
                return 200, None
            except FloodWait as e:
                retries += 1
                log.warning(f"FloodWait: Retrying in {e.x + 1} seconds (Retry {retries}/{max_retries})")
                await asyncio.sleep(e.x + 1)
            except InputUserDeactivated:
                log.warning(f"User {user_id} deactivated.")
                return 400, f"{user_id} : deactivated\n"
            except UserIsBlocked:
                log.warning(f"User {user_id} blocked the bot.")
                return 400, f"{user_id} : blocked the bot\n"
            except PeerIdInvalid:
                log.warning(f"User ID {user_id} is invalid.")
                return 400, f"{user_id} : user ID invalid\n"
            except Exception as e:
                log.error(f"Unexpected error for user {user_id}: {e}", exc_info=True)
                return 500, f"{user_id} : {traceback.format_exc()}\n"
        return 500, f"{user_id} : Max retries exceeded\n"

    async def start(self):
        """Start broadcasting messages to all users."""
        all_users = await db.get_all_users()
        total_users = await db.total_users_count()

        start_time = time.time()
        done, failed, success = 0, 0, 0
        broadcast_log = io.BytesIO()
        broadcast_log.name = f"{datetime.datetime.utcnow()}_broadcast.txt"

        async for user in all_users:
            if self.cancelled:
                log.info("Broadcast cancelled by the admin.")
                break

            user_id = int(user["id"])
            sts, msg = await self._send_msg(user_id)

            if msg:
                broadcast_log.write(msg.encode())

            if sts == 200:
                success += 1
            else:
                failed += 1

            if sts == 400:  # Remove invalid users from the database
                await db.delete_user(user_id)

            done += 1
            self.progress.update(dict(current=done, failed=failed, success=success))

            if done % 100 == 0:  # Periodic progress updates
                log.info(f"Progress: {done}/{total_users} done.")
                await self.client.send_message(
                    chat_id=Config.LOG_CHANNEL,
                    text=f"Broadcast in progress: {done}/{total_users} completed.",
                )

            await asyncio.sleep(0.3)  # Slight delay to avoid rate limits

        completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
        summary = (
            f"#broadcast completed in `{completed_in}`\n\n"
            f"Total users: {total_users}\n"
            f"Total done: {done}\nSuccess: {success}, Failed: {failed}\n"
            f"Status: {'Completed' if not self.cancelled else 'Cancelled'}"
        )

        broadcast_log.seek(0)
        if failed > 0:
            await self.client.send_document(
                chat_id=Config.LOG_CHANNEL,
                document=broadcast_log,
                caption=summary,
            )
        else:
            await self.client.send_message(
                chat_id=Config.LOG_CHANNEL,
                text=summary,
            )

        broadcast_log.close()
