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

## Directory Structure

```
openclaw-skills/
└── wiki-publisher/
    ├── SKILL.md
    ├── references/
    │   └── wiki-js-api.md
    └── scripts/
        └── publish_wiki.py
```

## Installation

1. Copy the skill directory to your OpenClaw skills folder:
   ```bash
   cp -r openclaw-skills/wiki-publisher ~/.openclaw/skills/
   ```

2. Ensure `WIKI_KEY` is set in your environment

3. Restart OpenClaw Gateway

## See Also

- [Anthropic Skills](../skills/) - Skills for Anthropic's Claude Code
