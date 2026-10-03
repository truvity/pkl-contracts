#!/usr/bin/env bash
# The authoring rules a contract is held to, for what Pkl's reflection cannot
# see (it exposes no constraint, only that a type exists). The reflection-side
# rules (documentation, no nullable-with-default) are test/LintTest.pkl.
#
# Reads tracked and untracked-but-not-ignored files, so it runs before a commit.
#
#   1. No ad-hoc constraints outside the vocabulary (the generator packages, which
#      are not contracts, are not held to this). A constraint is written
#      once, in packages/vocab/Vocab.pkl, reviewed once and used everywhere: no
#      `Regex(`, no constrained type (`String(length >= 1)`), no alias, in any
#      other module. The one exception is a cross-field rule, which is an alias
#      annotated @A.RequiredWhen or @A.RequiredUnless so that a generator can read it.
#   2. The vocabulary spells every pattern one way: through `search`, which
#      has search semantics and refuses a newline; never `matches`, which is a
#      full match. Each pattern alias is annotated with the same constant.
#      A property MAY carry `@A.Range` and `@A.Length` (a bound narrowing the type
#      it has; `contracts.vocab.Check` makes Pkl enforce it, and the generators
#      read it like an alias's), because those are a fixed set of data, not an
#      expression. `@A.Pattern` is the vocabulary's alone: a pattern is a regular
#      expression, and a regular expression is an ad-hoc constraint.
#   3. No `null` in a contract: an optional field is absent, not null.
#   4. No `X | Y?`: the `?` binds to `Y` alone, so the union is not "nullable X
#      or Y" but a nullable member, which every reflection reads as a REQUIRED
#      field. Write `(X | Y)?`. (The model refuses it too, by reflection, for a
#      generator; this catches it in the source, before one runs.)
#   5. One version. A tag-shaped string appears in packages/Release.pkl and
#      nowhere else a human writes it.
set -uo pipefail
cd "$(dirname "$0")/.."

fail=0
say() { echo "LINT: $*"; fail=1; }

mapfile -t pkl < <(git ls-files --cached --others --exclude-standard -- '*.pkl' 'PklProject' '**/PklProject')

code() { # a file's lines with comments removed, numbered
  awk '{ line=$0; sub(/^[[:space:]]*\/\/.*$/, "", line); sub(/[[:space:]]\/\/ .*$/, "", line); if (line != "") printf "%d:%s\n", NR, line }' "$1"
}

vocab=packages/vocab/Vocab.pkl

