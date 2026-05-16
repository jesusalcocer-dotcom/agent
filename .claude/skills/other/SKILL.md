---
name: other
description: "Catch-all passthrough. Triggers: '/other', 'other project', 'algo más', 'algo distinto', 'pregunta general'. Drops the user back into a regular Claude Code conversation with no scripted flow — Claude responds normally to whatever the user asks. Use when the user wants to discuss something not covered by the school or work flows."
---

# Other — passthrough to regular Claude Code

There's no scripted flow here. The user picked "Other" because they want to talk to Claude as they normally would — ask a question, get help with something one-off, brainstorm, debug, etc.

## Behavior

1. Greet briefly. One sentence. e.g. *"What's on your mind? I'm listening."*
2. **Do not assume** the user wants any particular workflow.
3. Respond to their next message as regular Claude Code would — use whatever tools and reasoning the task requires.
4. If at any point the user says something that matches the school or work skill triggers, route to that skill instead.

That's it. No scaffolding, no checklists, no auto-files. Just be Claude.
