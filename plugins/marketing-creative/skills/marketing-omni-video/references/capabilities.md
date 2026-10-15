# Omni Flash capability register

Verified 2026-10-15 against the [Omni guide](https://ai.google.dev/gemini-api/docs/omni), [model card](https://ai.google.dev/gemini-api/docs/models/gemini-omni-flash), [Interactions API](https://ai.google.dev/api/interactions-api) and [streaming guide](https://ai.google.dev/gemini-api/docs/streaming). These sources own the model-specific limits; general multimodal/SDK fields do not imply support in Omni.

| Capability | Script support |
| --- | --- |
| Text and generated sound | mode=text; camera, lighting, subject motion, dialogue, music, SFX and time cues through prompt |
| Image animation | mode=image; one image bound as first_frame, with optional other references |
| Interpolation | mode=interpolate; first_frame and last_frame with explicit bindings |
| Loop | mode=loop; binds the same image as both endpoints |
| Image/likeness references | mode=reference or references alongside a source; reference tags distinguish appearance from literal frame sources |
| Video reference | Up to three video_reference clips, each <=3s; likeness/appearance guidance, with their audio ignored; not multi-video narrative reasoning |
| Uploaded-video editing | mode=edit with one video_source, <=10s; preserve requested content through the prompt |
| Conversational editing | Python continue RUN CONFIG or mode=edit with previousRun/previousInteractionId; inherits omitted parent settings, saves turn links and reads local branch history; each turn generates a new video |
| Continuation | mode=extend with an uploaded source or stored prior turn; append at the end, with a combined target <=40s |
| Resolution/upscale | 360p, 720p, 1080p and 4k; higher resolutions are upscaled. mode=upscale requests a 3..10s source at 1080p/4k, preserving duration |
| Output format | Native 16:9/9:16, 3..10-second requested output, 24 FPS, MP4, inline or URI delivery |
| Execution/storage | Unary, background and SSE; store=true enables later retrieval/chaining; store=false retains only creation output locally |
| Strict task override | Optional task values text_to_video, image_to_video, reference_to_video, edit, extend; prompt/role binding remains the preferred default |
| Lifecycle | Saved interaction identity, one-shot status, ready-file download, background cancellation, local metadata/hash review |

Default model is gemini-omni-1.1-flash; gemini-omni-flash-preview is an explicit alternate whose availability/feature parity must be checked. The helper targets Gemini Developer API, not Vertex-specific GCS delivery. Uploaded supported video formats can be supplied inline or via Files; large sources use the upload helper. URI inputs declare their measured duration in the config so dry-run remains offline.

Limitations matter for marketing: no standalone audio-reference upload, voice editing, system instructions, temperature/top_p, stop sequences, dedicated negativePrompt field, YouTube source or provisioned throughput. Put ordinary negative directions in prompt text. Uploaded edit/extension sources are <=10s; uploaded references <=3s. Do not use several primary videos as a reasoning task. Certain people/minor inputs and uploaded-video edits/extensions have regional restrictions; generated multi-turn footage follows the documented exception. Uploaded talking footage cannot be extended with new dialogue, while generated multi-turn dialogue extension is supported.

Prompt timecodes and identities are directions, not guaranteed exact output. Extension may alter the joining frames; inspect whether the provider returned a joined clip or continuation. Inputs/outputs pass provider safety controls; all generated videos carry SynthID. English prompting is the evaluated baseline.

Use current [pricing](https://ai.google.dev/gemini-api/docs/pricing) to estimate input, thinking and output costs at the selected resolution/mode. The example estimate is illustrative, not a hard billing ceiling. No video batch discount is asserted.
