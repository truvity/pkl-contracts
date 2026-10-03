#!/usr/bin/env python3
"""Every default the contract declares is in every artifact, with the same value.

    python3 hack/defaults-check.py [generated-dir]

The conformance suite compares verdicts (accepted or refused), and a dropped
default changes no verdict: a JSON Schema without `default` accepts exactly what
it accepted with one. So this check is structural. The expectation is Pkl's own
reflection (examples/service/Defaults.pkl); each artifact is read back and must
carry exactly those defaults:

  - the JSON Schema of each document        (`default` on the property)
  - the chart's values.schema.json          (the same, per embedded document)
  - values.yaml                             (the key, with the default, wherever
                                             its object is present)
  - zod                                     (`.default(...)`)
  - pydantic                                (`Field(default=...)`)
  - the docs table                          (the Default column)

A default may be any value, an object included (an open object, or a class
given a default of its own): each artifact must carry it whole.

The same artifacts are checked for what a property that is SET AT INSTALL
(`@SetAtInstall`) must look like: required by every schema and validator
(a JSON Schema `required`, a zod field and a pydantic one without `optional`,
`None` or a default, a docs row that says required and "Set at install"), and
absent from values.yaml, where its object is present. A default for it would
let an install that forgot it pass.

It fails on a missing default, a different one, and one nobody declared. The
directory defaults to examples/service/generated.
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
gen = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "examples/service/generated"

expected = json.loads(
    subprocess.run(
        [str(ROOT / "bin/pkl"), "eval", "--project-dir", "examples/service", "-f", "json",
         "examples/service/Defaults.pkl"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
)

problems: list[str] = []
checked = 0


def canon(v):
    return json.dumps(v, sort_keys=True)


def compare(where: str, want: dict, got: dict):
    """want and got: property -> default."""
    global checked
    for k, v in want.items():
        checked += 1
        if k not in got:
            problems.append(f"{where}: `{k}` has no default, the contract says {canon(v)}")
        elif canon(got[k]) != canon(v):
            problems.append(f"{where}: `{k}` defaults to {canon(got[k])}, the contract says {canon(v)}")
    for k in got.keys() - want.keys():
        problems.append(f"{where}: `{k}` defaults to {canon(got[k])}, the contract declares none")


# ---- JSON Schema ------------------------------------------------------------

def schema_defaults(node) -> list:
    """(property, default) of every property under any `properties` map."""
    out = []
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict):
            for name, sub in props.items():
                if isinstance(sub, dict) and "default" in sub:
                    out.append((name, sub["default"]))
        for k, v in node.items():
            if k != "$defs":
                out += schema_defaults(v)
    elif isinstance(node, list):
        for v in node:
            out += schema_defaults(v)
    return out


def as_map(where: str, pairs) -> dict:
    m = {}
    for k, v in pairs:
        if k in m and canon(m[k]) != canon(v):
            problems.append(f"{where}: `{k}` has two different defaults")
        m[k] = v
    return m


def want_map(pairs) -> dict:
    return {k: v for k, v in pairs}


for key, doc in expected["documents"].items():
    path = gen / "schemas" / f"{key}.json"
    got = as_map(str(path.relative_to(gen)), schema_defaults(json.loads(path.read_text())))
    compare(f"schemas/{key}.json", want_map(doc["defaults"]), got)

values_schema = json.loads((gen / "helm/values.schema.json").read_text())
compare("helm/values.schema.json (chart)", want_map(expected["chartRoot"]),
        as_map("helm", schema_defaults({k: v for k, v in values_schema.items() if k != "$defs"})))
for key, doc in expected["documents"].items():
    sub = values_schema["$defs"].get(doc["id"])
    if sub is None:
        problems.append(f"helm/values.schema.json: no $defs entry for {doc['id']}")
        continue
    compare(f"helm/values.schema.json ({key})", want_map(doc["defaults"]),
            as_map("helm", schema_defaults(sub)))

# ---- values.yaml ------------------------------------------------------------

# Pkl reads the YAML (hack/yaml-to-json.pkl), so this needs nothing but Python's
# standard library and the Pkl the repository already pins.
values = json.loads(
    subprocess.run(
        [str(ROOT / "bin/pkl"), "eval", "-f", "json", "-p", f"file={(gen / 'helm/values.yaml').resolve()}",
         "hack/yaml-to-json.pkl"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
)
for e in expected["chart"]:
    *parents, leaf = e["path"].split(".")
    cur = values
    for p in parents:
        cur = cur.get(p) if isinstance(cur, dict) else None
    if not isinstance(cur, dict):
        continue  # the object is not in the chart's values, so neither is its default
    compare(f"helm/values.yaml ({e['path']})", {leaf: e["default"]}, {leaf: cur[leaf]} if leaf in cur else {})

# ---- zod --------------------------------------------------------------------

ts = next((gen / "ts").glob("*.ts")).read_text()
zod = {}
zod_lines = {}
for m in re.finditer(r"^export const (\w+)_shape = \{\n(.*?)^\};", ts, re.S | re.M):
    zod_lines[m.group(1)] = {f.group(1): f.group(0) for f in re.finditer(r"^  (\w+): .*$", m.group(2), re.M)}
    zod[m.group(1)] = {
        f.group(1): json.loads(f.group(2))
        for f in re.finditer(r"^  (\w+): .*\.default\((.*)\),$", m.group(2), re.M)
    }

# ---- pydantic ---------------------------------------------------------------

py = next((gen / "py").glob("*.py")).read_text()
pyd = {}
pyd_lines = {}
# A class ends at the next class or module-level name, not at any line that starts
# in column 0: a multi-line docstring has such lines.
for m in re.finditer(r"^class (\w+)\(.*?\):\n(.*?)(?=^(?:class |SCHEMAS|EOF|\w+ = ))", py + "\nEOF", re.S | re.M):
    pyd_lines[m.group(1)] = {f.group(1): f.group(0) for f in re.finditer(r"^    (\w+): .*$", m.group(2), re.M)}
    # A default is `Field(default=<literal>)`; a class's is built through the class,
    # `Field(default_factory=lambda: <Class>.model_validate(<literal>))`.
    pyd[m.group(1)] = {
        f.group(1): ast.literal_eval(f.group(2) or f.group(3))
        for f in re.finditer(
            r"^    (\w+): .* = Field\((?:default=(.*)|default_factory=lambda: \w+\.model_validate\((.*)\))\)$",
            m.group(2), re.M)
    }

# ---- docs table -------------------------------------------------------------

md = (gen / "docs/reference.md").read_text()
docs = {}
for m in re.finditer(r"^### `(\w+)`\n(.*?)(?=^#|\Z)", md, re.S | re.M):
    rows = {}
    for r in re.finditer(r"^\| `(\w+)` \|((?:[^|\\]|\\.)*\|){3}", m.group(2), re.M):
        cells = re.split(r"(?<!\\)\|", r.group(0))
        cell = cells[4].strip()
        if cell:
            rows[r.group(1)] = json.loads(cell.strip("`"))
    docs[m.group(1)] = rows

for qname, want in expected["classes"].items():
    compare(f"zod {qname}", want, zod.get(qname, {}))
    compare(f"pydantic {qname}", want, pyd.get(qname, {}))
    compare(f"docs table {qname}", want, docs.get(qname, {}))

# ---- set at install ---------------------------------------------------------

def schema_at(root: dict, defs: dict, path: str):
    """The property schema at a dotted path, and the schema that holds it."""
    holder, node = None, root
    for part in path.split("."):
        while isinstance(node, dict) and "$ref" in node:
            node = defs[node["$ref"]]
        holder, node = node, node["properties"][part]
    return holder, node


for path in expected["chartAtInstall"]:
    checked += 1
    *parents, leaf = path.split(".")
    holder, prop = schema_at({k: v for k, v in values_schema.items() if k != "$defs"}, values_schema["$defs"], path)
    if leaf not in holder.get("required", []):
        problems.append(f"helm/values.schema.json: `{path}` is set at install and must be in `required`")
    if "default" in prop:
        problems.append(f"helm/values.schema.json: `{path}` is set at install and must have no default")
    cur = values
    for p in parents:
        cur = cur.get(p) if isinstance(cur, dict) else None
    if isinstance(cur, dict) and leaf in cur:
        problems.append(f"helm/values.yaml: `{path}` is set at install and must be left out, it is {canon(cur[leaf])}")

for qname, names in expected["classesAtInstall"].items():
    for name in names:
        checked += 1
        where = f"`{qname}.{name}`"
        z = zod_lines.get(qname, {}).get(name)
        if z is None or ".optional()" in z or ".default(" in z:
            problems.append(f"zod: {where} is set at install and must be required: {z}")
        y = pyd_lines.get(qname, {}).get(name)
        if y is None or "None" in y or "Field(" in y:
            problems.append(f"pydantic: {where} is set at install and must be required: {y}")
        rows = [r for r in re.findall(rf"^\| `{name}` \|.*$", next(iter(re.findall(rf"^### `{qname}`\n(.*?)(?=^#|\Z)", md, re.S | re.M)), ""), re.M)]
        if not rows or "| yes |" not in rows[0] or "Set at install" not in rows[0]:
            problems.append(f"docs table: {where} is set at install and its row must say so: {rows[:1]}")

if checked == 0:
    problems.append("no default was checked: the contract declares none, or the check reads nothing")

if problems:
    print("defaults-check: a default is missing or differs:", file=sys.stderr)
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    sys.exit(1)
print(f"defaults-check: {checked} default checks across schemas, values schema, values.yaml, zod, pydantic and docs")
