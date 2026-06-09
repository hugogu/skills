---
name: wordpress-blogger
description: >
  Publish articles to WordPress blogs via REST API. Handles post creation, category/tag management,
  and SEO-friendly English slug generation. Use when user asks to publish blog posts, create WordPress
  articles, post content to their blog, or transfer/move content to their blog. TRIGGER this skill whenever user mentions publishing to
  blog, WordPress posting, creating articles on their WordPress site, or transferring content to blog.
triggers:
  - "publish to blog"
  - "post to blog"
  - "create blog post"
  - "WordPress posting"
  - "publish article"
  - "转到 blog"
  - "转到博客"
  - "发布到博客"
  - "发布到 blog"
  - "sync to blog"
  - "move to blog"
  - "transfer to blog"
  - "发到博客"
  - "发到 blog"
license: MIT
allowed-tools: Bash
---

# WordPress Blog Publisher

Publish articles to WordPress blogs safely with automatic category/tag management and English URL slugs.

---

## When to Use This Skill

**Trigger this skill when user says:**
- "publish to blog" / "post to blog" / "create blog post"
- "WordPress posting" / "publish article"
- "转到 blog" / "转到博客" / "发布到博客" / "发布到 blog"
- "sync to blog" / "move to blog" / "transfer to blog"
- "发到博客" / "发到 blog"
- "把这篇文章发到博客"
- "转到我/他的 Blog"

**Do NOT use browser automation for WordPress.** The correct approach is:
1. Read this skill
2. Use WordPress REST API with curl + Application Password
3. Never use browser login/form submission for API operations

**Why not browser?**
- Browser automation is fragile and slow
- WordPress has nonce/CSRF protection that breaks scripted form submission
- REST API is the official, stable way to programmatically manage WordPress content
- Application Passwords are designed for exactly this use case
- Browser sessions get stuck with targetId mismatch errors
- Form-based login is for humans, API calls are for automation

---

## Prerequisites
- WordPress has nonce/CSRF protection that breaks scripted form submission
- REST API is the official, stable way to programmatically manage WordPress content
- Application Passwords are designed for exactly this use case

WordPress credentials must be configured in the workspace `.env` file:

```bash
# WordPress Blog Credentials
WP_BLOG_URL="https://blog.example.com"      # Blog base URL (no trailing slash)
WP_USERNAME="your_username"                  # WordPress admin username (NOT display name)
WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx"   # Application password
```

**Critical: Username vs Display Name**
- `WP_USERNAME` must be the **WordPress login username** (e.g., `your_login_username`), NOT the display name (e.g., `Your Display Name`)
- The login username is what you enter on the wp-login.php form
- Display name is what appears on the blog posts
- If unsure, check the WordPress admin dashboard → Users → All Users → the "Username" column
- Common mistake: Using display name instead of login username will cause 401 errors

**How to create an Application Password:**
1. Log in to WordPress admin dashboard
2. Go to Users → Profile
3. Scroll to "Application Passwords" section
4. Click "Add New Application Password"
5. Copy the generated password (keep the spaces — they are part of the password)

---

## Step 1 — Read Credentials & Verify Username

Read credentials from workspace `.env`:

```bash
# Load credentials from .env file
source /root/.openclaw/workspace/.env

WP_URL="${WP_BLOG_URL:-https://blog.example.com}"
WP_USER="${WP_USERNAME}"
WP_PASS="${WP_APP_PASSWORD}"

# Verify credentials exist
if [ -z "$WP_USER" ]; then
  echo "❌ Error: WP_USERNAME not found in .env file"
  exit 1
fi

if [ -z "$WP_PASS" ]; then
  echo "❌ Error: WP_APP_PASSWORD not found in .env file"
  exit 1
fi

# Verify username is correct (not display name)
# Test with a simple API call first
echo "Verifying credentials..."
AUTH_TEST=$(curl -s "${WP_URL}/wp-json/wp/v2/users/me" \
  --user "${WP_USER}:${WP_PASS}")

if echo "$AUTH_TEST" | grep -q '"code":"rest_not_logged_in"'; then
  echo "❌ Authentication failed. Common causes:"
  echo "   1. WP_USERNAME is the display name instead of login username"
  echo "   2. WP_APP_PASSWORD is incorrect or expired"
  echo "   3. WordPress REST API is disabled"
  exit 1
fi

if echo "$AUTH_TEST" | grep -q '"id":'; then
  echo "✅ Authentication successful"
  echo "   User: $(echo "$AUTH_TEST" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)"
else
  echo "⚠️ Unexpected API response: $AUTH_TEST"
fi
```

---

