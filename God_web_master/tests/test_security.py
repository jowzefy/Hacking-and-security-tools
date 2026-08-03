import pytest
from core.security.encryptor import DataEncryptor
from core.security.ratelimiter import RateLimiter
import asyncio


def test_encryption():
    enc = DataEncryptor()
    key = enc.generate_key()
    enc2 = DataEncryptor(key=key)
    original = "secret data"
    encrypted = enc2.encrypt(original)
    decrypted = enc2.decrypt(encrypted)
    assert original == decrypted

@pytest.mark.asyncio
async def test_rate_limiter():
    limiter = RateLimiter(max_requests=2, time_window=0.5)
    await limiter.acquire()
    await limiter.acquire()
    # Third acquire should wait
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    assert elapsed >= 0.5