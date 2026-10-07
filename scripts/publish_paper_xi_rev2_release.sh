#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-paper-xi-rev2-20261007}"
TITLE="AuraOS Paper XI Rev.2 + Aura World Seed V5"

ARENA="AURA_WORLD_SEED__DEVELOPER_ONE_STOP_V5_D0__20261007.html"
PACKAGE="AURA_PACKAGE__DEVELOPER_ONE_STOP_GEM_ARENA_V5_D0__20261007.zip"
PAPER="AuraOS_Paper_XI_Rev2_Consequence_Local_Computing_and_Reconstructible_World_Seeds_2026-10-07.pdf"

for f in "$ARENA" "$PACKAGE" "$PAPER"; do
  test -f "$f" || { echo "Missing release asset: $f" >&2; exit 1; }
done

echo "Verifying pinned SHA-256 values..."
printf '%s  %s\n' "22e7fb9ef2cfc10b1545179450cb8062a1022e962f9f80597f6614c2b3651bb1" "$ARENA" | sha256sum -c -
printf '%s  %s\n' "c977bff4fa9f6d0c6fd4fd3a97abb8dc932223370da26e102de0a298cdb5b2bc" "$PACKAGE" | sha256sum -c -

gh release create "$TAG" "$ARENA" "$PACKAGE" "$PAPER" \
  --title "$TITLE" \
  --notes-file docs/PAPER_XI_REV2_ZENODO.md

echo "Published $TAG"
