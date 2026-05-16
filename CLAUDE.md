# Claude orientation for the `agent/` workspace

This folder is a multi-project hub. Workflows live in `.claude/skills/`.

## Available slash commands

- `/agent` — top-level menu (router)
- `/school` — school assignment concierge (main workflow)
- `/work` — work projects (stub for now)
- `/other` — other projects (stub for now)

When the user types one of these, read the matching `SKILL.md` and follow it.

## Auto-trigger phrases for `/school`

If the user says any of these without a slash, route to the school skill:
- "nueva tarea", "tengo tarea", "nueva asignación"
- "new homework", "new assignment", "homework", "/homework"
- "school project", "tarea de la escuela"

## Important behavioral rules

- **Default language for school deliverables is Spanish** (user is at UNIR, a Spanish-language master's). Conversation with the user can stay in English unless they switch.
- **Never start work on an assignment without an explicit slash command or trigger phrase.** Just because files are in `school/<project>/` does not mean Claude should start analyzing or drafting.
- **Use the installed `docx` skill** (`.claude/skills/docx/`) for any Word document creation/editing — it's Anthropic's official skill, same engine as Claude.ai.
- **Use the installed `pdf` skill** (`.claude/skills/pdf/`) for any PDF reading/extraction.
- **Use `tools/transcribe.py`** for any audio/video transcription. It auto-chunks files larger than 25 MB. Reads `OPENAI_API_KEY` from `.env`.
- **Use `tools/pages_to_md.py`** for any `.pages` file conversion.
- **Git is set up.** At major checkpoints in the school flow, commit progress with a descriptive message. Never commit `.env`, media files, or `unpacked/` working directories — `.gitignore` handles this.

## Resumption

Each project's `reasoning/progress.md` is the source of truth for current step. Any future Claude session should:
1. Read `reasoning/progress.md` first
2. Pick up at the step listed under "next step"
3. Update `progress.md` after every meaningful step
