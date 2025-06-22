import asyncio
import logging
from typing import AsyncIterator

from telemetry.v1 import telemetry_pb2

from .crypto import CryptoEngine
from .sensor import Sensor

logger = logging.getLogger(__name__)


async def pipeline(
    sensor: Sensor, crypto: CryptoEngine, rate: int
) -> AsyncIterator[telemetry_pb2.TelemetryRequest]:
    interval = 1.0 / rate
    while True:
        payload = crypto.encrypt(sensor.get_data().SerializeToString())
        if payload:
            yield telemetry_pb2.TelemetryRequest(payload)
        else:
            logger.error("Cipher error occurred. Skipping this telemetry message.")
        await asyncio.sleep(interval)
