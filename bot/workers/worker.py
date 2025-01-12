import asyncio
import logging
from collections import defaultdict
from contextlib import asynccontextmanager

from async_timeout import timeout

from bot.config import Config

logger = logging.getLogger(__name__)


class TooMuchProcess(Exception):
    """Custom exception raised when a user exceeds the allowed process limit."""
    pass


class Worker:
    def __init__(self):
        self.worker_count = Config.WORKER_COUNT
        self.user_process_count = defaultdict(lambda: 0)
        self.queue = asyncio.Queue()

    async def start(self):
        """Start the worker tasks."""
        for _ in range(self.worker_count):
            asyncio.create_task(self._worker())
        logger.debug("Started %d workers", self.worker_count)

    async def stop(self):
        """Stop all workers gracefully."""
        logger.debug("Stopping workers")
        for _ in range(self.worker_count):
            self.new_task(None)  # Send sentinel to signal workers to stop
        await self.queue.join()
        logger.debug("All workers have stopped")

    def new_task(self, task):
        """Add a new task to the queue."""
        self.queue.put_nowait(task)

    @asynccontextmanager
    async def count_user_process(self, chat_id):
        """
        Context manager to track the number of processes per user.
        Raises TooMuchProcess if the limit is exceeded.
        """
        if self.user_process_count[chat_id] >= Config.MAX_PROCESSES_PER_USER:
            raise TooMuchProcess

        self.user_process_count[chat_id] += 1
        try:
            yield
        finally:
            self.user_process_count[chat_id] -= 1

    async def _worker(self):
        """Worker task that processes items from the queue."""
        while True:
            task = await self.queue.get()
            try:
                if task is None:
                    break  # Sentinel received; exit the worker loop

                chat_id, process_factory = task
                handler = process_factory.get_handler()

                try:
                    async with self.count_user_process(chat_id), timeout(Config.TIMEOUT):
                        await handler.process()
                except asyncio.TimeoutError:
                    logger.warning("Process timed out for chat_id: %s", chat_id)
                    await handler.cancelled()
                except asyncio.CancelledError:
                    logger.warning("Process cancelled for chat_id: %s", chat_id)
                    await handler.cancelled()
                except TooMuchProcess:
                    logger.info(
                        "Too many processes for chat_id: %s, retrying after delay",
                        chat_id,
                    )
                    await asyncio.sleep(10)  # Retry after a delay
                    self.new_task((chat_id, process_factory))

            except Exception as e:
                logger.error("Error in worker: %s", e, exc_info=True)
            finally:
                self.queue.task_done()
