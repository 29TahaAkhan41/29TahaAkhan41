#!/usr/bin/env bash
# Packs the mod's two files into dist/:
#   solartech.hmod   the content mod (block, model, textures, recipe)  -> <game folder>/horizon-mods/
#   solartech.hnmod  the native mod (Rust source the launcher builds)  -> <game folder>/horizon-native-mods/
# Layout: Horizon's docs/api/mod-files.md. Needs `zip`.
set -euo pipefail
cd "$(dirname "$0")"

ID=solartech
VERSION=0.2.1
# The Horizon commit the launcher builds the game from, as native/horizon-mixin.toml pins it.
# Not Nightly 2026-11-08 (fdc87ae): launcher 0.2.62 generates a game entry point that needs
# horizon_threads::GameAllocator, which that Nightly's source doesn't have. This is the first
# commit checked to have it; the hook points the mod uses are the same in both.
HORIZON=4acdda54f2ef1e44ade292ce3b02ed91910f9f83
# The horizon-mixins commit that Horizon's launcher uses (launcher/src/native_mods.rs, MIXINS_REV).
MIXINS=5a64af938ec86b00d53d16a408aabc0038fb3e57

grep -q "^version = \"$VERSION\"" content/horizon-mod.toml
grep -q "^version = \"$VERSION\"" native/horizon-mixin.toml
grep -q "^horizon_revision = \"$HORIZON\"" native/horizon-mixin.toml

rm -rf dist build
mkdir -p dist "build/mixins/$ID"

(cd content && zip -q -X -r "../dist/$ID.hmod" horizon-mod.toml assets data)

cat > build/horizon-native.json <<JSON
{"schema": 1, "id": "$ID", "version": "$VERSION", "game": "26.3", "horizon": "$HORIZON", "mixins": "$MIXINS"}
JSON
cp native/horizon-mixin.toml native/.gitignore "build/mixins/$ID/"
mkdir -p "build/mixins/$ID/api/src"
cp native/api/Cargo.toml "build/mixins/$ID/api/"
cp native/api/src/*.rs "build/mixins/$ID/api/src/"
(cd build && zip -q -X -r "../dist/$ID.hnmod" horizon-native.json mixins)
rm -rf build

ls -l dist
