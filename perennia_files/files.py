from typing import Optional, List

from .config import FilesConfig
from .db import Database
from .storage.local import LocalStorage
from .security import checksum, encryption
from .security.validation import validate_upload, guess_mime_type
from .repositories import (
    FileRepository,
    VersionRepository,
    ExtractedContentRepository,
    SummaryRepository,
    QARepository,
    GeneratedContentRepository,
)
from .models import LogicalFile, FileVersion, Summary, QAResult, GeneratedContent
from .ai import extraction as ai_extraction
from .ai import ocr as ai_ocr
from .ai import summarisation as ai_summarisation
from .ai import question_answering as ai_qa
from .ai import generation as ai_generation
from .exceptions import (
    FileNotFoundError,
    FileAccessDeniedError,
    AIUnavailableError,
    ChecksumMismatchError,
)

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


class PerenniaFiles:
    """Public API. Small, predictable surface.

    access: optional perennia-access PerenniaAccess instance (or any object
    exposing .require(identity, permission_code)). When provided, each
    operation enforces the matching file.* permission before acting.
    perennia-files never maintains its own RBAC.
    """

    def __init__(self, config: FilesConfig, access: Optional[object] = None):
        self._config = config
        self._db = Database(config.database)
        self._storage = LocalStorage(config.storage_path)
        self._access = access

        self._files = FileRepository(self._db)
        self._versions = VersionRepository(self._db)
        self._extracted = ExtractedContentRepository(self._db)
        self._summaries = SummaryRepository(self._db)
        self._qa = QARepository(self._db)
        self._generated = GeneratedContentRepository(self._db)

    # ------------------------------------------------------------- internal

    def _authorize(self, identity, permission_code: str) -> None:
        if self._access is not None:
            self._access.require(identity, permission_code)

    def _store_bytes(self, data: bytes) -> tuple:
        """Returns (storage_reference, encrypted_flag) after optional encryption."""
        reference = self._storage.generate_reference()
        if self._config.encryption_enabled:
            payload = encryption.encrypt(data, self._config.signing_secret)
            self._storage.write(reference, payload)
            return reference, True
        self._storage.write(reference, data)
        return reference, False

    def _load_bytes(self, storage_reference: str, encrypted: bool) -> bytes:
        raw = self._storage.read(storage_reference)
        if encrypted:
            return encryption.decrypt(raw, self._config.signing_secret)
        return raw

    def _require_active_file(self, cur, file_id: str) -> dict:
        row = self._files.get_by_id(cur, file_id)
        if not row or row["status"] != "active":
            raise FileNotFoundError(f"File '{file_id}' was not found.")
        return row

    # --------------------------------------------------------------- upload

    def upload(self, filename: str, data: bytes,
               identity=None, created_by: Optional[str] = None) -> LogicalFile:
        self._authorize(identity, "file.upload")
        ext = validate_upload(filename, data, self._config)
        digest = checksum.sha256_bytes(data)
        reference, encrypted = self._store_bytes(data)
        mime_type = guess_mime_type(ext)

        with self._db.transaction() as cur:
            file_id = self._files.create(cur, created_by)
            version_id = self._versions.create(
                cur, file_id, 1, filename, ext, mime_type, len(data),
                digest, reference, encrypted, created_by,
            )
            self._files.set_current_version(cur, file_id, version_id)
            row = self._files.get_by_id(cur, file_id)
        return self._files.to_model(row)

    def create_version(self, file_id: str, filename: str, data: bytes,
                        identity=None, created_by: Optional[str] = None) -> FileVersion:
        self._authorize(identity, "file.create_version")
        ext = validate_upload(filename, data, self._config)
        digest = checksum.sha256_bytes(data)
        reference, encrypted = self._store_bytes(data)
        mime_type = guess_mime_type(ext)

        with self._db.transaction() as cur:
            self._require_active_file(cur, file_id)
            version_number = self._versions.next_version_number(cur, file_id)
            version_id = self._versions.create(
                cur, file_id, version_number, filename, ext, mime_type, len(data),
                digest, reference, encrypted, created_by,
            )
            self._files.set_current_version(cur, file_id, version_id)
            version_row = self._versions.get_by_id(cur, version_id)
        return self._versions.to_model(version_row)

    # ------------------------------------------------------------- download

    def download(self, file_id: str, identity=None,
                 version_id: Optional[str] = None) -> tuple:
        """Returns (FileVersion, raw_bytes) for the current or a specific version."""
        self._authorize(identity, "file.download")
        with self._db.cursor() as cur:
            file_row = self._require_active_file(cur, file_id)
            target_version_id = version_id or file_row["current_version_id"]
            if not target_version_id:
                raise FileNotFoundError(f"File '{file_id}' has no stored version.")
            version_row = self._versions.get_by_id(cur, target_version_id)
            if not version_row or version_row["file_id"] != file_id:
                raise FileNotFoundError(f"Version '{target_version_id}' was not found.")

        data = self._load_bytes(version_row["storage_reference"], bool(version_row["encrypted"]))
        checksum.verify(data, version_row["checksum"])
        return self._versions.to_model(version_row), data

    # -------------------------------------------------------------- lookup

    def get_metadata(self, file_id: str, identity=None) -> LogicalFile:
        self._authorize(identity, "file.view")
        with self._db.cursor() as cur:
            row = self._require_active_file(cur, file_id)
        return self._files.to_model(row)

    def list_versions(self, file_id: str, identity=None) -> List[FileVersion]:
        self._authorize(identity, "file.view")
        with self._db.cursor() as cur:
            self._require_active_file(cur, file_id)
            rows = self._versions.list_for_file(cur, file_id)
        return [self._versions.to_model(r) for r in rows]

    # ------------------------------------------------------------ lifecycle

    def delete(self, file_id: str, identity=None, deleted_by: Optional[str] = None) -> None:
        self._authorize(identity, "file.delete")
        with self._db.transaction() as cur:
            self._require_active_file(cur, file_id)
            self._files.soft_delete(cur, file_id, deleted_by)

    def restore(self, file_id: str, identity=None) -> LogicalFile:
        self._authorize(identity, "file.restore")
        with self._db.transaction() as cur:
            row = self._files.get_by_id(cur, file_id)
            if not row:
                raise FileNotFoundError(f"File '{file_id}' was not found.")
            self._files.restore(cur, file_id)
            row = self._files.get_by_id(cur, file_id)
        return self._files.to_model(row)

    # -------------------------------------------------------------------- ai

    def _require_ai(self):
        if not self._config.ai_enabled or self._config.ai_provider is None:
            raise AIUnavailableError("AI capabilities are not enabled for this configuration.")
        return self._config.ai_provider

    def extract_text(self, file_id: str, identity=None,
                      version_id: Optional[str] = None) -> str:
        self._authorize(identity, "file.process")
        provider = self._require_ai()
        version, data = self.download(file_id, identity=identity, version_id=version_id)
        if version.extension in _IMAGE_EXTENSIONS:
            text = ai_ocr.ocr(provider, data, version.mime_type)
            processor = "ocr"
        else:
            text = ai_extraction.extract_text(provider, data, version.mime_type)
            processor = "extraction"
        with self._db.transaction() as cur:
            self._extracted.create(cur, file_id, version.id, processor, text)
        return text

    def summarize(self, file_id: str, identity=None,
                  version_id: Optional[str] = None) -> Summary:
        self._authorize(identity, "file.ai")
        provider = self._require_ai()
        version, _ = self.download(file_id, identity=identity, version_id=version_id)
        text = self._get_or_extract_text(file_id, version, identity)
        summary_text = ai_summarisation.summarize(provider, text)
        with self._db.transaction() as cur:
            record_id = self._summaries.create(cur, file_id, version.id, "summarizer", summary_text)
        return Summary(
            id=record_id, source_file_id=file_id, source_version_id=version.id,
            processor="summarizer", text=summary_text, created_at=None,
        )

    def ask(self, file_id: str, question: str, identity=None,
            version_id: Optional[str] = None) -> QAResult:
        self._authorize(identity, "file.ai")
        provider = self._require_ai()
        version, _ = self.download(file_id, identity=identity, version_id=version_id)
        text = self._get_or_extract_text(file_id, version, identity)
        answer = ai_qa.answer_question(provider, text, question)
        with self._db.transaction() as cur:
            record_id = self._qa.create(cur, file_id, version.id, "qa", question, answer)
        return QAResult(
            id=record_id, source_file_id=file_id, source_version_id=version.id,
            processor="qa", question=question, answer=answer, created_at=None,
        )

    def generate(self, file_id: str, instruction: str, identity=None,
                 version_id: Optional[str] = None) -> GeneratedContent:
        self._authorize(identity, "file.ai")
        provider = self._require_ai()
        version, _ = self.download(file_id, identity=identity, version_id=version_id)
        text = self._get_or_extract_text(file_id, version, identity)
        generated_text = ai_generation.generate(provider, text, instruction)
        with self._db.transaction() as cur:
            record_id = self._generated.create(
                cur, file_id, version.id, "generator", instruction, generated_text
            )
        return GeneratedContent(
            id=record_id, source_file_id=file_id, source_version_id=version.id,
            processor="generator", instruction=instruction, text=generated_text, created_at=None,
        )

    def _get_or_extract_text(self, file_id: str, version: FileVersion, identity) -> str:
        """Reuses extracted content only if it belongs to this exact version."""
        with self._db.cursor() as cur:
            existing = self._extracted.get_for_version(cur, version.id)
        if existing:
            return existing["content"]
        return self.extract_text(file_id, identity=identity, version_id=version.id)
