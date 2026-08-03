"""
Helper functions for console interaction.
"""

import os
import platform
from colorama import Fore, Style


def clear_screen():
    """Clear terminal screen cross-platform."""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')


def wait_for_enter():
    """Wait for user to press Enter."""
    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")


def get_user_choice(prompt: str, valid_choices: list) -> str:
    """Get and validate user choice from menu."""
    while True:
        choice = input(prompt).strip().upper()
        if choice in valid_choices:
            return choice
        print(f"{Fore.RED}[!] Invalid choice. Please try again.{Style.RESET_ALL}")