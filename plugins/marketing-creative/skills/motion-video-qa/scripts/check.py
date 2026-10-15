#!/usr/bin/env python3
"""Check project/build integrity and optionally encoded exports; not a visual review."""
import argparse
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys

spec = importlib.util.spec_from_file_location("motion_project", Path(__file__).resolve().parents[2] / "motion-video-producer/scripts/project.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.roots, self.media = [], [], []

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if "id" in props:
            self.ids.append(props["id"])
        if "data-composition-id" in props:
            self.roots.append(props)
        if tag in ("audio", "video", "img", "script", "link"):
            self.media.append((tag, props))


def probe(file):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(file)],
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def verify_export(root, variant, project):
    root = Path(root).resolve()
    file = P.local(root, f"renders/{variant['id']}.mp4")
    P.require(file.is_file(), f"Missing export: {file.relative_to(root)}")
    info = probe(file)
    videos = [s for s in info["streams"] if s["codec_type"] == "video"]
    audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
    P.require(len(videos) == 1, "Expected exactly one video stream")
    video = videos[0]
    P.require((video["width"], video["height"]) == (variant["width"], variant["height"]),
              f"Wrong export dimensions: {variant['id']}")
    P.require(video["codec_name"] == "h264", "Default export contract requires H.264")
    numerator, denominator = map(int, video["avg_frame_rate"].split("/"))
    P.require(denominator and abs(numerator/denominator - variant["fps"]) < .02, "Export FPS differs")
    duration = float(info["format"]["duration"])
    P.require(abs(duration - variant["duration"]) <= max(.1, 2/variant["fps"]), "Export duration differs")
    requires_audio = project.get("voice") or variant.get("audioRequired", False) or any(b.get("visual", {}).get("mode") == "footage"
        and b["visual"].get("hasAudio", False) for b in variant.get("beats", []))
    P.require(not requires_audio or audio, "Intended audio export has no audio stream")
    P.require(all(s["codec_name"] == "aac" for s in audio), "Default export audio requires AAC")
    placement = variant["placement"]
    if "maxFileBytes" in placement:
        P.require(file.stat().st_size <= placement["maxFileBytes"], "Export exceeds file-size limit")
    if "maxDuration" in placement:
        P.require(duration <= placement["maxDuration"] + .001, "Encoded duration exceeds placement limit")
    return {"file": str(file.relative_to(root)), "sha256": P.digest(file),
            "buildSha256": P.digest(root / "variants" / variant["id"] / "build.json"),
            "width": video["width"], "height": video["height"], "duration": duration,
            "hasAudio": bool(audio)}


