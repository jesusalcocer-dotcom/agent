# Claude orientation for the `agent/` workspace

This folder is a multi-project hub. The full architecture lives in `SPEC.md` at the repo root — **read it first** if you're a new Claude session picking up this workspace.

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
- **Single plan doc per project** — `reasoning/plan.md` contains the maximize analysis, the plan, justifications, alternatives, success criteria — all inline. No separate `adversarial.md` or `decision_log.md`.
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
