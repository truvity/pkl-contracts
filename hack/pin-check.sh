#!/usr/bin/env bash
# The supply-chain check this repository has. Nothing here ships code: it
# ships Pkl source, and the one binary it runs without devbox is the Pkl that
# bin/pkl fetches. This confirms, against what GitHub publishes for that
# release, that every sha256 pinned in bin/pkl is the digest of the asset of
# that name, so a pin that was mistyped, or an asset replaced upstream, is
# found by the daily security run rather than by a contributor's checksum
# failure.
#
# Needs the network and `jq`. Uses GITHUB_TOKEN when set, to stay under the
# anonymous rate limit.
set -euo pipefail
cd "$(dirname "$0")/.."

version="$(sed -n 's/^version="\(.*\)"$/\1/p' bin/pkl)"
[ -n "$version" ] || { echo "pin-check: no version in bin/pkl" >&2; exit 1; }

auth=()
[ -n "${GITHUB_TOKEN:-}" ] && auth=(-H "Authorization: Bearer $GITHUB_TOKEN")
release="$(curl -fsSL "${auth[@]}" "https://api.github.com/repos/apple/pkl/releases/tags/$version")"

fail=0
checked=0
# each case arm of bin/pkl: asset="<name>"; sha256="<hex>"
while read -r asset sha; do
  published="$(jq -r --arg a "$asset" '.assets[] | select(.name == $a) | .digest // empty' <<<"$release")"
  checked=$((checked + 1))
  if [ "$published" != "sha256:$sha" ]; then
    echo "pin-check: $asset $version: pinned sha256:$sha, GitHub publishes '${published:-nothing}'" >&2
    fail=1
  fi
done < <(sed -n 's/.*asset="\([^"]*\)"; *sha256="\([0-9a-f]*\)".*/\1 \2/p' bin/pkl)

[ "$checked" = 4 ] || { echo "pin-check: expected four pinned assets in bin/pkl, found $checked" >&2; exit 1; }
[ "$fail" = 0 ] && echo "pin-check: the four Pkl $version pins match GitHub's published digests"
exit $fail