## Step 2 — Analyze Content & Generate Metadata

Before publishing, analyze the article content to generate appropriate metadata:

### Generate English Slug

Create a URL-friendly English slug from the article title or content:

- Use lowercase with hyphens as separators
- Keep it under 50 characters when possible
- Include main keywords
- Remove stop words (a, an, the, and, or, etc.)

**Examples:**
- "AMD Ryzen 9 7950X vs Intel Core i9-13900K: A Detailed Benchmark Comparison" → `ryzen-7950x-vs-i9-13900k-benchmark-comparison`
- "How to Optimize Database Performance in Production" → `optimize-database-performance-production`
- "Understanding Container Orchestration with Kubernetes" → `understanding-container-orchestration-kubernetes`

### Suggest Categories & Tags

Based on article content, suggest appropriate WordPress categories and tags:

| Content Type | Suggested Categories | Suggested Tags |
|-------------|---------------------|----------------|
| Hardware reviews | Hardware, Reviews | CPU, benchmark, performance, AMD, Intel |
| Software development | Development, Programming | coding, best-practices, architecture |
| AI/LLM related | AI, Technology | machine-learning, LLM, artificial-intelligence |
| Career development | Career | career-growth, soft-skills, productivity |
| DevOps/Infrastructure | DevOps, Infrastructure | docker, kubernetes, ci-cd, cloud |

If user doesn't specify, use these reasonable defaults:
- **Category**: Based on content topic (create if not exists)
- **Tags**: Extract 2-4 keywords from content

---

## Step 3 — Create Category (if needed)

Check if category exists, create if not:

```bash
CATEGORY_NAME="Hardware"  # Use suggested or user-specified category

# Try to find existing category
CAT_ID=$(curl -s "${WP_URL}/wp-json/wp/v2/categories?search=${CATEGORY_NAME}&per_page=1" \
  -u "${WP_USER}:${WP_PASS}" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

# Create if not exists
if [ -z "$CAT_ID" ]; then
  CAT_RESULT=$(curl -s -X POST "${WP_URL}/wp-json/wp/v2/categories" \
    -u "${WP_USER}:${WP_PASS}" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"${CATEGORY_NAME}\"}")
  CAT_ID=$(echo "$CAT_RESULT" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
fi

echo "Category ID: $CAT_ID"
```

---

## Step 4 — Create Tags (if needed)

For each tag, check existence and create if needed:

```bash
TAGS=("CPU" "Benchmark" "AMD" "Performance")  # Use suggested or user-specified tags
TAG_IDS=""

for TAG in "${TAGS[@]}"; do
  # Try to find existing tag
  TID=$(curl -s "${WP_URL}/wp-json/wp/v2/tags?search=${TAG}&per_page=1" \
    -u "${WP_USER}:${WP_PASS}" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
  
  # Create if not exists
  if [ -z "$TID" ]; then
    TAG_RESULT=$(curl -s -X POST "${WP_URL}/wp-json/wp/v2/tags" \
      -u "${WP_USER}:${WP_PASS}" \
      -H "Content-Type: application/json" \
      -d "{\"name\": \"${TAG}\"}")
    TID=$(echo "$TAG_RESULT" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
  fi
  
  TAG_IDS="${TAG_IDS},${TID}"
done

# Remove leading comma
TAG_IDS=$(echo "$TAG_IDS" | sed 's/^,//')
echo "Tag IDs: $TAG_IDS"
```

---

## Step 5 — Create or Update Post

**⚠️ Important: Use Python for JSON handling, NOT bash string interpolation**

Bash string interpolation with JSON is extremely error-prone due to:
- Quote escaping issues (`"` → `\"`)
- Newline handling in content
- Special characters breaking JSON structure

**Recommended approach: Use Python script with curl**

```python
import json
import subprocess

# Post data
post_data = {
    "title": "Your Article Title",
    "content": "<p>HTML content...</p>",  # Pre-converted to HTML
    "slug": "your-article-slug",
    "excerpt": "Brief description...",
    "status": "publish",
    "categories": [1],
    "tags": []
}

# Write JSON to temp file
with open("/tmp/post_data.json", "w", encoding="utf-8") as f:
    json.dump(post_data, f, ensure_ascii=False)

# Use curl with file-based JSON
result = subprocess.run([
    "curl", "-s", "-X", "POST",
    f"{WP_URL}/wp-json/wp/v2/posts",
    "--user", f"{WP_USER}:{WP_PASS}",
    "-H", "Content-Type: application/json",
    "-d", "@/tmp/post_data.json"  # @filename reads from file
], capture_output=True, text=True)

response = result.stdout
if '"code":"' in response:
    print(f"❌ Error: {response}")
else:
    data = json.loads(response)
    print(f"✅ Published: {WP_URL}/{post_data['slug']}/")
```

