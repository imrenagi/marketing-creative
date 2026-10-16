# UTM decisions

Use existing workspace rules first. For a new taxonomy, a useful default is lowercase readable slugs with one documented separator, such as `gochi-hsk-id-2026q4`; this is a local convention, not a provider requirement. Do not silently normalize existing values: case differences can split reporting. Keep names stable after publication, and avoid unnecessary high-cardinality values.

| Parameter | Decision |
| --- | --- |
| `utm_source` | Referring publisher/site/list, e.g. `facebook`, `instagram`, `newsletter`. Do not collapse both Meta publishers into `meta` unless the existing taxonomy deliberately does so. |
| `utm_medium` | Channel vocabulary, e.g. `paid_social`, `email`, `cpc`. Reuse the analytics team's exact mapping; custom labels are not a guarantee of a default channel classification. |
| `utm_campaign` | Stable campaign name shared by these links; product/initiative and meaningful market or flight distinctions. Avoid tying it to a mutable creative headline. |
| `utm_id` | Optional stable campaign identifier. Agree its namespace with reporting/cost imports; do not fabricate an ad-platform campaign ID. |
| `utm_content` | Creative/variant identifier; include placement only when it helps distinguish measured variants. Use the creative team's stable IDs, not a new unrelated naming scheme. |
| `utm_term` | Keyword or another explicitly documented targeting meaning. Omit when unnecessary; never include personal identifiers or sensitive audience details. |
| `utm_source_platform` | Optional buying/management platform with an agreed reporting meaning. Distinguish it from the actual publisher in `utm_source`. |

The helper requires source, medium and campaign for complete manual tags; that is this workflow's validation rule. Optional values are omitted when unused. Do not fill every field with placeholders such as `unknown`. Missing necessary inputs keep the draft blocked for generation, while independent campaign notes can still be saved.

## URL and platform boundaries

Parse URLs and encode values once; do not concatenate an unescaped string. Preserve destination paths, existing non-UTM query parameters (including click identifiers), and fragments. Do not replace existing UTMs or remove auto-tagging without resolving which system owns them. Avoid manually rewriting signed URLs; use a suitable public landing page or the owner's supported tagging mechanism.

Default to static values. If the user needs provider macros, verify current supported tokens, insertion field, encoding and preview behavior against that provider's official documentation and record date/source. Keep a macro template separate from resolved URLs and label its validation state. The bundled static helper rejects macros; do not present an escaped literal macro as a working dynamic tag.

Do not tag internal website navigation with acquisition UTMs. App/deep-link attribution, redirectors, shorteners and QR services need their actual integration verified; a website UTM URL alone does not establish install attribution. No analytics SDK, pixel or consent configuration is changed by this skill.

## Official source register

Reviewed 2026-10-16:

- [Google Analytics: Traffic-source dimensions, manual tagging and auto-tagging](https://support.google.com/analytics/answer/11242870?hl=en): manual source/medium/campaign and content/term dimensions; integrated auto-tagging takes precedence for traffic classification, with fallback behavior when click identifiers cannot be used. Preserve identifiers and document the actual measurement setup.
- [Google Analytics: URL builders](https://support.google.com/analytics/answer/10917952?hl=en): case-sensitive parameter values and consistent naming. Search excerpts were available during review; the full page timed out. Recheck the full documentation before changing provider-specific behavior.

These sources describe Analytics behavior. Naming vocabulary, directory layout and required manual fields above are workflow decisions, not universal platform rules. Verify current documentation when configuring a specific analytics or ad-platform integration.
