# agent

Personal Claude Code workspace. A single git-tracked folder that holds school, work, and other projects, with reusable slash-command skills that walk Claude through repeatable workflows.

## How to use

1. Open Claude Code from this folder: `cd ~/Desktop/agent && claude`
2. Run a slash command:
   - `/agent` — top-level menu (School / Work / Other)
   - `/school` — jump straight to the school assignment flow
   - `/work` — work projects (stub)
   - `/other` — other projects (stub)

Claude reads the matching skill from `.claude/skills/` and walks you through the flow step-by-step.

## Folder layout

```
agent/
├── .claude/
│   ├── skills/
│   │   ├── agent/        router menu
│   │   ├── school/       school assignment concierge
│   │   ├── work/         stub
│   │   ├── other/        stub
│   │   ├── docx/         Anthropic official — Word document creation
│   │   └── pdf/          Anthropic official — PDF reading/extraction
│   └── plugins/          (reserved for future plugins)
├── tools/
│   ├── transcribe.py     Whisper API wrapper (video/audio → text)
│   └── pages_to_md.py    LibreOffice + pandoc wrapper (.pages → .md)
├── school/               one folder per assignment
│   └── <project-name>/
│       ├── instructions/    drop the assignment brief here
│       ├── background/      drop class videos, slides, notes here
│       ├── transcripts/     auto-generated Whisper output
│       ├── reasoning/       analysis, outline, progress (markdown)
│       └── output/          drafts + final .docx
├── work/                 stub for future use
├── other/                stub for future use
├── .env                  OPENAI_API_KEY (gitignored)
└── .gitignore
```

## Dependencies (already installed)

- `gh` — GitHub CLI
- `pandoc` — Universal document converter
- `ffmpeg` — Audio/video extraction
- `libreoffice` — Headless `.pages` and `.doc` conversion
- `docx-js` (npm global) — Word document creation
- `openai` (Python) — Whisper API client

## Resuming a project

If you close Claude Code mid-assignment and come back later:
1. Open Claude Code from `agent/`
2. Run `/school`
3. Pick the existing project — Claude reads `<project>/reasoning/progress.md` to see where you left off and continues from there.
