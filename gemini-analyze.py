#!/usr/bin/env python3
"""
Gemini multimodal analysis tool — images, videos, and YouTube URLs.

Model is auto-selected based on media type:
  image   → gemini-2.5-flash  (fast, sufficient for visual analysis)
  video   → gemini-2.5-pro    (long temporal context needs depth)
  youtube → gemini-2.5-pro    (same — often long content)

Output directory is auto-detected:
  - Inside a project folder (has .git, CLAUDE.md, package.json, etc.) → <project>/AI-Context/analysis/
  - Otherwise → ~/AI-Context/analysis/
  - Override with --output-dir

Usage:
  python gemini-analyze.py image   path/to/image.png              "what's in this UI?"
  python gemini-analyze.py video   path/to/video.mp4              "analyze the gameplay flow"
  python gemini-analyze.py youtube https://youtube.com/watch?v=... "analyze first 40 seconds"

  python gemini-analyze.py image   path/to/image.png  "prompt" --output-dir /path/to/AI-Context/analysis
  python gemini-analyze.py youtube https://...        "prompt" --model gemini-2.5-flash
"""

from __future__ import annotations

import sys
import os
import pathlib
from datetime import datetime

HOME = pathlib.Path.home()
API_KEY_FILE = HOME / ".config" / "delegate-to-gemini" / "api-key.txt"

_PROJECT_MARKERS = {".git", ".claude", "CLAUDE.md", "package.json", "project.json", "CMakeLists.txt"}

# Auto model selection per media type
_DEFAULT_MODELS = {
    "image":   "gemini-2.5-flash",  # fast + sufficient for image analysis
    "video":   "gemini-2.5-pro",    # local video needs deep temporal reasoning
    "youtube": "gemini-2.5-pro",    # long-form content, needs full capacity
}


def _resolve_output_dir(override: str | None = None) -> pathlib.Path:
    """Project-scoped output dir, or global ~/AI-Context/analysis as fallback."""
    if override:
        return pathlib.Path(override)
    cwd = pathlib.Path.cwd()
    if any((cwd / m).exists() for m in _PROJECT_MARKERS):
        return cwd / "AI-Context" / "analysis"
    return HOME / "AI-Context" / "analysis"


def load_api_key():
    """Reads the key from api-key.txt (first non-empty, non-comment line).
    Falls back to GEMINI_API_KEY / GOOGLE_API_KEY env vars if already set."""
    if API_KEY_FILE.exists():
        for line in API_KEY_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def analyze(media_type: str, source: str, prompt: str = None,
            output_dir: str = None, model: str = None):

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("ERROR: Run: pip install google-genai")
        sys.exit(1)

    api_key = load_api_key()
    if not api_key:
        print(f"ERROR: No API key found in {API_KEY_FILE}")
        print("Get a free key at https://aistudio.google.com/apikey, then paste it")
        print(f"as the only line in: {API_KEY_FILE}")
        print("(Run setup.py first if that file doesn't exist yet.)")
        sys.exit(1)

    # Pick model — explicit override > auto-select by media type
    chosen_model = model or _DEFAULT_MODELS.get(media_type, "gemini-2.5-pro")
    print(f"Model: {chosen_model}")

    client = genai.Client(api_key=api_key)

    default_prompts = {
        "image":   "Analyze this image in detail. Describe UI elements, layout, visual style, colors, and anything notable for a game developer.",
        "video":   "Analyze this video in detail. Describe the gameplay flow, UI/UX patterns, visual style, pacing, and key moments. Note anything useful for game design.",
        "youtube": "Analyze this video in detail. Describe the gameplay flow, UI/UX patterns, visual style, pacing, and key moments. Note anything useful for game design.",
    }
    prompt = prompt or default_prompts.get(media_type, "Describe this in detail.")

    if media_type == "youtube":
        print(f"Analyzing YouTube video...")
        try:
            response = client.models.generate_content(
                model=chosen_model,
                contents=[
                    types.Part.from_uri(file_uri=source, mime_type="video/mp4"),
                    prompt,
                ],
            )
        except Exception as e:
            _handle_error(e)
        slug = source.split("v=")[-1][:20].replace("&", "-")
        result_text = response.text

    else:
        file_path = pathlib.Path(source)
        if not file_path.exists():
            print(f"ERROR: File not found: {file_path}")
            sys.exit(1)

        print(f"Uploading {media_type}: {file_path.name}...")
        try:
            uploaded = client.files.upload(file=str(file_path))
        except Exception as e:
            print(f"\nERROR uploading file: {e}")
            print("May be a quota/rate limit. Check: https://aistudio.google.com")
            sys.exit(1)

        # Poll until file is ACTIVE (Google requires processing time after upload)
        import time
        print(f"Waiting for file to become active...")
        max_wait = 120  # seconds
        poll_interval = 3
        waited = 0
        while waited < max_wait:
            file_info = client.files.get(name=uploaded.name)
            state = getattr(file_info, "state", None)
            state_str = str(state).upper() if state else ""
            if "ACTIVE" in state_str:
                break
            if "FAILED" in state_str:
                print(f"ERROR: File processing failed (state={state})")
                sys.exit(1)
            time.sleep(poll_interval)
            waited += poll_interval
            print(f"  ...still processing ({waited}s)")
        else:
            print(f"ERROR: File did not become active within {max_wait}s")
            sys.exit(1)

        print(f"Analyzing...")
        try:
            response = client.models.generate_content(
                model=chosen_model,
                contents=[
                    types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type),
                    prompt,
                ],
            )
        except Exception as e:
            _handle_error(e)

        slug = file_path.stem.lower().replace(" ", "-")[:40]
        result_text = response.text

    resolved_dir = _resolve_output_dir(output_dir)
    resolved_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_file = resolved_dir / f"{date_str}_{media_type}-{slug}.md"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"# {media_type.title()} Analysis: {source}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** {chosen_model}\n")
        f.write(f"**Prompt:** {prompt}\n\n---\n\n")
        f.write(result_text)

    print(f"\n{'-'*50}\n{result_text}\n{'-'*50}")
    print(f"\nSaved to: {out_file}")
    return result_text


def _handle_error(e):
    err = str(e).lower()
    if "quota" in err or "rate" in err or "limit" in err or "429" in err:
        print(f"\nQUOTA/RATE LIMIT: {e}")
        print("Options:")
        print("  1. Wait and retry (free tier resets daily/per-minute)")
        print("  2. Switch to Flash: add --model gemini-2.5-flash")
        print("  3. Enable billing: https://aistudio.google.com")
    else:
        print(f"\nERROR: {e}")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    media_type = sys.argv[1].lower()
    if media_type not in ("image", "video", "youtube"):
        print("ERROR: First argument must be 'image', 'video', or 'youtube'")
        sys.exit(1)

    source = sys.argv[2]

    # Parse remaining args: optional prompt text + --output-dir + --model
    output_dir = None
    model_override = None
    prompt_parts = []
    remaining = sys.argv[3:]
    i = 0
    while i < len(remaining):
        if remaining[i] == "--output-dir" and i + 1 < len(remaining):
            output_dir = remaining[i + 1]
            i += 2
        elif remaining[i] == "--model" and i + 1 < len(remaining):
            model_override = remaining[i + 1]
            i += 2
        else:
            prompt_parts.append(remaining[i])
            i += 1

    prompt = " ".join(prompt_parts) if prompt_parts else None
    analyze(media_type, source, prompt, output_dir, model_override)
