"""
Simple progress indicator for CLI.
"""

import sys
import threading
import time
from colorama import Fore, Style


class ProgressTracker:
    def __init__(self):
        self.running = False
        self.thread = None
        self.message = ""

    def start(self, message="Processing"):
        self.message = message
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def _animate(self):
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while self.running:
            sys.stdout.write(f"\r{Fore.CYAN}{chars[i]} {self.message}...{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(chars)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()