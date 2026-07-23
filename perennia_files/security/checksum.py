import hashlib

from ..exceptions import ChecksumMismatchError


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_stream(chunks) -> str:
    h = hashlib.sha256()
    for chunk in chunks:
        h.update(chunk)
    return h.hexdigest()


def verify(data: bytes, expected_checksum: str) -> None:
    actual = sha256_bytes(data)
    if actual != expected_checksum:
        raise ChecksumMismatchError(
            "Stored file content does not match its recorded checksum."
        )
