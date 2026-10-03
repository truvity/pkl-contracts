#!/usr/bin/env bash
# Generates Go structs from the contract with the official pkl-go generator,
# through hack/codegen.sh (which pins it), into ./gen.
#
# The packages are named by their project URIs, because the generator imports
# its arguments and a module outside the project cannot resolve `@vocab`.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../.." && pwd)"
cd "$here"

version="$(sed -n 's/^version = "\(.*\)"$/\1/p' "$root/packages/Release.pkl")"
base="projectpackage://github.com/truvity/pkl-contracts/releases/download/v$version"
pkg=conformance.invalid/gen
c=../contract

rm -rf gen
"$root/hack/codegen.sh" go --project-dir ../.. --output-path . \
  --mapping contracts.vocab.Vocab=$pkg/vocab \
  --mapping contracts.fragments.Fragments=$pkg/fragments \
  --mapping contracts.fragments.Platform=$pkg/platform \
  --mapping contracts.templates.ServiceConfig=$pkg/service \
  --mapping contracts.test.Showcase=$pkg/showcase \
  --mapping conformance.contract.Web=$pkg/web \
  --mapping conformance.contract.Urls=$pkg/urls \
  --mapping conformance.contract.Redirect=$pkg/redirect \
  --mapping conformance.contract.Stat=$pkg/stat \
  --mapping conformance.contract.Prober=$pkg/prober \
  --mapping conformance.contract.Migrate=$pkg/migrate \
  --mapping conformance.contract.LogArchiver=$pkg/logarchiver \
  --mapping conformance.contract.Shortener=$pkg/shortener \
  --mapping conformance.contract.Installed=$pkg/installed \
  --mapping conformance.contract.Blocks=$pkg/blocks \
  --mapping conformance.contract.Inherit=$pkg/inherit \
  --mapping conformance.contract.Names=$pkg/names \
  --mapping conformance.contract.Literals=$pkg/literals \
  --mapping conformance.union.Union=$pkg/union \
  "$base/contracts.vocab@$version#/Vocab.pkl" \
  "$base/contracts.fragments@$version#/Fragments.pkl" \
  "$base/contracts.fragments@$version#/Platform.pkl" \
  "$base/contracts.templates@$version#/ServiceConfig.pkl" \
  ../../Showcase.pkl \
  "$c"/*.pkl ../union/*.pkl
