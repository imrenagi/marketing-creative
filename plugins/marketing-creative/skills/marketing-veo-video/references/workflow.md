# Veo request and recovery workflow

Use Python 3.10+, Pillow from the suite image requirements for local image inputs, and FFprobe for downloaded-file verification. No Google SDK is required. Set GEMINI_API_KEY in the helper's shell using the repository README's external .env instructions. Install the full plugin; common job mechanics live in the producer's scripts/video_provider.py.

Copy [veo.example.json](../assets/veo.example.json) to a campaign work directory. This fictional prompt and dated example quote need review; verify current pricing and replace costEstimate before approval. Configuration contains schemaVersion, id, model, mode, prompt, aspectRatio, durationSeconds, resolution and optional personGeneration, seed, negativePrompt and costEstimate. The latter has usd, source URL and checkedAt date. Unknown fields fail locally.

Mode-specific inputs:

- image: image is a local path or {path,mimeType}; interpolate additionally needs lastFrame.
- reference: referenceImages is a list of one to three local images.
- extend: sourceRun points to a completed earlier Veo run. Refresh/download it before expiry. The helper uses its generated URI or fingerprinted received bytes, checks provenance and adds seven seconds to the expected source runtime.

Media/sourceRun paths resolve relative to the config. A missing prompt is allowed for image-driven modes; write one when useful. Native output ratios are 16:9 and 9:16. Optional references do not force a new image-generation request; reuse available approved images.

```sh
VEO_TOOL="$SUITE/marketing-veo-video/scripts/veo_video.py"
python3 "$VEO_TOOL" submit veo.json --out /path/to/work/veo-v1 --dry-run
# After the user approves this exact plan and current estimate:
python3 "$VEO_TOOL" submit veo.json --out /path/to/work/veo-v1 --approve-request SHA_FROM_DRY_RUN --approval-note 'User approved this Veo request in chat'
python3 "$VEO_TOOL" status /path/to/work/veo-v1
python3 "$VEO_TOOL" download /path/to/work/veo-v1
```

Dry-run needs neither a key nor network and writes no files. Approval flags record existing human authorization; do not invent approval notes to bypass the gate. If prompt, media, settings, provenance or quote changes, prepare again and obtain approval for the changed request. The estimate is not a hard spend limit. No generation, retry or extension runs automatically.

state.json records provider/model/request/reference hashes, approval note, operation identity and output locations. Inline returned MP4 bytes are preserved as received-N.mp4 before probe/review. assets.json records local generated files, measured dimensions/duration/FPS/audio, hashes and reviewIssues. It does not mark footage reviewed. Retry downloads against the same job; matching files are retained and changed files are refused. Missing FFprobe leaves received output available for recovery.

Status makes one query and returns. Filtered/failed jobs are reported without regeneration. A lost submission response may have incurred cost; do not resubmit just because no operation name was saved. Provider-operation cancellation is not advertised by this Gemini Veo helper; inspect the supported provider controls before proposing cancellation.

For uploaded files needed by another workflow, the shared command surface also provides file-upload FILE --out NEW_DIR [--dry-run] and file-status UPLOAD_DIR. Uploads do not generate video and may expose private source media; use only sources authorized for provider upload. Veo image inputs stay inline, while extension uses its previous generated output.
