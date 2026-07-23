# perennia-files

Secure file storage, versioning, and optional AI processing for Perennia applications.

## Install

```
pip install perennia-files
pip install perennia-files[ai]   # optional: local PDF/DOCX text extraction
```

## Usage

```python
from perennia_files import PerenniaFiles, FilesConfig, DatabaseConfig

config = FilesConfig(
    storage_path="/var/lib/myapp/files",
    signing_secret=os.environ["FILES_SIGNING_SECRET"],
    database=DatabaseConfig(host="localhost", user="app", password="...", database="myapp"),
    max_upload_size=50 * 1024 * 1024,
    encryption_enabled=True,
    ai_enabled=False,
)

files = PerenniaFiles(config)

logical_file = files.upload("contract.pdf", data, created_by=subject_id)
version, data = files.download(logical_file.id)
files.create_version(logical_file.id, "contract-v2.pdf", new_data, created_by=subject_id)
files.delete(logical_file.id, deleted_by=subject_id)
files.restore(logical_file.id)
```

## Authorization

Pass a `perennia-access` `PerenniaAccess` instance (or anything exposing
`.require(identity, permission_code)`) as `access=` to enforce permissions:
`file.upload`, `file.view`, `file.download`, `file.create_version`,
`file.delete`, `file.restore`, `file.process`, `file.ai`.

## AI (optional)

```python
config = FilesConfig(..., ai_enabled=True, ai_provider=MyAIProvider())
files.summarize(file_id)
files.ask(file_id, "What is the termination clause?")
files.generate(file_id, "Write a client-friendly summary")
```

`ai_provider` must implement `perennia_files.AIProvider` (`extract_text`,
`ocr`, `summarize`, `answer_question`, `generate`). A reference
extraction-only implementation (`perennia_files.ai.local_provider.LocalDocumentProvider`)
covers PDF/DOCX/TXT via the `ai` extra; OCR/summarisation/QA/generation
need a real model backend supplied by the application.

## Schema

Apply `perennia_files/schema.sql` to your database before use.

## Design boundaries

No auth, no RBAC, no frontend, no Docker, no dashboards. See
`perennia-auth` and `perennia-access` for those concerns.
