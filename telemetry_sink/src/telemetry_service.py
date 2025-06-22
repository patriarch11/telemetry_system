from typing import AsyncIterator

import grpc.aio
from telemetry.v1 import telemetry_pb2, telemetry_pb2_grpc


class TelemetryService(telemetry_pb2_grpc.TelemetryServiceServicer):
    def StreamTelemetry(
        self,
        request_iterator: AsyncIterator[telemetry_pb2.TelemetryRequest],
        context: grpc.aio.ServicerContext[
            telemetry_pb2.TelemetryRequest, telemetry_pb2.TelemetryResponse
        ],
    ) -> AsyncIterator[telemetry_pb2.TelemetryResponse]: ...
