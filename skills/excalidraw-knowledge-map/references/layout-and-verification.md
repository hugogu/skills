# Compact layout and rendered proof

Read for initial layout decisions or any request to fix spacing globally.

## Content-first layout

Choose a reading scale and a column count appropriate to content density. Maintain a small style set for title, section header, card title, body, formula scale, padding, and gutters. Exact values depend on canvas scale and language.

For each card:

1. Measure text wraps and formula run extents at the intended font sizes.
2. Lay out the title, explanatory lines, equations, and examples using their actual line boxes.
3. Set the card bottom to its last occupied content edge plus bottom padding. This includes tall formula descenders and any sketch or caption.
4. Set the next row/section position from the greatest occupied bottom, not an old fixed row height. Recompute enclosing section frames and connectors.

Conceptually, `card_height = title_region + measured_body_height + bottom_padding`. Do not derive every sibling's height from a maximum. Shorter cards may end earlier while remaining aligned at the top; a maximum is appropriate for finding the *next row's start*.

Use shared axes and sensible line breaks to reduce wasted width. In worked examples, independent short equations can sit side by side. A tall column vector can sometimes be written as an equivalent transposed row vector; preserve grouping, orientation, and mathematical meaning. Do not flatten a formula in a way that obscures its reasoning.

Keep the learning route explicit. Masonry packing is optional and should not scramble dependencies. A modest gap below a short sibling can be useful; a huge empty card interior is a layout defect.

## Global repair procedure

- Save the existing task source and inventory its concepts, worked examples, formula-source links, and outputs.
- Diagnose whether emptiness comes from oversized cards, fixed row heights, wide columns, excessive section gaps, or needlessly tall notation. Fix the cause across every affected section.
- Reflow using the established style, allowing local adaptation for dense equations. Preserve readability and content; total-size reduction is an outcome rather than the acceptance target.
- Recalculate all geometry, then regenerate source and exports together.
- Compare old/new coverage and inspect the whole result. Never declare a global repair complete after adjusting only the user's screenshot region.

## Rendered acceptance

Inspect at two scales:

- **Overview:** section order, balanced density, hierarchy, consistent gutters, cross-links, and no unexpectedly empty bands.
- **Reading scale:** short/tall neighboring cards, dense cards, fractions/matrices, first and last lines, headings/captions, and arrow endpoints/labels. Text and formulas must remain within their intended bounds without clipping or collision.

When Excalidraw is accessible, open/import the final source and inspect those same regions. Use current observed UI state to navigate. Search results may require selecting the result before the viewport moves; inspect the actual zoom and location. Avoid assuming a keyboard shortcut toggled to the intended tool.

Do not reset a user's existing canvas merely to load a test. Use a safe task-owned scene or an available separate tab, preserve the source, and stop if loading would overwrite unsaved unrelated work.

Browser file pickers and export dialogs vary. If an export action produces no completion event, inspect visible state before retrying; do not poll indefinitely or create repeated downloads. A local rendering pipeline is a possible fallback, but it does not prove that a native editor export succeeded.

Report actual evidence: for example, “source imported; checked overview and four close-ups; assets survived reload.” If only source checks and local rendering were available, say so without claiming editor verification.
