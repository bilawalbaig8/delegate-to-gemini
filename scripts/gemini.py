#!/usr/bin/env python3
"""
delegate-to-gemini - one portable command for any AI agent (or a human) to hand work to Gemini.

Subcommands
  ask      Text task: research, ideation, drafting, summarising. Optional live Google Search.
  image    Analyse a local image (screenshot, mockup, art).
  video    Analyse a local video file.
  youtube  Analyse a public YouTube video by URL.
  check    Verify the API key and SDK work (makes one tiny Flash call).
  models   List the models your key can use.

Examples
  python gemini.py ask "Summarise the pros and cons of energy systems in puzzle games"
  python gemini.py ask --tier pro --web --save research --slug merge-games "Research top merge games in 2026"
  python gemini.py ask --tier pro --prompt-file brief.md --with-memory --save drafts --slug energy-gdd
  type big.log | python gemini.py ask --stdin "Find the root cause in this log"      (Windows)
  cat big.log  | python gemini.py ask --stdin "Find the root cause in this log"      (macOS/Linux)
  python gemini.py image ui.png "What would confuse a first-time player?"
  python gemini.py youtube https://youtu.be/VIDEO_ID "Break down the first 40 seconds"

API key (never printed, never written anywhere by this script)
  1. GEMINI_API_KEY or GOOGLE_API_KEY environment variable, else
  2. first non-comment line of ~/.config/delegate-to-gemini/api-key.txt
  (override the file path with DELEGATE_TO_GEMINI_KEY_FILE)

Models (override with env vars or --model)
  GEMINI_FLASH_MODEL  default gemini-flash-latest
  GEMINI_PRO_MODEL    default gemini-pro-latest

  GEMINI_TIMEOUT      request timeout in seconds (default 300)

Output folder for --save and media analysis
  AI_CONTEXT_DIR env var, else <project root>/AI-Context (nearest parent with .git, AGENTS.md,
  CLAUDE.md, package.json, ...), else ~/AI-Context.

Exit codes: 0 ok, 1 error, 2 setup/usage problem, 3 quota or rate limit.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import stat
import sys
import time
from datetime import datetime

HOME = pathlib.Path.home()
KEY_FILE = pathlib.Path(
    os.environ.get("DELEGATE_TO_GEMINI_KEY_FILE")
    or HOME / ".config" / "delegate-to-gemini" / "api-key.txt"
)
FLASH_MODEL = os.environ.get("GEMINI_FLASH_MODEL", "gemini-flash-latest")
PRO_MODEL = os.environ.get("GEMINI_PRO_MODEL", "gemini-pro-latest")

PROJECT_MARKERS = (".git", "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".claude", ".agents",
                   "package.json", "pyproject.toml", "project.json", "CMakeLists.txt",
                   "Cargo.toml", "go.mod", "ProjectSettings")
SAVE_CATEGORIES = ("research", "ideation", "drafts", "game-design", "analysis")

EXIT_ERROR, EXIT_SETUP, EXIT_QUOTA = 1, 2, 3

DEFAULT_MEDIA_PROMPTS = {
    "image": "Analyse this image in detail: layout, UI elements, visual style, colours, "
             "readability, and anything notable for a game or app developer.",
    "video": "Analyse this video in detail: flow, UI/UX patterns, visual style, pacing and key "
             "moments with timestamps. Note anything useful for game or product design.",
}
DEFAULT_MEDIA_PROMPTS["youtube"] = DEFAULT_MEDIA_PROMPTS["video"]

_api_key_cache: str | None = None


# --------------------------------------------------------------------------- helpers

def _utf8_stdio() -> None:
    """Windows consoles default to cp1252; model output often contains emoji/unicode."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def err(msg: str) -> None:
    print(redact(msg), file=sys.stderr)


def die(msg: str, code: int = EXIT_ERROR) -> None:
    err(f"ERROR: {msg}")
    sys.exit(code)


