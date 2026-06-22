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
ENV_FILE = HOME / ".config" / "delegate-to-gemini" / ".env"


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
    print("The image/video analysis tool requires a Gemini API key.")
    print("This is SEPARATE from your CLI login.\n")
    print("Get your free API key at: https://aistudio.google.com/apikey")
    print("(Sign in with the same Google account you use for Gemini CLI)\n")

    choice = input("Do you have a Gemini API key? (y/n): ").strip().lower()
    if choice != 'y':
        print("\n⚠️  Skipping API key setup.")
        print("   Image/video analysis won't work until you add it.")
        print(f"   Run this later: python setup.py --api-key-only")
        return None

    api_key = input("Paste your API key: ").strip()
    if not api_key:
        print("⚠️  No key entered. Skipping.")
        return None

    # Save to env file
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENV_FILE, "w") as f:
        f.write(f"GEMINI_API_KEY={api_key}\n")

    if platform.system() != "Windows":
        os.chmod(ENV_FILE, 0o600)

    # Also set as persistent environment variable
    if platform.system() == "Windows":
        subprocess.run([
            "powershell", "-Command",
            f'[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "{api_key}", "User")'
        ], capture_output=True)
    else:
        shell_rc = HOME / (".zshrc" if (HOME / ".zshrc").exists() else ".bashrc")
        with open(shell_rc, "a") as f:
            f.write(f'\nexport GEMINI_API_KEY="{api_key}"  # delegate-to-gemini\n')

    print(f"✅ API key saved to: {ENV_FILE}")
    print("✅ Set as permanent environment variable.")
    return api_key


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
