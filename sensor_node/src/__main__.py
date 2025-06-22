import argparse
import asyncio
import logging
import signal
from typing import AsyncIterator

import grpc
from telemetry.v1 import telemetry_pb2

from .pipeline import pipeline
from .sensor import Sensor
from .transport import GrpcClient

RECONNECT_DELAY = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("SensorAppOrchestrator")


def parse_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sensor Node Client")
    parser.add_argument(
        "--sink-address",
        default="localhost:50051",
        help="Address of the telemetry sink service",
    )
    parser.add_argument("--name", required=True, help="Unique name for this sensor")
    parser.add_argument(
        "--rate", type=int, default=1, help="Number of messages to send per second"
    )

    parser.add_argument(
        "--use-tls", action="store_true", help="Enable TLS for a secure connection"
    )
    parser.add_argument(
        "--ca-cert", help="Path to the CA certificate file for server verification"
    )
    parser.add_argument(
        "--use-mtls", action="store_true", help="Enable mutual TLS (requires --use-tls)"
    )
    parser.add_argument(
        "--client-cert", help="Path to the client certificate file (for mTLS)"
    )
    parser.add_argument(
        "--client-key", help="Path to the client private key file (for mTLS)"
    )

    return parser.parse_args()


def create_tls_credentials(
    args: argparse.Namespace,
) -> grpc.ChannelCredentials | None:
    if not args.use_tls:
        return None

    logger.info("Configuring secure TLS channel...")
    if not args.ca_cert:
        raise ValueError("--ca-cert is required for TLS to verify the server.")
    with open(args.ca_cert, "rb") as f:
        ca_cert = f.read()

    client_cert = None
    client_key = None

    if args.use_mtls:
        logger.info("mTLS is enabled. Loading client certificate and key.")
        if not (args.client_cert and args.client_key):
            raise ValueError("--client-cert and --client-key are required for mTLS.")
        with open(args.client_cert, "rb") as f:
            client_cert = f.read()
        with open(args.client_key, "rb") as f:
            client_key = f.read()

    return grpc.ssl_channel_credentials(
        root_certificates=ca_cert, private_key=client_key, certificate_chain=client_cert
    )


async def run_grpc_client(
    client: GrpcClient, request_iterator: AsyncIterator[telemetry_pb2.TelemetryRequest]
):
    while True:
        try:
            await client.start(request_iterator)
        except asyncio.CancelledError:
            logger.info("Reconnection loop stopping.")
            break
        logger.info(
            f"Session ended. Attempting to reconnect in {RECONNECT_DELAY} seconds..."
        )
        try:
            await asyncio.sleep(RECONNECT_DELAY)
        except asyncio.CancelledError:
            logger.info("Reconnection sleep cancelled. Stopping.")
            break


async def main():
    args = parse_cli_arguments()
    grpc_client = GrpcClient(args.sink_address, create_tls_credentials(args))
    request_iterator = pipeline(Sensor(args.name), args.rate)

    loop = asyncio.get_running_loop()
    main_task = loop.create_task(run_grpc_client(grpc_client, request_iterator))

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, main_task.cancel)

    try:
        await main_task
    except asyncio.CancelledError:
        logger.info("Main task was cancelled. Application is shutting down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application shut down forcefully.")
    except Exception as e:
        logger.error(f"An unhandled error occurred: {e}", exc_info=True)
