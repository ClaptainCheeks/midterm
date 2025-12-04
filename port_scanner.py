#!/usr/bin/env python3
"""
port_scanner.py - Respectful threaded port scanner for midterm assignment.

Usage examples:
    python port_scanner.py --host 127.0.0.1 --ports 1-1024 --workers 100 --delay 0.01
    python port_scanner.py --host scanme.nmap.org --ports 22,80,443

Important: This script enforces allowed targets (127.0.0.1 and scanme.nmap.org).
Do NOT use this against other hosts.
"""

import argparse
import socket
from datetime import datetime
import concurrent.futures
import time
import sys
import re

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "scanme.nmap.org"}

def log(msg: str):
    print(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] {msg}")

def parse_ports(port_spec: str):
    """Parse a port spec like '22,80,1000-1010' into a sorted list of ints."""
    ports = set()
    parts = [p.strip() for p in port_spec.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            if a < 1 or b > 65535 or a > b:
                raise ValueError(f"Invalid port range: {part}")
            ports.update(range(a, b + 1))
        else:
            n = int(part)
            if n < 1 or n > 65535:
                raise ValueError(f"Invalid port number: {n}")
            ports.add(n)
    return sorted(ports)

def scan_port(host: str, port: int, timeout: float):
    """Return (port, True/False) indicating open or closed."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            return port, (result == 0)
    except Exception as e:
        return port, False

def main():
    p = argparse.ArgumentParser(description="Threaded port scanner (allowed hosts only).")
    p.add_argument("--host", required=True, help="Target host (allowed: 127.0.0.1, scanme.nmap.org).")
    p.add_argument("--ports", required=True, help="Ports to scan, e.g. '22,80,8000-8010'.")
    p.add_argument("--workers", type=int, default=50, help="Max concurrent workers.")
    p.add_argument("--timeout", type=float, default=0.5, help="Socket timeout seconds.")
    p.add_argument("--delay", type=float, default=0.005, help="Delay (s) between submitted tasks to be polite.")
    args = p.parse_args()

    # Enforce allowed target
    if args.host not in ALLOWED_HOSTS:
        log(f"Refusing to scan {args.host}. Allowed targets: {ALLOWED_HOSTS}")
        sys.exit(1)

    try:
        ports = parse_ports(args.ports)
    except ValueError as e:
        log(f"Bad port specification: {e}")
        sys.exit(1)

    log(f"Starting scan on {args.host} ports={len(ports)} workers={args.workers}")
    start = time.time()
    open_ports = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {}
        for port in ports:
            futures[ex.submit(scan_port, args.host, port, args.timeout)] = port
            time.sleep(args.delay)
        for future in concurrent.futures.as_completed(futures):
            port, is_open = future.result()
            status = "OPEN" if is_open else "closed"
            if is_open:
                open_ports.append(port)
            log(f"Port {port}: {status}")

    duration = time.time() - start
    log(f"Scan complete in {duration:.2f}s. Open ports: {open_ports if open_ports else 'None'}")

if __name__ == "__main__":
    main()
