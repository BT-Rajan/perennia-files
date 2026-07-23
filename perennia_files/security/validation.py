import os
import zipfile
import io
from typing import Optional

from ..config import FilesConfig, PROHIBITED_EXTENSIONS
from ..exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    ZipValidationError,
)

_SIGNATURES = {
    ".pdf": [b"%PDF"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".tif": [b"II*\x00", b"MM\x00*"],
    ".tiff": [b"II*\x00", b"MM\x00*"],
    ".doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
    ".zip": [b"PK\x03\x04", b"PK\x05\x06"],
    ".docx": [b"PK\x03\x04"],
    ".dwg": [b"AC"],
}
# .dxf (often ASCII), .dgn, .webp (needs offset check) handled separately below.

_CAD_NO_RELIABLE_SIGNATURE = {".dxf", ".dgn"}


def _extension_of(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def validate_size(size_bytes: int, config: FilesConfig) -> None:
    if size_bytes <= 0:
        raise UnsupportedFileTypeError("Empty file uploads are not permitted.")
    if size_bytes > config.max_upload_size:
        raise FileTooLargeError(
            f"File exceeds the maximum allowed size of {config.max_upload_size} bytes."
        )


def validate_extension(filename: str, config: FilesConfig) -> str:
    ext = _extension_of(filename)
    if not ext:
        raise UnsupportedFileTypeError("File has no extension.")
    if ext in PROHIBITED_EXTENSIONS:
        raise UnsupportedFileTypeError(f"File type '{ext}' is prohibited.")
    if ext not in config.allowed_extensions:
        raise UnsupportedFileTypeError(f"File type '{ext}' is not permitted.")
    return ext


def sniff_content(ext: str, data: bytes) -> None:
    """Verifies the binary content actually matches the claimed extension.
    Never trusts the extension or client-provided MIME type alone."""
    if ext == ".webp":
        if len(data) < 12 or data[0:4] != b"RIFF" or data[8:12] != b"WEBP":
            raise UnsupportedFileTypeError("File content does not match a valid WEBP image.")
        return
    if ext in _CAD_NO_RELIABLE_SIGNATURE:
        # DXF/DGN have no universal binary signature; rejecting outright would
        # block legitimate CAD workflows. Size/extension/allowlist checks above
        # still apply; content is otherwise opaque to this layer.
        return
    signatures = _SIGNATURES.get(ext)
    if not signatures:
        return
    if not any(data.startswith(sig) for sig in signatures):
        raise UnsupportedFileTypeError(
            f"File content does not match the expected format for '{ext}'."
        )


def guess_mime_type(ext: str) -> str:
    return {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".zip": "application/zip",
        ".dwg": "image/vnd.dwg",
        ".dxf": "image/vnd.dxf",
        ".dgn": "application/octet-stream",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")


def validate_zip_contents(data: bytes, config: FilesConfig) -> None:
    """Inspects a ZIP archive's entries without extracting to disk.
    Rejects prohibited file types, path traversal, and unsafe expansion."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ZipValidationError("File is not a valid ZIP archive.") from exc

    policy = config.zip_policy
    infolist = zf.infolist()
    if len(infolist) > policy.max_entries:
        raise ZipValidationError("ZIP archive contains too many entries.")

    total_uncompressed = 0
    for info in infolist:
        name = info.filename
        if name.startswith("/") or ".." in name.replace("\\", "/").split("/"):
            raise ZipValidationError("ZIP archive contains an unsafe path entry.")
        if os.path.isabs(name):
            raise ZipValidationError("ZIP archive contains an unsafe absolute path entry.")

        if info.is_dir():
            continue

        entry_ext = _extension_of(name)
        if entry_ext in PROHIBITED_EXTENSIONS or not entry_ext:
            raise ZipValidationError(f"ZIP archive contains a prohibited file: '{name}'.")
        if entry_ext not in config.allowed_extensions:
            raise ZipValidationError(f"ZIP archive contains a disallowed file type: '{name}'.")
        if entry_ext == ".zip":
            raise ZipValidationError("Nested ZIP archives are not permitted.")

        total_uncompressed += info.file_size
        if total_uncompressed > policy.max_uncompressed_total:
            raise ZipValidationError("ZIP archive exceeds the maximum allowed expanded size.")

        if info.compress_size > 0:
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > policy.max_compression_ratio:
                raise ZipValidationError(
                    f"ZIP archive entry '{name}' has a suspicious compression ratio."
                )


def validate_upload(filename: str, data: bytes, config: FilesConfig) -> str:
    """Runs the full validation pipeline. Returns the validated extension."""
    validate_size(len(data), config)
    ext = validate_extension(filename, config)
    sniff_content(ext, data)
    if ext == ".zip":
        validate_zip_contents(data, config)
    return ext
