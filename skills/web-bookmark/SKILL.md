---
name: web-bookmark
description: Auto-bookmark and analyze websites shared in conversation. When the user sends a URL, fetch the page, extract title/category/primary purpose/key features/stack, persist to a local JSON store (and a kb mirror when kb MCP is available), and recall relevant bookmarks in future conversations. Use when the user shares a URL for saving, asks "我之前发给你的 X 网站是哪个", "之前收藏的关于 Y 的网站", or "我有哪些书签".
---

# Web Bookmark Skill

## When to use

Activate this skill when:

- The user sends a URL alone or with surrounding context (e.g., "看一下 https://example.com", "这个网站 https://...")
- The user asks to save / remember / bookmark a website
- The user asks about previously shared websites ("我之前发给你的 X 网站是哪个来着?", "之前那个关于 Y 的网站")
- The user asks to list or search bookmarks ("我收藏了哪些网站", "找一下我存过的 X 类书签")

## What this skill does

1. **Save**: detect URL → fetch → analyze → persist structured bookmark
2. **Recall**: search bookmarks by keyword, category, or domain
3. **List**: show all bookmarks grouped by category

## Storage

Primary store: `~/.claude/web-bookmarks/bookmarks.json`

File structure (JSON array, one entry per bookmark):

```json
[
  {
    "url": "https://www.example.com/path",
    "canonical_url": "https://www.example.com/path",
    "title": "Site Title",
    "description": "One-line description",
    "category": ["product", "education"],
    "primary_purpose": "1-2 sentence user-facing purpose",
    "key_features": ["...", "..."],
    "stack": ["Next.js", "Three.js"],
    "ip_notes": "License attribution, hardcoded secrets, trade secrets",
    "tags": ["keyword", "keyword"],
    "fetched_at": "2026-09-10T07:46:00Z",
    "status": "ok",
    "kb_mirror_path": "bookmarks/2026-09-10-example-com"
  }
]
```

Create `~/.claude/web-bookmarks/` if it does not exist.

When running in an environment with kb (next-wiki) MCP available (e.g., OpenClaw), also create a mirror page (see `OpenClaw integration` below).

## Save workflow

### Step 1: Detect URL

Pick the first URL from the user message. If the message contains multiple URLs, ask the user which to bookmark.

Normalize:

- Strip tracking params: `utm_*`, `fbclid`, `gclid`, `mc_*`, `_ga`
- Lowercase host
- Keep path and meaningful query params as-is
- Do not auto-resolve URL shorteners (could be link-rot traps)

### Step 2: Check duplicates

Before fetching, read `~/.claude/web-bookmarks/bookmarks.json` and check:

- Exact `canonical_url` match → ask: "Already bookmarked on YYYY-MM-DD. Update analysis or skip?"
- Same domain + similar title → warn the user before adding a near-duplicate

### Step 3: Fetch

Try in order:

1. `WebFetch` (Claude Code) / `web_fetch` (OpenClaw) for markdown extraction — preferred.
2. If returns thin content or fails, fall back to `curl`:

   ```bash
   curl -sL -A "Mozilla/5.0 (compatible; web-bookmark/1.0)" <url> | head -300
   ```

3. **GitHub README probe (new in v1.1)** — if the page looks like a Docsify / GitHub-rendered site and WebFetch only returns `Loading...` or similar shell:

   Detect GitHub hints in the raw HTML:

   - `<noscript>` fallback links pointing to `github.com/...`
   - `og:image` or `itemprop="image"` from `raw.githubusercontent.com/<owner>/<repo>/...`
   - `logo.webp` or `README.md` in same-path resources
   - Meta description mentioning "developers" / "open source" / community-driven language

   If hints found, extract `<owner>/<repo>` and `<branch>` (default: `master`, fall back to `main`), then fetch the README directly:

   ```bash
   # Try master first, then main
   for branch in master main; do
     curl -sLf "https://raw.githubusercontent.com/<owner>/<repo>/${branch}/README.md" \
       -o /tmp/readme.md && break
   done
   head -200 /tmp/readme.md  # title + intro + first sections
   ```

   This is the highest-yield strategy for curated-list sites (free-for.dev, awesome-* lists, GitHub-rendered docs) — WebFetch/readability cannot see the rendered Markdown content because Docsify hydrates client-side, but `raw.githubusercontent.com` serves the source directly.

