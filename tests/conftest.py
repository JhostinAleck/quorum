import pytest

from quorum.core import MemoryStore, SQLiteStore


@pytest.fixture(params=["memory", "sqlite"])
def store(request):
    """The same tests run against both backends."""
    return MemoryStore() if request.param == "memory" else SQLiteStore()
