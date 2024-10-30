#!/usr/bin/env python3

import time
import json
import sys
import threading
from zeroconf import ServiceBrowser, Zeroconf
from threading import Lock
from halo import Halo
from colorama import init, Fore, Style
import argparse

# Initialize colorama
init(autoreset=True)

def decode_properties(properties):
    """
    Recursively decode byte strings in the properties dictionary to UTF-8 strings.
    """
    decoded = {}
    for key, value in properties.items():
        if isinstance(key, bytes):
            key = key.decode('utf-8', errors='ignore')
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='ignore')
        elif isinstance(value, list):
            # Decode each item in the list if it's bytes
            value = [item.decode('utf-8', errors='ignore') if isinstance(item, bytes) else item for item in value]
        decoded[key] = value
    return decoded

class MyListener:
    def __init__(self):
        self.services = []
        self.lock = Lock()
        self.seen_services = set()

    def remove_service(self, zeroconf, type, name):
        with self.lock:
            self.services = [s for s in self.services if s['name'] != name]
            self.seen_services.discard(name)
        print(f"{Fore.RED}{Style.BRIGHT}Service Removed: {name}{Style.RESET_ALL}")

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            ipv4_address = '.'.join(map(str, info.addresses[0]))
            properties = decode_properties(info.properties)
            service_info = {
                'name': name,
                'type': type,
                'address': ipv4_address,
                'port': info.port,
                'properties': properties
            }
            with self.lock:
                if name not in self.seen_services:
                    self.services.append(service_info)
                    self.seen_services.add(name)
            print(f"{Fore.GREEN}{Style.BRIGHT}Service Added:{Style.RESET_ALL}\n{json.dumps(service_info, indent=2)}\n")

    def update_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            ipv4_address = '.'.join(map(str, info.addresses[0]))
            properties = decode_properties(info.properties)
            service_info = {
                'name': name,
                'type': type,
                'address': ipv4_address,
                'port': info.port,
                'properties': properties
            }
            with self.lock:
                for svc in self.services:
                    if svc['name'] == name:
                        svc.update(service_info)
                        break
            print(f"{Fore.YELLOW}{Style.BRIGHT}Service Updated:{Style.RESET_ALL}\n{json.dumps(service_info, indent=2)}\n")

def display_countdown(duration, spinner):
    """
    Displays a countdown timer with a spinner.
    """
    for remaining in range(duration, 0, -1):
        spinner.text = f"Discovery ends in {remaining} seconds..."
        time.sleep(1)
    spinner.stop()
    print(f"{Fore.CYAN}{Style.BRIGHT}Discovery complete!{Style.RESET_ALL}")

def perform_scan(discovery_time=30, output_file='discovered_services.json'):
    """
    Perform service discovery for LED strips and return the discovered services.

    Parameters:
    - discovery_time: Duration in seconds to run the discovery.
    - output_file: Path to save the discovered services as JSON.

    Returns:
    - List of discovered services.
    """
    zeroconf = Zeroconf()
    listener = MyListener()
    service_type = "_wled._tcp.local."
    browser = ServiceBrowser(zeroconf, service_type, listener)

    # Initialize the spinner
    spinner = Halo(text="Starting discovery...", spinner="dots")
    spinner.start()

    try:
        # Start the countdown in a separate thread
        countdown_thread = threading.Thread(target=display_countdown, args=(discovery_time, spinner))
        countdown_thread.start()

        # Wait for the countdown to finish
        countdown_thread.join()
    except KeyboardInterrupt:
        spinner.stop()
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Discovery interrupted by user.{Style.RESET_ALL}")
    finally:
        zeroconf.close()
        # Prepare JSON output
        with listener.lock:
            output = {
                'discovered_services': listener.services
            }
        try:
            json_output = json.dumps(output, indent=2)
            print(f"\n{Fore.BLUE}{Style.BRIGHT}Final JSON Output:{Style.RESET_ALL}")
            print(json_output)
            # Save to file
            with open(output_file, 'w') as f:
                f.write(json_output)
            print(f"\n{Fore.GREEN}{Style.BRIGHT}JSON output saved to '{output_file}'{Style.RESET_ALL}")
        except TypeError as e:
            print(f"\n{Fore.RED}{Style.BRIGHT}Error serializing to JSON: {e}{Style.RESET_ALL}")

    return listener.services

def main():
    parser = argparse.ArgumentParser(description="Zeroconf Service Discovery Script with Enhanced UI")
    parser.add_argument('--duration', type=int, default=30, help='Discovery duration in seconds')
    parser.add_argument('--output', type=str, default='discovered_services.json', help='Output JSON file')
    args = parser.parse_args()

    perform_scan(args.duration, args.output)

if __name__ == "__main__":
    main()
