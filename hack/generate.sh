#!/usr/bin/env bash
# Regenerates every artifact of the worked example (examples/service) into a
# directory: JSON Schema, the chart's values schema, defaults and values table,
# TypeScript with zod, Python with pydantic, and the Markdown reference.
#
#   hack/generate.sh [dir]     default: examples/service/generated
#
# TARGETS (default: all five) narrows it, and TREE names another checkout with
# the same layout (the compatibility check generates a release's schemas that
# way, with this checkout's generators laid over it).
#
# `just generate` writes the committed copy; `just generated` regenerates into a
# temporary directory and fails when the result differs from the committed one,
# so that a change to a generator or to the contract cannot leave a stale copy.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "${TREE:-$here}"

out="${1:-examples/service/generated}"
pkl="$here/bin/pkl"
project=examples/service
targets="${TARGETS:-jsonschema helm typescript python docs}"
rm -rf "$out"

run() { # generator, then its arguments
  local g="$1"; shift
  local log
  log="$("$pkl" run --project-dir "$project" "@$g/Generate.pkl" -- "$@" 2>&1)" || { echo "$log" >&2; return 1; }
}

has() { [[ " $targets " == *" $1 "* ]]; }

has jsonschema && run jsonschema --dir "$out/schemas" "$project/Config.pkl" "$project/Chart.pkl"
has helm && run helm --dir "$out/helm" "$project/values.pkl"
has typescript && run typescript --dir "$out/ts" "$project/Config.pkl" "$project/Chart.pkl"
has python && run python --dir "$out/py" "$project/Config.pkl" "$project/Chart.pkl"
has docs && run docs --dir "$out/docs" "$project/Config.pkl" "$project/Chart.pkl"
echo "generate: wrote $out"
