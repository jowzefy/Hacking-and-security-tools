import pytest
from core.scanner.webtech import WebTechScanner
from app.config import AppConfig
from utils.validators import URLValidator


@pytest.fixture
def config():
    return AppConfig()

@pytest.fixture
def scanner(config):
    return WebTechScanner(config)

@pytest.mark.asyncio
async def test_valid_url(scanner):
    result = await scanner.scan("https://example.com")
    assert result.success is True

def test_url_validator():
    validator = URLValidator()
    assert validator.is_valid("https://example.com") == True
    assert validator.is_valid("javascript:alert(1)") == False