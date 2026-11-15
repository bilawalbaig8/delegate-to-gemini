# delegate-to-gemini

**Give any AI coding agent a Gemini sidekick.** Claude, Codex, Cursor, Copilot or any other agent hands
Gemini the jobs it's best at: live web research, huge-context reading, long drafts, and
image / video / YouTube analysis. Your main agent keeps the coding.

It's an [Agent Skill](https://agentskills.io) (`SKILL.md`) plus one dependency-light Python script, so it
works anywhere an agent can run a shell command, on Windows, macOS and Linux.

```text
You:    "Research how the top merge games monetise, then plan our shop."
Agent:  > Delegating to Gemini Pro + web: merge-game monetisation research
        ...reads Gemini's cited report, saved to AI-Context/research/, and plans the shop
```

---

## Why

| | |
|---|---|
| 🔎 **Fresh facts** | `--web` grounds answers in live Google Search and lists the sources. |
| 📚 **Huge context** | Hand Gemini whole logs, docs or codebases (≈1M tokens) and get the summary back. |
| 🎬 **Sees media** | Screenshots, mockups, local videos and YouTube links, analysed with timestamps. |
| 🧠 **Right model, automatically** | Flash for quick jobs, Pro for deep ones, and an automatic fallback to Flash when Pro has no quota. |
| 🗂️ **Nothing gets lost** | Results save to `<your project>/AI-Context/`, with a shared `gemini-memory.md` any agent can read next session. |
| 🔐 **Safe by design** | Gemini only gets text. It has no shell and no file access. The key never touches the repo or the command line. |

---

## Quick start (2 minutes)

**1. Get the code and a free API key**

```bash
git clone https://github.com/bilawalbaig8/delegate-to-gemini.git
```

Create a key at **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**.

**2. Run setup**

```bash
python delegate-to-gemini/setup.py --enter-key
```

This installs the `google-genai` package, asks for your key at a hidden prompt, saves it to
`~/.config/delegate-to-gemini/api-key.txt` (readable only by you), and makes one tiny test call.
Prefer environment variables? Set `GEMINI_API_KEY` instead and run `python setup.py --check`.

**3. Install it into your agent** (see below), then just ask:

> *"Use Gemini to research the top 5 cozy games of 2026 and save the report."*

---

## Install into your agent

The skill is the whole folder. Put it where your agent looks for skills:

| Agent | Where to put the folder |
|---|---|
| **Claude Code** | `~/.claude/skills/delegate-to-gemini/` (or `.claude/skills/` inside a project) |
| **Codex, Gemini CLI, and other tools that read Agent Skills** | `~/.agents/skills/delegate-to-gemini/`, or your tool's own skills folder (check its docs) |
| **Anything else** (Cursor, Copilot, Windsurf, Cline, Aider, custom agents) | Keep the folder anywhere and add the snippet below to your `AGENTS.md`, rules file or system prompt |

```bash
# macOS / Linux, e.g. for Claude Code
cp -r delegate-to-gemini ~/.claude/skills/

# Windows PowerShell
Copy-Item -Recurse delegate-to-gemini "$HOME\.claude\skills\"
```

**Snippet for agents without skill support** (`AGENTS.md`, `.cursorrules`, etc.):

```markdown
## Gemini delegation
For web research, huge-file summaries, long drafts, or image/video/YouTube analysis, follow
/path/to/delegate-to-gemini/SKILL.md and call:
python "/path/to/delegate-to-gemini/scripts/gemini.py" ask|image|video|youtube ...
```

---

## Using it directly

The agent normally runs these for you, but they work fine by hand too:

```bash
G=delegate-to-gemini/scripts/gemini.py

python $G ask "Summarise the trade-offs of ECS vs OOP for a small Unity team"
python $G ask --tier pro --web --save research --slug merge-games "How do top merge games monetise?"
python $G ask --tier pro --prompt-file templates/game-design.md --with-memory --save game-design --slug energy
python $G ask --context crash.log "What's the root cause?"
cat huge.log | python $G ask --stdin "List every distinct error"

python $G image ui/menu.png "What would confuse a first-time player?"
python $G video clips/level1.mp4 --prompt-file templates/asset-review.md
python $G youtube "https://youtu.be/VIDEO_ID" "Break down the hook in the first 10 seconds"

python $G check     # verify key + SDK
python $G models    # list models your key can use
```

