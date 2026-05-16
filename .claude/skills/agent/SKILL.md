---
name: agent
description: "Top-level router for this workspace. Triggers: '/agent', 'agent menu', 'what should I work on', 'open the agent', 'start agent', 'menu principal'. Shows a picker (School / Work / Other) and routes the user to the chosen sub-skill. Read SPEC.md at the repo root for the full architecture."
---

# Agent — top-level router

Entry point for the `agent/` workspace. When invoked, show the user a picker and route to the right sub-skill.

## Behavior

1. **Greet briefly** — one sentence, friendly. e.g. *"What do you want to work on?"*
2. **Use AskUserQuestion** with three options:
   - 📚 **School** — Homework, papers, exams (UNIR Master's program)
   - 💼 **Work** — Work projects *(coming soon)*
   - 💬 **Other** — Anything else — talks to you like normal Claude Code, no scripted flow
3. **Route based on answer:**
   - School → invoke the `school` skill (use the `Skill` tool)
   - Work → invoke the `work` skill
   - Other → invoke the `other` skill

## Shortcuts (no router needed)

These slash commands skip this menu and go directly to the sub-skill:
- `/school` — straight to school
- `/work` — straight to work
- `/other` — straight to other

## Inline routing

If the user says one of School / Work / Other inline in their first message (e.g. *"agent, school"*), skip the picker and route directly.
