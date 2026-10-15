# Shared project contract, version 1

All JSON documents carry `schemaVersion: 1`. Use UTF-8. The production helpers use Python 3.9+ and Node 20+; framework/browser/FFmpeg dependencies are separate. Install the complete plugin to retain cross-skill references and tools. The planning skills can run without these tools.

## Ownership and files

| File | Owner / meaning |
| --- | --- |
| MARKETING_BRIEF.md | Marketing strategy, evidence and placement requirements |
| CONCEPTS.md / CREATIVE_BRIEF.md | Alternatives and selected idea with stable concept ID |
| STYLE.md | Brand sources, type, imagery and motion language |
| project.json | Project ID, language, selectedConcept, canvas/placement variants, style, optional voice and project-local generator |
| script.json | Ordered segments: `{id,text}`; empty array for silent work |
| storyboard.json | Ordered `beats`, optional `variants` object replacing beats for specific variant IDs |
| assets/manifest.json | `assets`: `{id,path,kind,source,sha256,width?,height?}`; paths are project-relative |
| audio/alignment.json | Audio hash, measured duration and aligned words |
| timing.resolved.json | Derived absolute timing and fingerprints of all inputs/assets |
| build.mjs or installed generator | Editable composition source |
| variants/<variant-id>/index.html | Generated composition; assets copied alongside |
| variants/<variant-id>/build.json | Input, generator and generated-file fingerprints |
| qa/report.json / qa/review.md | Machine findings and actual human/agent review notes |
| renders/<variant-id>.mp4 | Final encoded output, only after rendering |

A project's custom generator can replace the bundled construction example. Keep its path/revision in production notes. Do not treat changing the example's text as a complete production design.

## Project configuration

`project.json` requires `id`, `language`, `variants`. IDs start with a letter and contain letters/digits/underscore/hyphen. A variant has `id,ratio,width,height,duration,fps,safeArea,placement`. Four ratios: 16:9, 9:16, 4:5, 1:1. Positive even dimensions must match the ratio; custom resolutions are supported. Safe areas are top/right/bottom/left fractions of the canvas. See [placements.md](placements.md).

`style` accepts background/foreground/accent hex colors. Brand typography and advanced composition are authored in the generator and STYLE.md.

For custom placed music/SFX, set variant.audioRequired=true when an encoded audio stream is expected. Export checks also inspect declared audio and audible video elements, so required sound is not limited to narration. Keep sound-on/sound-off deliverables explicit in production notes.

Optional `voice`: `{audio:"audio/vo.wav",alignment:"audio/alignment.json",start:0}`. Working audio is mono 16-bit PCM WAV. All variants share this take. A shorter narration requires its own cutdown project. Do not truncate audio to fit.

## Script and alignment

Script: `{"schemaVersion":1,"segments":[{"id":"promise","text":"Finish one useful task."}]}`.

Alignment: `{"schemaVersion":1,"audioSha256":"<hash>","duration":4.2,"words":[{"id":"w0","segment":"promise","text":"Finish","start":0.2,"end":0.5},...]}`.

All script segment text must match the corresponding ordered alignment text after Unicode normalization, punctuation and spacing removal. Words have nonoverlapping positive durations within the measured WAV. Word timing can be imported from any provider if converted to this shape; keep the original response outside the distributable package. Han characters are preserved, and phrase matching supports providers that tokenize them differently. Latin cues require complete token boundaries.

## Storyboard

Beat fields: `id,job,start,end,visual`; `layoutNotes,captions,sfx` can record direction beyond the example renderer. Supported construction modes: `type,ui-tour,counter,collage,stage` require `text`, optionally `label`. Counter needs numeric `value`; collage can reference an asset ID. `image` and `footage` require an `asset` ID of kind image/video; text is optional for text-free proof shots. Footage takes optional `sourceStart` and `hasAudio`; its manifest asset must declare measured `duration`. The generator places video at the root to avoid nested timed media. For custom visuals, set project.generator to a project-local .mjs path and use `custom:<name>` with generator-specific fields. The resolver validates timing/assets without constraining custom visual content; run that custom generator instead of the bundled one. Its build manifest uses generator=`custom`, generatorPath matching project.generator and generatorSha256 of that file, plus the same inputHashes, timingSha256, generatedHashes and localRuntime fields. Custom generator source is fingerprinted.

Cues are either `{"seconds":0}` or `{"segment":"promise","quote":"useful task","edge":"start","offset":-0.1}`. Word cues optionally specify one-based `occurrence` when repeated; no implicit first match. Edge is start/end of the phrase. Offset is signed seconds.

Cover the complete runtime with contiguous beats. Represent intentional gaps with `intentionalBlank:true`; no visual is required for them. Transition overlaps live inside a beat, not as double-counted narrative intervals. Per-variant overrides are complete beat arrays under `variants.<variant-id>`. Missing overrides use the base beats.

## Rebuild and invalidation

The resolver hashes project/script/storyboard/manifest, voice/alignment and declared assets. Any input change makes timing stale. The composer refuses stale timing; its build manifest additionally hashes generator, timing and every generated file. QA detects edits to generated HTML and assets. Reconcile Studio/manual edits before rebuilding; preserve wanted changes in the source.

Voice edits create a unique backup of WAV, alignment, script and project, then write synchronized replacements. They invalidate timing, QA and existing variant build manifests. Earlier rendered files remain available but fail current export validation until rebuilt. Review notes must identify the input hashes reviewed; old notes do not approve new renders.