def redact(text: str) -> str:
    """Never let the key leak into logs, even if an SDK error message echoes it."""
    text = str(text)
    if _api_key_cache:
        text = text.replace(_api_key_cache, "***")
    return re.sub(r"AIza[0-9A-Za-z_\-]{30,}", "AIza***", text)


def load_api_key() -> str:
    global _api_key_cache
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not key and KEY_FILE.exists():
        # utf-8-sig strips the BOM Notepad adds, which would otherwise corrupt the key.
        for line in KEY_FILE.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                key = line
                break
        if key and os.name != "nt":
            mode = KEY_FILE.stat().st_mode
            if mode & (stat.S_IRGRP | stat.S_IROTH):
                err(f"WARNING: {KEY_FILE} is readable by other users. Run: chmod 600 \"{KEY_FILE}\"")
    if not key:
        die(
            "No Gemini API key found.\n"
            "  Get a free key: https://aistudio.google.com/apikey\n"
            f"  Then either set GEMINI_API_KEY, or paste it as the only line in:\n    {KEY_FILE}\n"
            "  (python setup.py creates that file for you.)",
            EXIT_SETUP,
        )
    _api_key_cache = key
    return key


def get_client(timeout: int | None = None):
    try:
        from google import genai  # noqa: F401
    except ImportError:
        die("The google-genai package is missing. Run: python -m pip install -U google-genai", EXIT_SETUP)
    from google import genai
    from google.genai import types
    # Without a timeout a stalled request can hang the calling agent forever.
    timeout_s = int(os.environ.get("GEMINI_TIMEOUT", timeout or 300))
    return genai.Client(api_key=load_api_key(), http_options=types.HttpOptions(timeout=timeout_s * 1000))


def is_quota_error(e: Exception) -> bool:
    s = str(e)
    return bool(re.search(r"\b429\b|RESOURCE_EXHAUSTED|quota|rate limit|exhausted your capacity", s, re.I))


def is_transient_error(e: Exception) -> bool:
    return bool(re.search(r"\b(500|502|503|504)\b|UNAVAILABLE|overloaded|DEADLINE_EXCEEDED|timed? ?out", str(e), re.I))


def short_error(e: Exception) -> str:
    """'429 RESOURCE_EXHAUSTED. {...json...}' -> '429 RESOURCE_EXHAUSTED: You exceeded your current quota...'"""
    s = str(e)
    m = re.search(r"'message':\s*'([^']+)'", s)
    head = s.split("{", 1)[0].strip().rstrip(".")
    return f"{head}: {m.group(1).strip()}" if m else s[:300]


class NoQuota(Exception):
    """The model has no usable quota right now (free-tier limit 0, or the reset is hours away)."""


def is_hard_quota(e: Exception) -> bool:
    return bool(re.search(r"limit:\s*0\b|retry in \d+h", str(e)))


def call_with_retry(fn, what: str, retries: int = 2, web: bool = False):
    """Retries transient server errors and short rate limits; gives clear messages otherwise."""
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as e:  # SDK raises several error types; classify by message
            last = attempt == retries
            msg = short_error(e)
            if "API_KEY_INVALID" in str(e) or "API key not valid" in str(e):
                die(f"Your Gemini API key was rejected. Check it at https://aistudio.google.com/apikey\n  {msg}",
                    EXIT_SETUP)
            if is_quota_error(e):
                if is_hard_quota(e):
                    raise NoQuota(msg) from None
                if last:
                    tips = ["wait a minute and retry"]
                    if web:
                        tips.append("drop --web (search grounding has a small free quota)")
                    tips += ["use --tier flash", "or enable billing at https://aistudio.google.com"]
                    die(f"Quota or rate limit hit while {what}.\n  {msg}\n  Options: " + ", ".join(tips), EXIT_QUOTA)
                wait = 20 * (attempt + 1)
            elif is_transient_error(e) and not last:
                wait = 5 * (attempt + 1)
            else:
                die(f"Gemini failed while {what}: {msg}")
            err(f"  ...{msg[:90]} - retrying in {wait}s")
            time.sleep(wait)


