"""
Interactive console menu with colored output.
"""

import sys
import asyncio
import time
from .config import AppConfig
from core.scanner.base import BaseScanner
from core.scanner.webtech import WebTechScanner
from core.scanner.clientinfo import ClientInfoScanner
from utils.helpers import clear_screen, wait_for_enter, get_user_choice
from utils.formatters import ReportFormatter
from utils.progress import ProgressTracker
from colorama import Fore, Style

BANNER = f"""
{Fore.RED} ██████╗  ██████╗ ██████╗      ██╗    ██╗███████╗██████╗     ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ 
{Fore.YELLOW}██╔════╝ ██╔═══██╗██   ██╗     ██║    ██║██╔════╝██   ██╗    ████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
{Fore.GREEN}██║  ███╗██║   ██║██    ██║    ██║ █╗ ██║█████╗  ██████╔╝    ██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝
{Fore.BLUE}██║   ██║██║   ██║██   ██╝     ██║███╗██║██╔══╝  ██   ██╗    ██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗
{Fore.MAGENTA}╚██████╔╝╚██████╔╝██████╝      ╚███╔███╔╝███████╗██████╔╝    ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║
{Fore.CYAN} ╚═════╝  ╚═════╝ ╚════╝        ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{Style.RESET_ALL}"""


def interactive_menu(config: AppConfig):
    while True:
        clear_screen()
        print(BANNER)
        print(f"{Fore.RED}🔍 Professional Web Scanner & Information Gatherer")
        print(f"{Fore.WHITE}   Developed by God_Web_Master\n")
        print(f"{Fore.YELLOW}{'─'*60}")
        print(f"{Fore.GREEN}  [1] {Fore.CYAN}# Web Technology Detection")
        print(f"{Fore.GREEN}  [2] {Fore.CYAN}# Client Information Gathering")
        print(f"{Fore.GREEN}  [3] {Fore.CYAN}# Comprehensive Report (Both)")
        print(f"{Fore.GREEN}  [4] {Fore.CYAN}# Help & About")
        print(f"{Fore.GREEN}  [5] {Fore.CYAN}# Exit")
        print(f"{Fore.YELLOW}{'─'*60}\n")
        
        choice = get_user_choice(f"{Fore.GREEN}Enter your choice [1-5]: {Style.RESET_ALL}", 
                                 ['1', '2', '3', '4', '5'])
        if choice == '1':
            _webtech_scan(config)
        elif choice == '2':
            _client_info(config)
        elif choice == '3':
            _comprehensive(config)
        elif choice == '4':
            _show_help()
        elif choice == '5':
            print(f"\n{Fore.YELLOW}👋 Goodbye!{Style.RESET_ALL}\n")
            sys.exit(0)


def _webtech_scan(config):
    clear_screen()
    print(BANNER)
    print(f"{Fore.CYAN}🌐 Web Technology Detection{Style.RESET_ALL}")
    url = input(f"{Fore.GREEN}Enter URL (or 'back'): {Style.RESET_ALL}").strip()
    if url.lower() == 'back':
        return
    scanner = WebTechScanner(config)
    progress = ProgressTracker()
    progress.start("Scanning...")
    result = asyncio.run(scanner.scan(url))
    progress.stop()
    scanner.display_results(result)
    if result.success:
        if get_user_choice("Save report? (Y/N): ", ['Y', 'N']) == 'Y':
            fname = input("Filename (Enter for auto): ").strip()
            formatter = ReportFormatter(config)
            formatter.save(result, fname if fname else None, 'json')
    wait_for_enter()


def _client_info(config):
    clear_screen()
    print(BANNER)
    print(f"{Fore.CYAN}💻 Client Information Gathering{Style.RESET_ALL}")
    if get_user_choice("Proceed? (Y/N): ", ['Y', 'N']) == 'N':
        return
    scanner = ClientInfoScanner(config)
    result = asyncio.run(scanner.scan("localhost"))
    scanner.display_results(result)
    if get_user_choice("Save report? (Y/N): ", ['Y', 'N']) == 'Y':
        fname = input("Filename (Enter for auto): ").strip()
        formatter = ReportFormatter(config)
        formatter.save(result, fname if fname else None, 'json')
    wait_for_enter()


def _comprehensive(config):
    clear_screen()
    print(BANNER)
    print(f"{Fore.CYAN}📊 Comprehensive Report{Style.RESET_ALL}")
    url = input(f"{Fore.GREEN}Enter URL: {Style.RESET_ALL}").strip()
    web_result = asyncio.run(WebTechScanner(config).scan(url))
    sys_result = asyncio.run(ClientInfoScanner(config).scan("localhost"))
    data = {
        "web_technologies": web_result.data.get('technologies', {}),
        "system_information": sys_result.data,
        "report_date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    fname = f"comprehensive_{int(time.time())}.json"
    formatter = ReportFormatter(config)
    formatter.save_dict(data, fname, 'json')
    print(f"{Fore.GREEN}[✓] Report saved{Style.RESET_ALL}")
    wait_for_enter()


def _show_help():
    clear_screen()
    print(BANNER)
    print("God Web Master v5.0\n"
          "Interactive mode: just run without arguments\n"
          "CLI mode: use --help for options")
    wait_for_enter()