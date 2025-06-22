import random
from datetime import datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp
from telemetry.v1 import telemetry_pb2


class Sensor:
    def __init__(self, name: str):
        self.name = name

    def get_data(self) -> telemetry_pb2.TelemetryRequest:
        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))
        return telemetry_pb2.TelemetryRequest(
            sensor_name=self.name,
            sensor_value=random.randint(0, 100),
            timestamp=ts,
        )
