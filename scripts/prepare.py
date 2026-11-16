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


def remove_sonatype_blocks(text):
    """Drop maven { ... } blocks pointing at the retired Sonatype hosts.

    The blocks may be one line or several, so match braces instead of lines.
    """
    lines = text.splitlines(keepends=True)
    result = []
    i = 0
    while i < len(lines):
        if re.match(r'^\s*maven\s*\{', lines[i]):
            block = []
            depth = 0
            while i < len(lines):
                depth += lines[i].count("{") - lines[i].count("}")
                block.append(lines[i])
                i += 1
                if depth <= 0:
                    break
            if "oss.sonatype.org" in "".join(block):
                continue
            result.extend(block)
            continue
        result.append(lines[i])
        i += 1
    return "".join(result)


def patch_repositories(text):
    text = text.replace("mavenLocal()", "")
    text = text.replace("jcenter()", "")
    text = remove_sonatype_blocks(text)
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

    # Tags 33-40 pack textures from a core build script that imports gdx-tools.
    core_script = mindustry / "core" / "build.gradle"
    if core_script.exists() and "com.badlogic.gdx.tools" in core_script.read_text():
        root = (
            "buildscript {\n"
            "    repositories {\n"
            "        maven { url 'https://repo.maven.apache.org/maven2' }\n"
            "    }\n"
            "    dependencies {\n"
            "        classpath 'com.badlogicgames.gdx:gdx-tools:1.9.8'\n"
            "    }\n"
            "}\n\n"
        ) + root

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
