// The TypeScript side of the conformance suite: one JSON line per (fixture,
// validator).
//
//   ajv  Ajv (draft 2020-12) on the generated JSON Schema
//   zod  the generated zod schema
//
// usage: node run.mjs <suite dir (test/)> <manifest> <generated schema dir> <generated zod .ts>
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { Ajv2020 } from "ajv/dist/2020.js";
import { parse } from "yaml";

const [suite, manifestPath, genDir, zodFile] = process.argv.slice(2);
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const docs = JSON.parse(readFileSync(join(suite, "conformance/documents.json"), "utf8"));
const { schemas } = await import(pathToFileURL(zodFile).href);

const files = (d) => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? files(join(d, f)) : f.endsWith(".json") ? [join(d, f)] : []));
const ajv = new Ajv2020({ allErrors: true, strict: false });
for (const f of files(genDir)) {
  const d = JSON.parse(readFileSync(f, "utf8"));
  ajv.addSchema(d, d.$id);
}
const idOf = (file) => JSON.parse(readFileSync(join(genDir, file), "utf8")).$id;

for (const e of manifest) {
  const doc = parse(readFileSync(e.path, "utf8"));
  const d = docs[e.schema] ?? {};
  const emit = (validator, accept, detail = "") => console.log(JSON.stringify({ id: e.id, validator, accept, detail }));
  try {
    // A chart's values schema embeds every document it refers to: it is
    // compiled alone, so that a reference that needed fetching would fail.
    const validate = e.selfContained
      ? new Ajv2020({ allErrors: true, strict: false }).compile(JSON.parse(readFileSync(e.schemaPath, "utf8")))
      : ajv.getSchema(idOf(d.schema));
    const ok = validate(doc);
    emit("ajv", ok, ok ? "" : `${validate.errors[0].instancePath || "(root)"} ${validate.errors[0].message}`);
  } catch (err) {
    emit("ajv", false, "error: " + String(err.message).split("\n")[0]);
  }
  if (!e.typed) continue;
  try {
    const r = schemas[d.schema.replace(/\.json$/, "")].safeParse(doc);
    emit("zod", r.success, r.success ? "" : `${r.error.issues[0].path.join(".") || "(root)"} ${r.error.issues[0].message}`);
  } catch (err) {
    emit("zod", false, "error: " + String(err.message).split("\n")[0]);
  }
}
