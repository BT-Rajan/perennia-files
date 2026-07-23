from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "perennia"
    charset: str = "utf8mb4"


DEFAULT_EXTENSIONS = [
    ".pdf", ".doc", ".docx", ".txt", ".zip",
    ".dwg", ".dxf", ".dgn",
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp",
]

PROHIBITED_EXTENSIONS = {
    ".mp3", ".wav", ".mp4", ".avi", ".mov", ".mkv",
    ".exe", ".dll", ".so", ".bat", ".cmd", ".com", ".msi",
    ".py", ".js", ".php", ".sh", ".ps1", ".jar", ".apk",
    ".sql", ".rb", ".pl", ".vbs",
}


@dataclass(frozen=True)
class ZipPolicy:
    max_entries: int = 200
    max_uncompressed_total: int = 200 * 1024 * 1024
    max_compression_ratio: int = 100


@dataclass(frozen=True)
class FilesConfig:
    storage_path: str
    signing_secret: str  # used to derive encryption key material; never logged
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    max_upload_size: int = 50 * 1024 * 1024
    allowed_extensions: List[str] = field(default_factory=lambda: list(DEFAULT_EXTENSIONS))
    encryption_enabled: bool = True
    ai_enabled: bool = False
    zip_policy: ZipPolicy = field(default_factory=ZipPolicy)
    ai_provider: Optional[object] = None  # instance implementing ai.interface.AIProvider

    def __post_init__(self):
        from .exceptions import InvalidConfigurationError

        if not self.storage_path or not self.storage_path.strip():
            raise InvalidConfigurationError("storage_path is required.")
        if self.encryption_enabled and not self.signing_secret:
            raise InvalidConfigurationError(
                "signing_secret is required when encryption_enabled=True."
            )
        if self.max_upload_size <= 0:
            raise InvalidConfigurationError("max_upload_size must be positive.")
        if not self.allowed_extensions:
            raise InvalidConfigurationError("allowed_extensions must not be empty.")
        normalized = [e.lower() for e in self.allowed_extensions]
        for ext in normalized:
            if not ext.startswith("."):
                raise InvalidConfigurationError(f"Extension '{ext}' must start with '.'")
            if ext in PROHIBITED_EXTENSIONS:
                raise InvalidConfigurationError(f"Extension '{ext}' is prohibited and cannot be allowed.")
        object.__setattr__(self, "allowed_extensions", normalized)
        if self.ai_enabled and self.ai_provider is None:
            raise InvalidConfigurationError(
                "ai_provider must be supplied when ai_enabled=True."
            )