| Command | What it does | Default model |
|---|---|---|
| `ask` | Text task. Add `--web` for Google Search grounding. | Flash (`--tier pro` for Pro) |
| `image` | Analyse a local image | Flash |
| `video` | Analyse a local video (uploaded, then deleted) | Pro → Flash fallback |
| `youtube` | Analyse a public YouTube video | Pro → Flash fallback |
| `check` / `models` | Health check / list available models | — |

Run `python scripts/gemini.py <command> -h` to see every flag.

### Ready-made prompts

`templates/` has fill-in-the-blanks prompts for **research**, **game design** (GDD sections) and **asset
review** (UI / gameplay). Copy one, fill the `[brackets]`, and pass it with `--prompt-file`.

### Where results go

```text
your-project/
└── AI-Context/
    ├── gemini-memory.md   ← short running notes any agent can read next session
    ├── research/          ← 2026-11-15_merge-games.md …
    ├── game-design/
    ├── ideation/
    ├── drafts/
    └── analysis/          ← image / video / YouTube reports
```

The project root is the nearest folder with `.git`, `AGENTS.md`, `CLAUDE.md`, `package.json`, etc.
Outside a project, results go to `~/AI-Context/`. Set `AI_CONTEXT_DIR` to choose your own folder.

---

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | — | API key (takes priority over the key file) |
| `DELEGATE_TO_GEMINI_KEY_FILE` | `~/.config/delegate-to-gemini/api-key.txt` | Key file location |
| `GEMINI_FLASH_MODEL` | `gemini-flash-latest` | Model for the Flash tier |
| `GEMINI_PRO_MODEL` | `gemini-pro-latest` | Model for the Pro tier |
| `AI_CONTEXT_DIR` | auto | Where results are saved |
| `GEMINI_TIMEOUT` | `300` | Seconds before a request gives up (so an agent never hangs) |

The `-latest` aliases always point at Google's current models, so the skill doesn't break when
old versions are retired.

---

## Security & privacy

- **Your key is never in this repo.** It lives in your environment or in a per-user file outside
  every repo. `setup.py` restricts that file to your user (`chmod 600` / Windows ACL).
- **The key never appears on a command line or in output.** Error messages are scrubbed of
  anything that looks like a key.
- **Gemini gets text and media only.** It cannot run commands or touch your files through this
  skill. (The old version used Gemini CLI `--yolo`, which gave it both.)
- **Uploaded media is deleted** from Google's file store right after analysis.
- **What you send goes to Google.** Don't delegate secrets, `.env` files or private customer data.
  Free-tier API traffic may be used by Google to improve its products. See
  [Google's terms](https://ai.google.dev/gemini-api/terms).
- A [gitleaks](https://github.com/gitleaks/gitleaks) workflow scans every push and pull request for
  leaked secrets.

---

## Troubleshooting

| Message | Fix |
|---|---|
| `No Gemini API key found` | `python setup.py --enter-key`, or set `GEMINI_API_KEY` |
| `Your Gemini API key was rejected` | Create a new key at aistudio.google.com/apikey |
| `NOTICE: … has no quota … Falling back to Flash` | Normal on the free tier: Pro needs billing. The answer still comes from Flash. |
| `Quota or rate limit hit` | Wait a minute, drop `--web`, or enable billing in AI Studio |
| `google-genai package is missing` | `python -m pip install -U google-genai` |
| `python` not found | Use `python3` (macOS/Linux) or `py` (Windows) |

---

## Upgrading from v1

v1 drove the Gemini CLI with a Google-account login. Google has since stopped serving that login
path (`IneligibleTierError`), the `gemini-2.5-*` model names it hardcoded now return 404, and newer
CLI versions open interactive mode when given a bare prompt. All of these broke delegation. v2
talks to the Gemini API directly:

- `gemini --yolo "…"` → `python scripts/gemini.py ask --web "…"`
- `gemini --thinking "…"` (not a real flag) → `ask --tier pro "…"`
- `~/.claude/tools/gemini-analyze.py image …` → `scripts/gemini.py image …` (you can delete the old copy)
- Your existing `api-key.txt` keeps working as-is.

---

## Project layout

```text
delegate-to-gemini/
├── SKILL.md            ← instructions the agent follows
├── scripts/gemini.py   ← the one command (ask / image / video / youtube / check / models)
├── templates/          ← research, game-design, asset-review prompts
├── setup.py            ← one-time setup and health check
└── README.md
```

Requirements: Python 3.9+ and `google-genai`. Node and the Gemini CLI are **not** required.

## License

[MIT](LICENSE)
