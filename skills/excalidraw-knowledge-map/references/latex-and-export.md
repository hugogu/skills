# LaTeX and portable Excalidraw exports

Read when creating or repairing formulas. Check the available editor/runtime capabilities instead of assuming a particular Excalidraw version supports live TeX.

## Source and rendering

Keep a structured source representation separate from rendering. Each content block should have a stable ID, card/section association, explanatory text, and marked LaTeX segments. Keep notation consistent across the map.

A proven portable route is **TeX → MathJax SVG paths → Excalidraw image elements**. An equivalent renderer is acceptable if its output remains self-contained and reproducible. Use an available maintained library instead of writing a TeX renderer.

- Render valid TeX, not screenshots of literal commands. Detect renderer errors explicitly.
- Use self-contained SVGs with a `viewBox` and intrinsic dimensions. MathJax's local font cache can keep path definitions inside each asset; disabling the font cache is also possible. Do not reference definitions in another SVG or external fonts/services.
- Preserve aspect ratio. Retain baseline/ascent/descent metrics alongside width and height so inline formulas align with native text; tall formulas must enlarge their own line box.
- Avoid `foreignObject` and CSS-dependent text for formula paths intended to travel between viewers.
- Store the original TeX on each equation image, for example in `customData.latex`, and retain a stable source-block reference such as `customData.sourceTextId`. These are application conventions, not mandatory Excalidraw schema fields.
- Also save a UTF-8 JSON catalog of the text blocks and TeX. Source identifiers should survive reflow and allow regeneration; do not rely only on an opaque image hash to find an equation.

Chinese explanations remain native text. Mixed lines can be laid out as text runs plus formula image runs, sharing a baseline and spacing measured from rendered dimensions. Keep them grouped with the surrounding card so later edits do not scatter the parts.

## Scene and assets

Inspect an available valid scene or the current format/API documentation before emitting schema-sensitive fields. Put image assets in the scene's file collection, resolve every image's `fileId`, and preserve the fields needed for loading and display. Image MIME types and data URLs must agree. Do not put machine-specific absolute file paths into the distributed scene.

When exporting SVG/PNG, embed the assets required for independent viewing. If promising an editable SVG/PNG, embed the Excalidraw scene using the supported export format and test reopening it. A visually correct SVG without scene metadata is a vector export, not an editable Excalidraw source.

Exports must correspond to the same final scene. Prefer a reusable source-to-output pipeline; after a layout or formula change, regenerate all affected outputs rather than hand-patching only the preview.

## Verification

- Parse the scene and every SVG; reject duplicate element IDs, non-finite dimensions, unresolved file IDs, and non-deleted images with missing assets.
- Check SVG fragment references against definitions within the same asset; external links must not be required to display formulas.
- Check TeX-source coverage. Search native text for leftover math notation, including headings, captions, dimensions, and assumptions. Counts alone are insufficient: legitimately merged or split runs can change the number of image elements.
- Inspect a fraction, a subscript/superscript, a matrix, and a mixed text/formula line in the actual rendered output when those occur.
- Verify metadata round-tripping when an embedded scene is part of the promised export.

Describe editing accurately: the card text and shapes are directly editable; formula images can be moved/resized, but changing their math requires editing the retained TeX and rendering again unless a working native formula editor is available.