4. For JS-heavy sites (HTML body is just `<div id="root"></div>`), fetch JS bundles for stack analysis:

   ```bash
   curl -sL <url> | grep -oE '<script[^>]+src="[^"]+"' | head -10
   curl -sL <bundle-url>
   ```

### Step 4: Analyze

Extract structured info. Be concise but useful.

| Field | Source |
|---|---|
| `title` | `<title>` or first `<h1>` |
| `description` | meta description or 1-line summary from first paragraph |
| `category` | pick 1-3 from the categories list below |
| `primary_purpose` | 1-2 sentences on what the site does (user value, not tech) |
| `key_features` | 3-5 concrete bullets |
| `stack` | if observable from HTML/headers/JS bundle; omit if uncertain |
| `ip_notes` | attribution, license, hardcoded secrets (flag prominently), trade secrets; omit if none |
| `tags` | 2-5 free-form keywords |

If the site is unreachable (404, 5xx, paywalled, geo-blocked), record `status: unreachable` and capture the failure mode in `description`. Do not fabricate stack / features.

### Step 5: Persist

Append the new entry to the JSON array. Use `Write` tool to save the file. Create `~/.claude/web-bookmarks/` directory if it does not exist.

If kb MCP is available, also create a mirror page (see `OpenClaw integration`). Set `kb_mirror_path` in the JSON entry.

### Step 6: Confirm

Reply with a brief summary:

```
✅ Bookmarked
- Title: <title>
- URL: <canonical_url>
- Category: <cats>
- Stack: <stack> (if any)
- <2-3 line summary>

📍 ~/.claude/web-bookmarks/bookmarks.json
🌐 kb: <path> (if mirrored)
```

## List workflow

When the user asks "我收藏了哪些网站" / "list bookmarks":

1. Read `~/.claude/web-bookmarks/bookmarks.json`
2. Group entries by primary `category`
3. Print compact grouped list with counts:

```
📚 My bookmarks (12 total)

### product (3)
- ORBIT · 太阳系漫游 — https://www.orbits.observer/ (2026-09-10)
- ...

### blog (2)
- ...
```

In OpenClaw with kb MCP, also surface any kb `bookmarks/` pages not yet mirrored to JSON.

## Recall workflow

When the user asks "之前发过的 X 网站" / "找一下关于 Y 的网站":

1. Read JSON store.
2. Filter case-insensitive against `title`, `description`, `primary_purpose`, `tags`, `url`, `key_features`.
3. Rank: title match > description > tags > URL.
4. Return top 5 results with URL + title + date + 1-line snippet.
5. If no exact match, return closest 3 with note that they are close-but-not-exact matches.

In OpenClaw with kb MCP, also `next-wiki__search_wiki` on `bookmarks/` namespace for cross-session semantic results.

## Categories reference

Pick 1-3 categories that best describe the site's primary purpose.

| Category | Examples |
|---|---|
| `developer-tool` | GitHub projects, online editors, debuggers |
| `framework` | React, Astro, Next.js, Vue |
| `library` | Utility libraries, packages |
| `reference` | API docs, MDN, language references |
| `docs` | Product documentation |
| `blog` | Personal / company blogs |
| `article` | Long-form articles, essays |
| `tutorial` | How-to guides, courses |
| `product` | End-user web apps |
| `saas` | Subscription products |
| `design` | Design inspiration, galleries |
| `portfolio` | Personal / agency portfolios |
| `news` | News sites, aggregators |
| `academic` | Papers, journals, scientific |
| `research` | Research datasets, experiments |
| `entertainment` | Games, video, music |
| `social` | Social networks |
| `finance` | Trading, banking, crypto |
| `shopping` | E-commerce |
| `other` | Doesn't fit above |

## Examples

### Example 1: Save a website

User: "看一下 https://www.orbits.observer/"

