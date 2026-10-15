#!/usr/bin/env python3
"""Portable project validation and semantic timing resolution (Python stdlib)."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import unicodedata
import wave
from datetime import date

PRESETS = {"16:9": (1920, 1080), "9:16": (1080, 1920),
           "4:5": (1080, 1350), "1:1": (1080, 1080)}
MODES = {"type", "ui-tour", "counter", "collage", "stage", "image", "footage"}
INPUTS = ("project.json", "script.json", "storyboard.json", "assets/manifest.json")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, name, minimum=0):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= minimum, f"Invalid {name}: {value!r}")
    return value


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]*", value),
            f"Invalid ID: {value!r}")
    return value


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local(root, relative):
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(),
            f"Expected project-relative file: {relative!r}")
    path = (Path(root) / relative).resolve()
    require(path.is_relative_to(Path(root).resolve()), f"Path escapes project: {relative}")
    return path


def safe_output(root, relative):
    root = Path(root).resolve()
    path = local(root, relative)
    current = root
    for part in Path(relative).parts:
        current = current / part
        require(not current.is_symlink(), f"Symlinked output path refused: {relative}")
    return path


def normalized(text):
    """Preserve all scripts; ignore punctuation/spacing, never strip Han characters."""
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def phrase_span(words, segment, quote, occurrence=None):
    selected = [(i, w) for i, w in enumerate(words) if w["segment"] == segment]
    require(selected, f"No aligned words for segment {segment}")
    needle = normalized(quote)
    require(needle, "Cue phrase must contain letters or digits")
    chars, owners = "", []
    boundaries = {0}
    for index, word in selected:
        token = normalized(word["text"])
        chars += token
        owners.extend([index] * len(token))
        boundaries.add(len(chars))
    matches, start = [], 0
    while (at := chars.find(needle, start)) >= 0:
        end = at + len(needle)
        # Latin/numeric cues match whole aligned tokens, not 'one' inside 'someone'.
        if not needle.isascii() or (at in boundaries and end in boundaries):
            matches.append((owners[at], owners[end - 1]))
        start = at + 1
    require(matches, f'Phrase {quote!r} not found in segment {segment}')
    if occurrence is None:
        require(len(matches) == 1, f'Ambiguous phrase {quote!r}; supply occurrence (1..{len(matches)})')
        return matches[0]
    require(isinstance(occurrence, int) and not isinstance(occurrence, bool)
            and 1 <= occurrence <= len(matches), "Occurrence out of range")
    return matches[occurrence - 1]


def validate_alignment(root, project, script):
    voice = project.get("voice")
    if not voice:
        return None
    audio = local(root, voice["audio"])
    alignment = read(local(root, voice["alignment"]))
    require(alignment.get("schemaVersion") == 1, "Unsupported alignment schema")
    require(audio.is_file() and digest(audio) == alignment.get("audioSha256"),
            "Audio changed or missing; re-align before resolving timing")
    with wave.open(str(audio), "rb") as wav:
        require(wav.getnchannels() == 1 and wav.getsampwidth() == 2,
                "Working narration must be mono 16-bit PCM WAV")
        duration = wav.getnframes() / wav.getframerate()
    require(abs(number(alignment.get("duration"), "alignment duration") - duration) < .002,
            "Alignment duration differs from WAV duration")
    segments = {s["id"]: s["text"] for s in script["segments"]}
    words = alignment.get("words", [])
    require(words, "Alignment has no words")
    seen, last = set(), 0
    segment_order = [s["id"] for s in script["segments"]]
    last_segment = -1
    for word in words:
        require(word["id"] not in seen, "Duplicate aligned word ID")
        seen.add(word["id"])
        require(word.get("segment") in segments, "Aligned word has unknown segment")
        current_segment = segment_order.index(word["segment"])
        require(current_segment >= last_segment, "Alignment segments are out of script order")
        last_segment = current_segment
        require(isinstance(word.get("text"), str) and normalized(word["text"]), "Empty aligned word")
        start, end = number(word["start"], "word start"), number(word["end"], "word end")
        require(start >= last - .0001 and end > start and end <= duration + .001,
                f'Invalid/overlapping word timing: {word["id"]}')
        last = end
    for segment, text in segments.items():
        require(normalized(text) == normalized("".join(w["text"] for w in words if w["segment"] == segment)),
                f"Script/alignment text differs in {segment}; re-align or revise together")
    number(voice.get("start", 0), "voice start")
    return alignment


def load(root):
    root = Path(root).resolve()
    project, script, board, manifest = [read(root / name) for name in INPUTS]
    for name, obj in zip(INPUTS, (project, script, board, manifest)):
        require(obj.get("schemaVersion") == 1, f"Unsupported schema in {name}")
    identifier(project.get("id"))
    if project.get("generator"):
        generator = local(root, project["generator"])
        require(generator.is_file() and generator.suffix == ".mjs", "Custom generator must be a project-local .mjs file")
    require(isinstance(project.get("language"), str) and project["language"], "Missing language")
    variants = project.get("variants", [])
    require(variants, "No output variants")
    seen = set()
    for variant in variants:
        identifier(variant.get("id"))
        require(variant["id"] not in seen, "Duplicate variant ID")
        seen.add(variant["id"])
        ratio = variant.get("ratio")
        require(ratio in PRESETS, f"Unsupported ratio {ratio}")
        w, h = variant.get("width"), variant.get("height")
        require(all(isinstance(n, int) and not isinstance(n, bool) and n > 0 and n % 2 == 0 for n in (w, h)),
                "Canvas dimensions must be positive even integers")
        a, b = map(int, ratio.split(":"))
        require(w * b == h * a, f"Canvas does not match {ratio}")
        number(variant.get("duration"), "variant duration", .01)
        require(isinstance(variant.get("fps"), int) and 1 <= variant["fps"] <= 120, "FPS must be 1..120")
        safe = variant.get("safeArea", {})
        for side in ("top", "right", "bottom", "left"):
            require(0 <= number(safe.get(side), f"safeArea.{side}") < 1, "Safe area uses fractions")
        require(safe["top"] + safe["bottom"] < 1 and safe["left"] + safe["right"] < 1,
                "Safe area leaves no visible region")
        placement = variant.get("placement", {})
        require(placement.get("verificationStatus") in ("unverified", "verified"), "Missing placement verification status")
        if placement["verificationStatus"] == "verified":
            date.fromisoformat(placement["verifiedOn"])
            require(re.match(r"https?://", placement.get("sourceUrl", "")), "Verified placement needs source URL")
        for key in ("maxDuration", "maxFileBytes", "minWidth", "minHeight"):
            if key in placement:
                number(placement[key], key, .01)
        if "maxDuration" in placement:
            require(variant["duration"] <= placement["maxDuration"], "Duration exceeds placement limit")
        for key, dim in (("minWidth", w), ("minHeight", h)):
            if key in placement:
                require(dim >= placement[key], f"Canvas below placement {key}")
    require(isinstance(script.get("segments"), list), "script.segments must be an array")
    segment_ids = set()
    for segment in script["segments"]:
        identifier(segment.get("id"))
        require(segment["id"] not in segment_ids and isinstance(segment.get("text"), str)
                and normalized(segment["text"]), "Duplicate/empty script segment")
        segment_ids.add(segment["id"])
    asset_ids = set()
    for asset in manifest.get("assets", []):
        identifier(asset.get("id"))
        require(asset["id"] not in asset_ids, "Duplicate asset ID")
        asset_ids.add(asset["id"])
        path = local(root, asset["path"])
        require(path.is_file(), f"Missing asset: {asset['path']}")
        require(asset.get("source"), f"Missing provenance: {asset['id']}")
        require(asset.get("sha256") == digest(path), f"Changed asset: {asset['id']}; update manifest after review")
    alignment = validate_alignment(root, project, script)
    return project, script, board, manifest, alignment


def input_hashes(root, project=None):
    root = Path(root)
    project = project or read(root / "project.json")
    paths = list(INPUTS)
    if project.get("generator"):
        paths.append(project["generator"])
    if project.get("voice"):
        paths.extend(project["voice"][key] for key in ("audio", "alignment"))
    manifest = read(root / "assets/manifest.json")
    paths.extend(asset["path"] for asset in manifest.get("assets", []))
    return {name: digest(local(root, name)) for name in sorted(set(paths))}


def cue_time(cue, alignment, offset):
    require(isinstance(cue, dict), "Cue must be an object")
    if "seconds" in cue:
        require(set(cue) == {"seconds"}, "Seconds cue cannot also contain a word anchor")
        return number(cue["seconds"], "cue seconds")
    require(alignment, "Word cue needs aligned narration; use explicit seconds for unaligned audio")
    lo, hi = phrase_span(alignment["words"], cue["segment"], cue["quote"], cue.get("occurrence"))
    edge = cue.get("edge", "start")
    require(edge in ("start", "end"), "Cue edge must be start or end")
    shift = cue.get("offset", 0)
    require(isinstance(shift, (int, float)) and math.isfinite(shift), "Invalid cue offset")
    return offset + alignment["words"][lo if edge == "start" else hi][edge] + shift


def resolve(root, save=True):
    project, script, board, manifest, alignment = load(root)
    overrides = board.get("variants", {})
    require(set(overrides) <= {v["id"] for v in project["variants"]}, "Storyboard override has unknown variant")
    output = {"schemaVersion": 1, "inputHashes": input_hashes(root, project), "variants": []}
    assets = {a["id"] for a in manifest.get("assets", [])}
    for variant in project["variants"]:
        beats = overrides.get(variant["id"], board.get("beats", []))
        require(beats, f'No beats for {variant["id"]}')
        resolved, seen, previous = [], set(), 0
        for beat in beats:
            identifier(beat.get("id"))
            require(beat["id"] not in seen, "Duplicate beat ID")
            seen.add(beat["id"])
            start = cue_time(beat["start"], alignment, project.get("voice", {}).get("start", 0))
            end = cue_time(beat["end"], alignment, project.get("voice", {}).get("start", 0))
            require(start >= 0 and end > start and end <= variant["duration"] + .001, f'Invalid beat window: {beat["id"]}')
            require(abs(start - previous) <= .001, f'Gap/overlap before {beat["id"]}; cover it with an explicit beat')
            previous = end
            if not beat.get("intentionalBlank", False):
                visual = beat.get("visual", {})
                mode = visual.get("mode", "")
                custom = isinstance(mode, str) and re.fullmatch(r"custom:[A-Za-z][\w-]*", mode)
                require(mode in MODES or (custom and project.get("generator")),
                        f'Unknown visual mode in {beat["id"]}; custom:<name> requires project.generator')
                if mode in {"type", "ui-tour", "counter", "collage", "stage"}:
                    require(isinstance(visual.get("text"), str) and visual["text"].strip(), "Visual text is required for this example primitive")
                if mode in {"image", "footage"}:
                    require(visual.get("asset") in assets, "Image/footage needs a declared asset")
                    asset = next(a for a in manifest["assets"] if a["id"] == visual["asset"])
                    require(asset.get("kind") == ("video" if mode == "footage" else "image"), "Media asset kind differs")
                    if mode == "footage":
                        source_start = number(visual.get("sourceStart", 0), "footage sourceStart")
                        require(source_start + end - start <= number(asset.get("duration"), "asset duration", .01) + .001,
                                "Footage source runs out before beat ends")
                        require(isinstance(visual.get("hasAudio", False), bool), "hasAudio must be boolean")
                        policy=asset.get("audioPolicy")
                        if policy=="mute":
                            require(not visual.get("hasAudio",False),"Footage hasAudio contradicts muted asset audioPolicy")
                        elif policy in {"retain","mix"}:
                            require(asset.get("hasAudio") is True and visual.get("hasAudio",False),
                                    "Retained/mixed footage needs a measured audio stream and hasAudio=true")
                if visual["mode"] == "counter":
                    number(visual.get("value"), "counter value")
                if "asset" in visual:
                    require(visual["asset"] in assets, "Visual refers to unknown asset")
            resolved.append({**copy.deepcopy(beat), "start": round(start, 6), "end": round(end, 6)})
        require(abs(previous - variant["duration"]) <= .001, f'Uncovered ending in {variant["id"]}')
        if alignment:
            require(project["voice"].get("start", 0) + alignment["duration"] <= variant["duration"] + .001,
                    "Narration would be truncated; create a separate cutdown")
        output["variants"].append({**copy.deepcopy(variant), "beats": resolved})
    if save:
        write(safe_output(root, "timing.resolved.json"), output)
    return output


def init(root, slug, ratios, duration):
    root = Path(root)
    identifier(slug)
    number(duration, "duration", .1)
    require(not root.exists() or not any(root.iterdir()), "Refusing to initialize a nonempty project directory")
    require(ratios and len(ratios) == len(set(ratios)), "Ratios must be unique")
    root.mkdir(parents=True, exist_ok=True)
    variants = []
    for ratio in ratios:
        require(ratio in PRESETS, f"Unsupported ratio: {ratio}")
        w, h = PRESETS[ratio]
        variants.append({"id": "ratio-" + ratio.replace(":", "x"), "ratio": ratio, "width": w, "height": h,
                         "duration": duration, "fps": 30,
                         "safeArea": {"top": .08, "right": .08, "bottom": .08, "left": .08},
                         "placement": {"platform": "unspecified", "name": "construction example",
                                       "verificationStatus": "unverified"}})
    write(root / "project.json", {"schemaVersion": 1, "id": slug, "language": "en", "selectedConcept": None,
                                  "exampleOnly": True, "variants": variants,
                                  "style": {"background": "#101923", "foreground": "#F7F5EF", "accent": "#FFBC69"}})
    write(root / "script.json", {"schemaVersion": 1, "segments": []})
    source = Path(__file__).resolve().parents[2] / "motion-composer/assets/example/storyboard.json"
    board = read(source)
    for beat in board["beats"]:
        beat["start"]["seconds"] *= duration / 8
        beat["end"]["seconds"] *= duration / 8
    write(root / "storyboard.json", board)
    write(root / "assets/manifest.json", {"schemaVersion": 1, "assets": []})
    resolve(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("init")
    start.add_argument("project")
    start.add_argument("--id", required=True)
    start.add_argument("--ratios", nargs="+", choices=PRESETS, default=list(PRESETS))
    start.add_argument("--duration", type=float, default=8)
    for command in ("validate", "resolve"):
        sub.add_parser(command).add_argument("project")
    args = parser.parse_args()
    if args.command == "init":
        init(args.project, args.id, args.ratios, args.duration)
    else:
        expected = resolve(args.project, save=args.command == "resolve")
        if args.command == "validate":
            require(read(Path(args.project) / "timing.resolved.json") == expected,
                    "Resolved timing is stale; run resolve")
    print(f"{args.command}: project valid")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError, wave.Error) as error:
        print(f"project: {error}", file=sys.stderr)
        sys.exit(1)