def generate(client, model: str, contents, config, what: str, web: bool, fallback: bool):
    """Calls Gemini; if the chosen model has no quota (e.g. Pro on the free tier), falls back to Flash."""
    def run(m):
        return call_with_retry(
            lambda: client.models.generate_content(model=m, contents=contents, config=config), what, web=web
        )
    try:
        return run(model), model
    except NoQuota as e:
        problem = str(e)
    if fallback and model != FLASH_MODEL:
        err(f"NOTICE: {model} has no quota on this key (free tier?). Falling back to {FLASH_MODEL}.")
        try:
            return run(FLASH_MODEL), FLASH_MODEL
        except NoQuota as e:
            problem = str(e)
    tips = "enable billing at https://aistudio.google.com, or wait for the quota reset"
    if web:
        tips = "drop --web (search grounding has its own small quota), " + tips
    die(f"No quota left for this request.\n  {problem[:400]}\n  Options: {tips}", EXIT_QUOTA)


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    for d in (start, *start.parents):
        if d == HOME or d == d.parent:
            break
        if any((d / m).exists() for m in PROJECT_MARKERS):
            return d
    return None


def ai_context_dir() -> pathlib.Path:
    if os.environ.get("AI_CONTEXT_DIR"):
        return pathlib.Path(os.environ["AI_CONTEXT_DIR"]).expanduser()
    root = find_project_root(pathlib.Path.cwd().resolve())
    return (root or HOME) / "AI-Context"


def slugify(text: str, fallback: str = "untitled") -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50].strip("-")
    return s or fallback


def unique_path(folder: pathlib.Path, stem: str) -> pathlib.Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{stem}.md"
    n = 2
    while path.exists():
        path = folder / f"{stem}-{n}.md"
        n += 1
    return path


def write_report(folder: pathlib.Path, slug: str, title: str, meta: dict, body: str) -> pathlib.Path:
    stamp = datetime.now()
    path = unique_path(folder, f"{stamp:%Y-%m-%d}_{slug}")
    lines = [f"# {title}", ""]
    lines += [f"- **{k}:** {v}" for k, v in meta.items() if v]
    lines += [f"- **Date:** {stamp:%Y-%m-%d %H:%M}", "", "---", "", body.rstrip(), ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def response_text(resp) -> str:
    text = getattr(resp, "text", None)
    if text:
        return text
    reason = ""
    try:
        reason = str(resp.candidates[0].finish_reason)
    except Exception:
        pass
    die(f"Gemini returned an empty answer{f' (finish reason: {reason})' if reason else ''}. "
        "Rephrase the prompt or try --tier pro.")


def grounding_sources(resp) -> list[str]:
    out, seen = [], set()
    try:
        for chunk in resp.candidates[0].grounding_metadata.grounding_chunks or []:
            web = getattr(chunk, "web", None)
            if web and web.uri and web.uri not in seen:
                seen.add(web.uri)
                out.append(f"- [{web.title or web.uri}]({web.uri})")
    except Exception:
        pass
    return out


def emit(text: str, saved: pathlib.Path | None) -> None:
    print(text.rstrip())
    if saved:
        print(f"\n[saved] {saved}")


# --------------------------------------------------------------------------- commands

def cmd_ask(a) -> None:
    from google.genai import types

    parts: list[str] = []
    if a.with_memory:
        mem = ai_context_dir() / "gemini-memory.md"
        if mem.exists():
            parts.append(f"PROJECT MEMORY (from {mem.name}):\n{mem.read_text(encoding='utf-8-sig')}")
    for ctx in a.context or []:
        p = pathlib.Path(ctx)
        if not p.exists():
            die(f"Context file not found: {p}", EXIT_SETUP)
        parts.append(f"FILE: {p.name}\n```\n{p.read_text(encoding='utf-8-sig', errors='replace')}\n```")
    if a.stdin:
        piped = sys.stdin.read()
        if piped.strip():
            parts.append(f"INPUT:\n{piped}")
    prompt = ""
    if a.prompt_file:
        prompt = pathlib.Path(a.prompt_file).read_text(encoding="utf-8-sig")
    if a.prompt:
        prompt = (prompt + "\n\n" + " ".join(a.prompt)).strip()
    if not prompt:
        die("No prompt given. Pass it as text, with --prompt-file, or both.", EXIT_SETUP)
    parts.append(f"TASK:\n{prompt}" if len(parts) else prompt)

    model = a.model or (PRO_MODEL if a.tier == "pro" else FLASH_MODEL)
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())] if a.web else None,
        system_instruction=(
            "You are a specialist assistant that another AI agent has delegated a task to. "
            "Be specific and structured, use Markdown headings, and flag uncertainty instead of guessing."
            + (" Use Google Search for current facts and name your sources." if a.web else "")
        ),
    )
    client = get_client()
    err(f"Gemini [{model}{' + web search' if a.web else ''}] working...")
    resp, model = generate(client, model, "\n\n".join(parts), config, "answering", a.web, not a.no_fallback)
    text = response_text(resp)
    sources = grounding_sources(resp) if a.web else []
    if sources and "## Sources" not in text:
        text = text.rstrip() + "\n\n## Sources (from Google Search)\n" + "\n".join(sources)

    saved = None
    if a.save:
        folder = ai_context_dir() / a.save
        saved = write_report(folder, a.slug or slugify(prompt[:60]), prompt.splitlines()[0][:100],
                             {"Model": model, "Web search": "yes" if a.web else ""}, text)
    emit(text, saved)


