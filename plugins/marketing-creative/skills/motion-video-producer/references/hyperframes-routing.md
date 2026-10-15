# HyperFrames capabilities in the marketing workflow

Reviewed all 21 published skills in the reference checkout's `skills/` directory on 2026-10-15, revision `03a9fab9a7b1c8742198bca8f475d04a51feaf5e` of [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes/tree/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills). This is a routing assessment of that snapshot, not a claim that its tools are installed or that a production has passed their checks. Links below identify the inspected sources; execution uses the actual installed, project-compatible skill and CLI contracts.

## Load only the capability the stage needs

motion-video-producer owns the deliverable, mixed-media timeline, selected sources and all requested variants. Use HyperFrames domains to implement or check that plan. The existing marketing brief, creative brief, exact script, STYLE.md, storyboard.json and resolved timing stay authoritative. A downstream reference is not a reason to repeat strategy intake or change a selected concept.

| HyperFrames skill | When it adds value | Marketing owner / useful contribution |
| --- | --- | --- |
| [hyperframes][entry] | Entering or resuming a HyperFrames project | Producer/composer: runtime entry, state-aware routing and current plugin/skill execution rules; skip answered intake using the existing handoff |
| [hyperframes-core][core] | Authoring HTML, mounting scenes, placing or cutting footage | Composer: clip/source timing, sub-compositions, unique media IDs and deterministic playback; prevents blank mounts and incorrect source frames |
| [hyperframes-creative][creative] | Developing a nontrivial visual treatment or a review board | Art director/storyboard: house-style and video-composition references, typography, beat direction, story-spine, design adherence and storyboard-recipe; gives a concrete alternative to generic web-page layouts |
| [hyperframes-registry][registry] | A beat names a chart, code window, reveal, transition or effect | Art director/composer: search by the intended move before building it; inspect a candidate, then adapt its copy, geometry and timing to the actual brand and ratio |
| [hyperframes-animation][animation] | Choreographing a scene, transition, 3D object or animated mascot | Art director/composer: atomic rules and scene blueprints; Three.js, Lottie, CSS, WAAPI and other runtime adapters; animation-map for reviewing choreography |
| [hyperframes-keyframes][keyframes] | A zoom, punch-in, reframe, shared-object handoff or 3D camera move needs precision | Composer/QA: visible pose ladders, continuity, masks/paths and focused shot/ghost diagnostics; distinguishes painted motion from helper-state logs |
| [media-use][media] | Finding/reusing a logo, icon, stock image, music/SFX, or treating real footage | Producer/art director: frozen local files, provenance inventory, source-aware correction/stylization/reveals and preprocessing; use its media-treatments reference for photographic polish |
| [hyperframes-audio][audio] | Narration, footage sound, music and effects share the placed timeline | Voice/composer/QA: fades, crossfades, gain/FX automation, voiceover carve and shared audio buses; source phrase replacement remains motion-voice's job |
| [hyperframes-cli][cli] | Inspecting, validating, comparing, previewing or exporting the assembled project | Composer/QA: timeline queries, lint/check, snapshots, compare/grade-compare, variable batches and render diagnostics; inspect actual encoded output separately |
| [hyperframes-studio][studio] | A person will review/edit the project or has changed it in Studio | Producer/composer: readable scene/caption/audio tracks, sub-composition organization and edit reconciliation; preserve the person's changes on rebuild |

The biggest immediate opportunities are registry discovery, animation adapters/keyframe proof, source-aware media treatment and placed-track audio finishing. Our suite already covers strategic intent, semantic narration timing, backed-up phrase revision and four-ratio project checks. Those remain its strengths; the domains above supply concrete implementation and review depth.

## Use specialized workflows only for a matching deliverable

These are optional work units or runtime handoffs, not eleven additional mandatory production stages. Read the chosen workflow's full input/output contract before using it; some have narrower footage, narration or format assumptions than our general producer.

| HyperFrames skill | Use when | Boundary / marketing handoff |
| --- | --- | --- |
| [general-video][general] | A custom mixed-media composition has no closer specialized workflow | Producer/composer: runtime build/assembly procedures for an established brief; preserve the suite's project and versioned asset handoff |
| [product-launch-video][product] | A product URL, real app/site demonstration or launch is the subject | Producer/director: capture product screens and brand assets, then use its product-motion/cut references; preserve verified product behavior and the selected campaign argument |
| [faceless-explainer][faceless] | A topic or mechanism needs invented diagrams/type/data visuals without product capture | Director/storyboard/composer: teaching progression and explanatory scene treatment; illustrative visuals remain distinct from product evidence |
| [motion-graphics][graphics] | A short unnarrated logo sting, stat hit, chart, map, title or overlay is needed | Art director/composer: build a focused motion asset; mount its composition or import its reviewed rendered clip through the producer; verify transparency format when an alpha overlay is required |
| [music-to-video][music] | Music is the timing spine of a kinetic promo or montage | Storyboard/composer: deterministic audio map and beat/phrase planning; use phrase/energy pacing when a calm track lacks reliable beats; a background bed alone does not select this workflow |
| [embedded-captions][captions] | Existing single-subject talking-head footage needs verbatim subtitles or embedded caption emphasis | Producer/voice/composer: local transcription, caption grouping and subject matting; inspect transcript, readability and occlusion; split unsuitable multi-shot input first, and keep footage unchanged |
| [talking-head-recut][talking] | Existing interview, testimonial or podcast footage needs designed graphics | Producer/storyboard/composer: transcript-timed cards, lower-thirds, quotes and PiP; despite its name the workflow keeps the source playing intact, so real trims/reorders belong to core/general-video |
| [figma][figma] | A supplied Figma design, brand, component or storyboard is an input | Art director/composer: local exports, tokens, component bindings and state-based motion reconstruction; freeze assets, inspect source fidelity and use authorized credentials |
| [pr-to-video][pr] | A developer-facing release/changelog video is explicitly based on a pull request | Director/producer: diff-backed facts and code-editorial treatment; a merged PR alone is not proof of deployment, availability or customer results |
| [slideshow][slides] | The user requests a navigable pitch, sales or interactive deck | Separate requested deliverable: discrete slides, fragments, hotspots and presenter mode; its normal output is a deck, so do not substitute it for a video ad |
| [remotion-to-hyperframes][remotion] | The user explicitly asks to migrate existing Remotion source | Composer: source mapping, unsupported-pattern lint and translation notes; preserve source for comparison and report losses; reference-only Remotion inspiration does not trigger migration |

