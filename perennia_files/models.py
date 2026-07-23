from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class LogicalFile:
    id: str
    current_version_id: Optional[str]
    status: str  # 'active' | 'deleted'
    created_at: datetime
    created_by: Optional[str]
    deleted_at: Optional[datetime]
    deleted_by: Optional[str]


@dataclass(frozen=True)
class FileVersion:
    id: str
    file_id: str
    version_number: int
    original_filename: str
    extension: str
    mime_type: str
    size_bytes: int
    checksum_algorithm: str
    checksum: str
    storage_reference: str
    encrypted: bool
    created_at: datetime
    created_by: Optional[str]


@dataclass(frozen=True)
class ExtractedContent:
    id: str
    source_file_id: str
    source_version_id: str
    processor: str
    text: str
    created_at: datetime


@dataclass(frozen=True)
class Summary:
    id: str
    source_file_id: str
    source_version_id: str
    processor: str
    text: str
    created_at: datetime


@dataclass(frozen=True)
class QAResult:
    id: str
    source_file_id: str
    source_version_id: str
    processor: str
    question: str
    answer: str
    created_at: datetime


@dataclass(frozen=True)
class GeneratedContent:
    id: str
    source_file_id: str
    source_version_id: str
    processor: str
    instruction: str
    text: str
    created_at: datetime
