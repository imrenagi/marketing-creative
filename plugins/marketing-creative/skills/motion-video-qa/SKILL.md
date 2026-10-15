---
name: motion-video-qa
description: Validate video project timing, assets and placement profiles, review frames and audio, and verify every requested ratio's encoded export before delivery.
---

# Motion Video QA

Read [checks.md](references/checks.md). Check the actual project's source, generated outputs and requested deliverables. A passing script proves only the checks it ran; it does not prove engagement, ad performance, full visual correctness or successful installation.

## Cheapest checks first

1. Run the [project validator](../motion-video-producer/scripts/project.py) and [production checker](scripts/check.py). Fail on missing/ambiguous cues, stale input fingerprints, missing or changed assets, invalid dimensions, overlapping beats, unexplained gaps, broken media paths and output mismatches.
2. Run installed HyperFrames lint/check per variant. Clear framework errors before trusting layout/contrast sample counts.
3. Capture boundaries, transition overlaps, midpoints, longest text and ending in every ratio. [Browser probe](scripts/probe.mjs) measures declared important elements, captures frames and checks repeat seeks; it requires Playwright and a local GSAP file. It is a lightweight visual probe, not the renderer and not media playback validation.
4. Inspect images at actual placement viewing size, with profile safe-area overlays when relevant. Listen to narration and any joins, music balance, transitions and ending. Assess argument/payoff/proof as well as motion.
5. After authorized rendering, check every encoded file with `check.py --exports`: dimensions, duration, video/audio stream presence, expected codec and configured placement limits.

## Errors versus creative findings

Technical failures block delivery of affected outputs. Unexpected blank frames require investigation. Intentional holds, silence, stationary cameras and marked blank intervals are allowed. Treat “feels flat,” “too much text,” weak attribution or a mismatched visual register as findings needing judgment; do not pretend to measure retention with a regex.

Generated screenshots are evidence only after they are reviewed. Capture does not set review status. Record visual/audio review notes per variant, remaining limitations and exact commands actually run in `qa/review.md`. Do not mark missing framework/media/export validation as passed.

For generated footage/images, inspect provider reviewIssues, measured media, request/provenance hashes and actual review notes. Check extension joins and source windows, intended sound against audioPolicy/hasAudio, and final typography/product claims rather than accepting model-rendered copy. Review custom Three.js/HTML scenes at repeat seeks within the same mixed-media timeline. Unreviewed imported assets and provider success alone cannot establish delivery readiness.

## Revisions

Reproduce the issue at reported times. Recheck changed beats, neighboring transitions, affected ratios and audio joins. Regenerate stale timing/compositions after source edits. Use findings to route work to its owning skill; avoid restarting strategy for a local layout issue.
