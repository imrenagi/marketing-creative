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

## Opt-in Omni increment 0.5.0

Validated on 2026-10-15: 79 offline regressions passed. New coverage exercises Omni source/reference bindings, first/last frames and loops, prior stored turns, uploaded edit/extension limits, upscale duration, unsupported controls, background cancellation, step-based SSE, interrupted stream identity, creation-URI preservation, unknown upload state and local recovery after provider file expiry. Package validation enforces explicit-only invocation for both paid-video skills; a 73-file archive and both Claude manifest checks passed.

Independent offline forward-testing covered both skills and reproduced the temporary-URI recovery issue, which now has a regression test. No live generation, uploads, cancellation or remote status/download calls were performed. Real provider compatibility and visual/audio output quality remain production-time checks.

## Mixed-media orchestration increment 0.6.0

Validated on 2026-10-15: 90 offline tests passed. Eleven new assembly tests cover import dry-runs, immutable source copying, provider hash/dimension/provenance checks, manifest backups, symlink refusal, measured audio, sound-policy wiring, custom-generator resource fingerprints and ordinary image/footage/overlay compositions in all four ratios. The importer preserves generated output findings and pending review, and new imports invalidate earlier timing/build fingerprints. Independent forward-testing found two request-provenance gaps; regression tests now preserve manifest-only request identity, reject conflicting state/approval identities and avoid attributing unbound sibling state.

The suite now has thirteen skill entry points and 75 distributed files. Both new provider skills remain explicit-only; motion-video-producer owns source selection and assembly, including custom Three.js/HTML generators. Source/data tests do not establish actual Three.js rendering, HyperFrames media playback, listening, live video model compatibility or finished campaign quality. No paid provider calls were made.

## Conversational continuation increment 0.6.1

Validated on 2026-10-15: 99 offline tests passed. Nine new regressions cover Python continue/history commands, inherited settings and measured duration, three-turn resumption after a process restart, deliberate branches, approval bound to the parent/edit, pending/stateless/unknown rejection, unchanged parent files after timeout, mismatched parent/asset identities, cycles and external/legacy history. Dry-run/history need no key or network and write no runs. Both changed skills passed structural validation; repository/Claude manifests passed, and two 75-file archives were byte-identical.

An independent forward-test passed eleven checks using fresh Python processes and synthetic transport, including two successive edits, an earlier-version branch, inherited settings, approval rejection and unresolved-turn recovery boundaries. No live conversational generation or provider retrieval was performed. Local history and mocked chaining verify request/state handling, not server-side context availability, retention or actual edit fidelity. Existing rendering limitations above remain unchanged.

## HyperFrames routing notes 0.6.2

Reviewed all 21 published entry points from HyperFrames revision 03a9fab9a7b1c8742198bca8f475d04a51feaf5e on 2026-10-15. The packaged routing map covers every published skill and verifies each immutable source link against that checkout; its entry points match the linked Git revision. Selected deeper creative, storyboard, animation-adapter, media-treatment, audio and CLI references were also inspected. Six revised skill entry points passed structural validation, repository/Claude manifest checks passed and two 76-file archives were byte-identical. The reference CLI's Node >=22 requirement was verified separately from the bundled composer's requirements.

This increment changes guidance and packaging metadata only. No code regressions, HyperFrames runtime commands, provider calls, rendering or listening checks were repeated; it does not establish installation or improved production quality. Prior executable validation remains recorded above. Upstream code, media and workflows are referenced rather than bundled.

## Public release baseline and automation

Validated on 2026-10-15. Public versioning starts at `v0.1.0`; the historical increment numbers above describe earlier implementation checks and are retained as recorded. Both client manifests were aligned with the public tag and the new imrenagicom repository. The tag was pushed and the validated 76-file ZIP attached to its GitHub release.

All 102 offline Python regressions passed with Python 3.12, Pillow and FFmpeg available; no image tests were skipped. Three release regressions cover synchronized manifest/package/lockfile versions, unchanged locked dependencies, actual allowlisted ZIP contents, invalid versions and missing metadata. Ten Node tests cover patch/minor/major selection, ordinary and documentation commits, breaking footers and `!`, highest-bump selection, no-change reruns and inclusion of skill documentation in release notes. Tests exposed an incompatible latest changelog preset; the pinned 9.x preset passes against semantic-release's current writer. Repository validation, both Claude manifest validations, diff checks and two byte-identical archive builds passed.

The workflow validates before publishing, uses `[self-hosted, linux]` for both jobs, serializes releases and gives only the release job `contents: write`. Release preparation builds outside the repository and commits only the changelog and version metadata before tagging. CI uses the automatic GitHub token and publishes no npm package. An authenticated live dry-run and the first self-hosted Actions run still require verification after committing/pushing this setup; these offline checks do not prove runner availability or GitHub publication.

`npm ci` succeeds, but `npm audit` reports fourteen upstream development-tool advisories (twelve high, two moderate), including braces/micromatch and dependencies bundled within semantic-release's npm dependency. A compatible `npm audit fix` did not resolve them; no forced downgrade or unverified dependency override was applied. These release-tool dependencies are excluded from the distributed skill ZIP. No paid provider calls, new production renders, browser inspection or listening review were performed for this change.

## GitHub-hosted runner switch

On 2026-10-15, verified that this repository is public and that GitHub documents standard hosted runners as free and unlimited for public repositories. Both jobs now use `ubuntu-latest`. The previous self-hosted run was queued because no matching runner was available. The earlier authenticated semantic-release dry-run passed and selected `v0.1.1`; it did not create that tag or publish a release. Hosted validation and publication will be checked after this change is pushed. The local test results and dependency-audit limitations above remain applicable.
