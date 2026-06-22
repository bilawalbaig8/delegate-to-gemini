# delegate-to-gemini v2 — Redesign Spec
**Date:** 2026-06-11
**Status:** Approved

---

## Problem Statement

The current `delegate-to-gemini` skill has three active pain points:
- **Output quality** — Gemini receives vague prompts, output needs too much cleanup
- **Routing ambiguity** — unclear when to use Gemini vs Claude, which model, which tier
- **Weak memory bridge** — Gemini forgets context between sessions; daily quota resets lose all progress

Three minor gaps also exist: no `--thinking` flag support, no cost/quota awareness, no fallback for missing `gemini-analyze.py`.

---

## Scope

This spec covers a full redesign of `SKILL.md` to address all pain points. A follow-on Phase C (task-type prompt templates) is noted but not in scope here.

---

## Design

### 1. Minor Fixes

| Fix | Change |
|-----|--------|
| `--thinking` flag | Add Pro+Thinking row to model table |
| Cost awareness | Flash = free tier; Pro = counts against daily quota |
| Missing script fallback | If `gemini-analyze.py` not found → tell user to run `setup.py`, Claude handles task inline |

---

### 2. Routing — 3-Question Decision Flow

Replace the flat lookup table with a decision flow Claude runs before every delegation:

```
Q1: Input or output > 50k tokens?        → YES → Pro
Q2: Needs web search or multi-source synthesis?  → YES → Pro
Q3: Hard reasoning task?                 → YES → Pro + --thinking
Otherwise → Flash
```

**Three tiers:**

| Tier | Model | Flag | When |
|------|-------|------|------|
| Flash | `gemini-2.5-flash` | `-m gemini-2.5-flash` | Lightweight, one-shot, no synthesis |
| Pro | default | none | Research, drafting, ideation, large files |
| Pro + Thinking | default | `--thinking` | Complex specs, deep analysis, hard reasoning |

**Token Economy Rules:**
- Flash tasks: skip brainstorming, call directly
- Pro tasks: invoke `superpowers:brainstorming` first if task is complex or ambiguous
- Pro + Thinking: always invoke `superpowers:brainstorming` first; batch related questions into one call
- Multiple related tasks in one session: batch into a single Gemini call to preserve quota

---

### 3. Superpowers Integration

Superpowers skills act as the intelligence layer on both sides of the Gemini call.

**Full pipeline:**
```
User request
    ↓
Claude routes (3-question flow above)
    ↓ [complex / Pro+ task]
superpowers:brainstorming → precise, structured Gemini prompt
    ↓
Gemini executes (Flash / Pro / Pro+Thinking)
    ↓
Claude receives output
    ↓ [if output is a spec, GDD, or doc]
superpowers:writing-plans → actionable implementation plan
    ↓
Memory update (mandatory — see Section 4)
```

**When to invoke brainstorming:**
- Task is routed to Pro + Thinking tier → always
- Task is routed to Pro tier AND the prompt is ambiguous or multi-part → yes
- Task is routed to Flash → skip

**When to invoke writing-plans:**
- Gemini produces a spec, GDD section, feature doc, or research synthesis → yes
- Gemini produces a quick factual answer → skip

---

### 4. Memory Bridge

**Structured `gemini-memory.md` format:**

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
- [unresolved questions Gemini should help answer]

## Recent Sessions
### YYYY-MM-DD — [topic slug]
- [bullet summaries of what was done]
```

**Mandatory Memory Update Protocol:**

After every task — whether it completes successfully or hits quota — Claude executes both steps before reporting back to the user:

1. **Update `$AI_CONTEXT/gemini-memory.md`** — add session summary under today's date, update Active Work, log any new decisions or open questions
2. **Update Claude project memory** (`~/.claude/projects/.../memory/`) — write what was done, what's next, any blockers

This ensures a quota reset never means lost context. Next session starts with full awareness on both sides.

---

### 5. Phase C — Task-Type Templates ✅ COMPLETED 2026-06-11

After Phase B is validated in practice, add dedicated prompt templates for each task category:
- Game Design: GDD sections, mechanic specs, feature ideation
- Research: competitor analysis, market research, reference gathering
- Asset Review: UI screenshots, gameplay video, mockup analysis

Each template pre-fills project context, output format, and success criteria to further reduce cleanup.

---

## Updated Decision Matrix

| Task | Route to | Brainstorm first? |
|------|----------|-------------------|
| Ideation, brainstorming features | Gemini Pro | Yes if complex |
| Web research, competitor analysis | Gemini Pro `--yolo` | Yes if multi-part |
| Complex specs, GDDs | Gemini Pro + `--thinking` | Always |
| Image analysis | `gemini-analyze.py` Flash | No |
| Video / YouTube analysis | `gemini-analyze.py` Pro | No |
| Large file summarization | Gemini Pro (pipe) | No |
| Quick factual question | Gemini Flash | No |
| Code generation | Claude | — |
| System design + implementation | Claude | — |
| Testing, QA, polish | Claude | — |

---

## What Changes in SKILL.md

1. Routing table → 3-question decision flow + 3-tier model table
2. Step 2 (Pick Model) → expanded with token economy rules
3. Step 3 (Call Gemini) → add brainstorming + writing-plans integration points
4. New section: Memory Update Protocol (mandatory after every task)
5. Error table → add missing `gemini-analyze.py` fallback row
6. Model table → add Pro+Thinking row with `--thinking` flag
7. Add cost/quota awareness note under model table
