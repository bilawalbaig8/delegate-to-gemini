# delegate-to-gemini Phase C — Task-Type Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dedicated prompt templates to SKILL.md for each task category (Game Design, Research, Asset Review) so Gemini gets structured context upfront — reducing output cleanup and improving first-call quality.

**Architecture:** Three template blocks added to SKILL.md under a new "Task-Type Templates" section. Each template pre-fills project context, output format, and success criteria. Claude substitutes real values before calling Gemini. No new files or scripts — all changes are in SKILL.md.

**Tech Stack:** Gemini CLI (`gemini --yolo`, `--thinking`), PowerShell/bash, `gemini-analyze.py`

---

## File Structure

- **Modify:** `C:\Users\Bilawal\.claude\skills\delegate-to-gemini\SKILL.md` — add Task-Type Templates section after Step 4
- **Modify:** `C:\Users\Bilawal\.claude\skills\delegate-to-gemini\docs\superpowers\specs\2026-06-11-delegate-to-gemini-redesign.md` — mark Phase C as completed

---

### Task 1: Define Template Format

Establish the standard shape every template follows before writing the three category templates.

**Files:**
- Modify: `SKILL.md` — add Task-Type Templates section header + format definition

- [ ] **Step 1: Open SKILL.md and locate insertion point**

Find the line `## Step 5 — After Every Delegation — Claude Does This` — the new section goes immediately before it.

- [ ] **Step 2: Add the section header and format spec**

Insert this block before Step 5:

```markdown
## Task-Type Templates

For complex or ambiguous tasks, use the matching template below. Claude fills in the `[bracketed]` values from project context before calling Gemini. Templates are used with the standard Step 4 prompt — replace the `YOUR TASK:` block with the template content.

> **How to use:** Resolve `$AI_CONTEXT`, pick the matching template, substitute all `[values]`, then call Gemini using the Step 4 pattern.
```

- [ ] **Step 3: Verify the section header reads clearly in context**

Read the surrounding area in SKILL.md — confirm the new section sits cleanly between Step 4 and Step 5 with no formatting breaks.

- [ ] **Step 4: Commit**

```bash
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" add SKILL.md
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" commit -m "feat: add task-type templates section header to SKILL.md"
```

---

### Task 2: Game Design Template

Covers GDD sections, mechanic specs, and feature ideation — the most common use case.

**Files:**
- Modify: `SKILL.md` — add Game Design template block under Task-Type Templates

- [ ] **Step 1: Define success criteria before writing**

A good Game Design template output should:
- Reference the game's genre and target audience without Claude needing to explain it
- Produce output in a consistent GDD format (Overview / Mechanics / Player Experience / Open Questions)
- Avoid generic advice — output should be specific to the project
- Need zero restructuring before copying into a GDD

- [ ] **Step 2: Add the Game Design template to SKILL.md**

Insert under the Task-Type Templates section header:

```markdown
### Game Design (GDD sections, mechanic specs, feature ideation)

**Model:** Pro + `--thinking` for complex mechanics; Pro for straightforward features
**Brainstorm first:** Yes if designing a new system; No for extending an existing one

```
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

## Open Questions
[Decisions still needed — flag anything that needs stakeholder input]
```
```

- [ ] **Step 3: Validate the template with a test call**

Pick a real current project. Fill in all `[bracketed]` values. Call Gemini:

```powershell
$prompt = @"
You are a senior game designer collaborating on [YOUR GAME NAME].
GAME CONTEXT:
- Genre: [fill in]
- Platform: [fill in]
- Target audience: [fill in]
- Current phase: [fill in]
- Core loop: [fill in]
TASK: [describe a real feature to design]
OUTPUT FORMAT:
## Overview
## Core Mechanics
## Player Experience
## Balance Considerations
## Open Questions
"@
gemini --thinking $prompt --output-format text *>&1 | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```

- [ ] **Step 4: Check output quality against success criteria from Step 1**

Verify: Does the output reference the game context? Is it in the correct format? Does it need restructuring? If output is weak — revise the template's GAME CONTEXT or OUTPUT FORMAT fields and re-test before proceeding.

- [ ] **Step 5: Commit**

```bash
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" add SKILL.md
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" commit -m "feat: add Game Design prompt template"
```

---

### Task 3: Research Template

Covers competitor analysis, market research, and reference gathering.

**Files:**
- Modify: `SKILL.md` — add Research template block

- [ ] **Step 1: Define success criteria before writing**

A good Research template output should:
- Answer the specific questions asked, not give a generic overview
- Cite sources or name specific examples (not vague claims)
- Produce output in a format ready to paste into a research doc
- Include a "What We Already Know" section so Gemini doesn't repeat existing knowledge

- [ ] **Step 2: Add the Research template to SKILL.md**

Insert under the Game Design template:

