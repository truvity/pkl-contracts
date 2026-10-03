#!/usr/bin/env python3
"""The conformance suite: generate, ask every validator about every fixture, compare.

    uv run --no-project --with pyyaml==6.0.2 python test/conformance/run.py [--kotlin]

Every validator must give the same verdict on every fixture, and that verdict
must be the fixture's label (`ok-*` accepted, `bad-*` refused). A split between
two validators, or a unanimous verdict against the label, fails the run. There
is no informational tier: where the engines disagreed (a line break that is not
a newline, white space beyond ASCII), the vocabulary was changed until they
agreed, and the case stayed as a fixture.

The validators:

  ajv, santhosh, pyjsonschema, networknt   four JSON Schema engines (ECMAScript,
                                           RE2, Python `re`, Java) on the
                                           generated schemas
  zod, pydantic                            the generated TypeScript and Python
  go, kotlin                               the schema's verdict AND the document
                                           decoded into the generated type: those
                                           types are shapes only, the schema is
                                           the validator
  pkl                                      Pkl's own enforcement, the oracle

The fixtures are `fixtures/<document>/<ok|bad>-<name>.yaml`, the probes
generated from the vocabulary's annotations (`Probes.pkl`), and, for each chart,
its generated values against its generated values schema. Kotlin is behind
`--kotlin` because Gradle makes it the slow part; the other engines run without.
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "test"
CONF = SUITE / "conformance"
WORK = CONF / ".work"
PKL = ROOT / "bin" / "pkl"
GEN = WORK / "schemas"
ZOD_DIR = CONF / "ts" / "gen"
PY_DIR = WORK / "py"
HELM = WORK / "helm"
TIMES: dict[str, float] = {}

SCHEMA_ONLY = ("ajv", "santhosh", "pyjsonschema", "networknt")
CHARTS = {"web": "WebValues", "stat": "StatValues", "migrate": "MigrateValues", "cond": "CondValues"}


def put(values, path, value):
    """A copy of `values` with `value` at the dotted `path`; `None` removes the key."""
    out = copy.deepcopy(values)
    node = out
    for step in path[:-1]:
        node = node.setdefault(step, {})
    if value is None:
        node.pop(path[-1], None)
    else:
        node[path[-1]] = value
    return out


# Edits of a chart's defaults beyond the two every chart gets, for the rules across
# fields on its own module: (label, name, edit). The defaults give `database.host`.
CHART_EDITS = {
    "cond": [
        ("bad", "host-missing", lambda v: put(v, ["database", "host"], None)),
        ("bad", "active-without-upstream", lambda v: put(v, ["phase"], "active")),
        ("ok", "active-with-upstream", lambda v: put(put(v, ["phase"], "active"), ["upstream", "url"], "https://up.example")),
        ("ok", "remote-without-host", lambda v: put(put(v, ["database", "host"], None), ["alerts", "remote", "enabled"], True)),
        ("bad", "remote-disabled-without-host", lambda v: put(put(v, ["database", "host"], None), ["alerts", "remote", "enabled"], False)),
    ],
}


def sh(step, cmd, cwd=ROOT, check=True, **kw):
    t = time.time()
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, **kw)
    TIMES[step] = TIMES.get(step, 0) + time.time() - t
    if check and r.returncode != 0:
        sys.exit(f"{step} failed:\n{r.stderr[-3000:]}\n{r.stdout[-1000:]}")
    return r


def pkl_run(step, target, *args):
    return sh(step, [PKL, "run", "--project-dir", SUITE, target, "--", *args])


def generate():
    shutil.rmtree(WORK, ignore_errors=True)
    shutil.rmtree(ZOD_DIR, ignore_errors=True)
    modules = sorted(str(p) for p in (CONF / "contract").glob("*.pkl"))
    modules += sorted(str(p) for p in (CONF / "union").glob("*.pkl"))
    modules += [str(SUITE / "Showcase.pkl")] + sorted(str(p) for p in (CONF / "charts").glob("*Chart.pkl"))
    pkl_run("generate json schema", "@jsonschema/Generate.pkl", "--dir", GEN, *modules)
    pkl_run("generate zod", "@typescript/Generate.pkl", "--dir", ZOD_DIR, *modules)
    pkl_run("generate pydantic", "@python/Generate.pkl", "--dir", PY_DIR, *modules)
    pkl_run("generate probes", str(CONF / "Probes.pkl"), "--dir", WORK / "probes")
    # Pkl writes U+0085 (NEL) raw, and a YAML 1.1 reader (PyYAML, Go's) folds one
    # inside a quoted scalar into a space, so the probe would reach those
    # validators changed. Escaped, every reader gets the character.
    for p in (WORK / "probes").glob("*.json"):
        p.write_text(p.read_text(encoding="utf-8").replace("\u0085", "\\u0085"), encoding="utf-8")
    for name, values in CHARTS.items():
        pkl_run("generate helm", "@helm/Generate.pkl", "--dir", HELM / name, CONF / "charts" / f"{values}.pkl")
    sh("generate go", [CONF / "go" / "generate.sh"])


def manifest():
    entries = []

    def doc(id_, schema, path, label):
        entries.append({"id": id_, "schema": schema, "path": str(path), "label": label, "typed": True,
                        "schemaPath": str(GEN / json.loads((CONF / "documents.json").read_text())[schema]["schema"])})

    for p in sorted((CONF / "fixtures").glob("*/*.yaml")):
        doc(f"fixture/{p.parent.name}/{p.stem}", p.parent.name, p, p.stem.split("-")[0])
    # `edge/` held the strings the engines still split on beyond a newline (a
    # carriage return, NEL, LS, a vertical tab, a no-break space), reported and
    # never failed. Each is now a fixture of the `showcase` document, refused by
    # every engine like any other; a new finding of this kind is a fixture too.
    for p in sorted((WORK / "probes").glob("*.json")):
        # `<ok|bad>-conditions-<n>` is a whole document of the `conditions` contract (its
        # rules across fields); every other probe is one property of the showcase.
        doc(f"probe/{p.stem}", "conditions" if p.stem.startswith(("ok-conditions-", "bad-conditions-")) else "showcase", p, p.stem.split("-")[0])
    # A chart's generated values must satisfy its generated values schema, which
    # embeds every document it refers to: nothing is fetched. Two edits of the
    # defaults, each of which must be refused.
    for name in CHARTS:
        d = HELM / name
        values = yaml.safe_load((d / "values.yaml").read_text())
        broken = {"digest": {**values, "images": {name: {**values["images"][name], "digest": "sha256:abc"}}},
                  "unknown-key": {**values, "bogus": 1}}
        extra = [(label, d / f"{label}-{key}.yaml", edit(values)) for label, key, edit in CHART_EDITS.get(name, [])]
        for label, path, instance in [("ok", d / "values.yaml", None)] + [("bad", d / f"bad-{k}.yaml", v) for k, v in broken.items()] + extra:
            if instance is not None:
                path.write_text(yaml.safe_dump(instance))
            entries.append({"id": f"chart/{name}/{path.stem.removeprefix('bad-').removeprefix('ok-')}", "schema": "", "path": str(path), "label": label,
                            "typed": False, "schemaPath": str(d / "values.schema.json"), "selfContained": True})
    (WORK / "manifest.json").write_text(json.dumps(entries, indent=1))
    return entries


def lines(r, what):
    # Split on "\n" alone: a validator's message may carry a raw NEL, LS or PS (the
    # very characters under test), which `splitlines()` would cut a line at.
    return [json.loads(line) for line in r.stdout.split("\n") if line.startswith("{")]


def run_validators(kotlin):
    m = WORK / "manifest.json"
    out = []
    env = {**os.environ, "PKL_EXEC": str(PKL)}
    r = sh("go: santhosh, go, pkl", ["go", "run", ".", SUITE, m, GEN], cwd=CONF / "go", env=env)
    out += lines(r, "go")
    r = sh("ts: ajv, zod", ["node", "run.mjs", SUITE, m, GEN, ZOD_DIR / "contract.zod.ts"], cwd=CONF / "ts")
    out += lines(r, "ts")
    r = sh("py: pyjsonschema, pydantic", ["uv", "run", "--no-project", "--with", "pydantic==2.12.5", "--with", "pyyaml==6.0.2",
                                          "--with", "jsonschema==4.25.1", "--with", "referencing==0.36.2",
                                          "python", CONF / "py" / "run.py", SUITE, m, GEN, PY_DIR / "contract_pydantic.py"])
    out += lines(r, "py")
    if kotlin:
        r = sh("kotlin: networknt, kotlin", [CONF / "kotlin" / "run.sh", SUITE, m, GEN], env=env)
        out += lines(r, "kotlin")
    return out


def report(entries, results, kotlin):
    cols = ["ajv", "santhosh", "pyjsonschema"] + (["networknt"] if kotlin else []) + ["zod", "pydantic", "go"] + (["kotlin"] if kotlin else []) + ["pkl"]
    by = {}
    for r in results:
        by.setdefault(r["id"], {})[r["validator"]] = r
    rows, split, against = [], [], []
    for e in entries:
        v = by.get(e["id"], {})
        mark = {c: ("A" if v[c]["accept"] else "R") for c in cols if c in v}
        # A chart's values have no type to decode into, and the generator refuses `platform`'s and `union`'s unions for Kotlin.
        missing = [c for c in cols if c not in v and (e["typed"] or c in SCHEMA_ONLY) and not (c == "kotlin" and e["schema"] in ("platform", "union"))]
        verdicts = set(mark.values())
        agree = len(verdicts) == 1 and not missing
        if not agree:
            split.append((e, mark, v, missing))
        elif (verdicts == {"A"}) != (e["label"] == "ok"):
            against.append(e)
        rows.append((e, mark, agree))
    n = len(rows)
    head = [f"conformance: {n} fixtures ({sum(1 for e, _, _ in rows if e['id'].startswith('fixture/'))} documents, "
            f"{sum(1 for e, _, _ in rows if e['id'].startswith('probe/'))} probes, "
            f"{sum(1 for e, _, _ in rows if e['id'].startswith('chart/'))} chart values) x {len(cols)} validators ({', '.join(cols)})",
            f"  unanimous: {n - len(split)} of {n}; split: {len(split)}; unanimous against the label: {len(against)}",
            f"  engine edges beyond the line-break rule: {len(split)} (every one is a fixture, and a split fails the run)"]
    detail = []
    for e, mark, v, missing in split:
        acc = [c for c in mark if mark[c] == "A"]
        rej = [c for c in mark if mark[c] == "R"]
        why = next((v[c]["detail"] for c in rej if v[c].get("detail")), "")
        detail.append(f"SPLIT {e['id']} (label {e['label']}): accepted by {', '.join(acc) or '-'}; rejected by {', '.join(rej) or '-'}"
                      + (f"; no verdict from {', '.join(missing)}" if missing else "") + f"; first rejection: {why[:120]}")
    for e in against:
        detail.append(f"AGAINST-LABEL {e['id']}: every validator says the opposite of its label ({e['label']})")
    table = ["| fixture | label | " + " | ".join(cols) + " | agree |", "|---|---|" + "---|" * (len(cols) + 1)]
    table += [f"| {e['id']} | {e['label']} | " + " | ".join(mark.get(c, "-") for c in cols) + f" | {'yes' if agree else '**NO**'} |"
              for e, mark, agree in rows if not e["id"].startswith("probe/") or not agree]
    timing = ["| step | seconds |", "|---|---|"] + [f"| {k} | {t:.1f} |" for k, t in TIMES.items()]
    text = "\n".join(head + detail)
    (WORK / "results.md").write_text("# Conformance\n\n" + "\n".join(head) + "\n\n" + "\n".join(f"- {d}" for d in detail)
                                     + "\n\n## Time\n\n" + "\n".join(timing) + "\n\n## Fixtures\n\n" + "\n".join(table) + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write((WORK / "results.md").read_text())
    print(text)
    print("time: " + ", ".join(f"{k} {t:.1f}s" for k, t in TIMES.items()))
    return not split and not against


def main():
    kotlin = "--kotlin" in sys.argv
    generate()
    entries = manifest()
    results = run_validators(kotlin)
    sys.exit(0 if report(entries, results, kotlin) else 1)


main()
