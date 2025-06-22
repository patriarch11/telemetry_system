import logging

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

KEY_LEN = 32
NONCE_LEN = 16

logger = logging.getLogger(__name__)


class CryptoEngine:
    def __init__(self, key: bytes):
        if len(key) != KEY_LEN:
            raise ValueError("Encryption key must be 32 bytes long")
        self.key = key

    def encrypt(self, data: bytes) -> bytes | None:
        try:
            nonce = get_random_bytes(NONCE_LEN)
            cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)  # type: ignore
            cipher_data, tag = cipher.encrypt_and_digest(data)

            return nonce + tag + cipher_data
        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            return None
