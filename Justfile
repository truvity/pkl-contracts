# Development commands. Tools come from devbox (`devbox shell`, or direnv);
# CI runs each recipe as its own job.
#
# Pkl itself is the exception, and a temporary one: `bin/pkl` fetches and
# verifies the pinned release (see the comment in it) because nixpkgs lags.
# Every recipe that evaluates Pkl goes through it, so a contributor runs the
# same Pkl CI does.
#
# `check` is the gate. It needs no credentials and no cluster: Pkl, git, and
# what devbox names.

pkl := "bin/pkl"
packages := "packages/vocab packages/fragments packages/templates"
projects := "packages/vocab packages/fragments packages/templates test examples/service"

# Everything CI requires
[doc("Everything CI requires")]
check: test lint example package leak-canary

# The tests: the vocabulary's probes against Pkl's own enforcement, the
# authoring lint by reflection, and the fragments and templates in use.
[doc("Run the Pkl tests")]
test:
    {{pkl}} project resolve test
    {{pkl}} test --project-dir test

# Every rule that is not a test: formatting, the lint of the source, the
# resolved dependencies being current, editorconfig.
[doc("Format check, authoring lint, dependency pins, editorconfig")]
lint:
    {{pkl}} format --diff-name-only packages test examples
    hack/lint.sh
    for p in {{projects}}; do {{pkl}} project resolve "$p" >/dev/null; done
    git diff --exit-code -- 'packages/*/PklProject.deps.json' 'test/PklProject.deps.json' 'examples/*/PklProject.deps.json'
    # Whitespace rules only (final newline, LF, UTF-8, no stray trailing
    # whitespace). Indentation WIDTH is the formatter's (`pkl format`), above.
    editorconfig-checker -disable-indentation -disable-indent-size

# Rewrite the Pkl files in the canonical format
[doc("Format the Pkl files")]
fmt:
    {{pkl}} format -w packages test examples

# Evaluate every module that stands alone, and render the worked example against
# its committed render. The templates have required fields, so they are
# evaluated through the example and the tests, never bare.
[doc("Evaluate the modules and the worked example")]
example:
    #!/usr/bin/env bash
    set -euo pipefail
    {{pkl}} project resolve packages/fragments >/dev/null
    for m in packages/vocab/Vocab.pkl packages/vocab/Annotations.pkl; do
        {{pkl}} eval --project-dir packages/vocab "$m" >/dev/null
    done
    for m in packages/fragments/Fragments.pkl packages/fragments/Platform.pkl; do
        {{pkl}} eval --project-dir packages/fragments "$m" >/dev/null
    done
    {{pkl}} project resolve examples/service >/dev/null
    diff <({{pkl}} eval --project-dir examples/service -f yaml examples/service/values.pkl) examples/service/values.yaml
    echo "example: renders as committed"

# Build the three packages exactly as a release will publish them, into .out/,
# and check the metadata against the URIs GitHub will serve.
[doc("Build the packages and check their metadata")]
package:
    {{pkl}} project package {{packages}} --output-path '.out/%{name}@%{version}'
    hack/package-check.sh

# Resolve every project's dependencies, after a version or a dependency change.
[doc("Resolve the PklProject.deps.json files")]
resolve:
    for p in {{projects}}; do {{pkl}} project resolve "$p"; done

# This repository is public and its history cannot be unpublished, so the
# rule (mechanism only; particulars are the consuming estate's) is enforced
# mechanically rather than remembered.
[doc("Refuse a particular that must never be published")]
leak-canary:
    hack/leak-canary.sh

# Report a problem with what this repository trusts from outside: the pinned
# Pkl's checksums against the digests GitHub publishes. Its own workflow
# (security.yaml), never the gate, like every repository's `vuln`: it needs the
# network, and an upstream change is news about the world, not about the
# change under review. There is no Go module here for govulncheck to read.
[doc("Check bin/pkl's pins against GitHub's published digests")]
vuln:
    hack/pin-check.sh
