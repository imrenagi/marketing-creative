# Workspace campaign records

Honor an existing campaign layout and source of truth. The following is a default for a workspace without one, not a migration requirement:

```text
marketing/campaigns/
  INDEX.md
  UTM_CONVENTIONS.md
  <campaign-id>/
    README.md
    MARKETING_BRIEF.md       # only when created or supplied as a file
    campaign.json
    MEASUREMENT.md
    CHANGELOG.md
    tracking/
      v001/
        campaign.json       # immutable generation snapshot
        utm-links.csv
        UTM_PLAN.md
```

Use a stable, nonpersonal campaign slug. Reuse the record for follow-up work; do not create a duplicate just because the chat or date changed. Check the index and existing IDs before assigning a new one. If the workspace has no writable local directory, explain the limitation and provide the proposed files; do not claim they were saved.

## What to record

- **INDEX.md:** campaign ID, product, objective, lifecycle status, record path and current tracking revision. Update only the affected rows. A campaign's lifecycle status is separate from its links' publication status.
- **UTM_CONVENTIONS.md:** exact source/medium vocabulary, campaign/creative/placement naming, optional field meanings, existing aliases, analytics/channel assumptions, owner and dated changes. Preserve established casing; suggest normalization for new values without rewriting historical tags.
- **Campaign README.md:** product and objective, audience/market/language when known, destination/CTA, relevant channels and variants, supplied brief path, facts/evidence, assumptions, open decisions and owner, current revision, and exact publishing handoff. Do not invent budgets, schedules or campaign results. Link to source documents rather than duplicating a supplied brief.
- **campaign.json:** current complete link plan; retain published and retired IDs. Snapshots under tracking revisions preserve earlier inputs and exports.
- **MEASUREMENT.md:** primary conversion and its definition, analytics destination/property if known, attribution scope, relevant auto-tagging, validation status/evidence/date, and unresolved implementation work. Keep measurement unknowns explicit.
- **CHANGELOG.md:** dated decisions, link additions/replacements, status transitions, reason and affected IDs. Distinguish planned, actually published and retired links; generating an export does not publish it.

For a small tagging request these files can be brief. Do not manufacture a research report or force a full marketing interview. If the user requests no filesystem changes, deliver the records in chat and respect that override.

## Revision and publication rules

Before changing the current plan, compare it with the latest snapshot. Existing published/retired IDs retain their destination and UTM values. A changed tracking tuple or destination needs a new link ID; record its predecessor. A status-only change can keep the ID. Update a draft ID in a new revision when appropriate, documenting the change.

Exports go into an unused revision directory. Never overwrite previous exports or repair an interrupted run by deleting it. Inspect retained files, then use the next unused revision; these operations have no paid submission. Preserve user-written campaign notes and unrelated local edits.

Keep campaign records in the product workspace, not in this plugin's source, global skill directories, ignored media output or temporary folders. Use relative documentation links where possible. Do not silently change `.gitignore`, initialize Git or stage files. Keep raw customer data, credentials, signed/private URLs, recordings and binary assets out of the records; reference approved workspace assets instead.

## Validation evidence

Local helper checks establish syntax, required fields, unique IDs and encoded parameter round-trips only. Also compare taxonomy values, campaign identity, destination and creative/placement mapping to the brief and prior revisions.

When live verification is authorized and tools are available, test a representative URL per destination/redirect path, record the final destination and whether parameters/click IDs survive, and inspect receipt in the intended analytics tool under the applicable consent state. Check the intended signup/purchase event separately when in scope. Do not trigger real purchases or mutate tracking settings merely to test a URL. Avoid visiting links that themselves perform an action.

Record checks as passed, failed or pending with evidence and date. HTTP success alone does not prove analytics collection; a collected visit does not prove conversion attribution. Assign blockers to the publishing or engineering owner and do not describe pending links as attribution-verified.
