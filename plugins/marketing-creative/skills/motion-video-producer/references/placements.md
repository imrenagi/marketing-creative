# Canvas and placement profiles

These are production presets, not asserted current upload limits:

| Ratio | Default resolution | Composition use |
| --- | --- | --- |
| 16:9 | 1920×1080 | Landscape; UI/proof and claim can share a horizontal composition |
| 9:16 | 1080×1920 | Full-screen portrait; tighter focal crop and stacked hierarchy |
| 4:5 | 1080×1350 | Portrait feed; reduce supporting detail, retain readable proof |
| 1:1 | 1080×1080 | Square; compact copy and balanced subject/CTA placement |

Select by actual placement, not device. Desktop does not imply every ad slot is 16:9. Mobile feed, Stories and Reels are distinct contexts. “Meta” alone does not determine duration, safe area or upload requirements. Non-video display inventory is outside this video export contract.

## Verify profiles at production time

A profile records `platform,name,verificationStatus` and, when verified, `sourceUrl,verifiedOn` (ISO date). Optional verified limits: `maxDuration,maxFileBytes,minWidth,minHeight`. Verify current official specs, account placement previews and overlays for the intended objective/placement. If unavailable, mark unverified and report the limitation. Never invent verification dates or copy old requirements as current.

Meta's general [Reels guidance](https://www.facebook.com/business/ads/facebook-instagram-reels-ads) emphasizes 9:16, audio and safe-zone messaging. Detailed [Ads Guide](https://www.facebook.com/business/ads-guide/) requirements are placement-specific and can change. Some pages require login. Cache selected evidence with its scope/date in production notes, not as a universal rule in this skill.

## Safe area

`safeArea` fractions mean reserved top/right/bottom/left edges. Initialization uses an 8% editorial margin on each side solely for a construction example. It is not a Meta UI mask. Supply actual placement exclusions before delivery and inspect overlays at the current platform preview.

Safe zones can vary by placement, caption expansion, CTA/button and account experience. For irregular overlays, add a mask to the project's review assets and inspect beyond the rectangular measurement check. Keep logos, text, product proof and action clear.

## Adapt, inspect, encode

Recompose each required ratio. Do not merely center-crop, letterbox or shrink a landscape video. Change the text measure, focal crop, camera coordinates, panel stacking and caption location while retaining the selected argument and claims.

Produce actual width/height at build time; the browser viewport must match for snapshots and export. Test longest text and transition extremes. A readable 16:9 frame is not evidence for 9:16. For a deliberate same-ratio lower-resolution proof, label it as a test export, not final delivery.

Default example export contract: MP4, H.264 video; AAC if narration/audio is required; configured FPS. Verify with FFprobe. Change codecs if the selected placement requires it. No hardcoded 179-second rule or universal platform duration cap is inherited.
