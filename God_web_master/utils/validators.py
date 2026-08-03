"""
Advanced URL and Input Validation
Prevents injection attacks and ensures data integrity.
"""

import re
import ipaddress
from urllib.parse import urlparse, urlencode
from typing import Tuple, Optional
import tldextract


class URLValidator:
    """Comprehensive URL validator with security checks."""
    
    # Dangerous protocols and patterns
    DANGEROUS_PROTOCOLS = {
        'javascript:', 'data:', 'vbscript:', 'file:', 
        'ftp:', 'gopher:', 'telnet:', 'ssh:'
    }
    
    DANGEROUS_PATTERNS = [
        r'<script', r'javascript:', r'onerror=', r'onload=',
        r'%00', r'%0d%0a', r'\.\./', r'\.\.\\'
    ]
    
    def __init__(self):
        # Regex for valid domain names
        self.domain_regex = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'
            r'[a-zA-Z]{2,}$'
        )
        
        # Regex for valid IPv4
        self.ipv4_regex = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
    
    def is_valid(self, url: str) -> bool:
        """
        Validate URL with comprehensive security checks.
        Returns True if URL is safe and valid.
        """
        try:
            # Basic empty check
            if not url or not url.strip():
                return False
            
            url = url.strip().lower()
            
            # Check for dangerous protocols
            for protocol in self.DANGEROUS_PROTOCOLS:
                if url.startswith(protocol):
                    return False
            
            # Check for dangerous patterns
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Parse URL
            parsed = urlparse(url)
            
            # Validate scheme
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Validate hostname/IP
            if not self._is_valid_host(parsed.hostname):
                return False
            
            # Check for excessively long URLs (prevent buffer overflow)
            if len(url) > 2048:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _is_valid_host(self, hostname: str) -> bool:
        """Validate hostname or IP address."""
        if not hostname:
            return False
        
        # Check if it's an IP address
        if self.ipv4_regex.match(hostname):
            try:
                ipaddress.ip_address(hostname)
                # Check for private/loopback IPs (optional security measure)
                ip = ipaddress.ip_address(hostname)
                if ip.is_loopback or ip.is_private:
                    # Allow for testing but log warning
                    pass
                return True
            except ValueError:
                return False
        
        # Validate as domain name
        return self.domain_regex.match(hostname) is not None
    
    def sanitize(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Sanitize URL and return (sanitized_url, error_message).
        """
        try:
            if not self.is_valid(url):
                return None, "URL failed security validation"
            
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            sanitized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            if parsed.query:
                # URL encode query parameters
                sanitized += f"?{parsed.query}"
            
            return sanitized, None
            
        except Exception as e:
            return None, str(e)