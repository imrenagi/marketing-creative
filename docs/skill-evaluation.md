# Behavioral evaluation scenarios

Run these by loading the skill and only the raw brief/reference needed for each case. Keep generated plans outside commits. Check output decisions, factual support, timing and producibility rather than exact headings or wording. A valid manifest is not a behavioral evaluation.

| Scenario | Observable acceptance criteria |
| --- | --- |
| 30-second cold-audience app ad, objective activated users, screenshots available, no price supplied | Chooses a relevant first-use task, measures activation instead of CPI alone, invents no price/trial, covers all 30 seconds, gives ready-to-say lines and usable capture directions |
| Same product, warm audience, price objection and verified offer | Changes ordering/proof to address the barrier; does not repeat unnecessary category setup; uses only the supplied terms and one matching destination |
| Six-second awareness cutdown requested from a 75-second creator ad | Writes one memorable product-linked idea; does not cram all dialogue or five full modules into six seconds; preserves attribution and explains the changed job |
| Reference recording starts mid-ad and contains post-ad browsing | Separates recording duration from creative span; labels proposed opening; excludes browsing/UI from authored creative; does not assert sample ROAS |
| "Make it viral; promise fluency in seven days" without evidence | Offers a strong demonstrable alternative and keeps the unsupported result out of final copy |
| Ten hooks and literal one-second breakdown | Produces distinct buyer/visual mechanisms, chooses a supported hypothesis, covers every second without requiring a cut each second, and pays off the actual hook |
| High retention, low sales supplied as the only results | Does not declare CTA the cause; inspects relevance, proof, offer, destination, tracking and downstream quality; proposes a discriminating next test |
| Creator comment reply requested without an authentic comment | Uses a labeled question/FAQ instead of manufacturing a customer endorsement; distinguishes demonstrator from real customer |

Keep sample-specific analyses, raw media, trial outputs, and evaluation outcomes local unless explicitly selected for publication. Do not infer successful installation, model behavior, or ad performance from structural packaging checks.

## Revised suite scenarios

| Scenario | Observable acceptance criteria |
| --- | --- |
| Strategy-only request | Marketing brief records objective/metric, audience/barrier, supported claims and placement requirements; does not force a hook or start production |
| Open brief followed by selection | Concepts differ in mechanism; selected creative brief retains ID/evidence; director scripts chosen idea without repeated intake |
| Supplied selected concept/script | Producer resumes downstream without unnecessary campaign interview |
| Desktop landscape, mobile Reels, portrait feed and square | Four canvases configured; placements distinguished from device; independent layout/frame/export checks |
| Real captures and no verified trial | Capture/image/footage or custom generator path explicit; illustrative UI is not proof; no invented offer |
| Narration arrives later | Provisional seconds replaced by word cues; missing alignment precision reported |
| Repeated CTA or Mandarin phrase | Ambiguity fails unless occurrence supplied; Han characters preserved; segmentation limits identified |
| CTA revision | Dry-run shows span/context; backup; synchronized script/audio/alignment; visual copy/cues/captions and neighboring beats reviewed |
| User edited generated HTML | Edits preserved/reconciled before rebuilding |
| Intentional silence/stillness | Editorial choices distinguished from broken coverage; no forced continuous motion |
| Runtime/browser/provider unavailable | Exact pending validation reported; no false rendered-delivery claim |
| Wrong-ratio/missing-audio/stale encode | Affected export fails; actual file/build hashes recorded after current render |

Executable regressions live in tests/test_production.py. Browser/framework smoke tests use temporary projects and local dependencies. Review actual snapshots and listen to audio where applicable. Fixtures and screenshots are not committed as finished campaign assets.

## Image workflow scenarios

| Scenario | Observable acceptance criteria |
| --- | --- |
| Brief, optional references and an open concept count | Chooses enough distinct ideas for the task; chooses a readable sheet ratio/grid; one board request; each occupied cell crops to its stable concept ID |
| Five or eleven concepts, portrait/landscape sheet | No fixed nine-item requirement; explicit or automatic grid has sufficient cells; blank trailing cells are not saved as assets |
| No reference, or product plus style references | Brief-only generation works; supplied references are viewed and assigned roles; final selected tile has the correct image index |
| Concept selected from the board | Stable ID maps to its own crop; standalone request uses original source plus selected tile; unselected ideas are not generated |
| Multi-slide carousel instead of alternatives | Plan preserves slide order and continuity; does not force nine unrelated concepts |
| Model adds gutters or uneven cells | Inspects board and uses measured crop boxes or deliberate revision; does not claim geometric splitting verified composition |
| Request nine production-resolution images | Explains preview resolution; reconstructs selected finals separately, instead of claiming nine 4K files from a single 4K board |
| Three selected finals with flexible deadline | Uses actual Batch API, persists job identity, returns for status/download later; distinguishes discount from output quality |
| One failed batch item, one wrong-ratio response | Preserves successes and wrong-ratio bytes, flags item errors and review issues; no automatic paid resubmission |
| Submission timeout or interrupted download | Unknown submission retains state for provider lookup; interrupted collection resumes with matching files and no new generation |
| Transparent product/reference or changed local tile | Crops preserve alpha; changed tile hash requires deliberate reconciliation |
| Square, portrait feed, vertical and landscape images | Requests 1:1, 4:5, 9:16 and 16:9 explicitly; checks actual dimensions and current placement specifications |
| No key or live provider validation | Dry-run and splitting work without credentials; reports that offline validation does not establish real model quality/access |

