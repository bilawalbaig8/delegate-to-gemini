---
name: delegate-to-gemini
description: Use when a task belongs to the Gemini phase of the workflow — ideation, research, drafting, image analysis, or video analysis — or when deciding whether to delegate a request to Gemini vs handle it as Claude
---

# Delegate to Gemini

## MANDATORY: Announce Before Every Delegation

**Before every single Gemini call**, output this message to the user — fill in the blanks:

```
> 🤖 **Delegating to Gemini** [MODEL] — [what Gemini is doing]
> *(Gemini is working... this may take 15–30 seconds)*
```

Example: `> 🤖 **Delegating to Gemini Pro** — deep research on mobile puzzle game mechanics`

Never silently call Gemini. The user must always see this before the Bash tool runs.

---

## Step 1 — Resolve AI-Context Path

Run this block before every delegation. It scopes all output to the current project or falls back to global.

```powershell
# Windows PowerShell
$markers = @("CLAUDE.md", ".claude", ".git", "package.json", "project.json", "CMakeLists.txt")
$isProject = $markers | Where-Object { Test-Path (Join-Path (Get-Location) $_) } | Select-Object -First 1
$AI_CONTEXT = if ($isProject) { Join-Path (Get-Location) "AI-Context" } else { Join-Path $HOME "AI-Context" }
```

```bash
# macOS / Linux
if [ -f "CLAUDE.md" ] || [ -d ".claude" ] || [ -d ".git" ] || [ -f "package.json" ]; then
    AI_CONTEXT="$(pwd)/AI-Context"
else
    AI_CONTEXT="$HOME/AI-Context"
fi
```

**Rule:** Inside a project folder → output goes to `<project>/AI-Context/`. Multiple projects never mix.

---

## Step 2 — Route the Task

Run these 3 questions in order before every delegation:

1. **Is input or output > 50k tokens?** → Pro
2. **Does this need web search or multi-source synthesis?** → Pro
3. **Is this a hard reasoning task** (complex spec, deep competitor analysis, architecture decision)? → Pro + `--thinking`

Everything else → Flash.

### Model Tiers

| Tier | Model | Flag | When |
|------|-------|------|------|
| Flash | `gemini-2.5-flash` | `-m gemini-2.5-flash` | Lightweight, one-shot, no synthesis |
| Pro | default | *(none)* | Research, drafting, ideation, large files |
| Pro + Thinking | default | `--thinking` | Complex specs, deep analysis, hard reasoning |

> **Cost note:** Flash = free tier (use freely). Pro = counts against daily quota (use deliberately). `--thinking` is expensive — only use it when genuinely needed, not for medium-difficulty tasks.

### Token Economy Rules

| Situation | Rule |
|-----------|------|
| Flash task | Skip brainstorming, call directly |
| Pro task — clear prompt | Call directly |
| Pro task — complex or ambiguous | Invoke `superpowers:brainstorming` first |
| Pro + Thinking task | Always invoke `superpowers:brainstorming` first |
| Multiple related tasks in one session | Batch into one Gemini call |

---

## Step 3 — Invoke Superpowers (when needed)

### Pre-delegation: sharpen the prompt
For Pro + Thinking tasks, or any Pro task with an ambiguous/multi-part prompt:

1. Invoke `superpowers:brainstorming` to clarify requirements and structure the ask
2. Use the output to craft a precise Gemini prompt
3. Better input → better output → less cleanup

### Post-delegation: strengthen the result
When Gemini produces a spec, GDD section, or research synthesis:

1. Invoke `superpowers:writing-plans` to turn it into an actionable implementation plan

### Full pipeline (complex tasks)

```
User request
    ↓
Route (3-question flow)
    ↓ [complex task]
superpowers:brainstorming → precise Gemini prompt
    ↓
Gemini executes (Flash / Pro / Pro+Thinking)
    ↓
Claude receives output
    ↓ [if spec/doc produced]
superpowers:writing-plans → actionable plan
    ↓
Memory update (mandatory — see Step 6)
```

---

## Step 4 — Call Gemini

