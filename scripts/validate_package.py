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
    require(not PLUGIN.is_symlink() and not (PLUGIN / "skills").is_symlink(),
            "Plugin and skill roots must not be symlinks")
    for path in sorted((PLUGIN / "skills").rglob("*")):
        require(not path.is_symlink(), f"Symlink is not a distributable asset: {path}")
        if "__pycache__" in path.parts:
            continue
        if path.is_file():
            relative = path.relative_to(PLUGIN / "skills")
            allowed = (len(relative.parts) == 2 and relative.name == "SKILL.md") or (
                len(relative.parts) >= 3 and relative.parts[1] in {
                    "agents", "references", "scripts", "assets"
                } and path.suffix in {
                    "agents": {".yaml"}, "references": {".md"},
                    "scripts": {".py", ".mjs"}, "assets": {".json", ".svg", ".html"}
                }[relative.parts[1]])
            allowed = allowed or (relative.parts[1:] == ("scripts", "requirements.txt")
                                  and relative.parts[0] == "marketing-image-producer")
            require(allowed, f"Unexpected skill asset: {path}")
            files.append(path)
    notices = PLUGIN / "third-party"
    require(not notices.is_symlink(), "Third-party root must not be a symlink")
    expected_notices = {"bang-motion.LICENSE", "hyperframe-pro.LICENSE"}
    require({p.name for p in notices.iterdir()} == expected_notices,
            "Unexpected or missing third-party notices")
    files.extend(notices / name for name in sorted(expected_notices))
    for path in files:
        require(path.is_file() and not path.is_symlink(), f"Missing/unsafe package file: {path}")
        require(path.resolve().is_relative_to(PLUGIN.resolve()), f"Package file escapes plugin: {path}")
        require(not any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(PLUGIN)),
                f"Symlinked package ancestor: {path}")
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
    expected_skills = {"marketing-brief", "creative-ideation", "ad-video-director",
                       "motion-video-producer", "motion-art-director", "motion-storyboard",
                       "motion-voice", "motion-composer", "motion-video-qa",
                       "marketing-image-board", "marketing-image-producer", "marketing-veo-video", "marketing-omni-video"}
    require({s.parent.name for s in skills} == expected_skills, "Missing/unexpected suite skills")
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
        if name[1] in {"marketing-veo-video","marketing-omni-video"}:
            require(re.search(r"^\s+allow_implicit_invocation: false$",ui,re.M),
                    f"Paid video generation must remain opt-in: {skill}")

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
        if path.suffix == ".json":
            read_json(path)
    return files


if __name__ == "__main__":
    files = validate()
    print(f"Validated shared skill resources, dual manifests and marketplaces: {len(files)} package files")