**Alternative: Pure curl with heredoc (for simple content)**

```bash
# Only use for simple content without special characters
cat > /tmp/post_data.json << 'EOF'
{
  "title": "Simple Title",
  "content": "<p>Simple content without quotes or newlines</p>",
  "status": "publish"
}
EOF

POST_RESULT=$(curl -s -X POST "${WP_URL}/wp-json/wp/v2/posts" \
  --user "${WP_USER}:${WP_PASS}" \
  -H "Content-Type: application/json" \
  -d "@/tmp/post_data.json")
```

**❌ NEVER do this (bash string interpolation):**
```bash
# DON'T DO THIS — breaks with quotes, newlines, special chars
POST_RESULT=$(curl -s -X POST "${WP_URL}/wp-json/wp/v2/posts" \
  -u "${WP_USER}:${WP_PASS}" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"${TITLE}\",
    \"content\": \"${CONTENT}\"
  }")
```

---

## Step 6 — Generate Public URL

Construct the public viewing URL (not the API endpoint):

```bash
# WordPress permalink structure: /{slug}/
PUBLIC_URL="${WP_URL}/${SLUG}/"

# If slug not set, use post ID format
if [ -z "$SLUG" ]; then
  PUBLIC_URL="${WP_URL}/?p=${POST_ID}"
fi

echo "✅ Article published successfully!"
echo ""
echo "📄 Title: ${TITLE}"
echo "🔗 URL: ${PUBLIC_URL}"
echo "📁 Category: ${CATEGORY_NAME}"
echo "🏷️ Tags: ${TAGS[*]}"
```

---

## Content Conversion

### Markdown to HTML

WordPress content field requires HTML. Convert markdown:

| Markdown | HTML |
|----------|------|
| `# Title` | `<h1>Title</h1>` |
| `## Subtitle` | `<h2>Subtitle</h2>` |
| `### H3` | `<h3>H3</h3>` |
| `**bold**` | `<strong>bold</strong>` |
| `*italic*` | `<em>italic</em>` |
| `- list item` | `<ul><li>list item</li></ul>` |
| `1. item` | `<ol><li>item</li></ol>` |
| `[text](url)` | `<a href="url">text</a>` |
| `` `code` `` | `<code>code</code>` |
| ````code block```` | `<pre><code>code block</code></pre>` |

### Handling Special Characters

Escape double quotes in content when building JSON:

```bash
# Escape quotes for JSON
ESCAPED_CONTENT=$(echo "$CONTENT" | sed 's/"/\\"/g')
```

---

## Complete Workflow Example

```bash
#!/bin/bash

# Load credentials
source /root/.openclaw/workspace/.env
WP_URL="${WP_BLOG_URL:-https://blog.example.com}"
WP_USER="${WP_USERNAME:-admin}"
WP_PASS="${WP_APP_PASSWORD}"

# Article content - CPU Benchmark example
TITLE="AMD Ryzen 9 7950X vs Intel Core i9-13900K: A Detailed Benchmark Comparison"
SLUG="ryzen-7950x-vs-i9-13900k-benchmark-comparison"
CATEGORY="Hardware"
TAGS=("CPU" "Benchmark" "AMD" "Intel" "Performance")

CONTENT="<p>The battle for desktop CPU supremacy continues...</p><h2>Test Methodology</h2><p>All tests were conducted on identical platforms...</p>"

# Step 1: Create/Get Category
CAT_RESULT=$(curl -s -X POST "${WP_URL}/wp-json/wp/v2/categories" \
  -u "${WP_USER}:${WP_PASS}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${CATEGORY}\"}")
CAT_ID=$(echo "$CAT_RESULT" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

# Step 2: Create/Get Tags
TAG_IDS=""
for TAG in "${TAGS[@]}"; do
  TAG_RESULT=$(curl -s -X POST "${WP_URL}/wp-json/wp/v2/tags" \
    -u "${WP_USER}:${WP_PASS}" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"${TAG}\"}")
  TID=$(echo "$TAG_RESULT" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
  TAG_IDS="${TAG_IDS},${TID}"
done
TAG_IDS=$(echo "$TAG_IDS" | sed 's/^,//')

# Step 3: Create Post
POST_RESULT=$(curl -s -X POST "${WP_URL}/wp-json/wp/v2/posts" \
  -u "${WP_USER}:${WP_PASS}" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"${TITLE}\",
    \"content\": \"${CONTENT}\",
    \"slug\": \"${SLUG}\",
    \"status\": \"publish\",
    \"categories\": [${CAT_ID}],
    \"tags\": [${TAG_IDS}]
  }")

POST_ID=$(echo "$POST_RESULT" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
PUBLIC_URL="${WP_URL}/${SLUG}/"

echo "✅ Published: ${PUBLIC_URL}"
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` / `rest_not_logged_in` | Wrong username or app password | Verify `WP_USERNAME` is the **login username** (not display name). Check app password is correct. |
| `401 Forbidden` / `rest_forbidden_context` | Correct auth but insufficient permissions | User needs `publish_posts` capability. Use admin account. |
| `403 rest_cannot_create` | Authenticated but missing `edit_posts` capability | Verify user has publishing permissions in WordPress |
| `rest_invalid_json` | JSON payload malformed | Use Python `json.dump()` or file-based curl (`-d @file.json`), NOT bash string interpolation |
| `term_exists` | Category/tag already exists | Fetch existing ID instead of creating |

