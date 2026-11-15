#!/usr/bin/env python3
"""
delegate-to-gemini setup - run once per machine.

  python setup.py              install the SDK, create the key file, verify everything works
  python setup.py --enter-key  same, and type/paste your API key at a hidden prompt
  python setup.py --check      only verify (no installs, no file changes)

Your API key is never passed on the command line, never printed, and never stored in this repo.
"""

from __future__ import annotations

import getpass
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE / "scripts" / "gemini.py"
KEY_FILE = pathlib.Path(
    os.environ.get("DELEGATE_TO_GEMINI_KEY_FILE")
    or pathlib.Path.home() / ".config" / "delegate-to-gemini" / "api-key.txt"
)
TEMPLATE = (
    "# Paste your Gemini API key on the line below - nothing else in this file.\n"
    "# Get a free key at https://aistudio.google.com/apikey\n"
    "# This file lives outside any repo. Never commit it or share it.\n"
)


def say(msg: str) -> None:
    print(msg, flush=True)


def lock_down(path: pathlib.Path) -> None:
    """Make the key file readable only by the current user."""
    if os.name == "nt":
        user = os.environ.get("USERNAME")
        if user:
            subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:F"],
                           capture_output=True)
    else:
        os.chmod(path, 0o600)


def has_key() -> bool:
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return True
    if not KEY_FILE.exists():
        return False
    return any(l.strip() and not l.strip().startswith("#")
               for l in KEY_FILE.read_text(encoding="utf-8-sig").splitlines())


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    args = set(sys.argv[1:])
    check_only = "--check" in args

    say("delegate-to-gemini setup\n")
    if sys.version_info < (3, 9):
        say(f"[x] Python 3.9+ is required (you have {sys.version.split()[0]}).")
        return 2
    say(f"[ok] Python {sys.version.split()[0]}")

    # 1. SDK
    try:
        import google.genai  # noqa: F401
        say("[ok] google-genai is installed")
    except ImportError:
        if check_only:
            say("[x] google-genai is missing. Run: python -m pip install -U google-genai")
            return 2
        say("[..] Installing google-genai ...")
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-U", "--user", "google-genai"])
        if r.returncode != 0:
            say("[x] pip install failed. Try: python -m pip install -U google-genai")
            return 2
        say("[ok] google-genai installed")

    # 2. Key file
    if not check_only:
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not KEY_FILE.exists():
            KEY_FILE.write_text(TEMPLATE, encoding="utf-8")
            lock_down(KEY_FILE)
            say(f"[ok] Created key file: {KEY_FILE}")
        if "--enter-key" in args:
            if not sys.stdin.isatty():
                say("[x] --enter-key needs an interactive terminal.")
                return 2
            key = getpass.getpass("Paste your Gemini API key (input is hidden): ").strip()
            if key:
                KEY_FILE.write_text(TEMPLATE + key + "\n", encoding="utf-8")
                lock_down(KEY_FILE)
                say("[ok] Key saved (only your user account can read the file)")

    if not has_key():
        say("\n[!] No API key yet. Do ONE of these, then run: python setup.py --check")
        say("    a) python setup.py --enter-key")
        say(f"    b) paste the key as the last line of: {KEY_FILE}")
        say("    c) set the GEMINI_API_KEY environment variable")
        say("    Free key: https://aistudio.google.com/apikey")
        return 0 if not check_only else 2

    # 3. Live check
    say("[..] Checking the key with one tiny Flash request ...")
    r = subprocess.run([sys.executable, str(SCRIPT), "check"])
    if r.returncode != 0:
        return r.returncode
    say(f"\nAll set. Agents call:  python \"{SCRIPT}\" ask \"your task\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
