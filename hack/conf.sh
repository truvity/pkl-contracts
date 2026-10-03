#!/usr/bin/env bash
# Run a command from the repository root inside the conformance toolchain
# (test/conformance/devbox.json: Go, Node, Python with uv, a JDK, Gradle).
# Devbox installs it on first use and changes into the config's directory, so
# the command is taken back to where it was called from.
#
#   hack/conf.sh <command> [args...]
set -euo pipefail
cd "$(dirname "$0")/.."
exec devbox run --config test/conformance -- env -C "$PWD" "$@"
