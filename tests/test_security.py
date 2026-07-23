import pytest

from perennia_files.exceptions import ChecksumMismatchError, EncryptionError
from perennia_files.security import checksum, encryption


def test_checksum_roundtrip():
    data = b"perennia contract v1"
    digest = checksum.sha256_bytes(data)
    checksum.verify(data, digest)  # should not raise


def test_checksum_mismatch_detected():
    data = b"perennia contract v1"
    digest = checksum.sha256_bytes(data)
    with pytest.raises(ChecksumMismatchError):
        checksum.verify(data + b"tampered", digest)


def test_encryption_roundtrip():
    secret = "signing-secret"
    plaintext = b"sensitive contract text"
    blob = encryption.encrypt(plaintext, secret)
    assert blob != plaintext
    recovered = encryption.decrypt(blob, secret)
    assert recovered == plaintext


def test_decryption_fails_with_wrong_secret():
    blob = encryption.encrypt(b"top secret", "secret-a")
    with pytest.raises(EncryptionError):
        encryption.decrypt(blob, "secret-b")


def test_decryption_fails_on_tampered_ciphertext():
    blob = bytearray(encryption.encrypt(b"top secret", "secret-a"))
    blob[-1] ^= 0xFF
    with pytest.raises(EncryptionError):
        encryption.decrypt(bytes(blob), "secret-a")
