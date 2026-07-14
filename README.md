# delegate-to-gemini

> A Claude Code skill that gives Claude a research partner — and makes them work together automatically.

**Gemini** researches, drafts, and analyses. **Claude** reasons, codes, and builds. This skill connects them so you never have to switch tools or copy prompts between them manually.

---

## What it does

You describe a task in plain English. Claude decides whether Gemini should handle it, picks the right model, runs the task, saves the output to your project folder, and updates shared memory so both AIs remember what was done next session.

| Gemini handles | Claude handles |
|---|---|
| Live web research & competitor analysis | Writing and generating code |
| Game design docs (GDDs) & mechanic specs | Architecture and system design |
| Video analysis — YouTube or local footage | Testing, QA, and polishing |
| UI & screenshot review | Multi-step implementation tasks |
| Summarising large files and codebases | Anything requiring precise reasoning |

---

## Why use it?

- **One prompt** — describe the task, no manual switching between tools
- **Three model tiers** — Flash (free/fast), Pro (deep research), Pro+Thinking (complex specs) — chosen automatically by a 3-question routing flow
- **Nothing is forgotten** — every Gemini result saves to disk; next session both AIs pick up exactly where you left off
- **Each project stays separate** — research for Game A never mixes with Game B
- **Ready-made templates** — game design, research, and asset review prompts built in

---

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| [Claude Code](https://claude.ai/code) | Any | |
| Node.js | 18+ | For Gemini CLI |
| Python | 3.8+ | For setup and image/video analysis |
| Google Account | — | Free Gmail works — used for Gemini CLI login |
| Gemini API Key | — | Free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — image/video only |

---

## Installation

**Step 1 — Copy the skill into your Claude skills folder**

```bash
# macOS / Linux
cp -r delegate-to-gemini ~/.claude/skills/

# Windows (PowerShell)
Copy-Item -Recurse delegate-to-gemini "$HOME\.claude\skills\"
```

**Step 2 — Run the setup script**

```bash
# macOS / Linux
python ~/.claude/skills/delegate-to-gemini/setup.py

# Windows
python "$HOME\.claude\skills\delegate-to-gemini\setup.py"
```

The script installs the Gemini CLI (if missing), the Python image/video helper, and creates your output folders. Your credentials stay on your machine — nothing is stored in this repo.

**Step 3 — Log in to Gemini**

Open a terminal, type `gemini`, then `/auth`, and sign in with your Google account. One-time only.

**Step 4 — Open Claude Code in your project and start asking**

The skill loads automatically. No configuration needed.

---

## Usage

Just talk to Claude:

```
"Research the top mobile merge games in 2025"
"Design the energy system for my game — costs, caps, regeneration rate"
"Analyse this gameplay video and write a dev spec from it"
"Review this UI screenshot — what would confuse a first-time player?"
```

Claude announces every Gemini call so you always know what's happening:

```
🤖 Delegating to Gemini Pro — web research on mobile merge games
*(Gemini is working... this may take 15–30 seconds)*
```

Results save automatically to your project's `AI-Context/` folder.

---

## Output structure

```
YourProject/
└── AI-Context/
    ├── gemini-memory.md     ← shared memory (read by both AIs every session)
    ├── research/            ← web research reports
    ├── game-design/         ← GDDs and mechanic specs
    ├── analysis/            ← image and video reviews
    └── drafts/              ← documents and specs
```

Open a different project → that project gets its own `AI-Context/` folder. Nothing mixes.

---

## Files in this repo

```
delegate-to-gemini/
├── SKILL.md              ← the skill itself (Claude reads this)
├── setup.py              ← one-time installer
├── gemini-analyze.py     ← image/video/YouTube analysis helper
├── README.md             ← this file
├── docs.html             ← plain English guide
└── docs-technical.html   ← full technical reference
```

---

## Documentation

| | |
|---|---|
| [docs.html](docs.html) | Plain English — for anyone |
| [docs-technical.html](docs-technical.html) | Technical reference — model tiers, routing flow, code templates |

---

## Privacy & credentials

- **OAuth login** — stored by the Gemini CLI in your local user profile. Never in this repo.
- **API key** — you paste it yourself into `~/.config/delegate-to-gemini/api-key.txt` (the setup script only creates the empty template). Never in this repo.
- **AI-Context output** — lives inside your project folder. Not part of this repo.

Each person who installs this skill uses their own Google account and API key.

---

## License

MIT — use it, modify it, share it.
