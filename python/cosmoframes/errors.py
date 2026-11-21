"""Shared command-line error handling."""
import sys

def die(message, code=1):
    print("ERROR: " + str(message), file=sys.stderr)
    raise SystemExit(code)
