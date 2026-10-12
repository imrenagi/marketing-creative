#!/usr/bin/env python3
"""Check this repository's dual-client packaging invariants (stdlib only)."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "marketing-creative"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def package_files():
    """An explicit surface allowlist; never archive the repository root."""
    files = [PLUGIN / kind / "plugin.json"
             for kind in (".codex-plugin", ".claude-plugin")]
    for path in sorted((PLUGIN / "skills").rglob("*")):
        require(not path.is_symlink(), f"Symlink is not a distributable asset: {path}")
        if path.is_file():
            require(path.suffix in {".md", ".yaml"}, f"Unexpected skill asset: {path}")
            files.append(path)
    for path in files:
        require(path.is_file() and not path.is_symlink(), f"Missing/unsafe package file: {path}")
    return files


def validate():
    codex = read_json(PLUGIN / ".codex-plugin/plugin.json")
    claude = read_json(PLUGIN / ".claude-plugin/plugin.json")
    for key in ("name", "version", "description", "author", "repository"):
        require(codex.get(key) == claude.get(key) and bool(codex.get(key)),
                f"Client manifests disagree or omit {key}")
    require(codex["name"] == "marketing-creative", "Unexpected plugin identity")
    require(re.fullmatch(r"\d+\.\d+\.\d+", codex["version"]), "Invalid release version")
    require(codex.get("skills") == "./skills/", "Codex skill path changed")
    require(codex.get("interface", {}).get("displayName"), "Missing Codex display name")
    require(codex.get("interface", {}).get("shortDescription"), "Missing Codex description")
    require(codex["author"].get("name"), "Missing publisher")

    marketplaces = [read_json(ROOT / p) for p in
                    (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json")]
    for market in marketplaces:
        require(market["name"] == "marketing-creative", "Unexpected marketplace identity")
        require(len(market["plugins"]) == 1, "Update validator when adding plugins")
        entry = market["plugins"][0]
        require(entry["name"] == codex["name"], "Marketplace/plugin identity mismatch")
        source = entry["source"]
        if isinstance(source, dict):
            require(source.get("source") == "local", "Expected local Codex source")
            source = source["path"]
        require(source == "./plugins/marketing-creative", "Unexpected plugin source path")
        require((ROOT / source).resolve() == PLUGIN, "Source must resolve from repository root")

    skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
    require(bool(skills), "No discoverable skills")
    for skill in skills:
        text = skill.read_text(encoding="utf-8")
        require(text.startswith("---\n"), f"Missing frontmatter: {skill}")
        frontmatter = text.split("---", 2)[1]
        name = re.search(r"^name: ([a-z0-9-]+)$", frontmatter, re.M)
        require(name and name[1] == skill.parent.name, f"Skill name/path mismatch: {skill}")
        require(re.search(r"^description: \S.+$", frontmatter, re.M), f"Missing description: {skill}")
        require(not re.search(r"\bTODO\b|\[TBD\]", text), f"Unfinished scaffold: {skill}")
        ui = (skill.parent / "agents/openai.yaml").read_text(encoding="utf-8")
        require(f"${name[1]}" in ui, f"UI prompt does not invoke skill: {skill}")

    files = package_files()
    for path in files:
        relative = path.relative_to(PLUGIN)
        require(not any(p in {"samples", "local-docs", "__pycache__"} for p in relative.parts),
                f"Private/generated material in package: {path}")
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            require("/Users/" not in text, f"Non-portable private path in package: {path}")
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                require(resolved.is_relative_to(PLUGIN) and resolved.exists(),
                        f"Broken or escaping resource link: {path}: {target}")
    return files


if __name__ == "__main__":
    files = validate()
    print(f"Validated shared skill resources, dual manifests and marketplaces: {len(files)} package files")
