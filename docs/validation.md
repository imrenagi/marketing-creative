# Suite validation

Implementation validation for the 0.2.0 skill suite:

- Nine skill entry points passed the skill-creator structural validator.
- Dual manifests, marketplace and explicit package allowlist passed repository validation; both Claude plugin validations passed.
- Two independently built ZIPs were byte-identical and included 49 approved files, including both upstream MIT notices. Samples, local documents, generated media and dependencies were excluded.
- Twenty-four executable regressions passed: four canvas builds, variant-specific layouts, Unicode/ambiguous cues, stale inputs/assets, backed-up trim/replacement including boundary edits and accented-language spacing, custom/image/footage contracts, encoded metadata/audio requirements, and symlink refusal for output/package paths.
- Four actual eight-second H.264 MP4s were rendered at 30 FPS through HyperFrames and passed export fingerprint, dimensions, duration and codec verification.
- Browser inspection sampled 17 frames per canvas (68 total) and checked important boxes, overflow and repeat-seek pixels. Actual midpoint contact-sheet frames were reviewed for all five construction primitives in all four ratios.
- HyperFrames 0.8.158 passed runtime, layout and contrast checks in all four canvases. Its static lint reported six nonblocking timeline-organization warnings per compact five-beat construction example. These examples are architectural specimens; larger productions should use coherent sub-compositions.

Tests use disposable projects and synthetic/fictional content. They do not establish advertising performance, actual platform placement acceptance, model compliance on every brief, or inaudible joins in real narration. Paid TTS/provider calls were not exercised. Current placement limits and safe-area previews remain explicit production-time checks.

Run the reproducible local regressions and packaging commands in README.md. Browser/framework/export smoke tests additionally need a local GSAP file, Playwright/Chromium, HyperFrames and FFmpeg. Generated smoke artifacts are intentionally outside the repository.

## Image suite 0.3.0

Validated on 2026-10-15:

- The two new image skills passed skill-creator structural validation; all eleven skills passed the repository package checks. Both Claude manifest validations passed.
- Fifty-three offline regressions passed: twenty-four existing production tests and twenty-nine image tests. Image coverage includes arbitrary concept counts, automatic/explicit rectangular packing, partial rows, optional/multiple/CLI references, selected-tile indexing, extended image ratios, inline/JSONL batch contracts, upload headers, keyed/ordered results, partial failures, interrupted collection, ratio warnings, alpha preservation, exact crop geometry, payload bounds and unknown submission state.
- Independent forward-testing reproduced three recovery/fidelity issues; narrow fixes and regression tests now preserve unexpected-ratio output, recover interrupted downloads and retain transparent crop pixels.
- Two independently built ZIPs were byte-identical and included sixty approved files. Generated images, Python environments and credentials remain excluded.

No live Gemini generation, upload or batch submission was performed. Mocked responses establish local handling and documented request contracts; real API access, model grid adherence, product fidelity, copy accuracy and final visual quality still require a configured project and an authorized live run. This update did not rerun the historical video rendering smoke tests above.

## Opt-in Veo increment 0.4.0

Validated on 2026-10-15: 66 offline tests passed, including thirteen new generated-video regressions. Coverage includes the request-bound approval gate, changed reference fingerprints, Veo generation modes and local constraints, extension provenance/runtime, one-shot status, unknown submissions, secret-safe download redirects, filtered outputs and recovery after FFprobe failure. A synthetic local H.264 fixture was decoded and measured; no provider generation was performed.

Skill structural validation, both Claude manifest validations, the repository allowlist and a 67-file ZIP build passed. Provider access, real REST responses, model quality and regional availability remain unverified by the offline checks.
