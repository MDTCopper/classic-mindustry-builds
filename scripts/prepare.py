#!/usr/bin/env python3
"""Trim an old Mindustry Gradle build down to what a desktop jar needs.

The tags 33-57 carry Android, HTML, iOS and packer projects that need SDKs and
Gradle plugins this job does not install.  Only the JVM projects are kept, the
dead repositories are dropped, and uCore is wired in as a sibling project built
from the full clone.
"""

import re
import sys
from pathlib import Path

KEEP = {"core", "desktop", "kryonet", "annotations"}
START = re.compile(r'^(buildscript|allprojects|project\(":(\w+)"\))\s*\{\s*$')


def blocks(text):
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        match = START.match(lines[i])
        if not match:
            i += 1
            continue
        start = i
        depth = 0
        while i < len(lines):
            depth += lines[i].count("{") - lines[i].count("}")
            i += 1
            if depth <= 0:
                break
        yield match.group(1), match.group(2), "".join(lines[start:i])


def patch_repositories(text):
    text = text.replace("mavenLocal()", "")
    text = text.replace("jcenter()", "")
    text = re.sub(
        r'^\s*maven\s*\{\s*url\s*["\']https://oss\.sonatype\.org[^\n]*\n',
        "",
        text,
        flags=re.M,
    )
    text = re.sub(r'^\s*google\(\)\s*\n', "", text, flags=re.M)
    # Old Gradle's mavenCentral() can still use the retired plain-HTTP endpoint.
    text = text.replace(
        "mavenCentral()", "maven { url 'https://repo.maven.apache.org/maven2' }"
    )
    return text


def main():
    work = Path(sys.argv[1])
    mindustry = work / "Mindustry"
    ucore = work / "uCore"

    kept = []
    for header, name, block in blocks((mindustry / "build.gradle").read_text()):
        if header == "buildscript":
            continue
        if header == "allprojects" or name in KEEP:
            kept.append(block)

    root = patch_repositories("\n\n".join(kept))
    if "jitpack.io" not in root:
        root = root.replace(
            "repositories {",
            "repositories {\n        maven { url 'https://jitpack.io' }",
            1,
        )
    (mindustry / "build.gradle").write_text(root)

    (mindustry / "settings.gradle").write_text(
        """include ':core'
include ':desktop'
include ':kryonet'
if (new File(settingsDir, 'annotations/build.gradle').exists()) {
    include ':annotations'
}
include ':uCore'
project(':uCore').projectDir = new File(settingsDir, '../uCore')
"""
    )

    (ucore / "build.gradle").write_text(
        patch_repositories((ucore / "build.gradle").read_text())
    )


if __name__ == "__main__":
    main()