1. URL: `https://www.orbits.observer/` (already canonical)
2. `WebFetch` succeeds, returns markdown with title "ORBIT · 太阳系漫游"
3. Analysis:

   ```json
   {
     "url": "https://www.orbits.observer/",
     "canonical_url": "https://www.orbits.observer/",
     "title": "ORBIT · 太阳系漫游",
     "description": "从太阳到奥尔特云,探索运行中的三维太阳系。调节时间,走近行星,理解我们的宇宙家园。",
     "category": ["product", "education"],
     "primary_purpose": "Interactive 3D solar system explorer with time controls and multi-language UI, covering 14 bodies from sun to Oort cloud comets.",
     "key_features": [
       "14 天体 (太阳、行星、冥王星、4 颗彗星)",
       "时间流速实时控制(实时 / 1 天每秒 / 1 年每秒 / 10 年每秒)",
       "多语言(简体中文 / English / 日本語)",
       "Keplerian 实时位置计算 (cosinekitty/astronomy)",
       "移动端响应式"
     ],
     "stack": ["Next.js", "vinext (RSC runtime)", "Three.js", "cosinekitty/astronomy"],
     "ip_notes": "数据来源 NASA / JPL (Public Domain); cosinekitty/astronomy (MIT). Bundle is open: client-side only, no backend, all logic in JS.",
     "tags": ["solar-system", "3d", "astronomy", "real-time", "education"],
     "fetched_at": "2026-09-10T07:46:00Z",
     "status": "ok"
   }
   ```

4. No duplicate in JSON.
5. Persist to JSON + kb mirror at `bookmarks/2026-09-10-orbits-observer`.
6. Reply with brief confirmation.

### Example 2: Recall

User: "我之前发给你的那个太阳系网站是哪个来着?"

1. Read JSON; search keyword "太阳系".
2. Match: ORBIT · 太阳系漫游.
3. Optional: `next-wiki__search_wiki` for cross-session results.
4. Reply: "ORBIT · 太阳系漫游 — https://www.orbits.observer/ — bookmarked 2026-09-10. Interactive 3D solar system with 14 bodies."

### Example 3: List all

User: "我收藏了哪些网站?"

Read JSON, group by primary category, print compact grouped list with counts.

## Notes

- Do not bookmark sites with credentials / private content; warn the user first.
- Strip tracking params before storing the canonical URL.
- If the site is down / 404 / paywalled / behind login, record `status: unreachable` and the failure cause in `description`. Do not fabricate content.
- Stack inference should be conservative — only include what is clearly observable from HTML / JS bundles / headers.
- IP / security: hardcoded API keys, secrets, PII → flag prominently in both the reply and `ip_notes`.
- Analysis should be concise — this is a reference for future recall, not a full audit.
- Do not auto-resolve URL shorteners — they can be link-rot traps or hide the canonical destination.
- The skill is read-only on the URL itself. Do not follow `robots.txt` directives beyond what a normal browser would (no aggressive crawling, no auth bypass).

## OpenClaw integration

When running in OpenClaw with kb (next-wiki) MCP available, after persisting to JSON:

1. Create a kb page via `next-wiki__create_page`:

   - **Path**: `bookmarks/YYYY-MM-DD-<domain-slug>`
     - slug = host without TLD, dots replaced with dashes
     - e.g., `https://www.orbits.observer/` → `bookmarks/2026-09-10-orbits-observer`
   - **Space**: `generated`
   - **Locale**: `zh-CN` (Hugo's primary)
   - **Frontmatter**: type=Bookmark, source URL, category, tags, fetchDate, owner=Hugo
   - **Body**: structured analysis mirroring the JSON entry

2. Set `kb_mirror_path` in the JSON entry to the kb path.

3. For recall, prefer `next-wiki__search_wiki` on the `bookmarks/` namespace — it gives cross-session semantic results that pure JSON scan cannot.

4. List workflow: also surface kb `bookmarks/` pages not yet mirrored to JSON (run `next-wiki__list_pages pathPrefix=bookmarks`).

## Claude Code integration

- Primary store: JSON file (`~/.claude/web-bookmarks/bookmarks.json`)
- No kb mirror
- Tools: `WebFetch`, `Read`, `Write`, `Bash` (for `curl` fallback)
- For complex JS bundle analysis, optionally delegate to a sub-agent

## Maintenance

- The JSON store is append-mostly. Edits (deletes, corrections) should preserve the `fetched_at` of the original entry for audit.
- Periodically (e.g., weekly via cron), re-fetch the canonical URL of each bookmark to detect link rot or major content changes. Update `fetched_at` and note changes in `description`.
- If the JSON file is corrupted, back it up before rewriting: `cp bookmarks.json bookmarks.json.bak-$(date +%Y%m%d)`.