### API Response Check

Always check API responses for errors:

```bash
if echo "$RESULT" | grep -q '"code":"'; then
  ERROR_CODE=$(echo "$RESULT" | grep -o '"code":"[^"]*"' | head -1)
  ERROR_MSG=$(echo "$RESULT" | grep -o '"message":"[^"]*"' | head -1)
  echo "❌ API Error: $ERROR_CODE - $ERROR_MSG"
  exit 1
fi
```

---

## Safety Rules

- ✅ Always generate English slug for SEO-friendly URLs
- ✅ Create reasonable category/tags if user doesn't specify
- ✅ Return public viewing URL, not API endpoint
- ✅ Escape content properly for JSON payload (use Python or file-based curl)
- ✅ Verify credentials before attempting API calls (test with `/wp-json/wp/v2/users/me`)
- ✅ Use `curl --user` for Basic Auth (handles Base64 encoding correctly)
- ❌ Never hardcode credentials in scripts
- ❌ Never return API URLs (with /wp-json/) as the result
- ❌ Never use bash string interpolation for JSON payloads (breaks with quotes/newlines)
- ❌ Never use Python `urllib.request` with manual Basic Auth header (use `curl --user` instead)

---

## Troubleshooting Guide

### Issue: "rest_not_logged_in" (401)

**Symptoms:** API returns `{"code":"rest_not_logged_in","message":"您目前没有登录。"}`

**Root Causes:**
1. **Wrong username** — Using display name instead of login username
   - Display name: `Your Display Name` ❌
   - Login username: `your_login_username` ✅
   - Fix: Check WordPress admin → Users → All Users → "Username" column

2. **Wrong password** — Using regular login password instead of Application Password
   - Regular password: your normal login password ❌
   - Application password: `xxxx xxxx xxxx xxxx xxxx` ✅
   - Fix: Generate Application Password in WordPress profile

3. **Application Password not enabled** — WordPress < 5.6 or disabled by plugin
   - Fix: Update WordPress or check security plugin settings

**Verification:**
```bash
# Test authentication
curl -s "${WP_URL}/wp-json/wp/v2/users/me" \
  --user "${WP_USER}:${WP_PASS}"

# Expected success response: {"id":1,"name":"Your Name",...}
# Expected fail response: {"code":"rest_not_logged_in",...}
```

### Issue: "rest_invalid_json" (400)

**Symptoms:** API returns `{"code":"rest_invalid_json","message":"传入的 JSON 体无效。"}`

**Root Cause:** Bash string interpolation breaks JSON structure

**Fix:** Use Python `json.dump()` or file-based curl:
```python
import json
with open("/tmp/post.json", "w") as f:
    json.dump(post_data, f, ensure_ascii=False)
# Then: curl -d @/tmp/post.json
```

### Issue: "rest_cannot_create" (401)

**Symptoms:** API returns `{"code":"rest_cannot_create","message":"抱歉，您不能为此用户创建文章。"}`

**Root Cause:** Authentication succeeded but user lacks `publish_posts` capability

**Fix:** Verify user has admin/editor role in WordPress

### Issue: Python `urllib.request` 401

**Symptoms:** Python script fails with 401, but curl works

**Root Cause:** `urllib.request` doesn't handle Basic Auth the same way as curl

**Fix:** Use `subprocess.run(["curl", "--user", f"{USER}:{PASS}", ...])` instead of `urllib.request`

---

## Response Format

After successful publication, respond with:

```
✅ Article published successfully!

📄 Title: [Article Title]
🔗 URL: [Public Viewing URL]
📁 Category: [Category Name]
🏷️ Tags: [Tag List]
```
