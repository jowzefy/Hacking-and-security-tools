#!/usr/bin/env python3
"""
God Web Master - Professional Web Scanner
Main entry point.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import AppConfig
from app.cli import handle_cli
from app.menu import interactive_menu
from utils.logger import setup_logging


def main():
    # Load configuration
    config = AppConfig.load()
    
    # Setup professional logging
    setup_logging(
        log_dir=config.output.log_dir,
        level="INFO"
    )
    
    # Decide mode based on command-line arguments
    if len(sys.argv) > 1:
        handle_cli(config)
    else:
        try:
            interactive_menu(config)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()