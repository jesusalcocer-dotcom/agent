# agent

Personal Claude Code workspace. A single git-tracked folder that holds school, work, and other projects. Reusable slash-command skills walk Claude through repeatable workflows — mostly autonomous after a single "go" confirmation.

## How to use

1. Open Claude Code from this folder: `cd ~/Desktop/agent && claude`
2. Run a slash command:
   - `/agent` — top-level menu (School / Work / Other)
   - `/school` — school assignment flow
   - `/work` — work projects (stub for now)
   - `/other` — anything else (regular Claude Code, no scripted flow)

Claude reads the matching skill from `.claude/skills/` and walks you through the flow step-by-step.

## The school flow (overview)

**Two — and only two — user touchpoints.** Everything else is autonomous.

1. **Setup**: pick or create a project; drop your files; tell Claude "ready"
2. **"Go" confirmation**: Claude identifies your instructions and asks once if it should start the autonomous run
3. **Autonomous run** (status updates only, no input required):
   - Preprocesses every file — `.pages` → `.docx` → `.md`, PDFs → text, videos → Whisper transcripts
   - Reads everything, builds a maximize-score analysis with an internal adversarial review pass
   - Writes a single plan doc with reasoning + justifications inline
   - Executes the plan to draft `output/draft.md`
   - Self-reviews against success criteria
   - Exports to `.docx` with formatting pulled from the instructions
   - **Opens the final Word doc in Microsoft Word**
4. **Word doc review**: you see the finished file; tell Claude *"looks good"* or *"change X"*

See `SPEC.md` for the full architecture.

## Folder layout

```
agent/
├── SPEC.md                       architecture + design spec
├── CLAUDE.md                     project orientation for Claude
├── README.md                     this file
├── .env                          OPENAI_API_KEY (gitignored)
├── .gitignore                    excludes .env, media, unpacked dirs
├── .claude/
│   ├── skills/
│   │   ├── agent/                router menu
│   │   ├── school/               school assignment concierge
│   │   ├── work/                 stub
│   │   ├── other/                regular-Claude passthrough
│   │   ├── docx/                 Anthropic official — Word generation
│   │   └── pdf/                  Anthropic official — PDF reading
│   └── plugins/                  reserved
├── tools/
│   ├── transcribe.py             Whisper API wrapper (auto-chunks > 20MB)
│   ├── pages_to_md.py            .pages → .docx → .md (LibreOffice + pandoc)
│   └── estimate_pages.py         word-count → page estimate heuristic
├── school/                       one folder per assignment
│   └── <project-slug>/
│       ├── instructions/         drop the assignment brief here
│       ├── background/           drop class videos, slides, notes here
│       ├── transcripts/          auto-generated Whisper output
│       ├── reasoning/
│       │   ├── plan.md           maximize analysis + plan + reasoning (single doc)
│       │   └── progress.md       resumption state
│       └── output/
│           ├── draft.md          markdown source of truth
│           └── <slug>_v<N>.docx  Word exports
├── work/                         reserved
└── other/                        reserved
```

## Dependencies (all installed)

- `gh` — GitHub CLI
- `pandoc` — universal document converter
- `ffmpeg` — audio extraction from video
- `libreoffice` — headless `.pages` and `.doc` conversion
- `poppler` — `pdfinfo`, `pdftoppm`
- `docx-js` (npm global) — Word document creation
- `openai` (Python) — Whisper API client
- VS Code (`code` CLI on PATH) — for opening markdown reasoning files

## Resuming a project

If you close Claude Code mid-assignment and come back later:
1. Open Claude Code from `agent/`
2. Run `/school`
3. Pick the existing project — Claude reads `<project>/reasoning/progress.md` to see where it left off and continues from there.
