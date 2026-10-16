# Plan the beat before the generator

Use the script's meaning to decide what the viewer needs to see. These are editorial decision rules, not guarantees of retention. Preserve the selected brand, exact mandated wording and evidence requirements. Silent and music-led work can use seconds or an approved music grid instead of narration cues.

## Job → hero → action

The hero is the primary visual carrying the beat's meaning. Identify one dominant hero; supporting elements should clarify it rather than demand equal attention.

| Line or moment | Beat job | Useful hero and action |
| --- | --- | --- |
| An event happens: an order arrives, a file disappears | Make the event understood | Show the event unfolding in footage, a staged illustration or an authored scene; land the decisive action on its cue |
| A viewer recognizes a specific product/OS screen | Recognition and proof | Use an authentic capture, cropped to the relevant state; highlight the actual control or result |
| A sensation or abstract mechanism | Explain what cannot be captured directly | Use an object, diagram or illustration whose state changes; do not invent an OS warning as evidence |
| A numbered sequence is promised | Set expectations | Show the supported count or route; keep progress visible when it helps a longer sequence |
| A reversal: “but actually…” | Replace the viewer's expectation | Transform the prior state or reveal the contrast; avoid an unrelated title reset |
| A supported numeric result | Make the change legible | Count or compare the spoken value with a clear unit; preserve the baseline and scale |
| A demonstrated step | Make the action reproducible | Show the relevant screen/object and its changed state; navigation crumbs support rather than replace available proof |
| A recap or total | Connect the parts | Reuse the items actually established; verify the arithmetic before showing a sum |
| Closing line or CTA | Show the next action | Pair the exact line with the destination/action it names |

Choose the visual treatment deliberately: authentic captures for claims about real screens; footage/photography when physical action and realism matter; illustration/HTML/Three.js for concepts, sensations or a selected stylized brand. Photorealism is a choice, not a universal rule for threats. Label reconstructed/illustrative UI as such and do not present it as product proof. A generic icon is weak evidence for a specific screen the audience is meant to recognize.

## Beat sheet

Write one row per meaningful visual response, not automatically one per sentence. Keep stable beat IDs shared with storyboard.json.

| ID / job | Start → end cue | Hero / treatment / asset | Visible action or state change | Framing and zones per ratio | Exact type / annotation | Handoff and sound |
| --- | --- | --- | --- | --- | --- | --- |
| recognition / establish problem | problem: “storage is full” → solution: “clear” | authentic capture / storage-alert | focus the capacity value | 9:16: tight screen crop above caption strip; 16:9: screen left, explanation right; character absent | supplied alert copy; one measured highlight | screen yields to changed state on “clear”; optional soft hit |
| proof / demonstrate result | solution: “clear” → result: “space” | reviewed before/after captures | show the actual freed-space state | repeat the focal detail in each ratio; move overlay if it occludes the value | verified result and unit | hold long enough to compare; avoid a decorative whoosh |

For each requested ratio, declare media, type/caption and optional character zones using normalized bounds or measured canvas coordinates. Mark unused zones absent. Overlap is allowed when intentional and legible, such as a callout attached to a control; text crossing the hero's key detail or a presenter's face requires correction. Measure annotations against the source crop and verify their rendered position.

Map executable fields to the [project contract](../../motion-video-producer/references/project-contract.md): id/job, start/end, visual, layoutNotes, captions and sfx. Put detailed zone geometry and rationale in layoutNotes or the readable beat sheet; a custom generator may implement additional fields explicitly. Directional notes alone do not place overlays or sounds. Use segment + exact phrase anchors and explicit occurrence for repeated phrases; missing anchors are errors, never a reason to guess a timestamp.

## Review gates before handoff

1. **Meaning:** Can the viewer identify what changed and why this visual belongs to the line? If the beat is only text plus decoration, show an action, comparison or progressive explanation, or record why a deliberate type hold serves the line.
2. **Hero/readability:** Inspect at the intended viewing size in every ratio. Crop to the important detail or sequence competing information before shrinking the hero. A screen occupying roughly three quarters of the width can be a useful starting point for a screen-led portrait beat; it is not a fixed pixel rule for all visuals or canvases.
3. **Zones:** Check captions, overlays, annotations and characters together. Reframe or move the secondary material when zones collide. Do not fix a crowded composition solely by reducing type size.
4. **Continuity:** Inspect the outgoing state, transition extreme and incoming state. Start the exit relative to the next cue and bring the new focal information in soon enough to avoid an unexplained empty interval. A roughly 0.4-second exit is a starting point, not mandatory timing.
5. **Ownership:** An old screenshot or annotation must exit, transform or remain for an explicit comparison when the step changes. A retained object should carry continuity, not accidentally cover later beats.
6. **Purposeful holds:** Unexplained loss of focal information, particularly in the opening, needs revision. About 1.2 seconds without meaningful focal content is a useful review trigger for a brisk narrated cut, not a universal ban on silence or breathing room. Mark deliberate blank beats with intentionalBlank and explain their purpose in layoutNotes.
7. **Evidence:** Numeric overlays agree with the script and source; totals add up; actual screens match the demonstrated platform/state; private identities are cropped or redacted. Record a fallback and its evidence limitation if an authentic capture is unavailable.
8. **Sound:** Name the reason and anchor for any SFX; identify mute/retain/mix for footage. Effects should support an action, not accompany every entrance. Place and listen to them during composition/QA.

These gates require editorial/frame review. The bundled resolver enforces contiguous beat coverage and valid cues/assets; the browser probe samples visibility, safe bounds and overflow. Neither certifies these editorial decisions or continuously measures hero size, collisions or dead air. Record actual inspected frames/times and unresolved items rather than claiming that a passing resolver proves the beat works.

Adapted from Hyperframe Pro's job/hero planning, zone separation and visual ownership guidance; see the [source and license register](../../motion-video-producer/references/sources.md). This suite keeps multi-ratio layouts, intentional silence and evidence-aware stylization.
