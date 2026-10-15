# Marketing Creative

Nine agent skills take a campaign from marketing strategy through creative ideas, exact scripts and animated video production. Codex and Claude Code use the same source. Production supports **16:9, 9:16, 4:5 and 1:1** as independently composed and reviewed variants.

## Skills and handoffs

| Skill | Input → output |
| --- | --- |
| `marketing-brief` | Product facts, research and goal → strategic brief, evidence, placement requirements |
| `creative-ideation` | Marketing brief → distinct concepts and selected creative brief |
| `ad-video-director` | Selected idea and brief → exact script, copy, shot direction and production handoff |
| `motion-video-producer` | Authorized production request → coordinated project and deliverables |
| `motion-art-director` | Selected concept and brand → visual system, camera and motion language |
| `motion-storyboard` | Script and style → visual beats, semantic cues and per-ratio framing |
| `motion-voice` | Narration/script → aligned audio, pause trimming and backed-up phrase replacement |
| `motion-composer` | Resolved storyboard → seekable HyperFrames compositions in requested ratios |
| `motion-video-qa` | Source/build/export → integrity checks, frame review and encoded-file verification |

Use only the stages needed. Supplied briefs, selected ideas and recordings enter downstream; small revisions do not restart intake. Planning alone does not launch campaigns or render a video. A general explainer can bypass advertising strategy. Existing ad-video-director invocations continue to work, with strategy and ideation routed to their new owners when needed.

## Install

The complete plugin lives in plugins/marketing-creative/. Install the whole suite: sibling references and tools are part of its contract. Copying only one skill folder is no longer a complete standalone installation.

### Codex

```sh
codex plugin marketplace add /absolute/path/to/marketing-creative
codex plugin add marketing-creative@marketing-creative
```

Or register imrenagi/marketing-creative after the relevant release is published. Reload the client if needed. Invoke $marketing-brief, $creative-ideation, or any skill in the table.

### Claude Code

```sh
claude --plugin-dir ./plugins/marketing-creative
```

Invoke /marketing-creative:marketing-brief, for example. For installation, use /plugin marketplace add /absolute/path/to/marketing-creative, then /plugin install marketing-creative@marketing-creative.

For clients without plugin support, reference the complete skill tree from the client's instruction file, retaining all sibling skills and third-party/ notices. No global installation or client configuration is changed by this repository.

## Example requests

> Use $marketing-brief for our task app. Goal: users completing their first assignment. Audience: small design teams. We have real captures but no verified trial offer. Plan Meta feed, Reels, landscape and square deliverables.

> Use $creative-ideation with this marketing brief. Give me three distinct directions, explain the evidence each needs, and recommend one.

> Use $ad-video-director to turn the selected demonstration concept into a 20-second Indonesian script. Preserve the brief's objective, offer and destination.

> Use $motion-video-producer to produce the selected concept in 16:9, 9:16, 4:5 and 1:1. Recompose for each placement and review every output.

> Use $motion-voice to replace this CTA in the existing recording. Preview the matched phrase first, preserve the original take and retime downstream cues.

## Production tools

Planning needs no renderer, account, API key or paid service. Project validation uses Python 3.9+; composition uses Node 20+. HyperFrames is the external default preview/render runtime. FFmpeg/FFprobe are needed for audio conversion and encoded-file checks. Playwright plus a Chromium browser is optional for the visual probe. ElevenLabs is one optional TTS adapter; supplied audio/alignment works without it.

### API keys and local configuration

Keep optional credentials outside this repository, in **`~/.config/marketing-creative/.env`** or your preferred secret manager. The bundled tools read environment variables; they **do not automatically load `.env` files**.

| Credential | Used by | Required when |
| --- | --- | --- |
| `ELEVENLABS_API_KEY` | `motion-voice/scripts/voice.py` | Generating narration or a replacement phrase through the ElevenLabs adapter |

No API key is required for briefs, ideation, scripts, supplied audio/alignment, pause trimming, supplied replacement audio, composition, or local QA. External image/media connectors and HyperFrames manage their own authentication; this package does not currently read `FAL_KEY`, OpenAI keys, or HyperFrames credentials directly.

