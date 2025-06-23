import json
import logging
from typing import AsyncIterator

import grpc.aio
from telemetry.v1 import telemetry_pb2, telemetry_pb2_grpc

from .buffer import Buffer
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class TelemetryService(telemetry_pb2_grpc.TelemetryServiceServicer):
    def __init__(self, buffer: Buffer, rate_limiter: RateLimiter):
        super().__init__()
        self._buffer = buffer
        self._rate_limiter = rate_limiter

    async def StreamTelemetry(
        self,
        request_iterator: AsyncIterator[telemetry_pb2.TelemetryRequest],
        context: grpc.aio.ServicerContext[
            telemetry_pb2.TelemetryRequest, telemetry_pb2.TelemetryResponse
        ],
    ) -> AsyncIterator[telemetry_pb2.TelemetryResponse]:
        peer = context.peer()
        logger.info(f"New stream connection established from: {peer}")

        try:
            async for request in request_iterator:
                message_size = request.ByteSize()

                if not await self._rate_limiter.consume(message_size):
                    logger.warning(
                        f"Rate limit exceeded for peer {peer}. "
                        f"Dropping message of size {message_size} bytes."
                    )
                    yield telemetry_pb2.TelemetryResponse(
                        status=telemetry_pb2.TelemetryResponse.Status.RATE_LIMITED
                    )
                    continue

                await self._buffer.push(
                    json.dumps(
                        {
                            "sensor_name": request.sensor_name,
                            "sensor_value": request.sensor_value,
                            "timestamp": request.timestamp.ToJsonString(),
                            "client_address": peer,
                        }
                    )
                )

                yield telemetry_pb2.TelemetryResponse(
                    status=telemetry_pb2.TelemetryResponse.Status.OK
                )
        except grpc.aio.AioRpcError as e:
            logger.error(f"Stream from {peer} terminated with RPC error: {e.details()}")
        finally:
            logger.info(f"Stream connection from {peer} closed.")
