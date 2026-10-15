# Mixed-media assembly

The producer owns one project and the final timeline. Keep the briefs, selected concept, script, STYLE.md, storyboard, asset manifest, semantic timing and per-ratio layouts authoritative. Provider clips and generated images are source assets; their requested duration is not final timeline truth.

## Choose sources and preserve authorization

Record a compact asset plan with beat/asset IDs, source type, source path or generation request, intended screen role, evidence status, aspect/framing, sourceStart, audible/muted/mixed policy and review state. Suitable sources include supplied captures, footage, generated images, approved Veo/Omni clips, HTML components, Three.js scenes, narration and music/SFX. Planning rows describe choices; they do not submit paid calls.

Default to supplied media and deterministic local construction. When generated footage is useful, prepare its actual config, media preview, model/mode/settings and current estimate. Obtain explicit user approval before paid submission. Do not silently choose a provider, run an expensive fallback, generate several candidates or extend a clip under general production permission. Resume saved jobs without submitting again; another generation/edit/extension needs approval covering that prepared request.

## Import immutable assets

The [importer](../scripts/assets.py) copies each selected local file to assets/imported/ID/, records SHA-256 and measured media metadata, backs up assets/manifest.json and appends one stable asset ID. It supports raster/SVG images, FFprobe-readable video/audio and explicit local scene resources such as GLB, JS, HTML, CSS and fonts. Resource dependencies are not rewritten: retain/bundle glTF sidecars and component imports in the project generator or use self-contained resources. Imported source files are not modified.

```sh
ASSET_TOOL="$SUITE/motion-video-producer/scripts/assets.py"
python3 "$ASSET_TOOL" /path/to/project --file /path/to/omni-v1/desk-detail-1.mp4 --id opening --provider-manifest /path/to/omni-v1/assets.json --generated-id desk-detail --audio-policy mute --dry-run
python3 "$ASSET_TOOL" /path/to/project --file /path/to/omni-v1/desk-detail-1.mp4 --id opening --provider-manifest /path/to/omni-v1/assets.json --generated-id desk-detail --audio-policy mute
python3 "$ASSET_TOOL" /path/to/project --file /path/to/product.png --id product --source 'user-supplied product image'
python3 "$ASSET_TOOL" /path/to/project --file /path/to/model.glb --id product-model --kind resource --source 'approved product model'
```

Use the actual filename in the generated assets manifest. Gemini batch images may live in its images/ subdirectory; --file always points to the actual selected file. --provider-manifest verifies the generated item hash, preserves model/request/approval provenance when available and rejects dimension mismatches. Request identities in the manifest, item, sibling state and approval must agree; a sibling state is attributed only when bound to a known manifest request. --generated-id selects the provider's original ID when the project uses another name. Use a new asset ID/version for replacement; the importer never overwrites existing asset directories. An interrupted import leaves its new file and manifest backup for reconciliation.

Imports default to reviewed=false. After actually inspecting frames/images or listening, --review-note can record that inspection; it cannot substitute for doing it. If recording a later review directly in the manifest, retain the reviewed file hash and note, then re-resolve/rebuild because metadata changed. Provider reviewIssues remain visible even when deliberately accepted for a composition. Do not deliver until material identity, claim, text, motion, crop and audio issues are resolved or explicitly accepted within scope.

## Compose one timeline

Use visual.mode=image with an image asset ID, or mode=footage with a video ID, sourceStart and hasAudio. Source windows must fit measured duration. Trim a scene to the narrative, not by stretching generated speech or trusting prompt timecodes. An extended result may already include its predecessor; inspect the join so composition does not duplicate the opening. Native provider footage is 24 FPS and 16:9/9:16; frame conversion and separate 4:5/1:1 compositions belong to the final render, without distorting content.

The importer's audioPolicy records mute, retain or mix; the composer must implement it. Silent b-roll has hasAudio=false. Retained/mixed footage needs a real audio stream and hasAudio=true. Music/SFX beds and ducking use timed audio in the custom composition; aligned speech remains motion-voice's responsibility. A metadata label alone does not perform a mix.

Three.js and authored HTML components use project.generator plus custom:<scene> beats. The same project-local generator can place ordinary images/footage, HTML overlays and 3D scenes. See the [project contract](project-contract.md) and [runtime contract](../../motion-composer/references/runtime.md). Follow installed HyperFrames/animation guidance for the current adapter: state must derive from the canonical seek time, with explicit initial states, seeded randomness, local dependencies and framework-owned media playback. Do not add an independently running animation clock, autoplay or second player. Freeze components/models/fonts/shaders before rendering and fingerprint every generated dependency. A compatible custom build manifest is mandatory.

The bundled construction generator handles its documented primitives and image/footage beats only. Do not send custom Three.js/HTML beats to it and claim they rendered. Author or reuse the appropriate project generator, preserve Studio edits in source, and report unavailable runtime/adapter verification honestly.

## Verify final integration

After imports or revisions, resolve timing, rebuild affected variants and run production QA. Manifest/input hashes invalidate older timing/build/export records; previous outputs remain intact for reference. Verify every source window, transition, overlay, important product detail, crop and audio handoff. Capture boundaries/midpoints and repeat-seek frames for custom scenes. Listen to mixed sound and check actual encoded exports in all requested ratios. Provider success, imported metadata or a local source check is not final delivery QA.