```markdown
### Research (competitor analysis, market research, reference gathering)

**Model:** Pro + `--yolo` (web search required)
**Brainstorm first:** Yes if multi-part or unclear scope; No if specific questions are already defined

```
You are a research analyst for a game studio. Use web search to find current, specific information.

RESEARCH CONTEXT:
- What we're researching: [e.g. "energy systems in top mobile puzzle games"]
- Why we need this: [e.g. "designing our own energy system, want to know what works"]
- What we already know: [bullet the existing knowledge — Gemini should not repeat this]
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
```
```

- [ ] **Step 3: Validate with a test call**

```powershell
gemini --yolo "
You are a research analyst for a game studio. Use web search to find current, specific information.
RESEARCH CONTEXT:
- What we're researching: [fill in a real topic]
- Why we need this: [fill in]
- What we already know: [fill in]
SPECIFIC QUESTIONS TO ANSWER:
1. [real question]
2. [real question]
OUTPUT FORMAT:
## Key Findings
## Answers to Specific Questions
## Patterns and Trends
## Recommendations for Our Game
## Sources
" --output-format text *>&1 | Where-Object { $_ -notmatch "^Loaded cached credentials" }
```

- [ ] **Step 4: Check output quality against success criteria**

Verify: Are answers specific (named games/examples)? Are sources cited? Is the "already know" content absent from findings? Revise template if needed.

- [ ] **Step 5: Commit**

```bash
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" add SKILL.md
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" commit -m "feat: add Research prompt template"
```

---

### Task 4: Asset Review Template

Covers UI screenshots, gameplay video, and mockup analysis via `gemini-analyze.py`.

**Files:**
- Modify: `SKILL.md` — add Asset Review template block

- [ ] **Step 1: Define success criteria before writing**

A good Asset Review template output should:
- Give actionable feedback, not vague impressions ("button is too small at 32px" not "button feels small")
- Reference what the asset is supposed to achieve (the design goal)
- Produce output as a prioritized list of findings, not a wall of prose
- Work for images (Flash) and video (Pro) without separate templates

- [ ] **Step 2: Add the Asset Review template to SKILL.md**

Insert under the Research template:

```markdown
### Asset Review (UI screenshots, gameplay video, mockup analysis)

**Model:** Auto-selected by `gemini-analyze.py` — Flash for images, Pro for video
**Brainstorm first:** No — call directly

For images:
```powershell
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

## Findings (prioritized)
- [P1] [Critical issue — blocks player or breaks experience]
- [P2] [Important issue — degrades experience]
- [P3] [Minor issue — polish/improvement]

## What's Working Well
[2-3 specific strengths]

## Recommended Next Steps
[Top 2-3 actionable changes]
"@

python "$HOME\.claude\tools\gemini-analyze.py" image "path\to\asset.png" $reviewPrompt --output-dir "$AI_CONTEXT\analysis"
```
```

- [ ] **Step 3: Validate with a real asset**

Pick a real screenshot or mockup. Fill in the context fields. Run the command. Check: Is feedback specific and actionable? Are findings prioritized? Does it reference the design goal?

- [ ] **Step 4: Commit**

```bash
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" add SKILL.md
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" commit -m "feat: add Asset Review prompt template"
```

---

### Task 5: Mark Phase C Complete

**Files:**
- Modify: `docs/superpowers/specs/2026-06-11-delegate-to-gemini-redesign.md` — update Phase C status
- Modify: `~/.claude/projects/.../memory/project_delegate-to-gemini-skill.md` — update status

- [ ] **Step 1: Update the spec doc**

In `2026-06-11-delegate-to-gemini-redesign.md`, change the Phase C section:

```markdown
### 5. Phase C — Task-Type Templates ✅ COMPLETED 2026-06-11
```

- [ ] **Step 2: Update Claude project memory**

In `C:\Users\Bilawal\.claude\projects\C--Users-Bilawal--claude-skills-delegate-to-gemini\memory\project_delegate-to-gemini-skill.md`, update current status to:

```
## Current Status (as of 2026-06-11)
**v2 + Phase C complete.** SKILL.md fully updated with routing, superpowers integration, memory protocol, and task-type templates for Game Design, Research, and Asset Review.
```

- [ ] **Step 3: Final commit**

```bash
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" add -A
git -C "C:/Users/Bilawal/.claude/skills/delegate-to-gemini" commit -m "feat: complete Phase C — all task-type templates validated and shipped"
```

---

## Self-Review

**Spec coverage check:**
- ✅ Game Design templates (GDD, mechanic specs, feature ideation)
- ✅ Research templates (competitor analysis, market research, reference gathering)
- ✅ Asset Review templates (UI screenshots, gameplay video, mockup analysis)
- ✅ Each template tested before committing
- ✅ Phase C marked complete in spec + memory

**Placeholder scan:** No TBDs or TODOs — all steps include actual template content and test commands.

**Type consistency:** Template format (CONTEXT → TASK/QUESTIONS → OUTPUT FORMAT) is consistent across all three categories.
