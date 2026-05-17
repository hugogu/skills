#!/usr/bin/env python3
"""
Wiki Publisher Script - Publish markdown content to Wiki.js via GraphQL API.

This script implements the wiki-publisher skill operations. For content formatting,
use the wiki-writer skill first.

Usage:
  python3 publish_to_wiki.py publish <file.md> --path <wiki/path> [--title <title>] [--description <desc>] [--tags tag1,tag2]
  python3 publish_to_wiki.py list
  python3 publish_to_wiki.py get <page-id>
  python3 publish_to_wiki.py delete <page-id>
"""

import argparse
import json
import os
import re
import sys

import requests


def get_wiki_config():
    """Get wiki configuration from environment variables."""
    wiki_key = os.environ.get("WIKI_KEY")
    raw_url = os.environ.get("WIKI_URL", "https://wiki.hugogu.cn")
    wiki_url = raw_url.rstrip('/')
    if not wiki_url.endswith('/graphql'):
        wiki_url = wiki_url + '/graphql'

    if not wiki_key:
        print("Error: WIKI_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    return wiki_url, wiki_key


def clean_content(content: str) -> str:
    """Remove YAML frontmatter from markdown content."""
    pattern = r'^---\s*\n.*?\n---\s*\n'
    return re.sub(pattern, '', content, flags=re.DOTALL).strip()


def extract_title(content: str, fallback: str) -> str:
    """Extract title from first H1 heading, or use fallback."""
    for line in content.split('\n'):
        if line.startswith('# '):
            return line[2:].strip()
    return fallback


def graphql_request(wiki_url: str, wiki_key: str, query: str, variables: dict = None) -> dict:
    """Execute a GraphQL request. Variables are JSON-serialized automatically."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(
        wiki_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wiki_key}"
        },
        data=json.dumps(payload)  # json.dumps handles all escaping
    )

    data = response.json()

    if data.get("errors"):
        print(f"⚠ GraphQL Error: {data['errors'][0]['message']}", file=sys.stderr)
        print(f"  Location: {data['errors'][0].get('locations')}", file=sys.stderr)

    return data


def list_pages(wiki_url: str, wiki_key: str) -> list:
    """List all wiki pages. Returns list of {id, path, title}."""
    query = """
    query {
      pages {
        list {
          id
          path
          title
        }
      }
    }
    """
    data = graphql_request(wiki_url, wiki_key, query)
    return data.get("data", {}).get("pages", {}).get("list", [])


def get_page(wiki_url: str, wiki_key: str, page_id: int) -> dict:
    """Get single page by ID."""
    query = """
    query GetPage($id: Int!) {
      pages {
        single(id: $id) {
          id
          path
          title
          content
          description
          tags { id tag }
        }
      }
    }
    """
    data = graphql_request(wiki_url, wiki_key, query, {"id": page_id})
    return data.get("data", {}).get("pages", {}).get("single")


def create_page(wiki_url: str, wiki_key: str, content: str, title: str,
                path: str, description: str = "", tags: list = None) -> dict:
    """Create a new Wiki.js page using GraphQL Variables."""
    query = """
    mutation CreatePage($content: String!, $title: String!,
                        $path: String!, $description: String!,
                        $tags: [String]!) {
      pages {
        create(
          content: $content
          title: $title
          path: $path
          description: $description
          tags: $tags
          editor: "markdown"
          isPublished: true
          isPrivate: false
          locale: "zh"
        ) {
          page { id path title }
          responseResult { succeeded errorCode message }
        }
      }
    }
    """
    variables = {
        "content": content,
        "title": title,
        "path": path,
        "description": description or title,
        "tags": tags or []
    }
    return graphql_request(wiki_url, wiki_key, query, variables)


def update_page(wiki_url: str, wiki_key: str, page_id: int, content: str,
                title: str, description: str = "", tags: list = None) -> dict:
    """Update an existing Wiki.js page using GraphQL Variables."""
    query = """
    mutation UpdatePage($id: Int!, $content: String!, $title: String!,
                        $description: String!, $tags: [String]!) {
      pages {
        update(
          id: $id
          content: $content
          title: $title
          description: $description
          tags: $tags
          editor: "markdown"
          isPublished: true
          isPrivate: false
        ) {
          page { id path title }
          responseResult { succeeded errorCode message }
        }
      }
    }
    """
    variables = {
        "id": page_id,
        "content": content,
        "title": title,
        "description": description or title,
        "tags": tags or []
    }
    return graphql_request(wiki_url, wiki_key, query, variables)


def delete_page(wiki_url: str, wiki_key: str, page_id: int) -> dict:
    """Delete a wiki page by ID."""
    query = """
    mutation DeletePage($id: Int!) {
      pages {
        delete(id: $id) {
          responseResult { succeeded errorCode message }
        }
      }
    }
    """
    return graphql_request(wiki_url, wiki_key, query, {"id": page_id})


def find_page_by_path(pages: list, target_path: str) -> dict:
    """Find a page by path in the pages list."""
    return next((p for p in pages if p["path"] == target_path), None)


def cmd_publish(args, wiki_url, wiki_key):
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        raw_content = f.read()

    content = clean_content(raw_content)
    title = args.title or extract_title(content, os.path.basename(args.file))
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    pages = list_pages(wiki_url, wiki_key)
    existing = find_page_by_path(pages, args.path)

    if existing:
        print(f"📝 Updating existing page (ID: {existing['id']}, path: {args.path})")
        result = update_page(wiki_url, wiki_key, existing["id"], content, title, args.description or "", tags)
        res = result.get("data", {}).get("pages", {}).get("update", {}).get("responseResult", {})
        if res.get("succeeded"):
            base = wiki_url.replace("/graphql", "")
            print(f"✅ Updated: {base}/zh/{existing['path']} (ID: {existing['id']})")
        else:
            print(f"❌ Update failed: {res.get('message')}", file=sys.stderr)
            if res.get("errorCode") == 403:
                print("  → API key requires 'pages.update' permission", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"📝 Creating new page at path: {args.path}")
        result = create_page(wiki_url, wiki_key, content, title, args.path, args.description or "", tags)
        res = result.get("data", {}).get("pages", {}).get("create", {}).get("responseResult", {})
        page = result.get("data", {}).get("pages", {}).get("create", {}).get("page")
        if res.get("succeeded") and page:
            base = wiki_url.replace("/graphql", "")
            print(f"✅ Created: {base}/zh/{page['path']} (ID: {page['id']})")
        else:
            print(f"❌ Create failed: {res.get('message')}", file=sys.stderr)
            if res.get("errorCode") == 403:
                print("  → API key requires 'pages.create' permission", file=sys.stderr)
            sys.exit(1)


def cmd_get(args, wiki_url, wiki_key):
    page = get_page(wiki_url, wiki_key, args.id)
    if page:
        print(f"Title: {page['title']}")
        print(f"Path: {page['path']}")
        print(f"Content length: {len(page.get('content', ''))} chars")
        print("---")
        print(page.get("content", "(no content)"))
    else:
        print(f"❌ Page {args.id} not found", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args, wiki_url, wiki_key):
    confirm = input(f"⚠ Delete page ID {args.id}? Type 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return
    result = delete_page(wiki_url, wiki_key, args.id)
    res = result.get("data", {}).get("pages", {}).get("delete", {}).get("responseResult", {})
    if res.get("succeeded"):
        print(f"✅ Deleted page ID {args.id}")
    else:
        print(f"❌ Delete failed: {res.get('message')}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Publish markdown content to Wiki.js")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # publish
    pub = subparsers.add_parser("publish", help="Create or update a wiki page")
    pub.add_argument("file", help="Markdown file to publish")
    pub.add_argument("--path", "-p", required=True, help="Wiki page path (e.g. tech/security/guide)")
    pub.add_argument("--title", "-t", help="Page title (auto-extracted from H1)")
    pub.add_argument("--description", "-d", help="Page description")
    pub.add_argument("--tags", help="Comma-separated tags")

    # list
    subparsers.add_parser("list", help="List all wiki pages")

    # get
    get_parser = subparsers.add_parser("get", help="Get a page by ID")
    get_parser.add_argument("id", type=int, help="Page ID")

    # delete
    del_parser = subparsers.add_parser("delete", help="Delete a page by ID")
    del_parser.add_argument("id", type=int, help="Page ID")

    args = parser.parse_args()
    wiki_url, wiki_key = get_wiki_config()

    if args.action == "publish":
        cmd_publish(args, wiki_url, wiki_key)
    elif args.action == "list":
        pages = list_pages(wiki_url, wiki_key)
        print(f"Total pages: {len(pages)}")
        for p in sorted(pages, key=lambda x: x["id"]):
            print(f"  {p['id']:>4}  {p['path']}")
    elif args.action == "get":
        cmd_get(args, wiki_url, wiki_key)
    elif args.action == "delete":
        cmd_delete(args, wiki_url, wiki_key)


if __name__ == "__main__":
    main()
