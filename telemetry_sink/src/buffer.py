import asyncio
import logging

import aiofiles

from .crypto import CryptoEngine

logger = logging.getLogger(__name__)


class Buffer:
    def __init__(
        self, size: int, flush_interval: float, log_file_path: str, crypto: CryptoEngine
    ):
        self._size = size
        self._flush_interval = flush_interval
        self._log_file_path = log_file_path
        self._crypto = crypto

        self._buffer: list[str] = []
        self._current_size = 0

        self._lock = asyncio.Lock()

    async def _flush(self) -> None:
        async with self._lock:
            if not self._buffer:
                return

            to_flush = self._buffer
            self._buffer = []
            self._current_size = 0

        logger.info(f"Flushing {len(to_flush)} messages to {self._log_file_path}")

        encrypted_messages: list[str] = []
        for msg in to_flush:
            encrypted_msg = self._crypto.encrypt(msg.encode())
            if encrypted_msg:
                encrypted_messages.append(encrypted_msg.hex())

        if not encrypted_messages:
            logger.warning("No messages to write after encryption.")
            return

        try:
            async with aiofiles.open(self._log_file_path, "a") as file:
                await file.write("\n".join(encrypted_messages) + "\n")
        except IOError as e:
            logger.error(f"Failed to write to log file {self._log_file_path}: {e}")

    async def run_periodic_flush(self):
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush()
            except asyncio.CancelledError:
                logger.info("Periodic flush task is stopping.")
                break

    async def push(self, message: str):
        async with self._lock:
            self._buffer.append(message)
            self._current_size += len(message)

        if self._current_size >= self._size:
            asyncio.create_task(self._flush())
