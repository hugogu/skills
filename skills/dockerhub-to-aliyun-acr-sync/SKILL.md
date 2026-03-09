---
name: dockerhub-to-aliyun-acr-sync
description: Sync a Docker Hub image tag into Aliyun ACR Personal with the same repository basename and tag. Supports platform selection (linux/amd64, linux/arm64, etc.) and a two-phase network-switch workflow for environments behind the GFW where Docker Hub and Aliyun ACR are on separate networks. Use when user gives an image like ubuntu/apache2:2.4-21.10_beta or asks to sync/mirror a Docker image to Aliyun ACR.
license: MIT
compatibility: Requires docker CLI and access to Aliyun ACR Personal.
---

Sync one Docker image tag from Docker Hub to Aliyun ACR Personal, with optional platform selection and a two-phase pull-then-push flow for network-switching environments.

**Input**

- A full Docker image reference with tag (for example `ubuntu/apache2:2.4-21.10_beta`).
- Optional platform (for example `linux/amd64`, `linux/arm64`). Default: `linux/amd64`.

If the user doesn't specify a platform, assume `linux/amd64` and mention it in your plan so they can correct it before running.

**Required environment variables**

- `ALIYUN_ACR_REGISTRY`: ACR Personal registry + namespace prefix, for example `crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com/hugopub`
- `ALIYUN_ACR_USERNAME`: Aliyun ACR username
- `ALIYUN_ACR_PASSWORD`: Aliyun ACR login password (must come from env var, never hardcode)

**Steps**

1. Validate input image has a tag (`name:tag`). If no tag is provided, stop and ask user to provide one.

2. Derive target repo name from the input image basename (the last path segment before `:`):
   - `ubuntu/apache2:2.4-21.10_beta` -> repo basename `apache2`
   - `library/nginx:1.27.3` -> repo basename `nginx`

3. Build target image reference:
   - `<ALIYUN_ACR_REGISTRY>/<repo_basename>:<same_tag>`

4. Set `SOURCE_IMAGE` to the exact user-provided input image (do not alter tag/repository path).

5. **Phase 1 — Pull from Docker Hub** (requires Docker Hub network access):

```bash
set -euo pipefail

SOURCE_IMAGE="<input-image-with-tag-from-user>"
PLATFORM="${PLATFORM:-linux/amd64}"

echo "Pulling ${SOURCE_IMAGE} (${PLATFORM}) from Docker Hub..."
docker pull --platform "${PLATFORM}" "${SOURCE_IMAGE}"
echo "Pull complete."
```

6. **Network-switch prompt**: After the pull succeeds, pause and ask the user to confirm they are ready to proceed:

   > "Phase 1 complete — image pulled from Docker Hub. If you need to switch to a network with Aliyun ACR access (e.g., disable VPN / switch Wi-Fi), do so now. Reply **yes** or **continue** when ready to push."

   Wait for the user's confirmation before running Phase 2.

7. **Phase 2 — Tag and push to Aliyun ACR** (requires Aliyun network access):

```bash
set -euo pipefail

: "${ALIYUN_ACR_REGISTRY:?Missing ALIYUN_ACR_REGISTRY}"
: "${ALIYUN_ACR_USERNAME:?Missing ALIYUN_ACR_USERNAME}"
: "${ALIYUN_ACR_PASSWORD:?Missing ALIYUN_ACR_PASSWORD}"

SOURCE_IMAGE="<input-image-with-tag-from-user>"
SOURCE_REPO="${SOURCE_IMAGE%%:*}"
SOURCE_TAG="${SOURCE_IMAGE##*:}"
TARGET_REPO_BASENAME="${SOURCE_REPO##*/}"
TARGET_IMAGE="${ALIYUN_ACR_REGISTRY}/${TARGET_REPO_BASENAME}:${SOURCE_TAG}"

printf '%s' "$ALIYUN_ACR_PASSWORD" | docker login "${ALIYUN_ACR_REGISTRY%%/*}" -u "$ALIYUN_ACR_USERNAME" --password-stdin
docker tag "${SOURCE_IMAGE}" "${TARGET_IMAGE}"
docker push "${TARGET_IMAGE}"

echo "Synced: ${SOURCE_IMAGE} -> ${TARGET_IMAGE}"
```

8. Return the final pushed image URL and remind user that the destination repo must already exist in ACR if auto-create is disabled.

**Output format**

```text
Sync complete.
Source:   <source-image>  [platform: linux/amd64]
Target:   <acr-image>
```

**Guardrails**

- Never print or hardcode `ALIYUN_ACR_PASSWORD`.
- Always use `docker login --password-stdin`.
- Preserve the input tag exactly.
- Use the repository basename for target naming to match expected format like `.../hugopub/apache2:<tag>`.
- Always show the platform being used so the user can catch mismatches before the pull runs.