# 1. ad-hoc constraints --------------------------------------------------
for f in "${pkl[@]}"; do
  case "$f" in
    packages/vocab/*) continue ;;     # where constraints live
    # The generators write Pkl that is not a contract: their string templates
    # contain the text of other languages (regular expressions, a closing
    # parenthesis after a name), which the checks below mistake for a constraint.
    packages/model/* | packages/jsonschema/* | packages/helm/* | packages/typescript/* | packages/python/* | packages/docs/*) continue ;;
    packages/Release.pkl) continue ;; # package metadata, not a contract
    packages/*/PklProject | */PklProject) continue ;;
    test/*) continue ;;               # the tests may construct what they refuse
  esac
  while IFS= read -r hit; do
    say "$f:${hit%%:*}: a regular expression outside the vocabulary: ${hit#*:}"
  done < <(code "$f" | grep -F 'Regex(' || true)

  # a constrained type: an identifier or `>` directly followed by `(`, in the
  # type position of a property (between the first `:` and any `=`).
  while IFS= read -r hit; do
    say "$f:${hit%%:*}: a constrained type outside the vocabulary: ${hit#*:}"
  done < <(code "$f" | awk -F: '
    { n=$1; s=substr($0, length($1)+2)
      if (s ~ /^[[:space:]]*(class|typealias|function|import|local|amends|extends|module|open)[[:space:]]/) next
      if (s ~ /^[[:space:]]*@/) next
      i=index(s, ":"); if (i == 0) next
      t=substr(s, i+1); j=index(t, "="); if (j > 0) t=substr(t, 1, j-1)
      if (t ~ /[A-Za-z0-9_>`]\(/) print n ":" s
    }')

  # an alias: only a cross-field rule, and only with the annotation that says so
  code "$f" | awk -F: -v f="$f" '
    { n=$1; s=substr($0, length($1)+2) }
    s ~ /Required(When|Unless)/ { ok=1 }
    s ~ /^[[:space:]]*(class|module|open module)[[:space:]]/ { ok=0 }
    s ~ /^[[:space:]]*typealias[[:space:]]/ {
      if (!ok) { printf "LINT: %s:%d: an alias outside the vocabulary: %s\n", f, n, s; bad=1 }
      ok=0
    }
    END { exit bad }' || fail=1
done

# 2. the vocabulary's own spelling -----------------------------------------
if code "$vocab" | grep -E '\bmatches\(' >/dev/null; then
  say "$vocab: matches() is a full match; a pattern has search semantics, so use search()"
fi
if [ "$(code "$vocab" | grep -cF 'Regex(')" != 1 ]; then
  say "$vocab: Regex( must appear once, in the search helper; every pattern goes through it"
fi
awk '
  /^@A\.Pattern/ { inpat=1 }
  inpat && /regex = / { match($0, /regex = [A-Za-z0-9]+/); want=substr($0, RSTART+8, RLENGTH-8); inpat=0 }
  /^typealias .*search\(this, / {
    match($0, /search\(this, [A-Za-z0-9]+\)/); got=substr($0, RSTART+13, RLENGTH-14)
    if (got != want) { printf "LINT: %s:%d: alias constrains %s but its @A.Pattern annotates %s\n", FILENAME, NR, got, want; bad=1 }
    want=""
  }
  END { exit bad }' "$vocab" || fail=1

# 3. null -------------------------------------------------------------------
for f in "${pkl[@]}"; do
  case "$f" in
    test/*) continue ;;
    # The model is the intermediate form, where "absent" is a null, and the
    # generators write other languages; neither is a contract.
    packages/model/*) continue ;;
  esac
  while IFS= read -r hit; do
    say "$f:${hit%%:*}: null in a contract: an optional field is absent, never null"
  done < <(code "$f" | grep -E '(^|[^!=<>])=[[:space:]]*null\b|\?\?[[:space:]]*null\b' || true)
done

# 4. the `X | Y?` trap -----------------------------------------------------
for f in "${pkl[@]}"; do
  case "$f" in
    packages/model/* | packages/jsonschema/* | packages/helm/* | packages/typescript/* | packages/python/* | packages/docs/*) continue ;;
    packages/Release.pkl | */PklProject | test/LintFixtures.pkl) continue ;;
  esac
  while IFS= read -r hit; do
    say "$f:${hit%%:*}: a union with a nullable member makes only that member nullable; write (X | Y)? : ${hit#*:}"
  done < <(code "$f" | awk -F: '
    { n=$1; s=substr($0, length($1)+2)
      if (s ~ /^[[:space:]]*(class|function|import|local|amends|extends|module|open|when|for)[[:space:]]/) next
      if (s ~ /^[[:space:]]*typealias[[:space:]]/) { i=index(s, "="); if (i == 0) next; t=substr(s, i+1) }
      else { i=index(s, ":"); if (i == 0) next; t=substr(s, i+1); j=index(t, "="); if (j > 0) t=substr(t, 1, j-1) }
      if (t ~ /\|[[:space:]]*[A-Za-z0-9_.">`]+\?/) print n ":" s
    }')
done

# 4b. a pattern is the vocabulary's alone ------------------------------------
for f in "${pkl[@]}"; do
  case "$f" in
    packages/vocab/* | packages/model/* | packages/jsonschema/* | packages/helm/* | packages/typescript/* | packages/python/* | packages/docs/*) continue ;;
    test/*) continue ;;
  esac
  while IFS= read -r hit; do
    say "$f:${hit%%:*}: @A.Pattern outside the vocabulary: a pattern is an ad-hoc constraint, add an alias to Vocab.pkl: ${hit#*:}"
  done < <(code "$f" | grep -E '@(A\.)?Pattern\b' || true)
done

# 5. one version ------------------------------------------------------------
for f in "${pkl[@]}"; do
  [ "$f" = packages/Release.pkl ] && continue
  while IFS= read -r hit; do
    say "$f:${hit%%:*}: a version written by hand; it lives in packages/Release.pkl: ${hit#*:}"
  done < <(code "$f" | grep -E '"v?[0-9]+\.[0-9]+\.[0-9]+"|/v[0-9]+\.[0-9]+\.[0-9]+|@[0-9]+\.[0-9]+\.[0-9]+' || true)
done

for p in packages/*/PklProject; do
  grep -q 'Release.metadata(' "$p" || say "$p: package metadata must come from Release.metadata"
done

[ "$fail" = 0 ] && echo "lint clean: ${#pkl[@]} Pkl files"
exit $fail
