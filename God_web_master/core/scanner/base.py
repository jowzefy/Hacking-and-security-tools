"""
Abstract Base Scanner
Implements Template Method Pattern and Strategy Pattern.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json


@dataclass
class ScanResult:
    """Data class for scan results."""
    target: str
    scan_type: str
    timestamp: datetime
    data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    scan_duration: float = 0.0
    
    @property
    def checksum(self) -> str:
        """Generate SHA-256 checksum of result data."""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'target': self.target,
            'scan_type': self.scan_type,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'success': self.success,
            'error_message': self.error_message,
            'scan_duration': self.scan_duration,
            'checksum': self.checksum
        }


class BaseScanner(ABC):
    """Abstract base class for all scanners."""
    
    def __init__(self, config):
        self.config = config
        self.result: Optional[ScanResult] = None
    
    @abstractmethod
    async def scan(self, target: str) -> ScanResult:
        """Execute the scan. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def validate_target(self, target: str) -> bool:
        """Validate the target before scanning."""
        pass
    
    def pre_scan_hook(self, target: str) -> None:
        """Hook executed before scanning. Override if needed."""
        pass
    
    def post_scan_hook(self, result: ScanResult) -> None:
        """Hook executed after scanning. Override if needed."""
        pass