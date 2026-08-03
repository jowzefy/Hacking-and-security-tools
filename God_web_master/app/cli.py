"""
CLI handler for command-line arguments.
"""

import argparse
import sys
import asyncio
import json
import time
from .config import AppConfig
from core.scanner.webtech import WebTechScanner
from core.scanner.clientinfo import ClientInfoScanner
from utils.validators import URLValidator
from utils.formatters import ReportFormatter
from utils.progress import ProgressTracker


def handle_cli(config: AppConfig):
    parser = argparse.ArgumentParser(
        description="God Web Master - Professional Web Scanner"
    )
    parser.add_argument('--url', '-u', help='Target URL for web technology scan')
    parser.add_argument('--mode', '-m', choices=['webtech', 'clientinfo', 'both'], 
                        default='webtech', help='Scan mode')
    parser.add_argument('--output', '-o', help='Output file name (saved in output/ folder)')
    parser.add_argument('--format', '-f', choices=['json', 'html', 'csv'], 
                        default='json', help='Report format')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress progress output')
    
    args = parser.parse_args()
    
    if args.mode == 'clientinfo':
        scanner = ClientInfoScanner(config)
        result = asyncio.run(scanner.scan("localhost"))
        if not args.quiet:
            scanner.display_results(result)
        if args.output:
            formatter = ReportFormatter(config)
            formatter.save(result, args.output, args.format)
        return
    
    if not args.url:
        parser.error("URL is required for webtech/both modes")
    
    validator = URLValidator()
    if not validator.is_valid(args.url):
        print(f"❌ Invalid URL: {args.url}")
        sys.exit(1)
    
    if args.mode in ('webtech', 'both'):
        scanner = WebTechScanner(config)
        progress = ProgressTracker() if not args.quiet else None
        if progress:
            progress.start("Scanning web technologies...")
        result = asyncio.run(scanner.scan(args.url))
        if progress:
            progress.stop()
        if not args.quiet:
            scanner.display_results(result)
        
        if args.mode == 'both':
            client_scanner = ClientInfoScanner(config)
            sys_result = asyncio.run(client_scanner.scan("localhost"))
            combined = {
                "web_technologies": result.data.get('technologies', {}),
                "system_information": sys_result.data,
                "report_date": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            formatter = ReportFormatter(config)
            formatter.save_dict(combined, args.output or f"comprehensive_report_{int(time.time())}.json", args.format)
        else:
            if args.output:
                formatter = ReportFormatter(config)
                formatter.save(result, args.output, args.format)