# Veo capability register

Verified 2026-10-15 against the [Veo guide](https://ai.google.dev/gemini-api/docs/veo), [model card](https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview), [Lite card](https://ai.google.dev/gemini-api/docs/models/veo-3.1-lite-generate-preview) and [SDK configuration reference](https://googleapis.github.io/js-genai/release_docs/interfaces/types.GenerateVideosConfig.html). Refresh the owning source and tests when updating these limits.

| Capability | Script support / constraint |
| --- | --- |
| Text to video | mode=text; camera, motion, appearance, dialogue, ambient sound and SFX through prompt |
| Image animation | mode=image with local image; additional prompt optional |
| First/last-frame interpolation | mode=interpolate with image and lastFrame |
| Subject/content references | mode=reference with one to three referenceImages, encoded as asset references |
| Continuation | mode=extend with sourceRun from previous Veo output; 720p, matching ratio, source <=141s; the combined video adds approximately seven seconds |
| Model selection | veo-3.1-generate-preview (default), veo-3.1-fast-generate-preview and veo-3.1-lite-generate-preview; no silent fallback |
| Native canvases | 16:9 or 9:16; other final canvases belong to composition |
| Duration/resolution | 4/6/8 seconds at 720p; 1080p/4k and references/extension require durationSeconds=8; Lite excludes 4k, references and extension |
| Sound/frame rate | Native generated soundtrack, always on, 24 FPS; mute or mix in composition |
| People | personGeneration control, with image-based modes restricted to allow_adult; check region-specific restrictions before spend |
| Additional controls | seed (not deterministic) and negativePrompt |
| Jobs and output | Asynchronous predictLongRunning, operation status, local download, measured metadata and hashes |

One video is requested per submission. Veo extension accepts previously generated Veo footage, not arbitrary uploaded edits; sourceRun preserves this provenance. The server retains generated videos for two days. Regional availability, safety and audio processing may prevent generation. English prompting is the documented baseline; review other languages explicitly. Outputs contain SynthID.

These are Gemini Developer API capabilities. Unified SDK fields for masks, arbitrary FPS, audio disabling, GCS output and other Vertex-specific controls are not evidence those controls work in this Gemini integration. Do not invent them. Describe desired editing in Omni or assemble locally when appropriate, with the same paid-use approval boundary.

Costs come from the current [pricing page](https://ai.google.dev/gemini-api/docs/pricing) and actual API project. Estimate the requested model/resolution/duration before approval; a stored quote is an estimate, not an enforced billing cap. No batch discount is asserted for video.
