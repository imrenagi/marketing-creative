# Runtime and dependencies

HyperFrames is the default external rendering runtime, not bundled in this plugin. The bundled composer uses Node 20+; the external CLI has its own version-dependent requirements (the HyperFrames snapshot reviewed on 2026-10-15 requires Node 22+). Use Python 3.9+ and FFmpeg/FFprobe for stdlib project/audio/export checks; image/video-provider helpers require Python 3.10+. Playwright is optional for the browser probe. Planning and stdlib project checks need no API key or paid service.

Before a HyperFrames build, read its installed entry/core/domain guidance when available. Check installed CLI help/version and use a project-compatible pinned version; do not guess current flags. Respect its usage/availability checks when actually creating/rendering. If unavailable, complete source preparation and report runtime/render validation as pending.

The [capability map](../../motion-video-producer/references/hyperframes-routing.md) routes all reviewed upstream skills by need, with source links and integration boundaries. Prefer those targeted domains over importing a second complete workflow for every task.

When handing off to a HyperFrames end-to-end workflow, read its installed brief-format/brief-contract references. Populate its BRIEF.md from the already established marketing/creative briefs, script, style, placements and authorization; do not run another intake interview. Treat that file as a derived runtime handoff and preserve an existing project's workflow and user decisions. Each independently rendered canvas gets its matching aspect/duration. Keep the suite's primary artifacts authoritative and reconcile framework/Studio edits before regenerating.

## Minimum composition contract

- Standalone sized root with static `data-composition-id,data-width,data-height,data-duration`.
- One paused seekable GSAP timeline registered at matching `window.__timelines[id]`.
- Runtime controls timed clip visibility and media; animate inner visual nodes.
- Audio has a unique ID, actual local src and explicit timing. Silent b-roll is muted; retain intended footage sound intentionally.
- No manual audio/video playback/seek loop, second OPENER player or autoplay for render-critical motion.
- No unseeded randomness, system clocks or render-time network for required media.
- Local fonts/assets; root layout uses 100% sizing. Initial transforms belong to explicit GSAP states, not conflicting CSS.
- Do not nest a timed video under a plain timed wrapper. Follow current runtime sub-composition rules for modular scenes.

The composer emits each canvas into `variants/<id>/` with its own HTML and copied assets. A local GSAP file is recommended through `--gsap`; CDN is only a development fallback and QA records it. The HTML is framework input, not a standalone autoplay deliverable.

## Verification and export

From each variant directory, use installed `hyperframes lint`, `check`, `snapshot`, `preview` and `render` according to current CLI help. Save actual command results. Render to `renders/<variant-id>.mp4` at the project root (pass an explicit output path supported by the CLI). Avoid relative-path ambiguity.

The packaged probe injects only a minimal timeline registry to seek visual construction examples in a browser. It cannot certify framework media playback, audio mixing or compiler behavior. Snapshot all required canvases; FFprobe-check encoded outputs separately.

For a custom generator, emit the same build manifest shape or extend the checker alongside the new generator. Preserve/reconcile Studio edits before rebuilding. Do not overwrite source or silently substitute another renderer when runtime setup fails.
