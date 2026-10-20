---
name: excalidraw-knowledge-map
description: Create and refine layered knowledge decomposition maps in Excalidraw, from a field overview to mechanisms, algorithms, mathematics, and data principles. Use for knowledge atlases, learning maps, topic drill-downs, or global formula/layout repairs (知识图谱、知识拆解图、分层学习地图). Intended for explanatory learning diagrams rather than database knowledge-graph construction or statistical plots.
---

# Excalidraw Knowledge Map

Deliver a coherent learning atlas that explains how a subject works, with editable structure, properly typeset mathematics, and compact readable cards. Default to the user's language. Preserve the chosen tool and existing visual vocabulary when continuing a map.

## Choose the scope

- **Overview:** progressively decompose a field into concepts, methods, mechanisms, and foundations. For AI, a useful route is field → tasks and approaches → model families → algorithms → mathematical and data principles. Adapt this route to the subject; do not force every branch into identical depths.
- **Drill-down:** expand one node into its own substantial map. State its role in the parent field and provide a parent-map reference when one exists. Cover the parts needed for that field, rather than duplicating a whole textbook.
- **Revision:** inspect the existing source and rendered map first. Preserve content and formula sources; apply a requested global repair across all sections, then regenerate affected exports.

Infer audience, purpose, depth, and outputs from the conversation and artifacts. Ask only when a missing choice materially changes the result. The previous map's card count, canvas dimensions, and topic count are examples, never fixed requirements.

## Organize the knowledge

1. Outline the learning dependencies before positioning cards. Distinguish a taxonomy from prerequisites, computations, and applications; do not imply that these relationships all mean “is a kind of.”
2. Build a visible reading order, usually top to bottom with numbered topic bands. Keep each level internally consistent: tasks, training paradigms, architectures, and algorithms are different classification dimensions.
3. Use cards with a clear title and enough substance to answer **what it is, how/why it works, and where it is used**. Add a defining equation, geometric sketch, limitations, or small example where it improves understanding. Avoid empty headings and a wall of disconnected keywords.
4. Explain symbols, shapes/units, assumptions, and scope alongside formulas. Distinguish mathematical definitions from framework storage conventions, and exact results from approximations.
5. Connect prerequisites and cross-topic mechanisms explicitly. Prefer a few labeled links, such as “projection → least squares” or “SVD → PCA,” over a web of crossing arrows.
6. Include small worked examples that expose the mechanism, plus a short learning route or self-check when useful. Verify calculations and conditions. Cite primary sources for specialized or uncertain claims; keep references accessible without filling every card with URLs.

## Visual and mathematical contract

- Use restrained section colors, a light background, consistent hierarchy, and approachable hand-drawn framing. Keep explanatory text as native editable Excalidraw text and group related card elements.
- **Render all mathematical notation through LaTeX**, including inline variables, dimensions, captions, and titles that contain math. Literal TeX in a text box, ASCII expressions such as `A_k`, and Unicode superscript substitutions do not satisfy this requirement. Plain numbers in section numbering or prose do not need equation assets.
- Retain the original TeX in a portable source catalog and associate each rendered formula with it. Use self-contained vector formula assets when direct formula support is unavailable or cannot preserve exports. Read [LaTeX and export mechanics](references/latex-and-export.md) when generating or changing formulas.
- **Size each card to its own content.** Do not give a short card the height of its tallest neighbor. Keep top alignment and consistent modest padding; place the next row or section after the deepest occupied bottom plus a modest gutter.
- Measure actual text and formula extents. Fractions, roots, sums, and matrices need their actual height and baseline. If a card is too tall, reorganize related equations, use mathematically equivalent notation, or split a concept at a meaningful boundary before reducing readable font sizes.
- Do not use blank space as filler, stretch formula images, omit knowledge to meet a size target, or shrink all text to conceal spacing problems. Preserve useful whitespace for grouping and scanning.
- After moving cards, update section boundaries, connector endpoints, labels, and reading order. Read [layout and visual verification](references/layout-and-verification.md) for global repairs.

## Produce and verify the result

For a substantial atlas, default to an editable `.excalidraw` source, vector SVG, high-resolution PNG, a smaller overview preview, and the formula source catalog when math is present. Adapt to the requested outputs. Explain any formula-editing limitation honestly: movable SVG equation images are not ordinary editable text.

Before delivery:

1. Check concepts, assumptions, dimensions, and numerical examples. For revisions, compare content coverage and formula-source associations before and after.
2. Check unique element IDs, valid dimensions, resolved image assets, and self-contained formula SVGs. Use embedded scene metadata only if it round-trips to the delivered source.
3. Render the complete map and inspect representative close-ups: a short card next to a tall one, dense formulas, worked examples, cross-section links, and the final section. Fix clipping, overlaps, large internal voids, and floating arrows throughout the map.
4. When editor access is available, open/import the delivered source in Excalidraw, zoom and pan to those regions, and verify assets persist on reload. A source edit or generated export alone does not prove correct editor rendering. State exactly which checks were performed if editor access is unavailable.

Use available filesystem/API tools for source and export work and the environment's supported browser tools for editor interaction. Preserve unrelated canvas content and working-tree changes. Saving the task's map does not authorize clearing another canvas, publishing externally, or committing unrelated files.

Deliver actual file links and a concise statement of scope, outputs, and verification. Show an overview or a relevant close-up when it helps assess the result. Do not substitute a plan, outline, or screenshot for the requested editable map.

For skill maintenance or smoke testing, use the observable outcomes in [acceptance scenarios](references/acceptance-scenarios.md).
