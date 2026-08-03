import pytest
from core.scanner.clientinfo import ClientInfoScanner
from app.config import AppConfig


@pytest.fixture
def config():
    return AppConfig()

@pytest.mark.asyncio
async def test_clientinfo(config):
    scanner = ClientInfoScanner(config)
    result = await scanner.scan()
    assert result.success
    assert "os_name" in result.data