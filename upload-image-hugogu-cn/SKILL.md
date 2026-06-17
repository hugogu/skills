# Upload Image to hugogu.cn Skill

Use this skill to upload images to the hugogu.cn static file server for use in Wiki.js articles.

## Prerequisites

- SSH access to `ali-sh` server configured in local SSH config
- Target directory exists on server (create if needed)

## Upload Process

### 1. Create directory (if needed)

```bash
ssh ali-sh "mkdir -p /mnt/wordpress-compose/apache/static/img/wiki/{PAGE_ID}"
```

Replace `{PAGE_ID}` with the Wiki.js page ID.

### 2. Upload image

```bash
scp /local/path/to/image.jpg ali-sh:/mnt/wordpress-compose/apache/static/img/wiki/{PAGE_ID}/
```

### 3. Verify URL

After upload, the image is accessible at:

```
https://www.hugogu.cn/img/wiki/{PAGE_ID}/{filename}
```

## Example

```bash
# Create directory for page ID 1945
ssh ali-sh "mkdir -p /mnt/wordpress-compose/apache/static/img/wiki/1945"

# Upload image
scp /tmp/rule_of_thirds_001.jpg ali-sh:/mnt/wordpress-compose/apache/static/img/wiki/1945/

# Accessible at:
# https://www.hugogu.cn/img/wiki/1945/rule_of_thirds_001.jpg
```

## Notes

- Images must be uploaded before referencing them in Wiki.js markdown
- Use absolute HTTPS URLs in Wiki.js markdown: `https://www.hugogu.cn/img/wiki/{PAGE_ID}/{filename}`
- Supported formats: jpg, png, gif, webp
- Max file size: 20MB (recommended < 5MB for web use)