def _youtube_slug(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{6,})", url)
    return "youtube-" + (m.group(1) if m else slugify(url[-30:]))


def cmd_media(a) -> None:
    from google.genai import types

    kind = a.command
    prompt = " ".join(a.prompt) if a.prompt else DEFAULT_MEDIA_PROMPTS[kind]
    if a.prompt_file:
        prompt = pathlib.Path(a.prompt_file).read_text(encoding="utf-8-sig") + ("\n\n" + prompt if a.prompt else "")
    model = a.model or (FLASH_MODEL if kind == "image" else PRO_MODEL)
    client = get_client()
    uploaded = None

    if kind == "youtube":
        if not re.match(r"https?://(www\.|m\.)?(youtube\.com|youtu\.be)/", a.source):
            die("youtube expects a public youtube.com or youtu.be URL.", EXIT_SETUP)
        media = types.Part.from_uri(file_uri=a.source, mime_type="video/*")
        slug = _youtube_slug(a.source)
    else:
        path = pathlib.Path(a.source)
        if not path.is_file():
            die(f"File not found: {path}", EXIT_SETUP)
        err(f"Uploading {path.name} to Gemini...")
        uploaded = call_with_retry(lambda: client.files.upload(file=str(path)), "uploading")
        waited, limit = 0, 300
        while True:
            info = client.files.get(name=uploaded.name)
            state = str(getattr(info.state, "name", info.state) or "").upper()
            if "ACTIVE" in state:
                break
            if "FAILED" in state:
                die("Google could not process this file (unsupported format or corrupt).")
            if waited >= limit:
                die(f"File was still processing after {limit}s. Try a shorter clip.")
            time.sleep(3)
            waited += 3
            if waited % 15 == 0:
                err(f"  ...still processing ({waited}s)")
        media = types.Part.from_uri(file_uri=info.uri, mime_type=info.mime_type)
        slug = f"{kind}-{slugify(path.stem)}"

    try:
        err(f"Gemini [{model}] analysing {kind}...")
        resp, model = generate(client, model, [media, prompt], None, f"analysing the {kind}", False,
                               not a.no_fallback)
        text = response_text(resp)
    finally:
        if uploaded is not None:  # don't leave the user's media sitting on Google's servers
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass

    saved = None
    if not a.no_save:
        folder = pathlib.Path(a.output_dir) if a.output_dir else ai_context_dir() / "analysis"
        saved = write_report(folder, slug, f"{kind.title()} analysis: {a.source}",
                             {"Model": model, "Prompt": prompt.replace("\n", " ")[:300]}, text)
    emit(text, saved)


