---
name: motion-voice
description: Generate or import narration with word alignment, trim pauses, or replace a spoken phrase while preserving and retiming the existing take. Use for voice timing and audio revisions.
---

# Motion Voice

Narration is the timing source for narrated videos. Use one continuous take for newly generated narration where practical; preserve supplied recordings and intentional splices. Do not force voice onto silent or music-led work.

Read [audio-workflow.md](references/audio-workflow.md) and the [project contract](../motion-video-producer/references/project-contract.md). The bundled [voice tool](scripts/voice.py) uses Python stdlib for import/splicing, FFmpeg for conversion, and an optional ElevenLabs adapter. It never reads a private config file automatically; credentials come from `ELEVENLABS_API_KEY` and are not printed or saved.

## Import or generate

For supplied recording + alignment, normalize the audio to mono 16-bit PCM WAV, validate timestamps and segment text, and record the audio hash. With no alignment, request/import provider or forced-alignment output through available tools. Browser pause detection is approximate sentence timing, not word alignment; use seconds cues until precise alignment exists.

For TTS, supply voice/model/language/settings explicitly in `voice-config.json`. Run the dry-run first to show text and configuration without spending. Generate only within authorized scope. Stop after an API error and report the actionable failure; do not repeatedly spend quota. Do not overwrite an existing take silently.

## Revise safely

Trim only inter-word silence supported by alignment, preserving a configurable pause; do not speed up approved narration to fit a duration. Listen at joins. A splice is sample-exact arithmetic, not proof of inaudibility.

Replacement dry-run must show the exact matched span and surrounding context. Repeated text needs an occurrence. The tool accepts a supplied replacement WAV/alignment so provider choice stays open; optional ElevenLabs generation passes preceding/following context. Preserve the original take and metadata in a unique backup before any overwrite. Level-match carefully and apply short amplitude ramps without consuming samples.

The tool updates script text, alignment, word IDs, duration and audio hash together. It invalidates resolved timing, compositions and QA. Re-cue deleted words and update captions/visual copy; downstream timing cannot repair a changed claim automatically. Boundary and speech-overlap checks must pass before mutation.

## Handoff

Run timing resolution again, rebuild, inspect/listen to joins and neighboring beats, then verify all outputs. Use hyperframes-audio for placed-track mixing, voiceover carve, ducking, fades, FX/automation and shared buses; follow its presets/diagnosis guidance and listen to the finished relationship. media-use can supply authorized music/SFX or transcription; embedded-captions can turn suitable talking-head alignment into captions. The [capability map](../motion-video-producer/references/hyperframes-routing.md) preserves source/provider ownership. Audio editing here is source preparation, not a second media playback engine.
