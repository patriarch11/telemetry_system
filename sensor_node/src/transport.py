import asyncio
import logging
from typing import AsyncIterator, Optional

import grpc
import grpc.aio
from telemetry.v1 import telemetry_pb2, telemetry_pb2_grpc

logger = logging.getLogger(__name__)


class GrpcClient:
    def __init__(self, address: str, credentials: Optional[grpc.ChannelCredentials]):
        self._address = address
        self._credentials = credentials

    async def _run_session_on_channel(
        self,
        channel: grpc.aio.Channel,
        request_iterator: AsyncIterator[telemetry_pb2.TelemetryRequest],
    ):
        stub: telemetry_pb2_grpc.TelemetryServiceAsyncStub = (
            telemetry_pb2_grpc.TelemetryServiceStub(channel)  # type: ignore
        )

        response_iterator = stub.StreamTelemetry(request_iterator)
        async for response in response_iterator:
            logger.debug(f"Server response received: {response.status}")

    async def start(
        self, request_iterator: AsyncIterator[telemetry_pb2.TelemetryRequest]
    ):
        try:
            if self._credentials:
                logger.info(f"Establishing secure connection to {self._address}")
                async with grpc.aio.secure_channel(
                    self._address, self._credentials
                ) as channel:
                    await self._run_session_on_channel(channel, request_iterator)
            else:
                logger.info(f"Establishing insecure connection to {self._address}")
                async with grpc.aio.insecure_channel(self._address) as channel:
                    await self._run_session_on_channel(channel, request_iterator)

        except grpc.aio.AioRpcError as e:
            logger.error(f"RPC Error during session: {e.code()} - {e.details()}")
        except asyncio.CancelledError:
            logger.info("Session cancelled. Closing connection...")
            raise
        except Exception as e:
            logger.error(f"Failed to connect or run session with {self._address}: {e}")
