#!/usr/bin/env bash
# The Kotlin side of the conformance suite. Generates the Kotlin classes from
# the contract with the official generator (pkl-codegen-kotlin, pinned and
# verified by hack/codegen.sh), builds them with Gradle, and prints one JSON line per
# (fixture, validator): `networknt`, a Java JSON Schema engine, and `kotlin`,
# its verdict AND the document decoded into the generated class.
#
# usage: run.sh <suite dir (test/)> <manifest> <generated schema dir>
#
# This is the slow part of the suite (Gradle), which is why it is a recipe of its
# own. `platform` is left out of the decode on purpose: the generator refuses
# union types (`Int | String`), which it uses.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../.." && pwd)"
suite="$1" manifest="$2" schemas="$3"
cd "$here"

release="$(sed -n 's/^version = "\(.*\)"$/\1/p' "$root/packages/Release.pkl")"
base="projectpackage://github.com/truvity/pkl-contracts/releases/download/v$release"
rm -rf src/main/kotlin/gen
"$root/hack/codegen.sh" kotlin --project-dir "$suite" --output-dir src/main/kotlin/gen \
  "$base/contracts.vocab@$release#/Vocab.pkl" \
  "$base/contracts.fragments@$release#/Fragments.pkl" \
  "$base/contracts.templates@$release#/ServiceConfig.pkl" \
  "$suite/Showcase.pkl" \
  "$suite"/conformance/contract/*.pkl >&2

gradle -q --console=plain --no-daemon run --args="$suite $manifest $schemas" 2>&1 | grep '^{' \
  || { echo "kotlin: gradle run failed" >&2; exit 1; }
