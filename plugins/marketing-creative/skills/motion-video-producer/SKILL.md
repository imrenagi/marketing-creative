---
name: motion-video-producer
description: Produce or revise an animated marketing video or explainer from a brief or selected concept, coordinating art direction, storyboard, narration, composition, QA, and requested export ratios.
---

# Motion Video Producer

Own the authorized deliverable and project state. Resume from existing artifacts before asking questions. For an inspection, edit, render or status request, perform that operation without restarting the full workflow.

## Route the missing work

| Need | Owner |
| --- | --- |
| Campaign strategy or audience/offer decisions | [marketing-brief](../marketing-brief/SKILL.md) |
| Distinct creative ideas or a selected creative brief | [creative-ideation](../creative-ideation/SKILL.md) |
| Exact ad script and production direction | [ad-video-director](../ad-video-director/SKILL.md) |
| Visual identity, style and motion language | [motion-art-director](../motion-art-director/SKILL.md) |
| Visual beats and semantic timing cues | [motion-storyboard](../motion-storyboard/SKILL.md) |
| Narration, alignment and audio revision | [motion-voice](../motion-voice/SKILL.md) |
| Renderable animation and media placement | [motion-composer](../motion-composer/SKILL.md) |
| Production checks, frame review and delivery validation | [motion-video-qa](../motion-video-qa/SKILL.md) |

A general explainer can bypass ad strategy. A supplied script/concept can enter downstream. Silent work skips voice. Music can drive timing when that is the request. Stage selection does not authorize subagents or require separate chats.

## Maintain one project

Read [project-contract.md](references/project-contract.md) and [placements.md](references/placements.md). The bundled [project tool](scripts/project.py) initializes profiles, validates artifacts and resolves word/seconds cues. Invoke it by its actual installed path; it locates its resources relative to its own file, independent of working directory or client-specific environment variables.

```sh
python3 <this-skill>/scripts/project.py init <project-dir> --id demo --ratios 16:9 9:16 4:5 1:1 --duration 8
python3 <this-skill>/scripts/project.py resolve <project-dir>
python3 <this-skill>/scripts/project.py validate <project-dir>
```

Initialization creates an explicitly labeled fictional construction example. Replace its content and requirements before making a real ad. Do not overwrite an existing project. A new output ratio needs its own layout, frame review and export check. Duration cutdowns with different narration use separate project directories sharing the briefs/concept.

## Execute and resume

For narrated work: establish script → art direction → actual audio/alignment → resolved storyboard → composition → QA → export. Art direction and provisional storyboard can start earlier, but final timing follows the recording. For silent work, use explicit seconds or a supplied beat grid.

Use HyperFrames as the default render runtime. When available, read its installed entry/core/domain skills for the current technical contract; they own framework setup, media behavior and renderer commands. The bundled [runtime reference](../motion-composer/references/runtime.md) gives the minimum handoff and dependency checks. Missing runtime does not prevent planning or artifact checks; state precisely what remains unverified.

Preserve existing selection and render authorization. Ask for creative decisions only when materially unresolved; do not add a universal approval step at every stage. Paid service calls, publishing and campaign changes require scope authorization; local reversible work proceeds. Do not claim a render or review happened when only structural validation ran.

## Revisions

Route a changed claim to scripting; a visual complaint to art/storyboard/composition; a spoken-line replacement or duration trim to voice. Reproduce reported problems at the affected moments. Regenerate timing after audio/script/storyboard/profile changes, rebuild, then review neighboring beats and all affected outputs. Generator output is disposable: preserve user edits from Studio before regeneration, migrate them into the generator, and never silently overwrite them.

See [sources.md](references/sources.md) for upstream origins and adaptations.