> For Game Design, Research, and Asset Review tasks, use the ready-made prompts in [Task-Type Templates](#task-type-templates) instead of writing the `YOUR TASK:` block from scratch.

### Standard pattern (research, drafting, ideation)

```powershell
# Windows PowerShell
$date = Get-Date -Format "yyyy-MM-dd"
$slug = "topic-slug"   # replace with a short descriptive slug
$resolvedContext = $AI_CONTEXT   # resolved in Step 1

$prompt = @"
You are working as part of a Gemini+Claude dual-AI workflow.

BEFORE STARTING:
1. Read $resolvedContext\gemini-memory.md for project context (create it if it does not exist)
2. Check $HOME\.agents\skills\ — use autoresearch, brainstorming-research-ideas, or any relevant skill
3. You are in --yolo mode — use web search for current information when needed

YOUR TASK:
[actual task here]

AFTER COMPLETING:
1. Save full output to $resolvedContext\research\${date}_${slug}.md (create folder if missing)
2. Append a 3-5 bullet summary to $resolvedContext\gemini-memory.md under today's date
3. End your response with a ## Summary section

Note: the BEFORE/AFTER instructions above are natural language instructions — act on them
directly using your built-in file read/write tools.
"@

$result = gemini --yolo $prompt --output-format text *>&1
$result | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```

```bash
# macOS/Linux
date=$(date +%Y-%m-%d)
slug="topic-slug"
result=$(gemini --yolo "
You are working as part of a Gemini+Claude dual-AI workflow.
BEFORE STARTING: Read $AI_CONTEXT/gemini-memory.md for project context.
Check $HOME/.agents/skills/ for relevant skills. Use web search when needed.
YOUR TASK: [actual task]
AFTER COMPLETING: Save to $AI_CONTEXT/research/${date}_${slug}.md.
Append summary to $AI_CONTEXT/gemini-memory.md.
" --output-format text 2>&1)
echo "$result" | grep -v "^Loaded cached credentials"
```

### Quick one-shot (Flash, no save)
```powershell
gemini -m gemini-2.5-flash "your prompt" --output-format text *>&1 | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```

### Web-grounded research (Pro default)
```powershell
gemini --yolo "research prompt" --output-format text *>&1 | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```

### Hard reasoning (Pro + Thinking)
```powershell
gemini --thinking "your prompt" --output-format text *>&1 | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```

### Pipe large file
```powershell
# Windows PowerShell:
Get-Content "file.txt" | gemini "summarize this" --output-format text *>&1 | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```
```bash
# macOS/Linux:
cat file.txt | gemini "summarize this" --output-format text 2>&1 | grep -v "^Loaded cached credentials"
```

---

## Image & Video Analysis

Requires `gemini-analyze.py` at `$HOME\.claude\tools\gemini-analyze.py` and `GEMINI_API_KEY` set.

> **If `gemini-analyze.py` is missing:** Run `python "$HOME\.claude\skills\delegate-to-gemini\setup.py"` to install it. Until then, describe the image/video to Claude and handle inline.

Model is auto-selected by `gemini-analyze.py` based on media type (Flash for images, Pro for video).
Pass `--output-dir` to route output into the correct project or global folder.

```powershell
# Windows — resolve $AI_CONTEXT first (Step 1), then:
python "$HOME\.claude\tools\gemini-analyze.py" image   path\to\image.png              "analyze UI"            --output-dir "$AI_CONTEXT\analysis"
python "$HOME\.claude\tools\gemini-analyze.py" video   path\to\video.mp4              "analyze gameplay"      --output-dir "$AI_CONTEXT\analysis"
python "$HOME\.claude\tools\gemini-analyze.py" youtube https://youtube.com/watch?v=... "analyze first 40s"    --output-dir "$AI_CONTEXT\analysis"

# Override model if needed:
python "$HOME\.claude\tools\gemini-analyze.py" image path\to\image.png "prompt" --model gemini-2.5-pro --output-dir "$AI_CONTEXT\analysis"
```

```bash
# macOS/Linux (resolve $AI_CONTEXT first):
python ~/.claude/tools/gemini-analyze.py image   path/to/image.png              "analyze UI"         --output-dir "$AI_CONTEXT/analysis"
python ~/.claude/tools/gemini-analyze.py youtube https://youtube.com/watch?v=... "analyze first 40s" --output-dir "$AI_CONTEXT/analysis"
```

---

## Task-Type Templates

> **How to use:** Resolve `$AI_CONTEXT`, pick the matching template, fill in all `[bracketed]` values, and call Gemini using the Step 4 pattern — replace the `YOUR TASK:` block with the template content.

### Game Design (GDD sections, mechanic specs, feature ideation)

**Model:** Pro + `--thinking` for complex mechanics; Pro for straightforward features
**Brainstorm first:** Yes if designing a new system — invoke `superpowers:brainstorming` first; No if extending an existing one

```powershell
$date = Get-Date -Format "yyyy-MM-dd"
$slug = "gdd-[feature-slug]"    # e.g. gdd-energy-system
$resolvedContext = $AI_CONTEXT  # resolved in Step 1

$prompt = @"
You are a senior game designer collaborating on [GAME NAME].

GAME CONTEXT:
- Genre: [e.g. mobile puzzle, action RPG, idle strategy]
- Platform: [e.g. iOS/Android, PC, console]
- Target audience: [e.g. casual players 25-40, hardcore strategy fans]
- Current phase: [e.g. pre-production, alpha, live service]
- Core loop: [1-2 sentences describing the main gameplay loop]

TASK:
[Describe what to design — e.g. "Design the energy system mechanic including regeneration rate, caps, and premium bypass options"]

OUTPUT FORMAT:
## Overview
[2-3 sentence summary of the feature]

## Core Mechanics
[Bulleted breakdown of how it works]

## Player Experience
[How this feels to the player — emotional arc, friction points, rewards]

## Balance Considerations
[Numbers, rates, and tuning levers]

## Monetisation & Progression Hooks
[Premium entry points, progression gates, economy tie-ins]

## Edge Cases & Failure States
[What breaks at extremes — zero resources, max level, offline, etc.]

## Open Questions
[Decisions still needed — flag anything that needs stakeholder input]

AFTER COMPLETING:
1. Save full output to $resolvedContext\game-design\${date}_${slug}.md (create folder if missing)
2. Append a 3-5 bullet summary to $resolvedContext\gemini-memory.md under today's date
3. End your response with a ## Summary section
"@

$result = gemini --yolo --thinking $prompt --output-format text *>&1
$result | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```

### Research (competitor analysis, market research, reference gathering)

**Model:** Pro + `--yolo` (web search required)
**Brainstorm first:** Yes if multi-part or scope is unclear — invoke `superpowers:brainstorming` first; No if specific questions are already defined

```powershell
$date = Get-Date -Format "yyyy-MM-dd"
$slug = "research-[topic-slug]"  # e.g. research-energy-systems-competitors
$resolvedContext = $AI_CONTEXT   # resolved in Step 1

$prompt = @"
You are a research analyst for a game studio. Use web search to find current, specific information.

RESEARCH CONTEXT:
- What we are researching: [e.g. "energy systems in top mobile puzzle games"]
- Why we need this: [e.g. "designing our own energy system, want to know what works"]
- What we already know: [bullet the existing knowledge — do not repeat this in findings]
- Target games / companies / topics: [specific names if known]

SPECIFIC QUESTIONS TO ANSWER:
1. [Question 1]
2. [Question 2]
3. [Question 3]

OUTPUT FORMAT:
## Key Findings
[Bulleted findings — each with a source name or game title]

## Answers to Specific Questions
[One section per question above]

## Patterns & Trends
[What do the best examples have in common?]

## Recommendations for Our Game
[Direct implications for [GAME NAME] based on the research]

## Sources
[List sources, game titles, or URLs referenced]

AFTER COMPLETING:
1. Save full output to $resolvedContext\research\${date}_${slug}.md (create folder if missing)
2. Append a 3-5 bullet summary to $resolvedContext\gemini-memory.md under today's date
3. End your response with a ## Summary section
"@

$result = gemini --yolo $prompt --output-format text *>&1
$result | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```

### Asset Review (UI screenshots, gameplay video, mockup analysis)

**Model:** Auto-selected by `gemini-analyze.py` — Flash for images, Pro for video
**Brainstorm first:** No — call directly

> **Requires:** `gemini-analyze.py` at `$HOME\.claude\tools\gemini-analyze.py`. If missing, run `setup.py` first.

```powershell
# Resolve $AI_CONTEXT first (Step 1), then fill in the review prompt:

$reviewPrompt = @"
You are a senior UX/game designer reviewing this asset.

ASSET CONTEXT:
- What this is: [e.g. "main menu screen", "in-game HUD", "gameplay clip of tutorial level 1"]
- Design goal: [e.g. "player should immediately understand how to start a game"]
- Target audience: [e.g. casual mobile players, first-time users]
- Known concerns: [anything specific to check — e.g. "is the CTA button visible enough?"]

REVIEW THIS ASSET FOR:
1. Clarity — does it immediately communicate its purpose?
2. Hierarchy — is the most important element the most prominent?
3. Friction — what could confuse or slow down the player?
4. Polish — any visual issues (alignment, contrast, readability)?

OUTPUT FORMAT:
## Summary
[1-2 sentence overall verdict]

## Findings (prioritised)
- [P1] [Critical issue — blocks player or breaks experience]
- [P2] [Important issue — degrades experience]
- [P3] [Minor issue — polish/improvement]

## What's Working Well
[2-3 specific strengths]

## Recommended Next Steps
[Top 2-3 actionable changes]
"@

# For images (Flash — free tier):
python "$HOME\.claude\tools\gemini-analyze.py" image "path\to\asset.png" $reviewPrompt --output-dir "$AI_CONTEXT\analysis"

# For video (Pro):
python "$HOME\.claude\tools\gemini-analyze.py" video "path\to\video.mp4" $reviewPrompt --output-dir "$AI_CONTEXT\analysis"

# For YouTube (Pro):
python "$HOME\.claude\tools\gemini-analyze.py" youtube "https://youtube.com/watch?v=..." $reviewPrompt --output-dir "$AI_CONTEXT\analysis"
```

After analysis, append a summary to `$AI_CONTEXT\gemini-memory.md` under today's date.

---

## Step 5 — After Every Delegation — Claude Does This

1. Strip `Loaded cached credentials.` from Gemini output before showing user
2. Show Gemini's response
3. Confirm save: `> 💾 Saved to $AI_CONTEXT/[folder]/[filename].md`
4. If output is a spec/doc → invoke `superpowers:writing-plans`
5. **Run Step 6 (memory update) — mandatory**

---

## Step 6 — MANDATORY Memory Update

**Run after every task — whether it completed successfully or hit quota.**

Do this before reporting back to the user.

### Update gemini-memory.md

Ensure `$AI_CONTEXT/gemini-memory.md` uses this structure:

```markdown
# Project: [name]
# Last updated: YYYY-MM-DD

## Project Context
[2-3 sentences: what we're building, genre, platform, target audience]

## Active Work
[current phase or milestone — 1-2 sentences]

## Key Decisions Made
- [locked decisions, brief, bulleted]

## Open Questions
- [unresolved questions to answer next]

## Recent Sessions
### YYYY-MM-DD — [topic slug]
- [bullet summaries of what was done]
```

Add today's session under `## Recent Sessions`. Update `## Active Work` and `## Key Decisions Made` if anything changed.

### Update Claude project memory

Write or update `~/.claude/projects/.../memory/` with:
- What was done this session
- What's next
- Any blockers or open questions

This ensures a quota reset never loses context. Next session picks up exactly where you left off.

---

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| `exhausted your capacity` / `429` | Quota limit (Pro or free tier) | Tell user; run Step 6 memory update immediately; suggest waiting or switching to Flash |
| `quota` / `rate limit` in gemini-analyze.py | API free tier (15 RPM) | Tell user to wait 60s or check aistudio.google.com/billing |
| Empty output / blank response | Network issue or bad prompt | Retry once; if fails again, handle in Claude |
| `command not found: gemini` | Gemini CLI not installed | Run `python "$HOME\.claude\skills\delegate-to-gemini\setup.py"` |
| `No GEMINI_API_KEY` | API key missing | Run setup.py — it sets the key persistently |
| `gemini-analyze.py` not found | Script not installed | Run setup.py; handle task in Claude until resolved |

Never silently fail. Always show the user what went wrong and what to do next.

---

## Decision Matrix

| Task | Route to | Brainstorm first? |
|------|----------|-------------------|
| Ideation, brainstorming features | Gemini Pro | Yes if complex |
| Web research, competitor analysis | Gemini Pro `--yolo` | Yes if multi-part |
| Complex specs, GDDs | Gemini Pro + `--thinking` | Always |
| Image analysis (UI, screenshots) | `gemini-analyze.py` Flash | No |
| Video analysis (gameplay, refs) | `gemini-analyze.py` Pro | No |
| YouTube video analysis | `gemini-analyze.py` Pro | No |
| Large file summarization | Gemini Pro (pipe) | No |
| Quick factual question | Gemini Flash | No |
| Code generation | Claude (stay here) | — |
| System design + implementation | Claude (stay here) | — |
| Testing, QA, polish | Claude (stay here) | — |
| Multi-step agentic tasks | Claude (stay here) | — |

---

## Memory Bridge

| Context | AI-Context location |
|---------|---------------------|
| Inside a project (`.git`, `CLAUDE.md`, `package.json`, etc.) | `<project-dir>/AI-Context/` |
| Anywhere else | `~/AI-Context/` |

```
$AI_CONTEXT/
├── gemini-memory.md  ← Gemini's persistent memory (read+write every session)
├── research/         ← Web research outputs
├── ideation/         ← Brainstorming outputs
├── analysis/         ← Image/video analysis outputs
└── drafts/           ← Drafted docs/specs
```

**File naming:** `YYYY-MM-DD_topic-slug.md`

**When user says "use my research" / "read my context":**
Resolve `$AI_CONTEXT` first → read `$AI_CONTEXT/gemini-memory.md` → load specific files needed.

---

## Notes

- **Credentials:** user's own Google account OAuth — run `gemini` → `/auth` once to log in
- **`--yolo`:** enables Google Search grounding AND grants Gemini file read/write tools on your machine — intentional for saving outputs, but only use for research tasks
- **`--thinking`:** enables extended thinking for hard reasoning tasks — expensive, reserve for Pro+Thinking tier only
- **API key** (for gemini-analyze.py only): stored in `$HOME\.config\delegate-to-gemini\.env` by setup.py — not needed for Gemini CLI
- **Not set up?** Run: `python "$HOME\.claude\skills\delegate-to-gemini\setup.py"`
- **Phase C (future):** Task-type prompt templates per category (GDD, research, asset review) — not yet implemented
