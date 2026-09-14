# OpenClaw Skills

This directory contains skills for [OpenClaw](https://github.com/openclaw/openclaw) - an AI agent framework.

## Skills

### wiki-publisher

Publish markdown content to Wiki.js with proper formatting and metadata handling.

**Location:** `openclaw-skills/wiki-publisher/`

**Features:**
- Automatic YAML frontmatter removal
- Proper Wiki.js GraphQL API integration
- Content formatting and validation
- Automatic tagging and path suggestions

**Usage:**
Place this skill in your OpenClaw skills directory (usually `~/.openclaw/skills/`).

**Requirements:**
- `WIKI_KEY` environment variable set
- Python 3.6+ with `requests` library (for helper script)

**Files:**
- `SKILL.md` - Main skill documentation
- `references/wiki-js-api.md` - Wiki.js GraphQL API reference
- `scripts/publish_wiki.py` - Helper script for publishing

### git-commit

Smart git commit with remote sync, amend intelligence, and conventional commits.

**Location:** `openclaw-skills/git-commit/`

**Features:**
- Automatic remote sync before committing (rebase if needed)
- Smart amend analysis (only when safe)
- Conventional commit message generation
- Proper author/committer attribution
- Conflict handling guidance

**Usage:**
Place this skill in your OpenClaw skills directory (usually `~/.openclaw/skills/`).

**Author/Committer Convention:**
- **Author**: `Hugo Gu <hugogu@outlook.com>` — The user who initiated the work
- **Committer**: `Lucy <hugogu.bot@outlook.com>` — The AI agent performing the commit

**Trigger phrases:**
- "commit these changes"
- "save work to git"
- "stage and commit"
- "push code"

**Files:**
- `SKILL.md` - Main skill documentation

### progressive-technical-narrative

A methodology for writing technical long-form articles and series. Two threads: **content follows the reader's understanding**, and **language should read like a person wrote it**.

**Location:** `openclaw-skills/progressive-technical-narrative/`

**Features:**
- Purpose before means: answer "why does this exist" before "how we built it"
- Progressive exposition: introduce concepts in the order a reader can absorb them
- Explain every term on first appearance (what it is, what it does, who made it, how it differs from its siblings)
- No bare tables, no testing sections, no meta-commentary about the writer's own principles
- Style pass: kill "not A but B" constructions, uniform paragraph shapes, filler adverbs, and trailing summary sentences

**Trigger phrases:**
- "write the next article in the series"
- "太模板化" / "AI 味重" / "语气生硬"
- "rewrite it like a tech blog, not a spec doc"

**Files:**
- `SKILL.md` - Main skill documentation

## Directory Structure

```
openclaw-skills/
├── wiki-publisher/
│   ├── SKILL.md
│   ├── references/
│   │   └── wiki-js-api.md
│   └── scripts/
│       └── publish_wiki.py
├── git-commit/
│   └── SKILL.md
└── progressive-technical-narrative/
    └── SKILL.md
```

## Installation

1. Copy the skill directories to your OpenClaw skills folder:
   ```bash
   cp -r openclaw-skills/wiki-publisher ~/.openclaw/skills/
   cp -r openclaw-skills/git-commit ~/.openclaw/skills/
   cp -r openclaw-skills/progressive-technical-narrative ~/.openclaw/skills/
   ```

2. For wiki-publisher: Ensure `WIKI_KEY` is set in your environment

3. Restart OpenClaw Gateway

## See Also

- [Anthropic Skills](../skills/) - Skills for Anthropic's Claude Code
- [OpenClaw Documentation](https://docs.openclaw.ai) - OpenClaw framework docs
