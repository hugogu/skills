# Content-Image Pairing Skill

Generate contextually relevant example images for Wiki articles based on the content structure, and upload them to the hugogu.cn image server.

## When to Use

Use this skill when:
- A Wiki article has sections that would benefit from visual examples
- The content describes visual concepts (photography, design, architecture, etc.)
- You need to illustrate abstract concepts with concrete examples
- The article mentions specific techniques, styles, or patterns that can be visualized

## Process

### Step 1: Analyze Content Structure

Read the article content and identify:
- Sections that describe visual concepts or techniques
- Places where examples would enhance understanding
- Specific styles, patterns, or configurations mentioned

Example analysis for a photography article:
```
## 基础构图法则
### 三分法（Rule of Thirds）
→ Needs: Grid overlay example showing subject placement

### 黄金分割与黄金螺旋
→ Needs: Spiral overlay on natural scene

### 对称构图
→ Needs: Perfectly symmetrical building/reflection

### 引导线（Leading Lines）
→ Needs: Road/railroad leading to horizon

### 框架构图（Framing）
→ Needs: Natural frame (window/archway) with subject
```

### Step 2: Generate Targeted Images

For each identified section, generate an image that specifically illustrates that concept:

```bash
# Example: Generate for Rule of Thirds
mmx image generate --prompt "Photography composition rule of thirds, landscape with subject at intersection point, grid overlay visible, educational example, professional photo" \
  --aspect-ratio 3:2 --out-prefix rule_of_thirds --quiet

# Example: Generate for Golden Spiral
mmx image generate --prompt "Golden ratio spiral composition, Fibonacci spiral overlay on beautiful nature photograph, nautilus shell pattern, educational diagram" \
  --aspect-ratio 1:1 --out-prefix golden_spiral --quiet
```

**Prompt Guidelines**:
- Include the specific technique/concept name in the prompt
- Describe the visual characteristics clearly
- Add "educational example" or "demonstration" to get clear illustrations
- Match the aspect ratio to the content type (landscape=16:9, portrait=2:3, square=1:1)

### Step 3: Upload Images

Use the upload-image-hugogu-cn skill to upload generated images:

```bash
# Create directory for the Wiki page
ssh ali-sh "mkdir -p /mnt/wordpress-compose/apache/static/img/wiki/{PAGE_ID}"

# Upload all generated images
scp /tmp/rule_of_thirds_001.jpg ali-sh:/mnt/wordpress-compose/apache/static/img/wiki/{PAGE_ID}/
scp /tmp/golden_spiral_001.jpg ali-sh:/mnt/wordpress-compose/apache/static/img/wiki/{PAGE_ID}/
# ... etc
```

### Step 4: Insert Images into Content

Place each image **immediately after** the section heading or description it illustrates:

```markdown
### 三分法（Rule of Thirds）

三分法是最基础也是最实用的构图法则...

![三分法示例——主体放置在九宫格交叉点上](https://www.hugogu.cn/img/wiki/1945/rule_of_thirds_001.jpg)

*三分法：将画面分为九宫格，主体放置在交叉点上，营造视觉张力*

### 黄金分割与黄金螺旋

黄金比例 φ ≈ 1.618...

![黄金螺旋示例——视线沿螺旋自然汇聚到中心](https://www.hugogu.cn/img/wiki/1945/golden_spiral_001.jpg)

*黄金螺旋：斐波那契螺旋引导视线从外端向中心汇聚*
```

**Placement Rules**:
1. Image must appear **after** the text description of the concept
2. Image must appear **before** the next section heading
3. Add a caption explaining what the image demonstrates
4. Use descriptive alt text: `[Technique Name——Key Visual Characteristic]`

### Step 5: Verify Integration

After updating the Wiki:
1. Check that each image is adjacent to its corresponding text
2. Verify images load correctly (visit the page)
3. Ensure no orphaned images (images without nearby explanatory text)

## Examples by Content Type

### Photography Articles
| Section | Image Type | Prompt Example |
|---------|-----------|----------------|
| Lens focal length | Comparison shots | "85mm portrait vs 35mm environmental portrait, side by side comparison" |
| Lighting patterns | Before/after | "Rembrandt lighting setup, dramatic triangle shadow on cheek, studio portrait" |
| Composition rules | Diagram overlay | "Rule of thirds grid overlay on landscape photo, subject at intersection" |

### Technical Architecture Articles
| Section | Image Type | Prompt Example |
|---------|-----------|----------------|
| System architecture | Diagram | "Microservices architecture diagram, containers, API gateway, load balancer" |
| Data flow | Flowchart | "Data pipeline flowchart, ETL process, cloud storage, visualization" |
| Performance comparison | Chart | "Bar chart comparing database query performance, colorful bars, clean design" |

### Design/UI Articles
| Section | Image Type | Prompt Example |
|---------|-----------|----------------|
| Color theory | Palette | "Color wheel with complementary colors, design palette, flat design" |
| Typography | Specimen | "Typography hierarchy example, heading and body text, clean layout" |
| Layout patterns | Mockup | "Grid layout example, card-based UI design, responsive breakpoints" |

## Common Mistakes to Avoid

1. **Don't batch-insert images at the top** — Images must be distributed throughout the content
2. **Don't use generic images** — Each image must specifically illustrate the adjacent concept
3. **Don't forget captions** — Every image needs explanatory text explaining what it shows
4. **Don't mismatch aspect ratios** — Landscape concepts need landscape images, portraits need portrait orientation
5. **Don't upload without testing** — Verify the image URL is accessible before updating Wiki

## Quality Checklist

- [ ] Each image is placed next to its corresponding text section
- [ ] Image alt text describes the technique/concept being shown
- [ ] Caption explains what the viewer should notice in the image
- [ ] Images are uploaded to the correct server directory
- [ ] URLs are accessible and images load correctly
- [ ] No orphaned images (images without nearby explanatory text)
- [ ] Aspect ratios match the content type (landscape/portrait/square)
