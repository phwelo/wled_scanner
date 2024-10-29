#!/usr/bin/env python3

import time
from zeroconf import ServiceBrowser, Zeroconf

class MyListener:
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            # Get the IPv4 address
            ipv4_address = '.'.join(map(str, info.addresses[0]))
            print(f"Service {name} added, IP: {ipv4_address}")

    def remove_service(self, zeroconf, type, name):
        print(f"Service {name} removed")

    def update_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            ipv4_address = '.'.join(map(str, info.addresses[0]))
            print(f"Service {name} updated, IP: {ipv4_address}")

zeroconf = Zeroconf()
listener = MyListener()
browser = ServiceBrowser(zeroconf, "_wled._tcp.local.", listener)

try:
    # Run for 30 seconds to allow discovery
    time.sleep(30)
finally:
    zeroconf.close()
