import pytest

from perennia_files.exceptions import StorageError
from perennia_files.storage.local import LocalStorage


def test_write_read_roundtrip(storage_path):
    store = LocalStorage(storage_path)
    ref = store.generate_reference()
    store.write(ref, b"file contents")
    assert store.read(ref) == b"file contents"


def test_references_are_unique(storage_path):
    store = LocalStorage(storage_path)
    refs = {store.generate_reference() for _ in range(50)}
    assert len(refs) == 50


def test_path_traversal_reference_rejected(storage_path):
    store = LocalStorage(storage_path)
    with pytest.raises(StorageError):
        store.write("../../../../etc/passwd", b"pwned")
