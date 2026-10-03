#!/usr/bin/env bash
# Compares the JSON Schemas this checkout generates for the worked example (the
# documents, and the chart's values schema) with the ones the last release tag
# generates, and fails on a breaking change: a removed property, a newly
# required one, a narrowed type, enum or range, a tightened pattern. The rules
# are packages/jsonschema/Compatibility.pkl, and are tested in test/CompatTest.pkl.
#
#   hack/compat.sh [tag]       default: the newest v* tag
#
# The release is built in a temporary worktree. It has no generators, so this
# checkout's are laid over it (the packages that generate; the release's
# vocabulary, fragments and templates are its own). A breaking change that is meant (a new major, or a minor
# before 1.0 that says so) passes when the CHANGELOG declares it with an entry
# beginning "- **Breaking": under `## Unreleased`, or, in the pull request that
# names the release, under that release's own `## vX.Y.Z` heading.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"

tag="${1:-$(git tag --list 'v*' --sort=-v:refname | head -1)}"
if [ -z "$tag" ]; then
  git fetch --quiet --depth=1 origin 'refs/tags/v*:refs/tags/v*' || true
  tag="$(git tag --list 'v*' --sort=-v:refname | head -1)"
fi
[ -n "$tag" ] || { echo "compat: no release tag to compare with; nothing to check"; exit 0; }
git rev-parse --quiet --verify "refs/tags/$tag" >/dev/null || git fetch --quiet --depth=1 origin "refs/tags/$tag:refs/tags/$tag"

tmp="$(mktemp -d)"
trap 'git worktree remove --force "$tmp/release" >/dev/null 2>&1 || true; rm -rf "$tmp"' EXIT
git worktree add --quiet --detach "$tmp/release" "$tag"

for p in model jsonschema helm typescript python docs; do
  rm -rf "$tmp/release/packages/$p"
  cp -r "packages/$p" "$tmp/release/packages/$p"
done
cp examples/service/PklProject "$tmp/release/examples/service/PklProject"
for p in model jsonschema helm typescript python docs; do bin/pkl project resolve "$tmp/release/packages/$p" >/dev/null; done
bin/pkl project resolve "$tmp/release/examples/service" >/dev/null

TARGETS="jsonschema helm" TREE="$tmp/release" hack/generate.sh "$tmp/before" >/dev/null
TARGETS="jsonschema helm" hack/generate.sh "$tmp/after" >/dev/null
rm -f "$tmp"/{before,after}/helm/README.md "$tmp"/{before,after}/helm/values.yaml

report="$tmp/report.txt"
bin/pkl run --project-dir test packages/jsonschema/Compat.pkl -- --before "$tmp/before" --after "$tmp/after" | tee "$report"
echo "compat: this checkout against $tag"

# The section that may declare a break: `## Unreleased` between releases, and,
# in the pull request that names a release (packages/Release.pkl newer than
# $tag), that release's own `## vX.Y.Z` heading, where the entries now sit.
declared="v$(sed -n 's/^version = "\(.*\)"$/\1/p' packages/Release.pkl)"
sections="Unreleased"
[ "$declared" != "$tag" ] && sections="Unreleased|$declared"

if grep -q '^BREAKING' "$report"; then
  if awk -v re="^## ($sections)( |$)" '$0 ~ re {f=1;next} /^## /{f=0} f' CHANGELOG.md | grep -q '^- \*\*Breaking'; then
    echo "compat: breaking changes, and the CHANGELOG says so (## $sections)"
    exit 0
  fi
  echo "compat: breaking changes against $tag; say so in the CHANGELOG (an entry that begins \"- **Breaking\" under '## Unreleased', or under '## $declared' in its release) if they are meant" >&2
  exit 1
fi
