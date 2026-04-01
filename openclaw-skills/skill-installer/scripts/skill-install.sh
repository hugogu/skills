#!/bin/bash
# skill-install.sh - 从 ClawHub 安装 OpenClaw skill

set -e

SKILL_SLUG="$1"

if [ -z "$SKILL_SLUG" ]; then
    echo "Usage: $0 <author/skill-name>"
    echo "Example: $0 antonia-sz/opinion-analyzer"
    exit 1
fi

# 解析 author 和 skill name
AUTHOR=$(echo "$SKILL_SLUG" | cut -d'/' -f1)
SKILL_NAME=$(echo "$SKILL_SLUG" | cut -d'/' -f2)

echo "📦 Installing skill: $SKILL_SLUG"

# 1. 获取下载 URL
echo "🔍 Fetching download URL..."
CLAWHUB_URL="https://clawhub.ai/$SKILL_SLUG"
DOWNLOAD_URL=$(curl -s "$CLAWHUB_URL" | grep -oE 'https://[^"]+\.convex\.site/api/v1/download[^"]+' | head -1)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "❌ Failed to get download URL from $CLAWHUB_URL"
    exit 1
fi

echo "📥 Download URL: $DOWNLOAD_URL"

# 2. 下载 zip
ZIP_FILE="/tmp/${SKILL_NAME}.zip"
echo "⬇️  Downloading to $ZIP_FILE..."
curl -L -o "$ZIP_FILE" "$DOWNLOAD_URL"

# 3. 验证是 zip 文件
if ! file "$ZIP_FILE" | grep -q "Zip archive"; then
    echo "❌ Downloaded file is not a zip archive"
    rm -f "$ZIP_FILE"
    exit 1
fi

# 4. 解压（使用 Python，避免 unzip 依赖）
EXTRACT_DIR="/tmp/${SKILL_NAME}"
rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"

echo "📂 Extracting..."
python3 -c "import zipfile; zipfile.ZipFile('$ZIP_FILE').extractall('$EXTRACT_DIR')"

# 5. 安装到 skills 目录
SKILLS_DIR="$HOME/.openclaw/skills"
TARGET_DIR="$SKILLS_DIR/$SKILL_NAME"

if [ -d "$TARGET_DIR" ]; then
    echo "⚠️  Skill already exists at $TARGET_DIR"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Installation cancelled"
        rm -rf "$ZIP_FILE" "$EXTRACT_DIR"
        exit 1
    fi
    rm -rf "$TARGET_DIR"
fi

echo "🚀 Installing to $TARGET_DIR..."
cp -r "$EXTRACT_DIR" "$TARGET_DIR"

# 6. 验证
if [ -f "$TARGET_DIR/SKILL.md" ]; then
    echo "✅ Successfully installed $SKILL_SLUG"
    echo "📄 Location: $TARGET_DIR"
    echo ""
    echo "Skill content:"
    head -10 "$TARGET_DIR/SKILL.md" | grep -E "^(name:|description:)" || true
else
    echo "❌ Installation failed - SKILL.md not found"
    exit 1
fi

# 清理
rm -rf "$ZIP_FILE" "$EXTRACT_DIR"

echo ""
echo "🎉 Done! You can now use the skill."
