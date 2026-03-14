#!/usr/bin/env python3
"""
I/O Load Generator
==================
Continuously creates, reads, and deletes files to generate a sustained
I/O load on the file system. Designed to run as a background process
while benchmarking I/O-bound programs.

Working Principle:
  Each worker thread runs a loop:
    1. CREATE  - write a file of random size [min_size, max_size] with random content
    2. READ    - read the file back to force page cache pressure
    3. DELETE  - remove the file to avoid filling the disk

  Multiple worker threads run concurrently to scale I/O pressure.
  The generator runs until interrupted (Ctrl+C or SIGTERM).

Usage:
  # Run in background while benchmarking
  python3 io_loadgen.py --workers 4 --min-size 65536 --max-size 1048576 --dir /tmp/io_load &
  <run your benchmark>
  kill %1
"""

import argparse
import os
import random
import shutil
import signal
import string
import sys
import threading
import time
from pathlib import Path

stop_event = threading.Event()


def random_bytes(size: int) -> bytes:
    """Generate random bytes of given size."""
    return random.randbytes(size)


def worker(worker_id: int, work_dir: Path, min_size: int, max_size: int):
    """
    Single I/O worker: repeatedly write, read, delete files until stopped.
    """
    my_dir = work_dir / f"worker_{worker_id}"
    my_dir.mkdir(parents=True, exist_ok=True)
    file_counter = 0

    while not stop_event.is_set():
        path = my_dir / f"file_{file_counter}"
        size = random.randint(min_size, max_size)

        # WRITE
        data = random_bytes(size)
        try:
            path.write_bytes(data)
        except OSError:
            break

        # READ (force page cache pressure)
        try:
            _ = path.read_bytes()
        except OSError:
            pass

        # DELETE
        try:
            path.unlink()
        except OSError:
            pass

        file_counter += 1

    # cleanup
    try:
        shutil.rmtree(my_dir, ignore_errors=True)
    except Exception:
        pass


def handle_signal(sig, frame):
    stop_event.set()


def main():
    parser = argparse.ArgumentParser(
        description="Continuous I/O load generator for benchmarking purposes."
    )
    parser.add_argument("--workers",   type=int,   default=2,              help="Number of concurrent I/O worker threads (default: 2)")
    parser.add_argument("--min-size",  type=int,   default=65536,          help="Min file size in bytes (default: 64KB)")
    parser.add_argument("--max-size",  type=int,   default=1048576,        help="Max file size in bytes (default: 1MB)")
    parser.add_argument("--dir",       type=str,   default="/tmp/io_load", help="Working directory for generated files (default: /tmp/io_load)")
    parser.add_argument("--duration",  type=float, default=None,           help="Run for N seconds then stop (default: run until killed)")
    args = parser.parse_args()

    work_dir = Path(args.dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT,  handle_signal)

    print(f"Starting I/O load generator: {args.workers} workers, "
          f"{args.min_size//1024}KB–{args.max_size//1024}KB files, dir={work_dir}",
          flush=True)

    threads = []
    for i in range(args.workers):
        t = threading.Thread(target=worker, args=(i, work_dir, args.min_size, args.max_size), daemon=True)
        t.start()
        threads.append(t)

    try:
        if args.duration:
            time.sleep(args.duration)
            stop_event.set()
        else:
            while not stop_event.is_set():
                time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()

    print("Stopping I/O load generator...", flush=True)
    for t in threads:
        t.join(timeout=5)

    shutil.rmtree(work_dir, ignore_errors=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()