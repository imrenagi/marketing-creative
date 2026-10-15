#!/usr/bin/env python3
"""Import/generate aligned narration and perform backed-up sample-exact revisions."""
import argparse
import array
import base64
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
import wave

spec = importlib.util.spec_from_file_location("motion_project", Path(__file__).resolve().parents[2] / "motion-video-producer/scripts/project.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


def pcm_read(path):
    with wave.open(str(path), "rb") as wav:
        P.require(wav.getnchannels() == 1 and wav.getsampwidth() == 2, "Expected mono 16-bit PCM WAV")
        rate = wav.getframerate()
        data = array.array("h", wav.readframes(wav.getnframes()))
    if sys.byteorder != "little":
        data.byteswap()
    return data, rate


def pcm_write(path, data, rate):
    values = array.array("h", data)
    if sys.byteorder != "little":
        values.byteswap()
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(values.tobytes())


def convert(source, dest):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(dest)],
                   check=True, capture_output=True)


def ramp(data, joins, rate):
    n = max(1, round(rate * .006))
    for join in joins:
        for k in range(min(n, join)):
            data[join - 1 - k] = round(data[join - 1 - k] * k / n)
        for k in range(min(n, len(data) - join)):
            data[join + k] = round(data[join + k] * k / n)


def commit(root, data, rate, alignment, script, project):
    root = Path(root).resolve()
    for name in ("audio/vo.wav", "audio/alignment.json", "audio/backups", "script.json", "project.json", "timing.resolved.json", "qa/report.json"):
        P.safe_output(root, name)
    project = copy.deepcopy(project)
    project["voice"] = {**project.get("voice", {}), "audio": "audio/vo.wav", "alignment": "audio/alignment.json"}
    alignment = copy.deepcopy(alignment)
    alignment["schemaVersion"] = 1
    alignment["duration"] = len(data) / rate
    for i, word in enumerate(alignment["words"]):
        word["id"] = f"w{i}"
    with tempfile.TemporaryDirectory(prefix="motion-voice-") as temp:
        staged = Path(temp)
        (staged / "audio").mkdir()
        pcm_write(staged / "audio/vo.wav", data, rate)
        alignment["audioSha256"] = P.digest(staged / "audio/vo.wav")
        P.write(staged / "audio/alignment.json", alignment)
        P.write(staged / "script.json", script)
        P.write(staged / "project.json", project)
        P.validate_alignment(staged, project, script)
        backup = None
        if (root / "project.json").exists():
            (root / "audio/backups").mkdir(parents=True, exist_ok=True)
            backup = Path(tempfile.mkdtemp(prefix="take-", dir=root / "audio/backups"))
            for name in ("project.json", "script.json"):
                shutil.copy2(root / name, backup / name)
            previous = P.read(root / "project.json").get("voice")
            if previous:
                shutil.copy2(P.local(root, previous["audio"]), backup / "vo.wav")
                shutil.copy2(P.local(root, previous["alignment"]), backup / "alignment.json")
            print(f"Backup: {backup.relative_to(root)}")
        names = ("audio/vo.wav", "audio/alignment.json", "script.json", "project.json")
        # Stage siblings first; os.replace keeps individual files intact on interruption.
        # Restore originals on ordinary write failure; backup supports interruption recovery.
        originals = {name: (root / name).read_bytes() if (root / name).exists() else None for name in names}
        try:
            for name in names:
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                fd, temporary = tempfile.mkstemp(prefix=".voice-", dir=dest.parent)
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write((staged / name).read_bytes())
                    os.replace(temporary, dest)
                finally:
                    Path(temporary).unlink(missing_ok=True)
        except OSError:
            for name, old in originals.items():
                if old is None:
                    (root / name).unlink(missing_ok=True)
                else:
                    (root / name).write_bytes(old)
            raise
    (root / "timing.resolved.json").unlink(missing_ok=True)
    (root / "qa/report.json").unlink(missing_ok=True)
    print(f"Saved {len(data) / rate:.4f}s; re-resolve cues, rebuild and review audio/visuals")


