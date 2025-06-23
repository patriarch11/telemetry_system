import logging

import grpc
import grpc.aio
from telemetry.v1 import telemetry_pb2_grpc

from .telemetry_service import TelemetryService

logger = logging.getLogger(__name__)


class Server:
    def __init__(
        self,
        service: TelemetryService,
        bind_address: str,
        credentials: grpc.ServerCredentials | None,
    ):
        self._telemetry_service = service
        self._bind_address = bind_address
        self._credentials = credentials
        self._server: grpc.aio.Server = grpc.aio.server()  # type:ignore

        telemetry_pb2_grpc.add_TelemetryServiceServicer_to_server(
            self._telemetry_service, self._server
        )

        if self._credentials:
            self._server.add_secure_port(self._bind_address, self._credentials)
            logger.info(f"Server configured to listen securely on {self._bind_address}")
        else:
            self._server.add_insecure_port(self._bind_address)
            logger.info(
                f"Server configured to listen insecurely on {self._bind_address}"
            )

    async def start(self):
        logger.info("Starting gRPC server...")
        await self._server.start()
        logger.info("gRPC server started.")
        await self._server.wait_for_termination()
        logger.info("gRPC server has been terminated.")

    async def stop(self):
        logger.info("Stopping gRPC server gracefully...")
        await self._server.stop(grace=1)
        logger.info("gRPC server stopped.")
