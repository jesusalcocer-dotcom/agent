# Claude orientation for the `agent/` workspace

This folder is a multi-project hub. The full architecture lives in `SPEC.md` at the repo root — **read it first** if you're a new Claude session picking up this workspace.

## ⚠️ Required session configuration

**This workspace requires Claude Opus 4.7 with max effort and dangerously-skip-permissions mode. No exceptions.**

Launch command:
```bash
claude --dangerously-skip-permissions
```

Then in-session:
```
/effort max
```

If you (Claude, a future session reading this) detect you are NOT on Opus 4.7, surface a one-line warning to the user and recommend they relaunch. If permission prompts appear during workflow execution, the launch flag was missing.

**Every sub-agent spawned via the Agent tool uses `model: claude-opus-4-7` and `effort: max`, pinned at the agent-definition level.** The custom agents live in `.claude/agents/`:
- `blind-maximize-critic.md` — used in Step 6c of the school skill
- `blind-draft-critic.md` — used in Step 7d of the school skill

Their YAML frontmatter pins the exact model ID and max effort. Their body system prompts include a self-identity verification line that the orchestrator checks. Do not weaken these.

## Available slash commands

- `/agent` — top-level menu (router)
- `/school` — school assignment concierge (main workflow)
- `/work` — work projects (stub for now)
- `/other` — passthrough to regular Claude Code (no scripted flow)

When the user types one of these, read the matching `SKILL.md` in `.claude/skills/<name>/` and follow it.

## Auto-trigger phrases for `/school`

If the user says any of these without a slash, route to the school skill:
- "nueva tarea", "tengo tarea", "nueva asignación", "asignación nueva"
- "new homework", "new assignment", "homework", "/homework"
- "school project", "tarea de la escuela", "examen", "actividad evaluable"

## The school workflow at a glance

**Two — and only two — user touchpoints:**
1. **"Go" confirmation** after files are dropped and instructions identified
2. **Word doc review** after the .docx is open in Microsoft Word

Between those two points, Claude runs autonomously — preprocessing, maximize analysis (with internal adversarial pass), planning, drafting, exporting. Status updates only; no input required.

See `.claude/skills/school/SKILL.md` for the full step-by-step.

## Important behavioral rules

- **Default language for school deliverables is Spanish** (user is at UNIR, a Spanish-language master's). Conversation with the user can stay in English unless they switch.
- **Auto-open every artifact** the user might want to see. Markdown → `code <path>`. Final .docx → `open -a "Microsoft Word" <path>`. The user is non-technical — never make them navigate Finder.
- **Speak like a colleague briefing, not a developer log.** "Building the plan now" — not "Writing reasoning/plan.md to disk."
- **Use the installed `docx` skill** (`.claude/skills/docx/`) for any Word document creation/editing — it's Anthropic's official skill.
- **Use the installed `pdf` skill** (`.claude/skills/pdf/`) for any PDF reading/extraction.
- **Use `tools/transcribe.py`** for any audio/video transcription. Auto-chunks files >20 MB. Reads `OPENAI_API_KEY` from `.env`.
- **Use `tools/pages_to_md.py`** for any `.pages` file conversion.
- **Use `tools/estimate_pages.py`** for rough page-count estimates from markdown. Word-count + font heuristic. **Do not** use PDF round-trips for exact counts (too slow, prone to loops).
- **Multi-doc reasoning per project**, but lean:
  - `reasoning/sources/*.md` — one comprehensive analysis per source file (instructions, background docs, transcripts). Mandatory; must be deep, not paragraph-stubs.
  - `reasoning/plan.md` — maximize analysis + plan + sub-agent A critique + sources index.
  - `reasoning/outline.md` — outline with self-critique at top (revised internally before drafting).
  - `reasoning/audit.md` — chat-friendly audit summary written before the .docx opens.
  - `reasoning/progress.md` — lightweight resumption state.
  No `decision_log.md`, no `adversarial.md`, no `maximize_v1.md` etc.
- **Git tracks everything.** Commit at each major checkpoint with conventional-commit messages. Never commit `.env`, media files, or `unpacked/` working directories.
- **Don't push to GitHub automatically** — the user pushes when they want.

## Resumption

Each project's `reasoning/progress.md` is the source of truth for current step. Any future Claude session should:
1. Read `progress.md` first
2. Pick up at the phase it says is next
3. Update `progress.md` after every meaningful step

## Behaviors to avoid

- Don't pause for AskUserQuestion during the autonomous phase (after "Go" until the .docx opens in Word). Status updates only.
- Don't generate intermediate files the user doesn't need (`maximize_v1.md`, `adversarial.md`). One plan.md.
- Don't summarize the assignment back to the user.
- Don't lecture about API keys, security, or git best practices.
- Don't make the user navigate Finder. Auto-open everything.