def provider_take(segments, config, folder, previous=None, following=None):
    for field in ("voiceId", "modelId", "language", "voiceSettings"):
        P.require(field in config, f"Voice configuration missing {field}")
    P.require(re.fullmatch(r"[A-Za-z0-9_-]+", config["voiceId"]), "Invalid voice ID")
    key = os.environ.get("ELEVENLABS_API_KEY")
    P.require(key, "ELEVENLABS_API_KEY is required for this adapter")
    text = "\n".join(s["text"] for s in segments)
    body = {"text": text, "model_id": config["modelId"], "language_code": config["language"],
            "voice_settings": config["voiceSettings"], "seed": config.get("seed", 42)}
    if previous:
        body["previous_text"] = previous
    if following:
        body["next_text"] = following
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{config['voiceId']}/with-timestamps?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "xi-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Do not print provider bodies/headers that could expose account/request information.
        raise ValueError(f"TTS HTTP {error.code}; no automatic paid retry") from None
    alignment = result.get("normalized_alignment") or result["alignment"]
    chars, starts, ends = (alignment[k] for k in ("characters", "character_start_times_seconds", "character_end_times_seconds"))
    owners = []
    for segment in segments:
        owners.extend([segment["id"]] * len(P.normalized(segment["text"])))
    require_text = P.normalized(text)
    P.require(P.normalized("".join(chars)) == require_text,
              "Provider normalized text differs from script; inspect/import alignment explicitly")
    words, current, pos = [], None, 0
    for char, start, end in zip(chars, starts, ends):
        if char.isspace():
            if current:
                words.append(current)
                current = None
            continue
        size = len(P.normalized(char))
        owner = owners[min(pos, len(owners) - 1)] if owners else None
        if current and current["segment"] != owner:
            words.append(current)
            current = None
        if current is None:
            current = {"segment": owner, "text": char, "start": start, "end": end}
        else:
            current["text"] += char
            current["end"] = end
        pos += size
    if current:
        words.append(current)
    words = [w for w in words if P.normalized(w["text"])]
    mp3, wav = Path(folder) / "take.mp3", Path(folder) / "take.wav"
    mp3.write_bytes(base64.b64decode(result["audio_base64"]))
    convert(mp3, wav)
    data, rate = pcm_read(wav)
    return data, rate, {"schemaVersion": 1, "words": words}


def dry_summary(args, script, words=None):
    if args.command == "generate":
        print("Would generate one continuous take:")
        print("\n".join(s["text"] for s in script["segments"]))
        return
    lo, hi = P.phrase_span(words, args.segment, args.find, args.occurrence)
    before = " ".join(w["text"] for w in words[max(0, lo - 12):lo])
    after = " ".join(w["text"] for w in words[hi + 1:hi + 13])
    print(f"Matched {words[lo]['start']:.4f}–{words[hi]['end']:.4f}s: " + " ".join(w["text"] for w in words[lo:hi + 1]))
    print(f"Context: {before} | replacement | {after}")
    return lo, hi, before, after