Executable image regressions live in tests/test_marketing_images.py and use synthetic pixels and mocked API responses. Independent forward-testing exercised the requested board → selection → batch → recovery path offline. Live marketing-image quality requires an authorized provider run and visual review.

## Optional generated video and assembly

| Scenario | Observable acceptance criteria |
| --- | --- |
| Produce an ad without provider approval | Producer uses supplied/local sources; Veo/Omni remain off; optional generation plan does not launch a paid call |
| User asks to explore Veo or Omni | Prepares exact prompt/media, model/mode/settings and current estimate; dry-run needs no key/network; asks for approval before paid generation |
| Approved request subsequently changes | Changed content/settings/reference/quote invalidates the approval fingerprint; no silent reuse or model fallback |
| First/last frames and character/style references | Correct explicit source/reference roles; loops reuse their endpoint; unsupported duration/model/control combinations fail locally |
| Uploaded talking footage requested for voice editing | Omni limitation is identified; narration revision routes to motion-voice, preserving existing footage when appropriate |
| Submission timeout, interrupted SSE or provider expiry | Preserves identity/received files, queries once, downloads/reuses verified local output; no automatic paid regeneration |
| Follow-up edits in the same conversation after a restart | Python history/continue selects the intended saved run, chains its interaction ID, inherits omitted settings and preserves each parent; every paid edit has a new approval |
| Earlier-version branch or unresolved conversational turn | Explicit parent selection controls branching; pending/unknown/stateless turns fail before submission; old outputs remain intact and local history never claims server context is permanent |
| Three.js scene, HTML overlay, product image and generated b-roll | Producer maintains one timeline/manifest, imports selected source hashes and measured media, routes custom scenes to a project generator; does not claim bundled engine renders arbitrary custom visuals |
| Native vertical footage requested as square/feed ad | Reframes in separate 1:1/4:5 compositions, reviews focal detail/text/audio in each; a new provider generation still needs approval |
| Retained soundtrack or mute/mix mismatch | Measured source audio and storyboard hasAudio agree with audioPolicy; actual playback/mix/listening verified before delivery |
| Imported unreviewed or changed source | Changed hashes fail; provider findings and pending review remain visible; imports invalidate timing/build/export fingerprints |

tests/test_generated_video.py uses fake providers, synthetic media and actual local FFprobe checks. tests/test_asset_assembly.py covers immutable imports, provenance, source hashes, backups, audio policy, all four ordinary-media compositions and custom-generator resource contracts. Contract fixtures do not establish actual Three.js rendering or live generated-video quality.

## Optional HyperFrames capabilities

| Scenario | Observable acceptance criteria |
| --- | --- |
| Named effect, 3D product scene or mascot in a selected concept | Relevant registry/animation adapter is read before implementation; compatible generator preserves seekable playback, selected brand, stable timing and dependency hashes |
| Existing briefs handed to a specialized runtime workflow | Derives the upstream handoff without repeating strategy; preserves all four requested ratios, source evidence and paid-provider approval rules |
| Sound, media polish or revision review needs improvement | Routes to the matching audio/media/keyframe/CLI domain; actual frame/listening evidence establishes quality, not loading a skill |
| Reference checkout exists but required tool is unavailable | Uses accessible guidance, completes independent work and identifies missing execution/verification; does not claim installation, render success or send public feedback |


## Campaign operations and UTM records

| Scenario | Observable acceptance criteria |
| --- | --- |
| Existing brief, two channels and a destination | Starts from supplied facts, creates/reuses a campaign directory and taxonomy, generates distinct links and saves a reproducible revision without a full intake restart |
| Existing workspace taxonomy with mixed-case legacy tags | Preserves exact legacy values and IDs; documents any proposed convention for new tags without rewriting published values |
| Revisit an existing campaign in a later chat | Finds the index/current revision, preserves notes and exports, records changes under the existing campaign and uses the next unused revision |
| Published creative gets a new destination or tracking tuple | Keeps old link identity and snapshot; introduces a new link ID and records replacement/retirement instead of silently rewriting history |
| Destination contains query, click ID, fragment or existing UTMs | Preserves unrelated query bytes/fragment; existing UTM conflicts block generation until ownership is resolved |
| User requests Meta macros or app install attribution | Verifies official provider integration requirements and labels unresolved templates; does not treat encoded macros or static website UTMs as verified install tracking |
| Analytics inaccessible or consent checks unperformed | Distinguishes local URL validity from live collection, records pending checks and owner, and makes no performance claim |
| User wants files they can commit | Records remain in the product workspace with text plans/registries and no secrets; no implicit Git commit, push or campaign publication |
| Marketing Performance installed alone | Both skills have portable local references, brief generation needs no creative tools, and the extracted helper runs without Marketing Creative |

These are behavioral evaluation scenarios, not claims of completed model evaluation. Executable URL/export regressions use fictional plans and temporary directories; no live analytics or ad accounts are needed.
