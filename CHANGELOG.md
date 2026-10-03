# Changelog

What changed for someone consuming these packages, newest first, one heading
per tag. The prose bullets are written for a consumer; the commit subjects under
them are the GitHub Release's own list. All packages are released together
under one version, so a heading covers all of them.

## Unreleased

### Fixes

- **A block whose fields all have defaults is optional, and carries its default,
  in every generated artifact.** Pkl gives a property of a class type that nobody
  sets an instance of the class built from its defaults (`resources: Resources`),
  so an author may leave it out, but the generators listed it as required with no
  default: a JSON Schema validator refused a document Pkl accepted, and the chart's
  values schema said `required` for a key `values.yaml` already carried. A class is
  now default-complete when every property has a default, is nullable, or is such a
  block itself; such a property is out of `required` and has the rendered instance
  as its `default` (the JSON Schema, the chart's values schema, `values.yaml`,
  zod's `.default(...)`, pydantic's `Field(default_factory=...)` and the
  reference's "Required: no" with its default). A block with a field that has no
  default, with a value set at install, or an open object that must carry keys,
  stays required. This is a widening: a document valid before is valid now.
- **A class that extends another one that is not a document of its own keeps what
  it inherits.** The inherited properties were dropped from the JSON Schema, zod,
  pydantic and the reference, and a document that set one was refused as an unknown
  key.
- **A property whose name is not an identifier generates working code.** zod emitted
  `service-lib: ...` as a bare key (a syntax error); pydantic declared it as an
  attribute, and also a Python keyword (`global`), a leading digit and a leading
  underscore (which pydantic drops as private). zod now quotes the key; pydantic
  declares a name Python can and sets `Field(alias="<key>")`, so the document's key
  is unchanged. `@RequiredWhen` over such a name is written the same way.
- **A default with a line break, a tab, a separator, a quote or a backslash no
  longer breaks the generated source.** A raw line feed in a zod `.default("...")`
  or a pydantic `Field(default="...")` made the whole file fail to parse; control
  characters and the line and paragraph separators are now escapes. A class
  documentation that ends in a quote no longer closes pydantic's docstring early.
  In the reference and the chart's values table such a default is one escaped
  cell, and a bar in a default no longer splits the values table's row.
- **A map keyed by an enum** (`Mapping<LogLevel, X>`) names its keys in the JSON
  Schema (`propertyNames`), so an unknown key is refused as Pkl does, and is a
  partial record in zod (zod 4 reads a record keyed by an enum as needing every
  member).
- **A union with a list, a map, a format or a required key in it keeps what each
  member says.** `Listing<NonEmptyString> | NonEmptyString` came out as
  `type: ["array", "string"]`, so the items were never checked; it is now an
  `anyOf` of each member's own schema.
- **A rule across fields on a class that is not a document of its own is in the JSON
  Schema.** `@RequiredWhen` was written only for a document (`@Schema`); used on a
  nested class it was enforced by Pkl, zod and pydantic and ignored by the schema.
- **A non-nullable open object that must carry keys** (`V.Named`) no longer stops the
  generators with an evaluation error: the empty object it would default to is not
  valid, so the property is required.
- **Set at install is structured data as well as prose.** Every JSON Schema (and the
  chart's values schema) marks such a property `x-set-at-install: true`, and the
  reference has a `Set at install` column that says `yes`; the `**Set at install.**`
  prose stays. An annotation: no validator reads it, and the compatibility diff
  treats it as no change.

## v0.3.0 — 2026-10-03

This is a minor release (0.2.x to 0.3.0): it changes the vocabulary's patterns,
adds annotations and aliases, and moves one class. What it narrows is listed
first.

### Breaking

- **Breaking: every pattern alias now refuses every line break, not only `\n`.**
  A value containing a carriage return, a form feed, a vertical tab, NEL
  (U+0085), LS (U+2028) or PS (U+2029) was accepted by some engines and refused
  by others (Java, so Pkl, let `$` match before a final `\r`; RE2 and Python
  accepted a vertical tab). Now `search` refuses all seven in Pkl, JSON Schema
  pairs each `pattern` with `not: { pattern: "[...]" }` over them, zod and
  pydantic refuse them in a refinement and a validator, so no engine admits one.
  A consumer whose documents carried one in a host and port, a path, an origin,
  a duration, a digest, an environment variable name or any other patterned
  value (a trailing `\r` from a file with Windows line endings is the likely
  case) must strip it; the schema now says so. The generated JSON
  Schemas carry a different `not` pattern, and the TypeScript helper is renamed
  `noLineBreak` (Python's `_no_line_break`).
- **Breaking: white space in a pattern is an explicit class, and it is the
  widest reading.** `HostPort`, `ReportUri`, `CollectorUrl`, `UrlPath` and
  `UrlPathOrEmpty` spelled `\s`, which ECMAScript and Python read as Unicode
  white space and Java and RE2 as ASCII only. They now refuse space, tab, the
  no-break space and the Unicode space separators everywhere, which is what
  ECMAScript and Python already did; Pkl and Go consumers that accepted a
  no-break space in a host and port will now refuse it. `AbsPath` spells `.` as
  `[^\n]`, which matches the same strings (a line break never reaches it); the
  compatibility diff flags the changed pattern text, and it is not a narrowing.
- **Breaking: `ServiceLib` moved from `ChartValues` to `Fragments`.** A chart
  that does not extend `ChartValues` can now declare `` `service-lib`:
  F.ServiceLib? `` itself. A chart that extends `ChartValues` is unaffected, but
  the generated TypeScript and Python name of the class changes
  (`ChartValuesServiceLib` to `ServiceLib`).

### Added

- **`@A.Range` and `@A.Length` on a property.** A field whose rule is only a
  bound (a minimum of 600, a length of at least 16, a port that may be zero, a
  name of at most 253 characters) takes a vocabulary type and a property
  annotation, intersected with the type's own bound. Every generator reads it as
  it reads an alias's, the probes run its boundaries, and Pkl enforces it:
  `contracts.vocab.Check` (a new module of the vocabulary) reflects over a value
  and compares each property with its annotations, and `ServiceConfig`,
  `ChartValues` (in their `output`) and the Helm generator call it, so a document
  or a chart's `values.pkl` outside a bound fails with the path and the bound.
- **`@A.SetAtInstall`.** A property the schema requires and the chart's defaults
  leave out (a bucket name, a host): `V.NonEmptyString?` in Pkl, required in the
  JSON Schema, zod, pydantic and the reference, absent from `values.yaml`. It
  replaces a default of `""`.
- **Object-valued defaults.** A default that is an open object or a class given a
  default of its own is now carried by the JSON Schema `default`, `values.yaml`,
  zod, pydantic and the reference, not only scalars, lists and maps.
- **Vocabulary aliases `Quantity`** (a Kubernetes quantity: `256Ki`, `500m`,
  `1.5Gi`; never empty, so a field that may be left out is `Quantity?`) **and
  `BufferLimit`** (a whole number with `Ki`, `Mi`, `Gi`, `k`, `M`, `G`, a
  gateway's request buffer limit).
- **Lints.** A literal union used in two places, or two that overlap, must be a
  vocabulary enum: the model refuses to generate for such a contract, and names
  both places. `X | Y?` is refused in the source (`hack/lint.sh`) and by
  reflection: write `(X | Y)?`. `@A.Pattern` outside the vocabulary is refused.

### Tooling

- The conformance suite has no informational tier any more: the six strings the
  engines still split on (a carriage return, NEL, LS, a vertical tab, a no-break
  space) are fixtures every engine must refuse, and the report of engine edges is
  zero. Probes now try every line break after each valid example.
- `hack/defaults-check.py` covers object-valued defaults and set-at-install
  properties (required by every artifact, absent from `values.yaml`).
- The worked example gains an open-object default, a class default, a
  set-at-install bucket and a property bound.

## v0.2.1 — 2026-10-03

### Fixes

- **Generated JSON Schemas and chart values schemas now carry property
  defaults.** `contracts.jsonschema` dropped `default` (the zod, pydantic and
  documentation outputs already had it), so a schema accepted the same documents
  but told an editor, a form or a reader nothing of the default. Regenerate to
  pick it up; no document that was valid becomes invalid. The worked example's
  generation now checks, beyond the verdicts, that every default is present and
  equal in the schemas, `values.yaml`, zod, pydantic and the docs table.

### Tooling

- The root devbox no longer installs Go, Node, uv, a JDK or Gradle. They moved to
  `test/conformance/devbox.json`, which only `just conformance` and
  `just conformance-kotlin` use (through `hack/conf.sh`), so every other CI job
  installs far less.

## v0.2.0 — 2026-10-03

### Packages

- **`contracts.model`: the reflection every generator shares.** A contract's
  modules as classes, properties, types and the vocabulary's constraints.
  Annotations are recognised by class name, so a generator works for a consumer
  that depends on the vocabulary as a package.
- **`contracts.jsonschema`: JSON Schema (draft 2020-12).** One document per
  shape, composed by `$ref`, the vocabulary's constraints as keywords; a
  pattern is paired with `not: { pattern: "\\n" }` so that it never admits a
  newline in any engine. Its second entry point, `Compat.pkl`, compares two
  directories of schemas and reports what is breaking: a removed property, a
  newly required one, a narrowed type, enum or range, a closed object, a
  tightened pattern.
- **`contracts.helm`: a chart's values.** `values.schema.json` with the platform
  and config schemas composed (every document embedded, so that Helm validates
  offline), the `values.yaml` defaults, and a README values table.
- **`contracts.typescript`: TypeScript types and zod schemas.**
- **`contracts.python`: pydantic v2 models.** An explicit `null` for an optional
  field is refused, and an integral float is an integer.
- **`contracts.docs`: a Markdown reference** of every field with its type,
  default, constraints and whether it names a secret.
- Each generator is a `pkl:Command` (`Generate.pkl`) that takes the modules of a
  contract as arguments. Go and Kotlin come from the official generators, pinned
  behind `hack/codegen.sh`; their types are shapes and the schema is the
  validator.

### Tooling

- **Cross-language conformance** (`just conformance`, and `just
  conformance-kotlin` for Kotlin): nine validators (four JSON Schema engines,
  zod, pydantic, Go and Kotlin through the official generators' types, and Pkl
  itself) must agree on every fixture and probe. The three splits the
  prototype found are gone: a trailing newline, an explicit `null`, and an
  integral float.
- **`just generated`** fails when `examples/service/generated` is stale, and
  **`just compat`** fails on a breaking change against the last release tag.
- The test loader (`test/Load.pkl`) now refuses an explicit `null` and accepts an
  integral float, as decision 0010 says.

### Releases

- Patch releases are cut automatically: when merged changes have moved
  master past the latest tag, a pull request gives the CHANGELOG its heading
  and bumps the declared version in the same commit, and the tag follows its
  merge. Minors and majors stay manual.

## v0.1.0 — 2026-10-03

### Packages

- **`contracts.vocab`: the constrained vocabulary of a data contract.** Named
  types that mean the same thing wherever they appear (a port, a duration, a
  host and port, an image digest, the enums of a log level and a TLS mode, and
  so on), each stating its constraint twice, as the expression Pkl enforces and
  as an annotation a generator reads, from the same named constants. The
  annotations are their own module (`Annotations.pkl`), so that a language
  generator that wants only the types need not generate them. A pattern has
  JSON Schema search semantics and refuses any value that contains a newline.
- **`contracts.fragments`: the shapes shared between services.** The listener,
  probes, log, drain, TLS, PostgreSQL, NATS (connection and consumer) and
  object-store configuration fragments, and the `platform` block of a service
  chart, written from the hand-written JSON Schemas of `truvity/policy` and
  keeping their `$id`s.
- **`contracts.templates`: what a service's own contract starts from.**
  `ServiceConfig`, the envelope every service's configuration carries
  (`probes`, `log`, `drain`), and `ChartValues`, the values of a service chart
  (`platform`, `config` and the image map).

### Tooling

- **Pkl 0.32.1, pinned.** `bin/pkl` downloads the release, verifies a pinned
  sha256 per platform, and runs it; it is temporary, until nixpkgs ships Pkl
  0.32 or newer.
- **The gate:** the vocabulary's probes against Pkl's own enforcement, an
  authoring lint, the worked example, and the packages built as a release will
  publish them and their metadata checked against the URIs GitHub will serve.

Nothing is released yet. The first release will be v0.1.0.
