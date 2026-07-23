class PerenniaFilesError(Exception):
    """Base error. Safe to show a generic message to clients."""
    code = "files_error"


class InvalidConfigurationError(PerenniaFilesError):
    code = "invalid_configuration"


class InvalidFileError(PerenniaFilesError):
    code = "invalid_file"


class UnsupportedFileTypeError(InvalidFileError):
    code = "unsupported_file_type"


class FileTooLargeError(InvalidFileError):
    code = "file_too_large"


class FileNotFoundError(PerenniaFilesError):  # noqa: A001 - intentional shadow, scoped to package
    code = "file_not_found"


class FileAccessDeniedError(PerenniaFilesError):
    code = "file_access_denied"


class StorageError(PerenniaFilesError):
    code = "storage_error"


class ChecksumMismatchError(PerenniaFilesError):
    code = "checksum_mismatch"


class EncryptionError(PerenniaFilesError):
    code = "encryption_error"


class ZipValidationError(InvalidFileError):
    code = "zip_validation_error"


class AIUnavailableError(PerenniaFilesError):
    code = "ai_unavailable"


class ProcessingError(PerenniaFilesError):
    code = "processing_error"