## Integrate without breaking the production contract

1. **Resolve availability.** Use the relevant installed skill, or read the matching entry and references from an available user-provided checkout. A reference checkout alone supplies guidance, not a built renderer. Follow the installation-specific execution rules and inspect the project's CLI help/version before commands. Install/update only the needed capabilities within scope; do not install all workflows as a prerequisite. If a capability is unavailable, continue independent work and report the missing implementation or verification clearly.
2. **Adapt the handoff.** For an end-to-end HyperFrames workflow, derive its BRIEF.md and required design/storyboard files from the established marketing artifacts using its current format references. Translate timing/alignment/media schemas explicitly: upstream STORYBOARD.md, transcription JSON and media ledgers are not drop-in replacements for this suite's JSON. Reconcile edits back into generator source and authoritative artifacts so a rebuild preserves them. Installed design tokens and our STYLE.md must agree; do not silently replace brand direction with an upstream preset.
3. **Keep sources and ratios deliberate.** Adopt/freeze resources, record hashes and required license/credits, then import selected outputs with assets.py. Reuse registry primitives through a compatible project generator and fingerprint their files/dependencies. Preserve the requested 16:9, 9:16, 4:5 and 1:1 compositions; upstream default canvases and Studio action/title boxes are starting conventions, not current Meta/desktop placement limits or automatic support for every ratio. Reframe and verify each requested canvas explicitly.
4. **Preserve authorization.** Capability discovery does not authorize a paid generation, provider switch, new cloud render, publication or external feedback message. Keep Gemini image helpers and motion-voice for their existing source-generation/revision roles. Veo/Omni remain separately approved opt-in helpers, including follow-up turns; an upstream media fallback never bypasses that boundary. Export any optional FIGMA_TOKEN or other provider credential from the external credential store; do not adopt project-local secrets. Inherited user authorization remains valid; optional capability notes create no new approval gates for work already authorized. Do not execute upstream public feedback/report commands unless the user explicitly authorizes sending them.
5. **Review evidence.** Use the installed core and animation adapter for framework-owned media and canonical seek time, not a second player/clock. For a narrated mix, use hyperframes-audio to finish the music/voice relationship, inspect its carve/FX/automation choices and listen; JSON labels and stream presence cannot prove intelligibility. Validate actual assembled scenes, not only isolated fragments. Sample first/proof/final frames, transitions, mounted-scene midpoints and repeat seeks; use focused keyframe/animation diagnostics when relevant. Preserve intentional stillness or sparse design. Run final framework checks, inspect nonzero audit coverage, preview, then perform authorized export and per-ratio encoded/audio QA.

## Useful first reads inside the selected domain

- Art direction: hyperframes-creative references/house-style.md, references/video-composition.md and references/typography.md; use references/design-adherence.md when verifying the selected design.
- Reviewable boards: hyperframes-creative references/storyboard-recipe.md; its stills are sampled from the actual mounted composition. Keep concept-board ideation in marketing-image-board separate from production storyboard proof.
- 3D and characters: hyperframes-animation adapters/three.md or adapters/lottie.md, then only the chosen rules/blueprints. These supply the missing concrete custom-generator adapter guidance; they do not make the bundled construction generator a general 3D engine.
- Footage polish: media-use references/media-treatments.md; inspect the source and choose a justified correction/treatment, keeping an intentional look when it already fits.
- Sound: hyperframes-audio references/presets.md and references/attributes.md; use references/diagnosis.md for an undescribed audio fault, not an assumed EQ recipe.
- Regression review: hyperframes-cli references/lint-validate-inspect.md and references/compare-and-batch.md; hyperframes-keyframes for motion proof and hyperframes-studio for editable organization.

These notes reference upstream capabilities; no upstream workflow, script, asset or renderer is vendored by this change. Real visual/audio improvement must be established in the specific production, not inferred from routing alone.

[entry]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes/SKILL.md
[core]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes-core/SKILL.md
[creative]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes-creative/SKILL.md
[registry]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes-registry/SKILL.md
[animation]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes-animation/SKILL.md
[keyframes]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes-keyframes/SKILL.md
[media]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/media-use/SKILL.md
[audio]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes-audio/SKILL.md
[cli]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes-cli/SKILL.md
[studio]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/hyperframes-studio/SKILL.md
[general]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/general-video/SKILL.md
[product]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/product-launch-video/SKILL.md
[faceless]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/faceless-explainer/SKILL.md
[graphics]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/motion-graphics/SKILL.md
[music]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/music-to-video/SKILL.md
[captions]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/embedded-captions/SKILL.md
[talking]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/talking-head-recut/SKILL.md
[figma]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/figma/SKILL.md
[pr]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/pr-to-video/SKILL.md
[slides]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/slideshow/SKILL.md
[remotion]: https://github.com/heygen-com/hyperframes/blob/03a9fab9a7b1c8742198bca8f475d04a51feaf5e/skills/remotion-to-hyperframes/SKILL.md