def replace_script(script, words, lo, hi, text):
    result = copy.deepcopy(script)
    segment = next(s for s in result["segments"] if s["id"] == words[lo]["segment"])
    prefix = "".join(P.normalized(w["text"]) for w in words[:lo] if w["segment"] == segment["id"])
    length = sum(len(P.normalized(w["text"])) for w in words[lo:hi + 1])
    indices = []
    for i, char in enumerate(segment["text"]):
        indices.extend([i] * len(P.normalized(char)))
    start, end = indices[len(prefix)], indices[len(prefix) + length - 1] + 1
    # Include punctuation attached to the final replaced aligned word, if present.
    if words[hi]["text"] and not words[hi]["text"][-1].isalnum():
        while end < len(segment["text"]) and not segment["text"][end].isalnum() and not segment["text"][end].isspace():
            end += 1
    segment["text"] = segment["text"][:start] + text + segment["text"][end:]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("import", "generate", "trim", "replace"):
        command_parser = sub.add_parser(command)
        command_parser.add_argument("project")
        command_parser.add_argument("--dry-run", action="store_true")
        if command == "import":
            command_parser.add_argument("--audio", required=True)
            command_parser.add_argument("--alignment", required=True)
        if command == "generate":
            command_parser.add_argument("--config", required=True)
        if command == "trim":
            command_parser.add_argument("--cap", type=float, default=.24)
            command_parser.add_argument("--max-boundary-peak", type=float, default=.1)
        if command == "replace":
            command_parser.add_argument("--segment", required=True)
            command_parser.add_argument("--find", required=True)
            command_parser.add_argument("--occurrence", type=int)
            command_parser.add_argument("--replacement")
            command_parser.add_argument("--replacement-alignment")
            command_parser.add_argument("--text")
            command_parser.add_argument("--config")
    args = parser.parse_args()
    root = Path(args.project).resolve()
    project, script = P.read(root / "project.json"), P.read(root / "script.json")
    if args.command in ("import", "generate"):
        if args.command == "generate":
            P.require(not project.get("voice"), "Existing take: use replacement/import instead of paid full overwrite")
            P.require(script["segments"], "No narration text")
            config = P.read(args.config)
            for key in ("voiceId", "modelId", "language", "voiceSettings"):
                P.require(key in config, f"Missing {key}")
            if args.dry_run:
                dry_summary(args, script)
                print("Dry run: no API call or writes")
                return
        with tempfile.TemporaryDirectory() as temp:
            if args.command == "generate":
                data, rate, alignment = provider_take(script["segments"], config, temp)
            else:
                alignment = P.read(args.alignment)
                convert(args.audio, Path(temp) / "take.wav")
                data, rate = pcm_read(Path(temp) / "take.wav")
                if args.dry_run:
                    candidate = copy.deepcopy(project)
                    candidate["voice"] = {"audio": "take.wav", "alignment": "alignment.json", "start": 0}
                    alignment.update({"schemaVersion": 1, "duration": len(data) / rate, "audioSha256": P.digest(Path(temp) / "take.wav")})
                    P.write(Path(temp) / "alignment.json", alignment)
                    P.validate_alignment(temp, candidate, script)
                    print("Dry run: import valid; no project writes")
                    return
            commit(root, data, rate, alignment, script, project)
        return
    alignment = P.validate_alignment(root, project, script)
    P.require(alignment, "No aligned take")
    words = alignment["words"]
    data, rate = pcm_read(P.local(root, project["voice"]["audio"]))
    if args.command == "trim":
        P.number(args.cap, "pause cap", .05)
        P.require(0 <= args.max_boundary_peak <= 1, "Boundary peak fraction must be 0..1")
        cuts = []
        peak = max((abs(x) for x in data), default=0) or 1
        window = round(.015 * rate)
        for left, right in zip(words, words[1:]):
            if right["start"] - left["end"] <= args.cap:
                continue
            start = round((left["end"] + args.cap / 2) * rate)
            end = round((right["start"] - args.cap / 2) * rate)
            boundary = max(abs(x) for x in data[max(0, start - window):min(len(data), start + window)])
            boundary = max(boundary, max(abs(x) for x in data[max(0, end - window):min(len(data), end + window)]))
            P.require(boundary / peak <= args.max_boundary_peak, "Trim boundary contains signal; inspect alignment before cutting")
            if end > start:
                cuts.append((start, end))
        print(f"Would remove {sum(b-a for a,b in cuts)/rate:.4f}s in {len(cuts)} pauses")
        if args.dry_run or not cuts:
            return
        out, previous, removed, joins = array.array("h"), 0, 0, []
        for start, end in cuts:
            out.extend(data[previous:start])
            joins.append(len(out))
            previous = end
        out.extend(data[previous:])
        ramp(out, joins, rate)
        for word in words:
            for edge in ("start", "end"):
                frame = round(word[edge] * rate)
                word[edge] = (frame - sum(b-a for a,b in cuts if b <= frame)) / rate
        commit(root, out, rate, alignment, script, project)
        return
    lo, hi, before, after = dry_summary(args, script, words)
    P.require(P.normalized(args.find) == "".join(P.normalized(w["text"]) for w in words[lo:hi+1]),
              "Replacement must cover whole aligned tokens; import finer alignment for partial-token edits")
    supplied = bool(args.replacement or args.replacement_alignment)
    P.require((supplied and args.replacement and args.replacement_alignment and not args.config and not args.text)
              or (not supplied and args.config and args.text), "Provide replacement WAV+alignment OR text+config")
    if args.dry_run:
        print("Dry run: no API call or writes")
        return
    with tempfile.TemporaryDirectory() as temp:
        if supplied:
            replacement = P.read(args.replacement_alignment)
            convert(args.replacement, Path(temp) / "take.wav")
            new, new_rate = pcm_read(Path(temp) / "take.wav")
        else:
            new, new_rate, replacement = provider_take([{"id": args.segment, "text": args.text}], P.read(args.config), temp, before, after)
        P.require(new_rate == rate, "Replacement sample rate differs")
        nw = replacement["words"]
        P.require(nw and all(w["segment"] == args.segment for w in nw), "Replacement must use the matched segment ID")
        # Import the replacement transcript explicitly when supplied. Otherwise join
        # whole Latin-script tokens with spaces, including accented Latin letters.
        # Han/Kana/Hangul token streams do not acquire synthetic word spaces.
        token_texts = [w["text"] for w in nw]
        compact_script = all(any(any(script in unicodedata.name(c, "")
                                    for script in ("CJK", "IDEOGRAPH", "HIRAGANA", "KATAKANA", "HANGUL"))
                                 for c in token) for token in token_texts)
        text = args.text if args.text else replacement.get("text") or ("" if compact_script else " ").join(token_texts)
        new_script = replace_script(script, words, lo, hi, text)
        # Splice at the midpoint of available surrounding silence. Never read words[-1] at the opening.
        left = words[lo-1]["end"] if lo else 0
        right = words[hi+1]["start"] if hi+1 < len(words) else len(data)/rate
        cut_a = round((left + words[lo]["start"]) / 2 * rate)
        cut_b = round((words[hi]["end"] + right) / 2 * rate)
        P.require(0 <= cut_a < cut_b <= len(data), "Invalid splice boundaries")
        # Validate replacement timing before cropping; final commit validates the full synchronized take.
        previous = 0
        for w in nw:
            a, b = P.number(w["start"], "replacement start"), P.number(w["end"], "replacement end")
            P.require(a >= previous and b > a and b <= len(new)/rate + .001, "Invalid replacement timing")
            previous = b
        first = round(nw[0]["start"] * rate)
        last = round(nw[-1]["end"] * rate)
        pad = round(.04 * rate)
        begin, finish = max(0, first-pad), min(len(new), last+pad)
        new = new[begin:finish]
        def rms(values):
            return math.sqrt(sum(x*x for x in values) / max(1, len(values)))
        ref = rms(data[round(words[lo]["start"]*rate):round(words[hi]["end"]*rate)])
        level = rms(new)
        gain = ref / level if ref and level else 1
        P.require(.1 <= gain <= 10, "Extreme level difference; normalize/review replacement manually")
        new = array.array("h", [max(-32768, min(32767, round(x*gain))) for x in new])
        out = data[:cut_a] + new + data[cut_b:]
        ramp(out, [cut_a, cut_a + len(new)], rate)
        delta = (len(new) - (cut_b-cut_a)) / rate
        inserted = [{**w, "start": cut_a/rate + w["start"] - begin/rate,
                     "end": cut_a/rate + w["end"] - begin/rate} for w in nw]
        alignment["words"] = words[:lo] + inserted + [{**w,"start":w["start"]+delta,"end":w["end"]+delta} for w in words[hi+1:]]
        commit(root, out, rate, alignment, new_script, project)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError, wave.Error, subprocess.CalledProcessError) as error:
        print(f"voice: {error}", file=sys.stderr)
        sys.exit(1)
