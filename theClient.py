#!/usr/bin/env python3
"""
client.py

Simple interactive TCP client for testing server.py.

Usage:
    python client.py --host 127.0.0.1 --port 9000

Features:
- Attempts a connection to the server, with timeout and clear error messages.
- Interactive loop: type messages, press Enter to send.
- Type 'quit' or 'exit' to disconnect (graceful).
- Prints timestamps for each important event (good for screenshots).
"""
import argparse
import socket
from datetime import datetime
from typing import Tuple

def log(msg: str) -> None:
    print(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] {msg}")

def parse_args():
    p = argparse.ArgumentParser(description="Simple TCP client for testing server.")
    p.add_argument("--host", default="127.0.0.1", help="Server host to connect to (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=9000, help="Server port to connect to (default: 9000)")
    p.add_argument("--timeout", type=float, default=5.0, help="Connection timeout seconds (default: 5.0)")
    return p.parse_args()

def interactive_client(server: Tuple[str, int], timeout: float = 5.0) -> None:
    """Connect to server and run an interactive send/receive loop."""
    try:
        log(f"Attempting to connect to {server} ...")
        with socket.create_connection(server, timeout=timeout) as sock:
            log(f"Connected to {server}")
            sock.settimeout(None)
            while True:
                try:
                    msg = input("Enter message (type 'quit' to disconnect): ").strip()
                except (EOFError, KeyboardInterrupt):
                    log("Input interrupted, disconnecting.")
                    break
                if not msg:
                    continue
                if msg.lower() in ("quit", "exit"):
                    log("Requested disconnect.")
                    break
                try:
                    sock.sendall(msg.encode())
                except BrokenPipeError:
                    log("Server closed connection (BrokenPipe).")
                    break
                # receive reply
                try:
                    data = sock.recv(4096)
                    if not data:
                        log("Server closed connection.")
                        break
                    log("Received: " + data.decode(errors="replace").rstrip())
                except socket.timeout:
                    log("Timed out waiting for server response.")
    except ConnectionRefusedError:
        log("Connection refused: is the server running?")
    except socket.timeout:
        log("Connection attempt timed out.")
    except Exception as e:
        log(f"Unexpected error: {e}")

if __name__ == "__main__":
    args = parse_args()
    server_addr = (args.host, args.port)
    interactive_client(server_addr, timeout=args.timeout)
