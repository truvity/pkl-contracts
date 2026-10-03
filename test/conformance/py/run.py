"""The Python side of the conformance suite: one JSON line per (fixture, validator).

  pyjsonschema  python-jsonschema on the generated JSON Schema
  pydantic      the generated pydantic models

usage: run.py <suite dir (test/)> <manifest> <generated schema dir> <generated pydantic .py>
"""
import importlib.util
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

suite, manifest_path, gen_dir, pyd_file = (Path(a) for a in sys.argv[1:5])
manifest = json.loads(manifest_path.read_text())
docs = json.loads((suite / "conformance/documents.json").read_text())

spec = importlib.util.spec_from_file_location("contract_pydantic", pyd_file)
mod = importlib.util.module_from_spec(spec)
sys.modules["contract_pydantic"] = mod
spec.loader.exec_module(mod)

loaded = {str(p): json.loads(p.read_text()) for p in sorted(gen_dir.rglob("*.json"))}
registry = Registry().with_resources(
    (d["$id"], Resource.from_contents(d, default_specification=DRAFT202012)) for d in loaded.values()
)


def first(err):
    lines = str(err).splitlines()
    return " ".join(lines[:2])[:160]


for e in manifest:
    doc = yaml.safe_load(Path(e["path"]).read_text())
    d = docs.get(e["schema"], {})

    def emit(name, accept, detail=""):
        print(json.dumps({"id": e["id"], "validator": name, "accept": accept, "detail": detail}))

    # A chart's values schema embeds every document it refers to: it is checked
    # with an empty registry, so that a reference that needed fetching would fail.
    if e.get("selfContained"):
        validator = Draft202012Validator(json.loads(Path(e["schemaPath"]).read_text()))
    else:
        validator = Draft202012Validator(loaded[e["schemaPath"]], registry=registry)
    errs = sorted(validator.iter_errors(doc), key=lambda x: list(x.absolute_path))
    emit("pyjsonschema", not errs, "" if not errs else f"{'/'.join(map(str, errs[0].absolute_path)) or '(root)'}: {errs[0].message[:100]}")
    if not e["typed"]:
        continue
    try:
        mod.SCHEMAS[d["schema"].removesuffix(".json")].model_validate(doc)
        emit("pydantic", True)
    except Exception as err:  # noqa: BLE001
        emit("pydantic", False, first(err))
