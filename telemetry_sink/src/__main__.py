import logging
import os

from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    load_dotenv()

    key_hex = os.getenv("ENCRYPTION_KEY")
    if not key_hex:
        raise ValueError("Encryption key must be provided via  ENCRYPTION_KEY env var")
