"""
User-Agent rotation module.
Loads a list of user agents from a file and provides random selection.
"""

import random
import os
from typing import Dict, Optional


class UserAgentRotator:
    """Manage User-Agent strings for web requests."""

    def __init__(self, agents_file: str = "config/user_agents.txt"):
        self.agents = self._load_agents(agents_file)
        if not self.agents:
            # Fallback to a few common ones
            self.agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ]

    def _load_agents(self, filepath: str) -> list:
        if not os.path.exists(filepath):
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

    def get_random_agent(self) -> str:
        return random.choice(self.agents)

    def get_random_headers(self) -> Dict[str, str]:
        """Return headers with a random User-Agent."""
        return {
            "User-Agent": self.get_random_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }