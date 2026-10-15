# Audio tooling

Run `python3 <this-skill>/scripts/voice.py --help` for commands. All paths supplied to project configuration are relative to that project. Working takes are mono 16-bit PCM WAV. FFmpeg conversion has no implicit speed change.

## Import

`voice.py import PROJECT --audio TAKE.wav --alignment ALIGNMENT.json` validates the imported segment/word table against script.json, normalizes audio with FFmpeg, records the new hash/duration and writes audio/vo.wav plus audio/alignment.json. The imported alignment shape is the [project contract](../../motion-video-producer/references/project-contract.md); audioSha256/duration are replaced from measured audio. For MP3/provider timestamps, listen/check alignment after conversion.

## TTS

`voice.py generate PROJECT --config voice-config.json --dry-run`, then omit dry-run when authorized. Config requires voiceId/modelId/language/voiceSettings; optional seed. The adapter makes one ElevenLabs with-timestamps call for all script segments joined by line breaks. It maps provider character alignment to segment IDs and writes word alignment. Credentials come only from ELEVENLABS_API_KEY. Existing takes require an explicit revision/import path; no silent paid overwrite or retry loop.

The provider default is not baked into the skill; select an available model/voice intentionally. Other services can generate audio/alignment for import without using this adapter.

## Pause trimming

`voice.py trim PROJECT --cap 0.24 --dry-run`; run without dry-run after inspecting candidate cuts. Only aligned inter-word gaps larger than cap are removed, preserving half the cap each side. Check peak amplitude around each proposed boundary; the tool refuses boundaries above a configurable fraction of the take's peak. No new recording. Six-millisecond ramps change amplitudes in place and consume no samples. All timestamps derive from integer PCM frame positions.

## Replace a phrase

`voice.py replace PROJECT --segment cta --find "Try this today" --replacement replacement.wav --replacement-alignment replacement.json --dry-run`.

An imported replacement alignment uses exactly one segment with the same ID. `--occurrence` disambiguates repeated text. Alternatively use `--text` and `--config` to generate just the replacement with previous/next context; dry-run spends nothing. Partial-token replacements are rejected even if a phrase cue can locate a Han substring inside a token.

Include top-level `text` in the imported replacement JSON to preserve exact wording, punctuation and mixed-script spacing. Otherwise Latin/space-delimited tokens are joined with spaces and exclusively CJK token streams without spaces. The original phrase's script does not determine replacement spacing.

Cuts are between neighboring speech spans, without clipping adjacent words. Boundary ramps and measured gain matching reduce seams but do not guarantee prosody. Listen to joins; if they fail, adjust the replacement recording instead of automatically rerolling paid TTS.

## Backups and state

Every existing take mutation creates a unique directory under audio/backups with original audio, alignment, script and project. Validate the complete replacement before writing. Audio hashes detect partial/stale edits after interruption; recover from the named backup if needed. Source script text, alignment IDs/duration, WAV and voice config references update together; timing/QA/build manifests are invalidated. A generation creates a new take and still leaves previous unrelated assets untouched.

No tool can update the visual meaning of a changed price/claim. Edit corresponding copy, captions, evidence and cue anchors before rebuilding.
