#!/usr/bin/env python3
"""Validate a static campaign link plan and save a new, immutable export revision."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_id",
            "utm_content", "utm_term", "utm_source_platform")
REQUIRED = {"utm_source", "utm_medium", "utm_campaign"}
META_KEYS = ("placement", "creative_id", "status", "notes")
COLUMNS = ("campaign_id", "link_id", *META_KEYS, "destination_url", *UTM_KEYS, "url")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be a nonempty string")
    require(value == value.strip(), f"{label} must not have surrounding whitespace")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), f"{label} contains control characters")
    return value


def identifier(value, label):
    value = text(value, label)
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value), f"{label} must be a lowercase slug")
    return value


def object_fields(value, allowed, label):
    require(isinstance(value, dict), f"{label} must be an object")
    require(not set(value) - set(allowed), f"{label} contains unsupported fields")


def utm_values(value, label):
    object_fields(value, UTM_KEYS, label)
    for key, item in value.items():
        text(item, f"{label}.{key}")
        require(not any(c in unquote(item) for c in "{}"), f"{label}.{key}: static values only; macros are unsupported")
    return value


def tagged_url(destination, utm):
    text(destination, "destination_url")
    require(not any(c.isspace() for c in destination), "destination_url must encode whitespace")
    require(not re.search(r"%(?![0-9a-fA-F]{2})", destination), "destination_url contains invalid percent encoding")
    require(not any(c in unquote(destination) for c in "{}"), "destination_url contains an unresolved macro")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in unquote(destination)),
            "destination_url contains encoded control characters")
    parts = urlsplit(destination)
    require(parts.scheme in {"http", "https"} and parts.hostname, "destination_url must be absolute HTTP(S)")
    require(parts.username is None and parts.password is None, "destination_url must not contain credentials")
    # Accessing port also rejects malformed or out-of-range ports.
    _ = parts.port
    require(not any(k.lower().startswith("utm_") for k, _ in parse_qsl(parts.query, keep_blank_values=True)),
            "destination_url already contains UTM parameters; resolve ownership before building")
    encoded = urlencode([(key, utm[key]) for key in UTM_KEYS if key in utm])
    separator = "&" if parts.query and not parts.query.endswith("&") else ""
    result = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query + separator + encoded, parts.fragment))
    round_trip = {k: v for k, v in parse_qsl(urlsplit(result).query, keep_blank_values=True) if k in UTM_KEYS}
    require(round_trip == utm, "UTM serialization did not round-trip")
    return result


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON object key")
        result[key] = value
    return result


def build_plan(plan):
    object_fields(plan, {"schema_version", "campaign_id", "defaults", "links"}, "plan")
    require(type(plan.get("schema_version")) is int and plan["schema_version"] == 1,
            "schema_version must be 1")
    campaign_id = identifier(plan.get("campaign_id"), "campaign_id")
    defaults = utm_values(plan.get("defaults"), "defaults")
    require("utm_campaign" in defaults, "defaults.utm_campaign is required")
    links = plan.get("links")
    require(isinstance(links, list) and links, "links must be a nonempty list")
    rows, warnings, ids, urls = [], [], set(), {}
    for index, link in enumerate(links):
        label = f"links[{index}]"
        object_fields(link, {"link_id", "destination_url", "utm", *META_KEYS}, label)
        link_id = identifier(link.get("link_id"), f"{label}.link_id")
        require(link_id not in ids, f"Duplicate link_id: {link_id}")
        ids.add(link_id)
        values = {**defaults, **utm_values(link.get("utm"), f"{label}.utm")}
        require(REQUIRED <= values.keys(), f"{label} needs source, medium and campaign")
        for key in ("utm_campaign", "utm_id"):
            require(values.get(key) == defaults.get(key), f"{label}.{key} must match campaign defaults")
        metadata = {key: link.get(key, "planned" if key == "status" else "") for key in META_KEYS}
        for key, value in metadata.items():
            require(isinstance(value, str), f"{label}.{key} must be a string")
            if value:
                text(value, f"{label}.{key}")
        require(metadata["status"] in {"planned", "published", "retired"}, f"{label}: invalid status")
        destination = link.get("destination_url")
        url = tagged_url(destination, values)
        if url in urls:
            warnings.append(f"Links {urls[url]} and {link_id} resolve to the same URL; confirm variant mapping")
        urls[url] = link_id
        rows.append({"campaign_id": campaign_id, "link_id": link_id, **metadata,
                     "destination_url": destination, **{k: values.get(k, "") for k in UTM_KEYS}, "url": url})
    return {"campaign_id": campaign_id, "links": rows, "warnings": warnings}


def save_revision(output, source, result):
    output = Path(output).absolute()
    require(not any(p.is_symlink() for p in (output, *output.parents)), "Symlinked output paths are unsupported")
    # Never overwrite even an empty or incomplete prior revision.
    require(not output.exists(), "Output already exists; choose the next unused revision directory")
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(result["links"])
    lines = [f"# UTM plan: {result['campaign_id']}", "",
             f"Input SHA-256: `{hashlib.sha256(source).hexdigest()}`", "",
             "Local URL validation passed. Publication, redirects and analytics receipt are not verified.", ""]
    for row in result["links"]:
        # JSON strings keep arbitrary copy out of Markdown links/HTML.
        lines.extend([f"## {row['link_id']}", "", f"Status: {row['status']}", "", "```json",
                      json.dumps({key: row[key] for key in COLUMNS if row[key]}, indent=2, ensure_ascii=False), "```", ""])
    if result["warnings"]:
        lines.extend(["## Warnings", "", *[f"- {warning}" for warning in result["warnings"]], ""])
    output.mkdir(parents=True, exist_ok=False)
    for name, data in (("campaign.json", source), ("utm-links.csv", csv_buffer.getvalue().encode("utf-8")),
                       ("UTM_PLAN.md", "\n".join(lines).encode("utf-8"))):
        with (output / name).open("xb") as target:
            target.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path, help="New export revision directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview validated links without writes or network")
    args = parser.parse_args()
    if not args.dry_run and args.out is None:
        parser.error("--out is required unless --dry-run is used")
    try:
        source = args.plan.read_bytes()
        result = build_plan(json.loads(source.decode("utf-8"), object_pairs_hook=unique_keys))
        if args.dry_run:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            save_revision(args.out, source, result)
            print(f"Saved {len(result['links'])} links in {args.out}")
            for warning in result["warnings"]:
                print(f"Warning: {warning}")
    except (ValueError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