def cmd_check(a) -> None:
    client = get_client(timeout=45)
    source = "environment variable" if (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")) else str(KEY_FILE)
    print(f"Key source: {source}")
    resp = call_with_retry(
        lambda: client.models.generate_content(model=FLASH_MODEL, contents="Reply with the single word: ready"),
        "checking",
    )
    print(f"Flash model ({FLASH_MODEL}): {response_text(resp).strip()}")
    print(f"Pro model:   {PRO_MODEL}")
    print(f"AI-Context:  {ai_context_dir()}")
    print("OK - delegate-to-gemini is ready.")


def cmd_models(a) -> None:
    client = get_client()
    names = sorted(
        m.name.removeprefix("models/") for m in client.models.list()
        if "generateContent" in (getattr(m, "supported_actions", None) or []) and "gemini" in m.name
    )
    print("\n".join(names))


# --------------------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gemini.py",
        description="Delegate research, drafting and image/video analysis to Gemini.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run 'python gemini.py <command> -h' for details. Full docs: SKILL.md / README.md",
    )
    sub = p.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="text task (research, ideation, drafting, summarising)")
    ask.add_argument("prompt", nargs="*", help="the task (or use --prompt-file / stdin)")
    ask.add_argument("--tier", choices=("flash", "pro"), default="flash",
                     help="flash = fast and cheap (default); pro = deep reasoning, long docs, synthesis")
    ask.add_argument("--web", action="store_true", help="ground the answer in live Google Search results")
    ask.add_argument("--prompt-file", help="read the task from a file (best for long or templated prompts)")
    ask.add_argument("--stdin", action="store_true", help="also read piped input (logs, docs) from stdin")
    ask.add_argument("--context", action="append", metavar="FILE", help="attach a file as context (repeatable)")
    ask.add_argument("--with-memory", action="store_true", help="include AI-Context/gemini-memory.md as context")
    ask.add_argument("--save", choices=SAVE_CATEGORIES, help="also save the answer to AI-Context/<category>/")
    ask.add_argument("--slug", help="short file name for --save, e.g. merge-games")
    ask.add_argument("--model", help="exact model id (overrides --tier)")
    ask.add_argument("--no-fallback", action="store_true",
                     help="fail instead of falling back to Flash when Pro has no quota")
    ask.set_defaults(func=cmd_ask)

    for kind, help_text in (("image", "analyse a local image"), ("video", "analyse a local video"),
                            ("youtube", "analyse a public YouTube video")):
        m = sub.add_parser(kind, help=help_text)
        m.add_argument("source", help="URL" if kind == "youtube" else "file path")
        m.add_argument("prompt", nargs="*", help="what to look for (optional)")
        m.add_argument("--prompt-file", help="read the review prompt from a file")
        m.add_argument("--model", help="exact model id (default: flash for images, pro for video)")
        m.add_argument("--output-dir", help="where to save the report (default: AI-Context/analysis)")
        m.add_argument("--no-save", action="store_true", help="print only, do not save a report")
        m.add_argument("--no-fallback", action="store_true", help="fail instead of falling back to Flash")
        m.set_defaults(func=cmd_media)

    sub.add_parser("check", help="verify key + SDK with one tiny call").set_defaults(func=cmd_check)
    sub.add_parser("models", help="list models your key can use").set_defaults(func=cmd_models)
    return p


def main() -> None:
    _utf8_stdio()
    args = build_parser().parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        die("Cancelled.", EXIT_ERROR)


if __name__ == "__main__":
    main()
