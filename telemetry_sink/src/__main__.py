import argparse
import asyncio
import logging
import os
import signal

import grpc
from dotenv import load_dotenv

from .buffer import Buffer
from .crypto import CryptoEngine
from .rate_limiter import RateLimiter
from .server import Server
from .telemetry_service import TelemetryService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("SinkApp")


def parse_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telemetry Sink Service")
    parser.add_argument(
        "--bind-address", default="0.0.0.0:50051", help="Bind address for the server"
    )
    parser.add_argument("--log-file", required=True, help="Path to the output log file")
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=1024 * 1024,
        help="Buffer size in bytes before flushing",
    )  # 1MB
    parser.add_argument(
        "--flush-interval",
        type=float,
        default=5.0,
        help="Buffer flush interval in seconds",
    )  # 5 seconds
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=10 * 1024 * 1024,
        help="Max input rate in bytes/sec",
    )  # 10 MB/s
    parser.add_argument(
        "--encryption-key", help="32-byte encryption key in hex format (overrides .env)"
    )

    parser.add_argument(
        "--use-tls", action="store_true", help="Enable TLS for a secure connection"
    )
    parser.add_argument("--server-cert", help="Path to the server certificate file")
    parser.add_argument("--server-key", help="Path to the server private key file")
    parser.add_argument(
        "--use-mtls", action="store_true", help="Enable mutual TLS (requires --use-tls)"
    )
    parser.add_argument(
        "--ca-cert", help="Path to the CA certificate file for client verification"
    )

    return parser.parse_args()


def create_tls_credentials(
    args: argparse.Namespace,
) -> grpc.ServerCredentials | None:
    if not args.use_tls:
        return None
    logger.info("Configuring secure TLS channel...")
    if not (args.server_cert and args.server_key):
        raise ValueError("--server-cert and --server-key are required for TLS.")
    with open(args.server_key, "rb") as f:
        private_key = f.read()
    with open(args.server_cert, "rb") as f:
        certificate_chain = f.read()

    ca_cert = None
    require_client_auth = False
    if args.use_mtls:
        logger.info("mTLS is enabled. Client certificate will be required.")
        if not args.ca_cert:
            raise ValueError("--ca-cert is required for mTLS.")
        with open(args.ca_cert, "rb") as f:
            ca_cert = f.read()
        require_client_auth = True

    return grpc.ssl_server_credentials(
        [(private_key, certificate_chain)],
        root_certificates=ca_cert,
        require_client_auth=require_client_auth,
    )


async def main():
    load_dotenv()
    args = parse_cli_arguments()

    key_hex = args.encryption_key or os.getenv("ENCRYPTION_KEY")
    if not key_hex:
        raise ValueError(
            "Encryption key must be provided via --encryption-key or ENCRYPTION_KEY in .env"
        )

    crypto_engine = CryptoEngine(bytes.fromhex(key_hex))
    ratelimiter = RateLimiter(args.rate_limit)
    buffer = Buffer(
        int(args.buffer_size),
        float(args.flush_interval),
        args.log_file,
        crypto_engine,
    )
    service = TelemetryService(buffer, ratelimiter)
    credentials = create_tls_credentials(args)
    server = Server(service, args.bind_address, credentials)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def on_shutdown_signal():
        logger.info("Shutdown signal received. Initiating graceful shutdown...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, on_shutdown_signal)

    buffer_flush_task = loop.create_task(buffer.run_periodic_flush())
    server_task = loop.create_task(server.start())

    logger.info("Application started. Press Ctrl+C to exit.")

    await stop_event.wait()

    logger.info("Starting shutdown sequence...")
    await server.stop()
    buffer_flush_task.cancel()
    await asyncio.gather(server_task, buffer_flush_task, return_exceptions=True)
    logger.info("Performing final buffer flush...")
    await buffer.flush()
    logger.info("Application shut down gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"An unhandled error occurred: {e}", exc_info=True)
