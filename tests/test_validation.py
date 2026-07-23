import io
import zipfile

import pytest

from perennia_files.config import FilesConfig
from perennia_files.exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    ZipValidationError,
)
from perennia_files.security.validation import validate_upload


def test_rejects_disallowed_extension(config):
    with pytest.raises(UnsupportedFileTypeError):
        validate_upload("payload.exe", b"MZ\x90\x00", config)


def test_rejects_content_mismatch_disguised_as_pdf(config):
    # Not real PDF bytes, but named .pdf
    with pytest.raises(UnsupportedFileTypeError):
        validate_upload("document.pdf", b"MZ\x90\x00this-is-an-exe", config)


def test_accepts_genuine_pdf(config):
    ext = validate_upload("contract.pdf", b"%PDF-1.4\n...", config)
    assert ext == ".pdf"


def test_rejects_oversized_file(config):
    small_config = FilesConfig(
        storage_path=config.storage_path,
        signing_secret=config.signing_secret,
        max_upload_size=10,
    )
    with pytest.raises(FileTooLargeError):
        validate_upload("notes.txt", b"x" * 100, small_config)


def test_rejects_empty_file(config):
    with pytest.raises(UnsupportedFileTypeError):
        validate_upload("notes.txt", b"", config)


def _make_zip(entries: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_zip_with_only_allowed_types_passes(config):
    data = _make_zip({"notes.txt": b"hello", "readme.txt": b"world"})
    ext = validate_upload("bundle.zip", data, config)
    assert ext == ".zip"


def test_zip_rejects_prohibited_entry(config):
    data = _make_zip({"notes.txt": b"hello", "malware.exe": b"MZ"})
    with pytest.raises(ZipValidationError):
        validate_upload("bundle.zip", data, config)


def test_zip_rejects_path_traversal(config):
    data = _make_zip({"../../etc/passwd": b"root:x:0:0"})
    with pytest.raises(ZipValidationError):
        validate_upload("bundle.zip", data, config)


def test_zip_rejects_nested_zip(config):
    inner = _make_zip({"notes.txt": b"hello"})
    data = _make_zip({"inner.zip": inner})
    with pytest.raises(ZipValidationError):
        validate_upload("bundle.zip", data, config)
