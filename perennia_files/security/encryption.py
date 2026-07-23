import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..exceptions import EncryptionError

_NONCE_SIZE = 12  # 96-bit nonce, standard for GCM


def _derive_key(signing_secret: str) -> bytes:
    """Derives a 256-bit key from the configured secret. Key never logged or stored."""
    if not signing_secret:
        raise EncryptionError("Encryption key material is not configured.")
    return hashlib.sha256(signing_secret.encode("utf-8")).digest()


def encrypt(plaintext: bytes, signing_secret: str) -> bytes:
    """Returns nonce || ciphertext(with GCM tag). Authenticated encryption only."""
    try:
        key = _derive_key(signing_secret)
        aesgcm = AESGCM(key)
        nonce = os.urandom(_NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext
    except EncryptionError:
        raise
    except Exception as exc:
        raise EncryptionError("Failed to encrypt file content.") from exc


def decrypt(blob: bytes, signing_secret: str) -> bytes:
    if len(blob) < _NONCE_SIZE:
        raise EncryptionError("Encrypted payload is malformed.")
    try:
        key = _derive_key(signing_secret)
        aesgcm = AESGCM(key)
        nonce, ciphertext = blob[:_NONCE_SIZE], blob[_NONCE_SIZE:]
        return aesgcm.decrypt(nonce, ciphertext, None)
    except EncryptionError:
        raise
    except Exception as exc:
        raise EncryptionError("Failed to decrypt file content.") from exc
