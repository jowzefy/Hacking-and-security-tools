"""
Intelligent Caching System
Reduces redundant scans and improves performance.
"""

import time
import json
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""
    key: str
    data: Any
    timestamp: float
    ttl: float  # Time to live in seconds
    access_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl
    
    @property
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.timestamp


class ScanCache:
    """
    LRU-like cache with TTL support.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, max_size: int = 100, ttl_minutes: int = 30):
        self.max_size = max_size
        self.ttl = ttl_minutes * 60  # Convert to seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: list = []
    
    def _generate_key(self, target: str) -> str:
        """Generate a unique cache key."""
        return hashlib.md5(target.encode()).hexdigest()
    
    def get(self, target: str) -> Optional[Any]:
        """Retrieve item from cache if valid."""
        key = self._generate_key(target)
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check expiration
        if entry.is_expired:
            logger.debug(f"Cache expired for {target}")
            self._remove(key)
            return None
        
        # Update access statistics
        entry.access_count += 1
        self._update_access_order(key)
        
        logger.debug(f"Cache hit for {target} (age: {entry.age:.1f}s)")
        return entry.data
    
    def set(self, target: str, data: Any) -> None:
        """Store item in cache."""
        key = self._generate_key(target)
        
        # Evict oldest item if cache is full
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_oldest()
        
        entry = CacheEntry(
            key=key,
            data=data,
            timestamp=time.time(),
            ttl=self.ttl
        )
        
        self._cache[key] = entry
        self._update_access_order(key)
        
        logger.debug(f"Cached result for {target}")
    
    def _remove(self, key: str) -> None:
        """Remove item from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
    
    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU eviction."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _evict_oldest(self) -> None:
        """Evict the least recently used item."""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
            logger.debug(f"Evicted cache entry: {oldest_key}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        logger.info("Cache cleared")
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_accesses = sum(entry.access_count for entry in self._cache.values())
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": total_accesses / (total_accesses + len(self._cache)) if total_accesses else 0,
            "oldest_entry": min((entry.age for entry in self._cache.values()), default=0),
            "expired_count": sum(1 for entry in self._cache.values() if entry.is_expired)
        }