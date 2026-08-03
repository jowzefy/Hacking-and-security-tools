"""
Advanced Web Technology Scanner
Implements async operations, caching, and multiple detection engines.
"""

import asyncio
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import builtwith
from colorama import Fore, Style

from .base import BaseScanner, ScanResult
from core.security.ratelimiter import RateLimiter
from core.security.useragent import UserAgentRotator
from core.storage.cache import ScanCache
from utils.validators import URLValidator

logger = logging.getLogger(__name__)


class WebTechScanner(BaseScanner):
    """
    Professional web technology scanner with advanced features:
    - Async operations
    - Intelligent caching
    - Rate limiting
    - User-Agent rotation
    - Multiple detection strategies
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.url_validator = URLValidator()
        self.rate_limiter = RateLimiter(
            max_requests=config.security.rate_limit_requests,
            time_window=1.0
        )
        self.user_agent_rotator = UserAgentRotator()
        self.cache = ScanCache(ttl_minutes=30)
        
    async def scan(self, target: str) -> ScanResult:
        """Execute web technology scan asynchronously."""
        start_time = time.time()
        
        try:
            # Validate target
            if not self.validate_target(target):
                raise ValueError(f"Invalid URL: {target}")
            
            # Check cache first
            cached_result = self.cache.get(target)
            if cached_result:
                logger.info(f"Cache hit for {target}")
                return cached_result
            
            # Pre-scan hook
            self.pre_scan_hook(target)
            
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Rotate User-Agent
            headers = self.user_agent_rotator.get_random_headers()
            
            # Execute detection (simulated async)
            loop = asyncio.get_event_loop()
            technologies = await loop.run_in_executor(
                None, 
                lambda: builtwith.parse(target)
            )
            
            # Prepare result
            self.result = ScanResult(
                target=target,
                scan_type="webtech",
                timestamp=datetime.now(),
                data={"technologies": technologies} if technologies else {},
                success=True,
                scan_duration=time.time() - start_time
            )
            
            # Cache the result
            self.cache.set(target, self.result)
            
            # Post-scan hook
            self.post_scan_hook(self.result)
            
            return self.result
            
        except Exception as e:
            logger.error(f"Scan failed for {target}: {e}")
            return ScanResult(
                target=target,
                scan_type="webtech",
                timestamp=datetime.now(),
                data={},
                success=False,
                error_message=str(e),
                scan_duration=time.time() - start_time
            )
    
    def validate_target(self, target: str) -> bool:
        """Enhanced URL validation."""
        return self.url_validator.is_valid(target)
    
    def pre_scan_hook(self, target: str) -> None:
        """Log scan initiation."""
        logger.info(f"Initiating web tech scan for: {target}")
    
    def post_scan_hook(self, result: ScanResult) -> None:
        """Log scan completion."""
        if result.success:
            tech_count = sum(len(v) for v in result.data.get('technologies', {}).values())
            logger.info(f"Scan completed. Detected {tech_count} technologies")
        else:
            logger.warning(f"Scan failed: {result.error_message}")
    
    def display_results(self, result: ScanResult):
        """Display results in user-friendly format."""
        if not result.success:
            print(f"{Fore.RED}[✗] Scan failed: {result.error_message}{Style.RESET_ALL}")
            return
        
        techs = result.data.get('technologies', {})
        if not techs:
            print(f"{Fore.YELLOW}[!] No technologies detected{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"{Fore.YELLOW}🎯 Technologies detected on {Fore.WHITE}{result.target}")
        print(f"{Fore.GREEN}{'='*60}\n")
        
        for category, tech_list in techs.items():
            print(f"{Fore.CYAN}  📂 {category}:")
            for tech in tech_list:
                print(f"{Fore.WHITE}     └─ {Fore.YELLOW}{tech}")
            print()
        
        print(f"{Fore.GREEN}{'='*60}")
        print(f"{Fore.WHITE}⏱️  Duration: {result.scan_duration:.2f}s")
        print(f"{Fore.WHITE}🔒 Checksum: {result.checksum[:16]}...")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")