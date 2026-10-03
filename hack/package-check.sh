#!/usr/bin/env bash
# Checks what `pkl project package` produced (.out/) against what a GitHub
# release will serve, because nothing else can: a release is exercised only by
# a tag, and a mistake here is a package nobody can resolve.
#
# A package URI is
#
#   package://github.com/truvity/pkl-contracts/releases/download/v<V>/<name>@<V>
#
# and Pkl fetches it over HTTPS at exactly that path, the metadata, and then
# `<name>@<V>.zip` beside it. So, for every package:
#
#   - the asset directory, the metadata file and the zip are named
#     `<name>@<V>` as Pkl will ask for them;
#   - the metadata's URI, and its zip URL, point into the release `v<V>`;
#   - the version is the repository's, in packages/Release.pkl, and the same
#     for every package;
#   - each dependency is another of these packages, at the same version.
set -euo pipefail
cd "$(dirname "$0")/.."

base="package://github.com/truvity/pkl-contracts/releases/download"
zipbase="https://github.com/truvity/pkl-contracts/releases/download"
version="$(sed -n 's/^version = "\(.*\)"$/\1/p' packages/Release.pkl)"
[ -n "$version" ] || { echo "package-check: no version in packages/Release.pkl" >&2; exit 1; }

fail=0
bad() { echo "package-check: $*" >&2; fail=1; }

for dir in packages/*/; do
  # the package packages/<x> is named contracts.<x>
  name="contracts.$(basename "$dir")"
  asset="$name@$version"
  out=".out/$asset"
  meta="$out/$asset"

  for f in "$meta" "$out/$asset.zip" "$out/$asset.sha256" "$out/$asset.zip.sha256"; do
    [ -f "$f" ] || bad "missing $f"
  done
  [ -f "$meta" ] || continue

  field() { sed -n "s/^  \"$1\": \"\(.*\)\",\?\$/\1/p" "$meta" | head -1; }
  [ "$(field name)" = "$name" ]             || bad "$name: metadata name is '$(field name)'"
  [ "$(field version)" = "$version" ]       || bad "$name: metadata version is '$(field version)', not $version"
  [ "$(field packageUri)" = "$base/v$version/$asset" ] \
    || bad "$name: packageUri is '$(field packageUri)', want $base/v$version/$asset"
  [ "$(field packageZipUrl)" = "$zipbase/v$version/$asset.zip" ] \
    || bad "$name: packageZipUrl is '$(field packageZipUrl)', want $zipbase/v$version/$asset.zip"

  # every dependency is a sibling at this version, checksummed
  while IFS= read -r uri; do
    case "$uri" in
      "$base/v$version/contracts."*"@$version") ;;
      *) bad "$name: dependency '$uri' is not one of these packages at $version" ;;
    esac
  done < <(sed -n 's/^      "uri": "\(.*\)",\?$/\1/p' "$meta")
  # the zip's recorded checksum is the checksum of the zip
  want="$(sed -n 's/^    "sha256": "\(.*\)"$/\1/p' "$meta" | head -1)"
  have="$(cut -d' ' -f1 "$out/$asset.zip.sha256")"
  [ "$want" = "$have" ] || bad "$name: zip checksum $have is not the one the metadata records ($want)"
done

[ "$fail" = 0 ] && echo "package-check: ${version} - metadata, zips and URIs agree for $(ls -d packages/*/ | wc -l) packages"
exit $fail
