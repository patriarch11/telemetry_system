import argparse
import asyncio
import logging

import grpc

from .pipeline import pipeline
from .sensor import Sensor
from .transport import GrpcClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("SensorAppOrchestrator")


def create_ssl_credentials(
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


async def main():
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
    parser.add_argument("--encryption-key", help="32-byte encryption key in hex format")

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

    args = parser.parse_args()

    grpc_client = GrpcClient(args.sink_address, create_ssl_credentials(args))

    request_pipeline = pipeline(Sensor(args.name), args.rate)

    logger.info(f"Starting orchestrator for sensor '{args.name}'")
    while True:
        await grpc_client.start(request_pipeline)

        reconnect_delay = 5
        logger.info(
            f"Session ended. Attempting to reconnect in {reconnect_delay} seconds..."
        )
        await asyncio.sleep(reconnect_delay)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application shut down by user.")
    except Exception as e:
        logger.error(f"An unhandled error occurred: {e}", exc_info=True)
