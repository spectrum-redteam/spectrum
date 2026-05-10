import subprocess
from pathlib import Path

BIN = None  # Go portscan binary removed

def scan_ports_go(target_ip, start_port=1, end_port=1024):
    if not BIN.exists():
        raise FileNotFoundError(f"Port scanner binary not found at {BIN}. Run 'make' first.")
    result = subprocess.run(
        [str(BIN), target_ip, str(int(start_port)), str(int(end_port))],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return f"Port scan error: {result.stderr.strip()}"
    return result.stdout.strip()
