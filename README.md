# Marketing Creative

A repository for marketing skills and plugins, with one shared skill source for Codex and Claude Code.

The first skill, **ad-video-director**, turns product facts, goals and references into a creative brief, original hooks, a timed script, exact copy, shot direction, and a measurement plan. It supports awareness, consideration, conversion, activation, leads, retargeting and re-engagement. It plans ads; an actual video render or campaign launch is a separate deliverable.

## Install and use

The plugin lives in `plugins/marketing-creative/`. Codex and Claude manifests reference the same `skills/` directory; no generated copy or symlink is required.

### Codex

From a local checkout, using a version with plugin support:

```sh
codex plugin marketplace add /absolute/path/to/marketing-creative
codex plugin add marketing-creative@marketing-creative
```

Restart/reload the client if needed. The repo marketplace also makes the package discoverable from the desktop plugin directory. After this change merges, the Git source can be registered with `codex plugin marketplace add imrenagi/marketing-creative`.

Invoke `$ad-video-director`, for example:

> Use $ad-video-director to plan a 30-second Indonesian Reels ad for my app. Goal: activated users. Here are its current features, screenshots, audience objections, and onboarding destination. Give me hook alternatives and a shootable timeline.

### Claude Code

Local preview without installing:

```sh
claude --plugin-dir ./plugins/marketing-creative
```

Then invoke `/marketing-creative:ad-video-director`. To install from this checkout, run `/plugin marketplace add /absolute/path/to/marketing-creative`, then `/plugin install marketing-creative@marketing-creative`. After merge, use `/plugin marketplace add imrenagi/marketing-creative` for the GitHub source.

### Standalone skill

Copy `plugins/marketing-creative/skills/ad-video-director/` into a supported personal or project skill directory. Keep its `references/` and `agents/` subdirectories intact. No account, API key, renderer, or paid tool is required to draft a plan; browsing/media tools improve reference inspection when available.

## What it produces

- A concise brief grounded in audience awareness and campaign goal.
- Distinct hook hypotheses with first frame, exact words, expected payoff and evidence.
- A complete timeline with persuasive purpose, dialogue, overlay, action, assets and meaningful edit/audio cues. Literal one-second rows are available on request.
- Claim/asset requirements, placement copy, production notes and focused tests.
- Reference analysis that separates observations from performance claims and original adaptations.

The skill contains a source register covering eight published campaign examples, TikTok/Google/Meta guidance, and lessons from the user-provided deck's PDF pages 35–45. Timing templates are explicitly heuristics, not guaranteed winning formulas. Sample recordings, sample-specific notes, and trial outputs are not part of the package.

## Validate and package

```sh
python3 scripts/validate_package.py
claude plugin validate ./plugins/marketing-creative
claude plugin validate ./.claude-plugin/marketplace.json
python3 scripts/build_plugin.py --output /tmp/marketing-creative-plugin.zip
```

The build creates one dual-client plugin ZIP from an explicit allowlist of manifests and skill resources. It does not archive the repository or include samples, local documents, the PDF, or other untracked files. Review `docs/skill-evaluation.md` for behavioral evaluation scenarios. Sample media under `samples/` and local sample analyses and trial scripts under `local-docs/` are ignored and remain local.

Packaging follows [official OpenAI plugin documentation](https://developers.openai.com/plugins/build/plugins), [Claude's plugin reference](https://code.claude.com/docs/en/plugins-reference), and [Claude marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces). Structural checks do not establish successful installation or model behavior in every client version.
