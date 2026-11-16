#!/usr/bin/env bash
set -euo pipefail

: "${BUILD:?BUILD must be set to the Mindustry release tag number}"

workspace="${GITHUB_WORKSPACE:-$PWD}"
work="$workspace/work"
out="$workspace/out"

rm -rf "$work"
mkdir -p "$work" "$out"

echo "::group::Clone Mindustry v$BUILD"
git clone --quiet --depth 1 --branch "v$BUILD" https://github.com/Anuken/Mindustry.git "$work/Mindustry"
echo "::endgroup::"

echo "::group::Clone uCore"
# Full clone: the commit pinned by each Mindustry tag is looked up here instead of JitPack.
git clone --quiet https://github.com/Anuken/uCore.git "$work/uCore"
uCoreVersion="$(sed -n "s/.*uCoreVersion = '\([^']*\)'.*/\1/p" "$work/Mindustry/build.gradle" | head -n 1)"
if [ -z "$uCoreVersion" ]; then
  echo "Could not find uCoreVersion in Mindustry's build.gradle" >&2
  exit 1
fi
git -C "$work/uCore" checkout --quiet --detach "$uCoreVersion"
echo "uCore commit: $uCoreVersion"
echo "::endgroup::"

python3 "$workspace/scripts/prepare.py" "$work"

cd "$work/Mindustry"
chmod +x gradlew

# v50+ generate the locale list in a `finish` task; the official build ran `build`, not `dist`.
tasks=(:desktop:dist)
if grep -q 'task finish' build.gradle; then
  tasks=(:core:finish :desktop:dist)
fi

export GRADLE_OPTS="-Xmx2g -Dfile.encoding=UTF-8"
./gradlew --no-daemon --console=plain --stacktrace -Pbuildversion="$BUILD" "${tasks[@]}"

jar="$(find desktop/build/libs -maxdepth 1 -name '*.jar' -print -quit)"
if [ -z "$jar" ]; then
  echo "No desktop jar was produced" >&2
  exit 1
fi

# The jar must identify itself with the build field this job was asked to produce.
unzip -p "$jar" version.properties > "$work/version.properties"
grep -qx "build=$BUILD" "$work/version.properties"
grep -q '^Main-Class: io\.anuke\.mindustry\.desktop\.DesktopLauncher$' <(unzip -p "$jar" META-INF/MANIFEST.MF)

target="$out/Mindustry-Desktop-$BUILD.jar"
cp "$jar" "$target"
ls -lh "$target"
