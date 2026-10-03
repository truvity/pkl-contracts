#!/usr/bin/env bash
# One entry point for the languages that have an official generator: Go
# (`pkl-gen-go`, the Pkl package pkl.golang from pkl-go) and Kotlin
# (`pkl-codegen-kotlin`, from Pkl itself). Both are pinned here, with the Pkl
# release they need, and the Kotlin tool is checked against a pinned digest.
#
#   hack/codegen.sh go     [pkl-gen-go options] <module>...
#   hack/codegen.sh kotlin [pkl-codegen-kotlin options] <module>...
#
# Options are the generator's own (`--project-dir`, `--output-path` for Go and
# `--output-dir` for Kotlin, `--mapping`, `--rename`): see its --help. The types
# that come out are shapes, with none of the contract's constraints: a Go
# struct or a Kotlin class validates nothing, and the generated JSON Schema is
# what a service validates against (decision 0010 of the policy repository).
# Kotlin refuses a union type (`Int | String`), so a module that has one, the
# platform block, has no Kotlin class.
#
# Name a module outside a project by the project URI of its package (Pkl's own
# tools import their arguments, and `@dependency` is not a path):
#   projectpackage://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.fragments@<version>#/Fragments.pkl
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"

go_generator=package://pkg.pkl-lang.org/pkl-go/pkl.golang@0.14.0#/gen.pkl
kotlin_version=0.32.1
kotlin_sha256=b066795a04cfa9bd7136a426b413abf89405661bef7ed1ed7499eb772d58461d
cache="${XDG_CACHE_HOME:-$HOME/.cache}/pkl-contracts/codegen"

case "${1:-}" in
  go)
    shift
    exec "$here/bin/pkl" run "$go_generator" -- "$@"
    ;;
  kotlin)
    shift
    tool="$cache/pkl-codegen-kotlin-$kotlin_version"
    if ! { [ -x "$tool" ] && echo "$kotlin_sha256  $tool" | sha256sum -c --status; }; then
      mkdir -p "$cache"
      curl -fsSL -o "$tool" "https://github.com/apple/pkl/releases/download/$kotlin_version/pkl-codegen-kotlin"
      chmod +x "$tool"
      echo "$kotlin_sha256  $tool" | sha256sum -c --status || { echo "pkl-codegen-kotlin: checksum mismatch" >&2; rm -f "$tool"; exit 1; }
    fi
    exec "$tool" "$@"
    ;;
  *)
    echo "usage: hack/codegen.sh go|kotlin [generator options] <module>..." >&2
    exit 2
    ;;
esac
