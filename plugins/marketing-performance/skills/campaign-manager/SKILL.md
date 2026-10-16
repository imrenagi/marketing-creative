---
name: campaign-manager
description: Define campaign UTM conventions, generate tagged product campaign links, and maintain campaign plans and tracking records in the current workspace. Use for new campaign tagging or revisions to existing UTMs.
---

# Campaign Manager

Own both marketing operations (shared taxonomy and traceability) and campaign management (campaign decisions and usable links). Save the work in the user's current workspace so it can be reviewed and committed. Generating UTMs does not authorize campaign publication, ad-account changes or analytics implementation.

## Find the campaign record

Read workspace guidance, existing campaign directories, briefs and tagging conventions first. Reuse the user's campaign root; otherwise use `marketing/campaigns/` under the current workspace. Never save campaign work inside the installed plugin. Use [workspace-records.md](references/workspace-records.md) to create or resume the record and index without overwriting unrelated material.

Start from the supplied product, campaign or brief. For a URL-only request, establish just the destination, distribution sources/media, campaign identity and variants. Ask only about missing facts that change the links; draft unresolved decisions without inventing destinations, platform IDs, offers or a launch date. Use [marketing-brief](../marketing-brief/SKILL.md) when broader strategy is requested or materially missing, and save its output in this campaign's directory. Do not restart intake for an existing brief.

## Define and apply the convention

Read [utm-conventions.md](references/utm-conventions.md). Reuse the workspace taxonomy and exact existing values. When there is none, propose and document a compact convention, then apply it consistently. Separate stable campaign/link/creative IDs from display names; record who owns unresolved decisions.

Use one campaign identity across its links, source/medium for distribution, and `utm_content` to distinguish relevant creative or placement variants. Add optional IDs, platform or terms only with a defined meaning. Keep personal information and credentials out of URLs and records. Preserve auto-tagging and click identifiers; do not add UTMs to internal navigation. Dynamic provider macros require current official verification; the bundled helper supports static values only.

## Generate and retain the URLs

Create or update `campaign.json` using the [link plan contract](references/link-plan.md) and [fictional example](assets/campaign.example.json). Keep the full link inventory, including published/retired entries. Run the local helper with Python 3.10+ (standard library only):

```sh
python3 <skill-dir>/scripts/build_utm.py <campaign-dir>/campaign.json --dry-run
python3 <skill-dir>/scripts/build_utm.py <campaign-dir>/campaign.json --out <campaign-dir>/tracking/v001
```

Replace the placeholders with resolved paths; choose the next unused revision. Dry-run validates and previews URLs without writing or contacting a service. A real run saves the input snapshot, `utm-links.csv` and `UTM_PLAN.md` in a fresh directory. Existing UTMs cause an error rather than silent replacement; resolve their ownership before rebuilding. The helper preserves other query bytes and fragments.

Compare revisions before delivery. Never change a published link's meaning under the same ID: preserve it and add a new ID for a changed destination or tracking tuple. Record replacements, retirement and the reason. Update campaign notes and the shared index with the current revision path.

## Verify and hand off

Check the generated values against the taxonomy and campaign brief, including creative IDs and destination ownership. Record local checks separately from live checks. Follow [workspace-records.md](references/workspace-records.md) for redirect, consent/analytics and conversion checks when available within scope; unperformed checks stay pending. A valid URL does not prove attribution or performance.

Return the record path, current revision, usable links, naming decisions and remaining checks. Include the exact destination URLs and field mapping for the ad-publishing owner. Keep text records suitable for Git; follow workspace commit rules, but do not stage, commit or push merely because this skill ran.