def check(root, exports=False, record_export=None):
    root = Path(root).resolve()
    expected = P.resolve(root, save=False)
    P.require(P.read(root / "timing.resolved.json") == expected, "Stale resolved timing; run resolve")
    project, _, _, manifest, _ = P.load(root)
    warnings, variants = [], []
    variant_ids = {v["id"] for v in expected["variants"]}
    P.require(record_export is None or record_export in variant_ids, "Unknown export variant")
    for variant in expected["variants"]:
        dest = root / "variants" / variant["id"]
        build = P.read(dest / "build.json")
        P.require(build.get("inputHashes") == expected["inputHashes"], "Stale build inputs")
        P.require(build.get("timingSha256") == P.digest(root / "timing.resolved.json"), "Stale build timing")
        generator = Path(__file__).resolve().parents[2] / "motion-composer/scripts/compose.mjs"
        if build.get("generator") == "bundled-compose-v1":
            P.require(build["generatorSha256"] == P.digest(generator), "Bundled generator changed; rebuild")
        else:
            P.require(project.get("generator") and build.get("generatorPath") == project["generator"], "Custom build must identify project.generator")
            P.require(build["generatorSha256"] == P.digest(P.local(root, project["generator"])), "Custom generator changed; rebuild")
        P.require("index.html" in build.get("generatedHashes", {}), "Build does not fingerprint HTML")
        for relative, digest in build["generatedHashes"].items():
            file = P.local(dest, relative)
            P.require(file.is_file() and P.digest(file) == digest, f"Edited/missing generated file: {variant['id']}/{relative}")
        html = (dest / "index.html").read_text(encoding="utf-8")
        page = Page()
        page.feed(html)
        P.require(len(page.ids) == len(set(page.ids)), "Duplicate HTML ID")
        P.require(len(page.roots) == 1, "Expected one composition root")
        comp = page.roots[0]
        P.require((int(comp["data-width"]), int(comp["data-height"])) == (variant["width"], variant["height"]), "Root canvas differs")
        P.require(abs(float(comp["data-duration"]) - variant["duration"]) < .001, "Root duration differs")
        declared = re.search(r"window\.__motionTargets=(\[[^;]*\]);", html)
        if declared:
            for target in json.loads(declared[1]):
                P.require(target in page.ids, f"Missing declared animation target: {target}")
        # Catch direct ID selectors in common GSAP calls as well as declared generated targets.
        for selector in re.findall(r'\btl\.(?:to|from|fromTo|set)\(["\']([^"\']+)["\']', html):
            for target in re.findall(r"#([A-Za-z][\w-]*)", selector):
                P.require(target in page.ids, f"Missing animated target: {target}")
        narrated, audible_media = False, False
        for tag, props in page.media:
            src = props.get("src") or (props.get("href") if tag == "link" else None)
            if not src:
                continue
            if src.startswith(("http:", "https:")):
                warnings.append(f"{variant['id']}: remote resource {src}; freeze locally for delivery")
                continue
            if src.startswith("data:"):
                continue
            P.require(P.local(dest, src).is_file(), f"Missing media: {src}")
            if tag == "audio":
                P.require(props.get("id"), "Audio has no ID")
                narrated = narrated or props.get("id") == "narration"
                audible_media = True
            if tag == "video" and props.get("data-has-audio") == "true" and "muted" not in props:
                audible_media = True
        P.require(not project.get("voice") or narrated, "Narration not wired in HTML")
        if variant["placement"]["verificationStatus"] == "unverified":
            warnings.append(f"{variant['id']}: placement requirements/safe-area preview unverified")
        for asset in manifest.get("assets", []):
            if "width" in asset or "height" in asset:
                info = probe(P.local(root, asset["path"]))
                visual = next((s for s in info["streams"] if "width" in s), None)
                P.require(visual and visual["width"] == asset.get("width") and visual["height"] == asset.get("height"),
                          f"Stale dimensions for asset {asset['id']}")
        result = {"id": variant["id"], "sourceChecks": "passed"}
        if exports or record_export == variant["id"]:
            P.require(build.get("localRuntime"), "Freeze runtime locally before recording delivery exports")
            encoded = verify_export(root, {**variant, "audioRequired": audible_media or variant.get("audioRequired", False)}, project)
            records_path = P.safe_output(root, "renders/manifest.json")
            records = P.read(records_path) if records_path.exists() else {"schemaVersion": 1, "exports": {}}
            if record_export == variant["id"]:
                records["exports"][variant["id"]] = encoded
                P.write(records_path, records)
            if exports:
                P.require(records["exports"].get(variant["id"]) == encoded, "Export unrecorded or stale; render and record current variant")
            result["export"] = encoded
        variants.append(result)
    return {"schemaVersion": 1, "inputHashes": expected["inputHashes"], "variants": variants,
            "warnings": sorted(set(warnings)), "visualReview": "not performed by this checker",
            "frameworkValidation": "not performed by this checker", "audioListening": "not performed by this checker"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--exports", action="store_true")
    parser.add_argument("--record-export", metavar="VARIANT_ID")
    args = parser.parse_args()
    report = check(args.project, args.exports, args.record_export)
    P.write(P.safe_output(args.project, "qa/report.json"), report)
    print(f"Source checks passed for {len(report['variants'])} variants")
    for warning in report["warnings"]:
        print(f"Warning: {warning}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError, subprocess.CalledProcessError) as error:
        # Remove any earlier machine pass so a failed rerun cannot leave a misleading report.
        if len(sys.argv) > 1:
            try:
                P.safe_output(sys.argv[1], "qa/report.json").unlink(missing_ok=True)
            except ValueError:
                pass
        print(f"check: {error}", file=sys.stderr)
        sys.exit(1)
