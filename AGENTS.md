# Project Context for AI Assistants

## What This Project Is

This is a **Skills Repository** - a collection of Claude Code skills that can be installed by others via `npx skills add` or manual configuration.

## Directory Structure

```
/mnt/e/OpenSource/skills/
├── skills/                          # DELIVERABLES - Skills for others to use
│   ├── docker-deploy/              # Docker deployment infrastructure skill
│   ├── dockerhub-to-aliyun-acr-sync/ # Docker Hub to Aliyun ACR sync skill
│   └── grant-gitlab/               # GitLab permission management skill
├── .agents/skills/                  # DEPENDENCIES - Skills used BY this project
│   └── git-commit/                 # Skill for creating git commits
├── .claude/                         # Claude-specific configuration
├── README.md                        # Project documentation
└── AGENTS.md                        # This file
```

## Critical Rules

### 1. Skills Location
- **NEW skills go in `skills/`** - This is what gets distributed to users
- **`.agents/skills/` is for project dependencies only** - Skills this repo uses internally
- **Never put deliverable skills in `.agents/skills/`**

### 2. Skill Structure
Each skill in `skills/` should follow:
```
skills/<skill-name>/
├── SKILL.md              # Required: Main skill definition
├── scripts/              # Optional: Helper scripts
├── references/           # Optional: Reference templates
├── examples/             # Optional: Usage examples
└── evals/                # Optional: Test cases
```

### 3. Adding a New Skill

When creating a new skill:
1. Create directory under `skills/<skill-name>/`
2. Write SKILL.md with proper frontmatter (name, description)
3. Add any bundled resources (scripts, templates, examples)
4. Update README.md with skill documentation
5. Commit all changes

### 4. README.md Updates

When adding skills, update:
- Skills list section with description and features
- Project structure diagram
- Installation examples with correct paths (`skills/`, NOT `.agents/skills/`)

### 5. Git Conventions

- Use conventional commits: `feat:`, `fix:`, `docs:`
- One logical change per commit
- Update README.md in same PR as new skill

## Common Mistakes to Avoid

❌ **DON'T**: Put new skills in `.agents/skills/`  
✅ **DO**: Put new skills in `skills/`

❌ **DON'T**: Reference `.agents/skills/` in README.md  
✅ **DO**: Reference `skills/` in README.md

❌ **DON'T**: Think `.agents/skills/` is for distribution  
✅ **DO**: Remember `.agents/skills/` is only for this project's internal use

## Project Conventions

- **Language**: Chinese (README.md), English (SKILL.md and code)
- **License**: MIT
- **Documentation**: Every skill must have working examples in README
- **Paths**: Always use relative paths from repo root in documentation

## Testing New Skills

Before committing a new skill:
1. Verify skill structure matches convention
2. Check all paths in README.md point to `skills/`
3. Ensure scripts are executable (`chmod +x`)
4. Test skill can be loaded by Claude Code

## Questions?

If unsure about skill placement or structure, prefer `skills/` over `.agents/skills/` - it's better to have a skill in the deliverables folder than hidden in dependencies.
