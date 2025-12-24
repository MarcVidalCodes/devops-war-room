"""UI formatting utilities for demo scripts."""

import sys


def print_header(text):
    """Print a major section header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70 + "\n")


def print_section(text):
    """Print a subsection header."""
    print("\n" + "-" * 70)
    print(text)
    print("-" * 70 + "\n")


def print_check(text):
    """Print a check item."""
    print(f"  {text}")


def print_success(text):
    """Print success message."""
    print(f"  * {text}")


def print_error(text):
    """Print error message."""
    print(f"  ERROR: {text}", file=sys.stderr)


def print_warning(text):
    """Print warning message."""
    print(f"  WARNING: {text}")


def print_progress(current, total, prefix="Progress"):
    """Print a simple progress indicator."""
    pct = int(current / total * 100)
    bar_len = 40
    filled = int(bar_len * current / total)
    bar = "#" * filled + "-" * (bar_len - filled)
    print(f"\r  {prefix}: [{bar}] {pct}% ({current}/{total}s)", end="", flush=True)
    if current >= total:
        print()
