#!/usr/bin/env python3
"""Build a deterministic skills-only ZIP for both supported plugin clients."""
import argparse
from pathlib import Path
import zipfile

from validate_package import PLUGIN, validate


def build(output):
    files = validate()
    output = Path(output).resolve()
    if output.is_relative_to(PLUGIN):
        raise ValueError("Write the release outside the plugin source directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            entry = zipfile.ZipInfo(path.relative_to(PLUGIN).as_posix(), (2020, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    print(f"Built {output} with {len(files)} explicitly allowed plugin files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Destination ZIP (for example /tmp/plugin.zip)")
    build(parser.parse_args().output)
