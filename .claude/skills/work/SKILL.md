---
name: work
description: "Work projects. Triggers: '/work', 'work project', 'trabajo', 'proyecto de trabajo'. Currently a stub — workflow is not yet designed. Offers the user a way to design it or return to the menu."
---

# Work — stub

The work flow hasn't been designed yet. We'll figure it out together when the user is ready.

## Behavior

1. Tell the user (friendly): *"The work flow isn't built yet. Want to design it now, or back to the menu?"*
2. Use AskUserQuestion with two options:
   - **Design it now** — ask the user what kinds of work projects they want to track, what the typical artifacts are, who consumes the output, etc. Then propose a structure analogous to `school/` and add it to SPEC.md.
   - **Back to /agent** — invoke the `agent` skill.

Do **not** scaffold work projects or invent workflow steps without the user's input.
