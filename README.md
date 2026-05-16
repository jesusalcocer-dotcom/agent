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
3. **Autonomous run** (status updates + final audit summary, no input required):
   - Preprocesses every file — `.pages` → `.docx` → `.md`, PDFs → text, videos → Whisper transcripts
   - Writes a comprehensive analysis of every source (one file each in `reasoning/sources/`)
   - Builds the maximize-score analysis; spawns a blind sub-agent (Opus, max effort) to critique it; synthesizes the final plan
   - Writes the outline, self-critiques it for rubric coverage and source integration, revises until clean
   - Drafts the document section by section into `output/draft.md`
   - Spawns a second blind sub-agent (Opus) to critique the draft; revises
   - Applies academic formatting (per instructions + `FORMATTING.md` gaps) and exports to `.docx`
   - **Surfaces an audit summary in chat** so you can audit the reasoning before opening the doc
   - **Opens the final Word doc in Microsoft Word**
4. **Word doc review**: you see the finished file; tell Claude *"looks good"* or *"change X"*

See `SPEC.md` for the full architecture.

## Session configuration (required)

This workspace is designed for **Claude Opus 4.7, max effort, dangerously-skip-permissions**. Launch with:
```bash
claude --dangerously-skip-permissions
```
Then run `/effort max` once in-session. Every sub-agent spawned by the skill also runs on Opus.

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
│       │   ├── sources/          per-source analyses (one comprehensive file per source)
│       │   ├── plan.md           maximize + plan + sub-agent A critique + sources index
│       │   ├── outline.md        outline with self-critique at top
│       │   ├── audit.md          chat-friendly audit summary
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
