"""
Intelligent Rate Limiter
Prevents API abuse and respects service limits.
"""

import asyncio
import time
from collections import deque
from typing import Deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket algorithm implementation for rate limiting.
    Supports both sync and async operations.
    """
    
    def __init__(self, max_requests: int = 10, time_window: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time_window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times: Deque[float] = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """
        Acquire permission to make a request.
        Blocks if rate limit exceeded.
        """
        async with self._lock:
            current_time = time.time()
            
            # Remove old requests outside the time window
            while (self.request_times and 
                   self.request_times[0] < current_time - self.time_window):
                self.request_times.popleft()
            
            # Check if we need to wait
            if len(self.request_times) >= self.max_requests:
                sleep_time = self.request_times[0] + self.time_window - current_time
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached. Waiting {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            # Record this request
            self.request_times.append(time.time())
    
    def acquire_sync(self) -> None:
        """Synchronous version of acquire."""
        current_time = time.time()
        
        while (self.request_times and 
               self.request_times[0] < current_time - self.time_window):
            self.request_times.popleft()
        
        if len(self.request_times) >= self.max_requests:
            sleep_time = self.request_times[0] + self.time_window - current_time
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.request_times.append(time.time())
    
    @property
    def current_rate(self) -> float:
        """Calculate current request rate."""
        if not self.request_times:
            return 0.0
        current_time = time.time()
        recent_requests = sum(1 for t in self.request_times 
                            if t > current_time - self.time_window)
        return recent_requests / self.time_window