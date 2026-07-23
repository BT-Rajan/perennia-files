import shutil
import tempfile

import pytest

from perennia_files.config import FilesConfig
from perennia_files.security import checksum, encryption, validation
from perennia_files.storage.local import LocalStorage


@pytest.fixture
def storage_path():
    path = tempfile.mkdtemp(prefix="perennia-files-test-")
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def config(storage_path):
    return FilesConfig(
        storage_path=storage_path,
        signing_secret="test-secret-do-not-use-in-prod",
        encryption_enabled=True,
    )
