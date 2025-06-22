import asyncio
import logging
from typing import AsyncIterator

from telemetry.v1 import telemetry_pb2

from .sensor import Sensor

logger = logging.getLogger(__name__)


async def pipeline(
    sensor: Sensor, rate: int
) -> AsyncIterator[telemetry_pb2.TelemetryRequest]:
    interval = 1.0 / rate
    while True:
        yield sensor.get_data()
        await asyncio.sleep(interval)
