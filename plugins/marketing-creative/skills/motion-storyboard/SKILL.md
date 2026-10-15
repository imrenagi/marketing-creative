---
name: motion-storyboard
description: Convert a selected script and visual direction into actionable visual beats, semantic timing cues, framing, continuity, and per-ratio layout decisions before composition.
---

# Motion Storyboard

Read the script, selected creative brief, visual direction, assets and placement profiles. Decide what each beat shows before coding. A sentence, a visual beat, a camera move and a scene change are different units.

## Define each beat

Read the [project contract](../motion-video-producer/references/project-contract.md). Record stable ID; persuasive/narrative job; main visual and state/action change; cue start/end; framing and focal point; exact overlay; required assets/proof; transition; optional sound cue; caption and per-ratio layout decisions.

Use word anchors when aligned narration exists, seconds for deliberate silent timing, or times derived from an approved music beat grid. Resolve anchors through the [project tool](../motion-video-producer/scripts/project.py). Identify the script segment and an exact phrase; repeated phrases require an explicit occurrence. Missing/ambiguous matches fail instead of guessing.

Plan one visual response to each meaningful information change, not one scene per sentence. Keep enough time for comprehension. Intentional empty space or silence is allowed; mark an intentionally blank visual beat explicitly. Do not force real-screen assets into conceptual/illustrated explainers or add counters unsupported by the script.

For mixed-media beats, identify supplied/generated image or footage, authored HTML component or Three.js scene, plus stable asset IDs, measured source window and mute/retain/mix policy. Mark proposed paid generation as pending explicit approval; do not assume it exists. Use measured results and review extension joins before final timing. Request/import assets through motion-video-producer rather than having the storyboard silently invoke providers.

## Plan adaptations

For every required ratio, record subject framing, text zones, captions, crop and interaction focus. Use per-variant beat overrides when needed. If the same copy is unreadable, shorten the overlay or change layout while preserving claims and exact mandated copy. A different duration/argument needs a separate cutdown, not distorted timing.

## Handoff and revisions

Write `storyboard.json`, resolve it to `timing.resolved.json`, and provide a readable beat sheet. Review opening, transitions and ending as well as midpoints. Actual audio can invalidate provisional seconds; re-resolve before composition.

For revisions, preserve stable beat IDs where their meaning remains. Check the beats either side and all affected ratio overrides. Pass unresolved evidence/asset requirements to the composer explicitly.
