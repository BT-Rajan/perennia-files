import uuid
from datetime import datetime, timezone
from typing import Optional

from .db import Database
from .models import (
    LogicalFile,
    FileVersion,
    ExtractedContent,
    Summary,
    QAResult,
    GeneratedContent,
)


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FileRepository:
    def __init__(self, db: Database):
        self._db = db

    def create(self, cur, created_by: Optional[str]) -> str:
        file_id = new_id()
        cur.execute(
            "INSERT INTO files (id, status, created_by) VALUES (%s, 'active', %s)",
            (file_id, created_by),
        )
        return file_id

    def get_by_id(self, cur, file_id: str) -> Optional[dict]:
        cur.execute("SELECT * FROM files WHERE id=%s", (file_id,))
        return cur.fetchone()

    def set_current_version(self, cur, file_id: str, version_id: str) -> None:
        cur.execute(
            "UPDATE files SET current_version_id=%s WHERE id=%s", (version_id, file_id)
        )

    def soft_delete(self, cur, file_id: str, deleted_by: Optional[str]) -> None:
        cur.execute(
            "UPDATE files SET status='deleted', deleted_at=%s, deleted_by=%s WHERE id=%s",
            (utcnow(), deleted_by, file_id),
        )

    def restore(self, cur, file_id: str) -> None:
        cur.execute(
            "UPDATE files SET status='active', deleted_at=NULL, deleted_by=NULL WHERE id=%s",
            (file_id,),
        )

    def to_model(self, row: dict) -> LogicalFile:
        return LogicalFile(
            id=row["id"],
            current_version_id=row["current_version_id"],
            status=row["status"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            deleted_at=row["deleted_at"],
            deleted_by=row["deleted_by"],
        )


class VersionRepository:
    def __init__(self, db: Database):
        self._db = db

    def next_version_number(self, cur, file_id: str) -> int:
        cur.execute(
            "SELECT COALESCE(MAX(version_number), 0) AS n FROM file_versions WHERE file_id=%s",
            (file_id,),
        )
        return cur.fetchone()["n"] + 1

    def create(
        self, cur, file_id: str, version_number: int, original_filename: str,
        extension: str, mime_type: str, size_bytes: int, checksum: str,
        storage_reference: str, encrypted: bool, created_by: Optional[str],
    ) -> str:
        version_id = new_id()
        cur.execute(
            """INSERT INTO file_versions
               (id, file_id, version_number, original_filename, extension, mime_type,
                size_bytes, checksum_algorithm, checksum, storage_reference, encrypted, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'sha256', %s, %s, %s, %s)""",
            (version_id, file_id, version_number, original_filename, extension, mime_type,
             size_bytes, checksum, storage_reference, int(encrypted), created_by),
        )
        return version_id

    def get_by_id(self, cur, version_id: str) -> Optional[dict]:
        cur.execute("SELECT * FROM file_versions WHERE id=%s", (version_id,))
        return cur.fetchone()

    def list_for_file(self, cur, file_id: str) -> list:
        cur.execute(
            "SELECT * FROM file_versions WHERE file_id=%s ORDER BY version_number ASC",
            (file_id,),
        )
        return cur.fetchall()

    def to_model(self, row: dict) -> FileVersion:
        return FileVersion(
            id=row["id"],
            file_id=row["file_id"],
            version_number=row["version_number"],
            original_filename=row["original_filename"],
            extension=row["extension"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            checksum_algorithm=row["checksum_algorithm"],
            checksum=row["checksum"],
            storage_reference=row["storage_reference"],
            encrypted=bool(row["encrypted"]),
            created_at=row["created_at"],
            created_by=row["created_by"],
        )


class ExtractedContentRepository:
    def __init__(self, db: Database):
        self._db = db

    def create(self, cur, file_id: str, version_id: str, processor: str, text: str) -> str:
        record_id = new_id()
        cur.execute(
            """INSERT INTO file_extracted_content
               (id, source_file_id, source_version_id, processor, content)
               VALUES (%s, %s, %s, %s, %s)""",
            (record_id, file_id, version_id, processor, text),
        )
        return record_id

    def get_for_version(self, cur, version_id: str) -> Optional[dict]:
        cur.execute(
            "SELECT * FROM file_extracted_content WHERE source_version_id=%s "
            "ORDER BY created_at DESC LIMIT 1",
            (version_id,),
        )
        return cur.fetchone()

    def to_model(self, row: dict) -> ExtractedContent:
        return ExtractedContent(
            id=row["id"], source_file_id=row["source_file_id"],
            source_version_id=row["source_version_id"], processor=row["processor"],
            text=row["content"], created_at=row["created_at"],
        )


class SummaryRepository:
    def __init__(self, db: Database):
        self._db = db

    def create(self, cur, file_id: str, version_id: str, processor: str, text: str) -> str:
        record_id = new_id()
        cur.execute(
            """INSERT INTO file_summaries
               (id, source_file_id, source_version_id, processor, content)
               VALUES (%s, %s, %s, %s, %s)""",
            (record_id, file_id, version_id, processor, text),
        )
        return record_id

    def to_model(self, row: dict) -> Summary:
        return Summary(
            id=row["id"], source_file_id=row["source_file_id"],
            source_version_id=row["source_version_id"], processor=row["processor"],
            text=row["content"], created_at=row["created_at"],
        )


class QARepository:
    def __init__(self, db: Database):
        self._db = db

    def create(self, cur, file_id: str, version_id: str, processor: str,
               question: str, answer: str) -> str:
        record_id = new_id()
        cur.execute(
            """INSERT INTO file_qa_results
               (id, source_file_id, source_version_id, processor, question, answer)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (record_id, file_id, version_id, processor, question, answer),
        )
        return record_id

    def to_model(self, row: dict) -> QAResult:
        return QAResult(
            id=row["id"], source_file_id=row["source_file_id"],
            source_version_id=row["source_version_id"], processor=row["processor"],
            question=row["question"], answer=row["answer"], created_at=row["created_at"],
        )


class GeneratedContentRepository:
    def __init__(self, db: Database):
        self._db = db

    def create(self, cur, file_id: str, version_id: str, processor: str,
               instruction: str, text: str) -> str:
        record_id = new_id()
        cur.execute(
            """INSERT INTO file_generated_content
               (id, source_file_id, source_version_id, processor, instruction, content)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (record_id, file_id, version_id, processor, instruction, text),
        )
        return record_id

    def to_model(self, row: dict) -> GeneratedContent:
        return GeneratedContent(
            id=row["id"], source_file_id=row["source_file_id"],
            source_version_id=row["source_version_id"], processor=row["processor"],
            instruction=row["instruction"], text=row["content"], created_at=row["created_at"],
        )
