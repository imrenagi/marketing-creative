# Production verification

Commands:

```sh
python3 <this-skill>/scripts/check.py PROJECT
node <this-skill>/scripts/probe.mjs PROJECT
python3 <this-skill>/scripts/check.py PROJECT --exports
```

The source checker validates resolved input fingerprints, generated build fingerprints, declared media paths, IDs, animation target declarations and asset dimensions where FFprobe can inspect them. It checks configuration/coverage, not arbitrary browser visibility or aesthetic success. Stale timing is an error even if output files still exist.

After rendering a variant to renders/<variant-id>.mp4, run `check.py PROJECT --record-export VARIANT_ID`. This checks the encode and records its file hash and current build hash in renders/manifest.json. Then `--exports` requires all requested files to match their recorded provenance. Recording supplied files cannot prove which renderer created their pixels; document the actual render command. Any source/build/file change requires a new render and record, not merely renaming the old file.

The browser probe requires an installed Playwright package and Chromium. Pass its package entry as PLAYWRIGHT_MODULE when it is outside normal module resolution. It discovers each variant's canvas size, seeks boundary/midpoint samples, checks important text/visual boxes against the configured safe rectangle, captures PNGs, and compares same-time screenshots after an out-of-order seek. It writes probe findings separately; it never marks frames as reviewed.

If using an existing Chromium-based browser instead of Playwright's downloaded browser, set PLAYWRIGHT_EXECUTABLE to its actual executable path. Keep dependency installation outside generated projects when possible; dependencies are not included in the plugin ZIP.

For custom compositions, add `data-qa-important` to text and proof elements; `data-qa-target` declarations enumerate animation targets emitted by the generator. Browser box checks are approximate for rotated/masked/occluded content. Inspect images and framework audits. Timed media requires framework validation, not the standalone probe.

## Required review evidence

Record per variant in qa/review.md: input fingerprint, frame paths/times actually inspected, caption/text/UI/CTA readability, safe-area preview, transition extremes, audio listen/joins, framework check result, encoded path/dimensions/duration/audio, unresolved limitations. A checklist left unchecked is not a passing report.

Silent output must be intentional; narrated output must contain an audio stream. FFprobe validates H.264 and AAC for the default export profile, configured FPS/dimensions, duration tolerance of max(0.1 seconds, 2 frames), and profile limits. Other codecs require an explicit export-profile change. Frame review at every ratio remains required even when all encodes pass.

## Regression cases

- Source audio or storyboard changed without resolve/build → fail as stale.
- Removed animated element → target check fails.
- Declared asset recropped without dimensions/hash update → fail or require manifest update.
- Repeated word cue without occurrence → fail, no implicit first match.
- Mandarin phrase anchors retain Han characters.
- Line replacement at first/last word preserves neighboring speech and timestamps.
- Marked intentional blank beat → allowed; unexplained coverage gap → fail.
- Tallest/widest text in 16:9, 9:16, 4:5 and 1:1 → inspect boxes and snapshots.
- Wrong-ratio encode, missing narrated audio, truncated duration or stale render → fail.
