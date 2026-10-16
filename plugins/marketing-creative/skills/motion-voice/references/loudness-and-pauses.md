# Loudness and pause policy

These are source-narration operations. Music/SFX buses, ducking and the finished mix remain with the composer and runtime audio tools. Preserve supplied performance choices and listen to actual results.

## Measured loudness

```sh
python3 <this-skill>/scripts/voice.py normalize PROJECT --target-lufs -16 --true-peak -1.5 --lra 9 --dry-run
python3 <this-skill>/scripts/voice.py normalize PROJECT --target-lufs -16 --true-peak -1.5 --lra 9
```

The defaults are −16 LUFS integrated, −1.5 dBTP maximum true peak and target loudness range 9 LU. They are working mono-narration targets, not a verified platform specification or a guarantee about the final stereo mix. Valid filter ranges: integrated −70..−5, true peak −9..0, range 1..50. Select different targets deliberately when the project needs them.

Generated audio uses these controls by default; generate --no-normalize preserves its level. Imported recordings preserve their level; import --normalize applies the controls. For an existing take, normalize is entirely local and needs no API key. Trim/replace do not automatically normalize a whole approved take; run normalize after the final source edit when needed.

The helper measures the whole take, passes measured integrated loudness/range/peak/threshold/offset into a second FFmpeg loudnorm pass, then measures the resulting 16-bit PCM again. It requests linear processing; FFmpeg can fall back to dynamic processing when peak/range constraints prevent linear gain. The recorded mode identifies what actually happened. Output rate is set explicitly, and frame count/rate must equal the original so word timestamps stay valid. No speed change or padding is used to conceal a mismatch.

Measured integrated loudness must land within 0.5 LU of target, and true peak must not exceed target by more than 0.2 dB. A missed target, changed clock, silent/too-short unmeasurable take or FFmpeg failure leaves the existing project intact. Normalized generation saves its raw paid result first; if finishing fails, use that saved take with normalize or --no-normalize on a future new take, never automatically regenerate the successful paid request.

Successful normalization stores alignment.loudness with targets, measured integrated/truePeak/range, mode and audioSha256. The ordinary synchronized take backup includes prior metadata. Changing PCM through trim/replacement/import clears measurements tied to a different hash. Normalization refreshes audioSha256 and invalidates derived timing/QA; re-resolve/rebuild before delivery even though the word times are unchanged. Dry-run previews targets and does not measure audio or run FFmpeg.

Normalization does not repair prosody, denoise a recording or prove that a splice sounds natural. Listen after normalization, particularly if dynamic mode was used; measure/listen to the final music/voice/stereo export separately.

Verified 2026-10-16 against the official [FFmpeg loudnorm documentation](https://ffmpeg.org/ffmpeg-filters.html#loudnorm): two-pass measured parameters, linear/dynamic fallback, output sample-rate control, valid ranges and JSON measurements. Local executable checks use the available FFmpeg version recorded in the repository validation log. No TTS provider model, API contract or pricing is changed by these local operations.

## Explicit pause classes

```json
{
  "schemaVersion": 1,
  "classes": {"default": 0.24, "step": 0.42, "dramatic": null},
  "rules": [
    {"before": {"segment": "steps", "quote": "First"}, "class": "step"},
    {"before": {"segment": "reveal", "quote": "the result"}, "class": "dramatic"}
  ]
}
```

Use real segment IDs and exact phrases from the current script/alignment. All class names start with a letter and contain letters/digits/underscore/hyphen. A cap is a finite number ≥0.05 seconds; null preserves the entire gap. classes.default is required and overrides --cap as the fallback. Without --pause-config, --cap retains the previous single-cap behavior. No language-specific step detection runs automatically.

```sh
python3 <this-skill>/scripts/voice.py trim PROJECT --pause-config pause-policy.json --dry-run
python3 <this-skill>/scripts/voice.py trim PROJECT --pause-config pause-policy.json
```

Each rule selects the inter-word gap immediately before the phrase's first aligned token. A phrase repeated within a segment needs explicit one-based occurrence. Before cues accept segment, quote and optional occurrence only; seconds/offset/edge are not supported here. A rule before the take's first word is invalid because no inter-word gap exists. Unknown classes, missing/ambiguous cues or two rules selecting the same gap fail before mutation. Opening/trailing silence is outside this operation.

The dry-run lists each candidate cut's class, retained cap and actual integer-frame removal, plus explicitly preserved gaps. Caps are maximum retained silence, not added pauses; a gap already shorter than its cap is unchanged. Each cut retains half its cap at each edge, checks boundary signal and applies short in-place ramps. Timestamps shift by actual removed frames. Invalid rules and unsafe boundaries leave the original take untouched.

When a script revision deletes/changes an anchor, update the pause policy and review it again; a saved class file does not silently follow unrelated new words. Keep the chosen policy in project production notes so later revisions can reuse it. Deliberate holds may require corresponding storyboard timing and visual ownership changes.
