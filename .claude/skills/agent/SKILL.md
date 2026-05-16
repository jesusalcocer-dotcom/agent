---
name: agent
description: "Top-level router for this workspace. Triggers: '/agent', 'agent menu', 'what should I work on', 'open the agent', 'start agent'. Shows a picker (School / Work / Other) and routes the user to the appropriate sub-skill."
---

# Agent — top-level router

This is the entry point for the `agent/` workspace. When invoked, show the user a menu and route to the right sub-skill.

## Behavior

1. **Greet briefly.** Example: *"What do you want to work on?"* — keep it to one sentence.
2. **Ask via AskUserQuestion** with these three options:
   - **📚 School** — School assignments (UNIR master's program in Clinical Neuropsychology)
   - **💼 Work** — Work projects (stub for now)
   - **📦 Other** — Anything else (stub for now)
3. **Route based on answer:**
   - School → invoke the `school` skill
   - Work → invoke the `work` skill
   - Other → invoke the `other` skill

## Implementation note

Use the `Skill` tool to invoke the sub-skill directly. Don't ask "are you sure?" — the user already picked.

If the user says one of School / Work / Other inline in their message (e.g. *"agent, school"*), skip the picker and go straight to the matching sub-skill.

## Quick-pick aliases

These slash commands skip this router entirely:
- `/school` — straight to school
- `/work` — straight to work
- `/other` — straight to other

If the user uses one of those, the matching skill is invoked directly and this one isn't needed.
