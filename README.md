# classic-mindustry-builds

Desktop builds of the tagged Mindustry releases **33-57**, rebuilt from the tags in
[Anuken/Mindustry](https://github.com/Anuken/Mindustry/tags) and published to one release.

Run **Actions -> Build Classic Releases -> Run workflow**. The workflow builds every tag,
renames each jar to `Mindustry-Desktop-<build>.jar`, and updates the
[`classic-33-57`](../../releases/tag/classic-33-57) release.

Every jar is a runnable desktop build: `java -jar Mindustry-Desktop-<build>.jar`.
The `<build>` number is the `build` field in the jar's `version.properties`.
uCore is built from a full clone at the commit each tag pins, not from JitPack.
