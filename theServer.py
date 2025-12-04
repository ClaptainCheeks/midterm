#!/usr/bin/env python3
"""
server.py

Simple threaded TCP echo server for testing and assignments.

Usage:
    python server.py --host 127.0.0.1 --port 9000

Features:
- Accepts multiple clients (each handled in a separate thread).
- Logs actions with timestamps for screenshots/proof.
- Graceful shutdown on Ctrl-C (SIGINT/SIGTERM).
- Basic error handling for common socket errors.
"""
import argparse
import socket
import threading
import signal
import sys
from datetime import datetime
from typing import Tuple

_shutdown = False

def log(msg: str) -> None:
    print(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] {msg}")

def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    """Per-client handler: receive data, log it, and reply (echo-like)."""
    log(f"Client connected: {addr}")
    try:
        with conn:
            # Optional: set a read timeout if you want
            conn.settimeout(None)
            while True:
                try:
                    data = conn.recv(2048)
                except ConnectionResetError:
                    log(f"Connection reset by peer: {addr}")
                    break
                if not data:
                    # No more data, client disconnected cleanly
                    log(f"Client {addr} disconnected (no data).")
                    break
                try:
                    text = data.decode(errors="replace").rstrip()
                except Exception:
                    text = "<binary data>"
                log(f"Received from {addr}: {text}")
                reply = f"Server: received '{text}'\n"
                try:
                    conn.sendall(reply.encode())
                except BrokenPipeError:
                    log(f"Broken pipe when sending to {addr}.")
                    break
    except Exception as e:
        log(f"Exception in client handler {addr}: {e}")
    finally:
        log(f"Handler finished for {addr}")

def serve(host: str, port: int, backlog: int = 5) -> None:
    """Create listening socket and accept incoming connections."""
    global _shutdown
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow quick reuse of the address after restart
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
        sock.listen(backlog)
        log(f"Listening on {host}:{port} (press Ctrl-C to stop)")
        while not _shutdown:
            try:
                sock.settimeout(1.0)  # periodically check shutdown flag
                conn, addr = sock.accept()
                t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                log(f"Error accepting connection: {e}")
    except Exception as e:
        log(f"Server error (bind/listen): {e}")
    finally:
        log("Shutting down server socket.")
        try:
            sock.close()
        except Exception:
            pass

def _signal_handler(sig, frame) -> None:
    global _shutdown
    log(f"Signal {sig} received: initiating graceful shutdown...")
    _shutdown = True

def parse_args():
    p = argparse.ArgumentParser(description="Threaded TCP echo server (for assignment).")
    p.add_argument("--host", default="127.0.0.1", help="Host/IP to bind to (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=9000, help="Port to bind to (default: 9000)")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    # Register signals for graceful shutdown
    try:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
    except Exception:
        # Some platforms may not support signal registration the same way
        pass
    serve(args.host, args.port)