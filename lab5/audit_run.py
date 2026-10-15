"""audit_run.py - runs a Python program and prints its security-relevant events.

Usage: python3 audit_run.py backup_tool.py
Uses the audit hooks built into Python 3.8+ (PEP 578).
"""

import runpy
import sys

WATCH = {
    "open",
    "subprocess.Popen",
    "socket.connect",
    "socket.sendmsg",
    "os.remove",
    "os.chmod",
}


def hook(event, args):
    if event not in WATCH:
        return
    if event == "open":
        mode = str(args[1] or "r")
        if mode.startswith("r") and "+" not in mode:
            return  # skip read-only opens so writes stand out
    print(f"[audit] {event}: {args}", file=sys.stderr)


sys.addaudithook(hook)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