Create the local file, then edit it with your editor:

```sh
mkdir -p "$HOME/.config/marketing-creative"
chmod 700 "$HOME/.config/marketing-creative"
touch "$HOME/.config/marketing-creative/.env"
chmod 600 "$HOME/.config/marketing-creative/.env"
```

Its contents use shell assignment syntax (replace the example value locally):

```sh
ELEVENLABS_API_KEY='your-elevenlabs-api-key'
```

Export it in the **same shell that invokes the helper**, without printing its contents:

```sh
set -a
. "$HOME/.config/marketing-creative/.env"
set +a
python3 "$SUITE/motion-voice/scripts/voice.py" generate /path/to/video-project --config /path/to/voice-config.json --dry-run
```

Set `SUITE` to the installed skills directory (or the checkout path shown below). The dry-run makes no API call. Omit `--dry-run` only when ready to generate. For agent-run commands, have the agent load the local file in the helper's shell; a desktop app launched separately may not inherit your terminal's environment.

`voice-config.json` contains nonsecret voice/model IDs, language, voice settings and an optional seed; it does not contain the API key. Never place credentials in skill files, project JSON, prompts, commits, or release archives. Repository `.env` files are also ignored as a precaution.

The following runs an **original fictional construction example**, not a ready-made ad. Outputs stay outside the repository:

```sh
SUITE="$PWD/plugins/marketing-creative/skills"
python3 "$SUITE/motion-video-producer/scripts/project.py" init /tmp/video-example --id demo --ratios 16:9 9:16 4:5 1:1 --duration 8
node "$SUITE/motion-composer/scripts/compose.mjs" /tmp/video-example --gsap /path/to/local/gsap.min.js
python3 "$SUITE/motion-video-qa/scripts/check.py" /tmp/video-example
```

The generator includes type, illustrative UI, counter, collage and character-stage examples, plus supplied image and footage modes. Custom generators can register custom visual modes. Narration anchors preserve Unicode and reject missing/ambiguous matches. Project/input fingerprints detect stale timing, assets and builds; manually edited output is preserved until reconciled.

Read the [project contract](plugins/marketing-creative/skills/motion-video-producer/references/project-contract.md), [placement profiles](plugins/marketing-creative/skills/motion-video-producer/references/placements.md), [audio workflow](plugins/marketing-creative/skills/motion-voice/references/audio-workflow.md) and [QA procedure](plugins/marketing-creative/skills/motion-video-qa/references/checks.md) for commands and limitations.

Canvas presets are 1920×1080, 1080×1920, 1080×1350 and 1080×1080. They are not universal ad-upload specifications. Select actual placements, verify current limits/safe areas, and adapt layouts; do not simply crop a landscape master. No platform-wide 179-second rule is imposed.

## Validate and package

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_package.py
claude plugin validate ./plugins/marketing-creative
claude plugin validate ./.claude-plugin/marketplace.json
python3 scripts/build_plugin.py --output /tmp/marketing-creative-plugin.zip
```

The deterministic ZIP includes only manifests, skill instructions/references, approved scripts/example resources and upstream notices. It excludes samples, local documents, generated video/audio, dependencies and credentials. samples/ and local-docs/ stay local and ignored. Tests do not call paid APIs.

[Behavioral evaluation scenarios](docs/skill-evaluation.md) complement executable tests. Package checks do not establish installation, model behavior, rendered quality or advertising performance. Machine QA explicitly distinguishes source checks from browser inspection, framework checks, listening and actual exports.

## Attribution

Visual direction is adapted from [Bang Motion](https://github.com/bangtutorial/bang-motion); timing/revision/verification ideas from [Hyperframe Pro](https://github.com/buildwithhanif/hyperframe-pro). Their MIT notices are retained in third-party/. See the [adaptation register](plugins/marketing-creative/skills/motion-video-producer/references/sources.md). Upstream gallery media and private sample assets are not bundled.
