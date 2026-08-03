"""
Client system information scanner.
Implements BaseScanner interface.
"""

import platform
import getpass
import time
import asyncio
from typing import Dict, Any
from datetime import datetime
import requests
import ipapi
from colorama import Fore, Style
from .base import BaseScanner, ScanResult
from core.security.ratelimiter import RateLimiter


class ClientInfoScanner(BaseScanner):
    """Gathers OS, IP, geolocation data."""

    def __init__(self, config):
        super().__init__(config)
        self.rate_limiter = RateLimiter(max_requests=1, time_window=5)  # gentle

    async def scan(self, target: str = "localhost") -> ScanResult:
        start_time = time.time()
        try:
            self.pre_scan_hook(target)
            await self.rate_limiter.acquire()
            
            loop = asyncio.get_event_loop()
            ip = await loop.run_in_executor(None, self._get_public_ip)
            
            data = {
                "os_name": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node(),
                "username": getpass.getuser(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "timestamp": datetime.now().isoformat(),
                "public_ip": ip
            }
            
            if ip and ip != "Unable to fetch":
                try:
                    geo = await loop.run_in_executor(None, ipapi.location, ip)
                    if geo:
                        data["geo_location"] = {
                            "country": geo.get("country_name", "Unknown"),
                            "city": geo.get("city", "Unknown"),
                            "region": geo.get("region", "Unknown"),
                            "isp": geo.get("org", "Unknown")
                        }
                except:
                    data["geo_location"] = "Unavailable"
            else:
                data["geo_location"] = "N/A"
            
            self.result = ScanResult(
                target="client_system",
                scan_type="clientinfo",
                timestamp=datetime.now(),
                data=data,
                success=True,
                scan_duration=time.time() - start_time
            )
            self.post_scan_hook(self.result)
            return self.result
            
        except Exception as e:
            return ScanResult(
                target="client_system",
                scan_type="clientinfo",
                timestamp=datetime.now(),
                data={},
                success=False,
                error_message=str(e),
                scan_duration=time.time() - start_time
            )

    def _get_public_ip(self) -> str:
        try:
            return requests.get('https://api.ipify.org', timeout=self.config.security.timeout).text.strip()
        except:
            return "Unable to fetch"

    def validate_target(self, target: str) -> bool:
        return True

    def display_results(self, result: ScanResult):
        if not result.success:
            print(f"{Fore.RED}[✗] Failed: {result.error_message}{Style.RESET_ALL}")
            return
        data = result.data
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"{Fore.YELLOW}💻 System Information")
        print(f"{Fore.GREEN}{'='*60}\n")
        print(f"{Fore.CYAN}  🖥️  System:")
        print(f"{Fore.WHITE}     OS: {Fore.YELLOW}{data.get('os_name', 'N/A')} {data.get('os_version', '')}")
        print(f"{Fore.WHITE}     Hostname: {Fore.YELLOW}{data.get('hostname', 'N/A')}")
        print(f"{Fore.WHITE}     Username: {Fore.YELLOW}{data.get('username', 'N/A')}")
        print(f"{Fore.WHITE}     Architecture: {Fore.YELLOW}{data.get('architecture', 'N/A')}")
        print(f"\n{Fore.CYAN}  🌐 Network:")
        print(f"{Fore.WHITE}     Public IP: {Fore.YELLOW}{data.get('public_ip', 'N/A')}")
        geo = data.get('geo_location', {})
        if isinstance(geo, dict):
            print(f"{Fore.WHITE}     Country: {Fore.YELLOW}{geo.get('country', 'N/A')}")
            print(f"{Fore.WHITE}     City: {Fore.YELLOW}{geo.get('city', 'N/A')}")
            print(f"{Fore.WHITE}     ISP: {Fore.YELLOW}{geo.get('isp', 'N/A')}")
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")