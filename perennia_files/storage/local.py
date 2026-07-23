import os
import uuid

from ..exceptions import StorageError


class LocalStorage:
    """Local filesystem storage. Never uses user-supplied filenames as paths."""

    def __init__(self, storage_path: str):
        self._root = os.path.abspath(storage_path)
        try:
            os.makedirs(self._root, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"Cannot initialize storage path: {storage_path}") from exc

    def _resolve(self, storage_reference: str) -> str:
        """Resolves a storage reference to an absolute path, guaranteed to stay
        within the configured root. storage_reference is always internally
        generated (see generate_reference) — never derived from user input."""
        full_path = os.path.abspath(os.path.join(self._root, storage_reference))
        if os.path.commonpath([self._root, full_path]) != self._root:
            raise StorageError("Resolved storage path escapes the storage root.")
        return full_path

    def generate_reference(self) -> str:
        """Generates a new internal storage identifier: sharded, collision-resistant,
        entirely independent of any user-supplied filename."""
        token = uuid.uuid4().hex
        return os.path.join(token[0:2], token[2:4], token)

    def write(self, storage_reference: str, data: bytes) -> None:
        path = self._resolve(storage_reference)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp_path = f"{path}.tmp-{uuid.uuid4().hex}"
            with open(tmp_path, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, path)
        except OSError as exc:
            raise StorageError("Failed to write file to storage.") from exc

    def read(self, storage_reference: str) -> bytes:
        path = self._resolve(storage_reference)
        try:
            with open(path, "rb") as fh:
                return fh.read()
        except OSError as exc:
            raise StorageError("Failed to read file from storage.") from exc

    def delete(self, storage_reference: str) -> None:
        path = self._resolve(storage_reference)
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as exc:
            raise StorageError("Failed to remove file from storage.") from exc
