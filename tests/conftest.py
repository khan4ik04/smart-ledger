import pytest

from app import db


@pytest.fixture
def conn():
    """테스트마다 새 메모리 DB. 실제 ledger.db는 건드리지 않는다."""
    c = db.connect(":memory:")
    yield c
    c.close()
