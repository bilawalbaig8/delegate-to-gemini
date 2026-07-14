#!/usr/bin/env python3
"""
delegate-to-gemini skill installer
Asks for credentials and sets up the AI-Context bridge folder.
Run once: python setup.py
"""

import os
import sys
import pathlib
import subprocess
import platform

HOME = pathlib.Path.home()
AI_CONTEXT = HOME / "AI-Context"
TOOLS_DIR = HOME / ".claude" / "tools"
API_KEY_FILE = HOME / ".config" / "delegate-to-gemini" / "api-key.txt"


def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def check_gemini_cli():
    section("Step 1 — Gemini CLI")
    try:
        result = subprocess.run(["gemini", "--version"], capture_output=True, text=True)
        print(f"✅ Gemini CLI found: v{result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Gemini CLI not found.")
        print("\nInstall it with:")
        print("  npm install -g @google/gemini-cli")
        print("\nThen run this setup again.")
        return False


def check_gemini_login():
    section("Step 2 — Gemini CLI Login")
    print("You need to be logged into Gemini CLI with your Google account.")
    print("\nIf not logged in yet, open a terminal and run:")
    print("  gemini")
    print("Then inside Gemini CLI type: /auth")
    print("Follow the browser login flow.")
    input("\nPress Enter once you're logged in (or already are)...")

    try:
        result = subprocess.run(
            ["gemini", "Say OK in one word", "--output-format", "text"],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0:
            print("✅ Gemini CLI login verified.")
            return True
        else:
            print("⚠️  Could not verify login. Continuing anyway.")
            print("   (You can re-run setup if Gemini CLI doesn't work)")
            return True
    except Exception:
        print("⚠️  Could not verify login. Continuing anyway.")
        return True


def setup_ai_context():
    section("Step 3 — AI-Context Bridge Folder")
    folders = ["research", "ideation", "analysis", "drafts"]
    for folder in folders:
        path = AI_CONTEXT / folder
        path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created: {AI_CONTEXT}")
    print("   Subfolders: research/, ideation/, analysis/, drafts/")


def setup_api_key():
    section("Step 4 — Gemini API Key (Image & Video Analysis)")
    print("The image/video analysis tool (gemini-analyze.py) needs a Gemini API key.")
    print("This is SEPARATE from your CLI login and is never stored in this repo.\n")

    API_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if API_KEY_FILE.exists() and API_KEY_FILE.read_text().strip().lstrip("#").strip():
        print(f"✅ Key file already has content: {API_KEY_FILE}")
        return

    API_KEY_FILE.write_text(
        "# Paste your Gemini API key below this line — nothing else in this file.\n"
        "# Get a free key at: https://aistudio.google.com/apikey\n"
        "# (Sign in with the same Google account you use for Gemini CLI)\n"
    )
    if platform.system() != "Windows":
        os.chmod(API_KEY_FILE, 0o600)

    print(f"✅ Created: {API_KEY_FILE}")
    print("\n➡️  ACTION NEEDED: open that file and paste your API key as the last line.")
    print("   Image/video analysis won't work until you do this.")


def install_tool():
    section("Step 5 — Install gemini-analyze.py")
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    source = pathlib.Path(__file__).parent / "gemini-analyze.py"
    dest = TOOLS_DIR / "gemini-analyze.py"

    if source.exists():
        import shutil
        shutil.copy2(source, dest)
        print(f"✅ Installed: {dest}")
    else:
        print(f"⚠️  gemini-analyze.py not found next to setup.py — skipping tool install.")


def check_python_deps():
    section("Step 6 — Python Dependencies")
    try:
        import google.genai
        print("✅ google-genai already installed.")
    except ImportError:
        print("Installing google-genai...")
        subprocess.run([sys.executable, "-m", "pip", "install", "google-genai"], check=True)
        print("✅ google-genai installed.")


def print_summary():
    section("Setup Complete!")
    print(f"""
What was set up:
  ✅ Gemini CLI login verified
  ✅ AI-Context bridge: {AI_CONTEXT}
  ✅ Image/video tool: {TOOLS_DIR / "gemini-analyze.py"}
  ✅ Python SDK: google-genai

Your workflow:
  GEMINI  → ideation, research, drafts, image/video analysis
              saves to ~/AI-Context/
  CLAUDE  → code, systems, testing, polish
              reads from ~/AI-Context/

Usage:
  • Research:  gemini --yolo "research topic" --output-format text
  • Ideation:  gemini -i "let's brainstorm..."
  • Image:     python ~/.claude/tools/gemini-analyze.py image photo.png "analyze"
  • Video:     python ~/.claude/tools/gemini-analyze.py video clip.mp4 "analyze"

Tell Claude: "read my AI-Context and let's build X"
""")
    key_content = API_KEY_FILE.read_text().strip() if API_KEY_FILE.exists() else ""
    if not key_content.lstrip("#").strip():
        print(f"⚠️  Image/video analysis needs an API key — paste one into: {API_KEY_FILE}")


def main():
    print("\n🔧 delegate-to-gemini — Skill Installer")
    print("Sets up the Gemini + Claude dual-AI workflow.\n")

    api_key_only = "--api-key-only" in sys.argv

    if api_key_only:
        setup_api_key()
        return

    if not check_gemini_cli():
        sys.exit(1)

    check_gemini_login()
    setup_ai_context()
    setup_api_key()
    install_tool()
    check_python_deps()
    print_summary()


if __name__ == "__main__":
    main()
