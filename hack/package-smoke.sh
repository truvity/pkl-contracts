#!/usr/bin/env bash
# A generator is run as a package, by a consumer that depends on the vocabulary,
# fragments and templates as packages: the way it will be used. That is not the
# way the tests use it (every project there depends on the others by path), and
# it differs where it matters: a class has one identity per URI, so a generator
# that recognised the vocabulary's annotations with `is` found none, and wrote
# nothing, for such a consumer.
#
# Serves .out/ (from `just package`) as GitHub would, resolves a throwaway
# consumer against it, runs every generator on the example's contract, and
# compares the result with the committed copy.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
version="$(sed -n 's/^version = "\(.*\)"$/\1/p' packages/Release.pkl)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

python3 hack/serve-assets.py .out "$tmp/port" 120 >/dev/null 2>&1 &
for _ in $(seq 50); do [ -s "$tmp/port" ] && break; sleep 0.1; done
port="$(cat "$tmp/port")"

base="package://github.com/truvity/pkl-contracts/releases/download/v$version"
mkdir "$tmp/consumer"
cp examples/service/Config.pkl examples/service/Chart.pkl "$tmp/consumer/"
cat > "$tmp/consumer/PklProject" <<PKL
amends "pkl:Project"

dependencies {
  ["vocab"] { uri = "$base/contracts.vocab@$version" }
  ["fragments"] { uri = "$base/contracts.fragments@$version" }
  ["templates"] { uri = "$base/contracts.templates@$version" }
}
PKL
flags=(--cache-dir "$tmp/cache" --http-rewrite "https://github.com/=http://127.0.0.1:$port/"
  --allowed-resources http:,https:,file:,env:,prop:,modulepath:,package:,projectpackage:)
bin/pkl project resolve "${flags[@]}" "$tmp/consumer" >/dev/null
for g in jsonschema typescript python docs; do
  bin/pkl run "${flags[@]}" --project-dir "$tmp/consumer" "$base/contracts.$g@$version#/Generate.pkl" -- \
    --dir "$tmp/out/$g" "$tmp/consumer/Config.pkl" "$tmp/consumer/Chart.pkl" >/dev/null 2>"$tmp/log" \
    || { cat "$tmp/log" >&2; exit 1; }
done
diff -r "$tmp/out/jsonschema" examples/service/generated/schemas
diff "$tmp/out/typescript/contract.zod.ts" examples/service/generated/ts/contract.zod.ts
diff "$tmp/out/python/contract_pydantic.py" examples/service/generated/py/contract_pydantic.py
echo "package-smoke: the generators, run as packages by a package consumer, write what is committed"
