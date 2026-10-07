# Changelog

What changed for someone consuming these packages, newest first, one heading
per tag. The prose bullets are written for a consumer; the commit subjects under
them are the GitHub Release's own list. All packages are released together
under one version, so a heading covers all of them.

## Unreleased

Everything here is additive: a contract that uses none of it generates exactly
the output it did, apart from the one case listed last. Together they let a
contract say what its consumers used to patch into the generated schema.

### Features

- **`@A.MultiLine`: a pattern that may span lines.** Every `pattern` is paired with
  a guard that refuses the seven line breaks, and stays so by default. On an alias,
  or on a property whose type has a `@A.Pattern`, the annotation drops the guard
  for that node: the JSON Schema keeps the `pattern` and loses
  `not: { pattern: <line breaks> }`, zod its `noLineBreak` refinement, pydantic its
  `_no_line_break` validator. For a PEM bundle matched by an unanchored marker.
  The model refuses it on a type with no pattern.
- **`@A.Nullable`: a property that admits JSON `null`, and is still optional.** On
  a property typed `T?`. JSON Schema is `type: [<t>, "null"]` where the type is a
  keyword (with a `null` member added to an `enum`) and
  `anyOf: [<schema>, { type: "null" }]` where it is a `$ref` or already an `anyOf`;
  zod `.nullable()`; pydantic `| None`, with the key listed in the class's
  `_nullable`, which the "null is not a value" validator of the base model reads.
  The loader and `Check` accept `null` for it. Refused beside `@A.Required` and on
  a type that is not `T?`.
- **`@A.OneOfValues { values = List(...) }`: a set of numbers.** JSON Schema `enum`
  beside `type: integer` or `number` (with a `null` member when the property is
  also `@A.Nullable`); a zod `refine`; a pydantic `AfterValidator`; the reference
  says "one of ...". On an alias, or on a property, where it narrows the type's own
  set and combines with `@A.Range`; Pkl enforces a property's through `Check`.
- **`@A.Required`: required, no default, nothing else.** For a list, an open object
  or a number that a document must carry, where Pkl would give a `Listing` or a
  `Dynamic` an empty default and `T?` is optional. It is `@A.SetAtInstall` without
  the claim that an install supplies it: in `required`, no `default`, no
  `x-set-at-install` key, "Required" (not "Set at install") in the reference and the
  values table, left out of the defaults, and no demand that a string be non-empty.
  `@A.SetAtInstall` is unchanged and stays the spelling for a value only an
  install can give.
- **Helm: a chart's own `@Def` definitions are in the root `$defs`.** Until now only
  the `@Schema` documents were, so a `$ref: "#/$defs/<name>"` to a definition used
  in the chart's own values dangled. They are written by name, beside the documents
  by `$id`. A chart with neither no longer gets an empty `$defs`.
- Fixtures: the `declared` contract (57 documents, good and bad, for the four
  annotations) and the `defs` chart, across every validator.

### Changed output

- The generated pydantic module gains two helpers (`_one_of`, and a `_nullable`
  class variable on the base model), and the Helm values schema omits an empty
  `$defs`. Neither changes what any document is accepted or refused as, so the
  compatibility check has nothing to report; `examples/service/generated/py` is
  regenerated.

## v0.5.0 — 2026-10-07

### Breaking

- **Breaking: `Bytes` no longer admits an upper-case `K`.** `5K` is not a Kubernetes
  quantity (the SI kilo is a lower-case `k`); the pattern is now
  `^[0-9]+(Ki|Mi|Gi|Ti|k|M|G|T)?$`. A value that was `5K` becomes `5k` (or `5Ki`).
- **Breaking: `DnsName` no longer admits the empty string.** A field that may be
  left out is `DnsName?`, absent, as every vocabulary type has it. Prefer the new
  `DnsSubdomain`, which also bounds each label and the whole and refuses a hyphen
  next to a dot.
- **Breaking: `PostgresUrl` checks more than the scheme.** It needs a host and
  refuses, as `NotPattern` rules, a password in the user info, a `password=`,
  `sslpassword=` or `passfile=` query parameter (also with a percent-encoded name,
  `pass%77ord=`), and `sslmode=`, `sslrootcert=`, `sslcert=` and `sslkey=`: the
  credential is a `SecretRef` and transport security a `TlsMode`, neither part of
  the address. A URL that carried `?sslmode=require` must drop it. The fragment
  `Postgres` and the worked example follow.
- **Widened, and reported by the compatibility check as breaking all the same:
  `GoDuration` and `PromDuration`.** The check cannot tell a widened pattern from
  a tightened one and reports every changed pattern as breaking, so these two
  appear in its report beside the real narrowings above. `GoDuration` is now a
  deprecated alias of the new `Duration` and admits Go's whole `time.ParseDuration`
  subset (compound parts, a decimal such as `1.5s`, `μs`), of which everything it
  admitted before is a member. `PromDuration` admits compound values and the units
  `ms`, `d`, `w` and `y` (`1h30m`, `1d`, `500ms`) as well as `s`, `m` and `h`.

### Features

- **A count on a list or a map: `@A.Items { min; max; unique }` and
  `@A.Properties { min; max }`.** On a property (laid over its type, like `Range`
  and `Length`) or on an alias. JSON Schema says `minItems`, `maxItems`,
  `uniqueItems`, `minProperties` and `maxProperties`; zod `.min()`, `.max()` and a
  `refine` for the distinct items and for the count of a record or an object;
  pydantic `Field(min_length=..., max_length=...)` and an `AfterValidator` for the
  distinct items; Pkl enforces them through `Check`; the reference lists them; the
  probes try the bound and one step either side. Items are distinct when their JSON
  is equal, whatever the order of an object's keys. A constraint written on the
  type itself (`Listing<String>(length >= 1)`) cannot be read by a generator
  (reflection erases it), which is why it is an annotation.
- **`@A.NotPattern { regex; reason; invalid }`: a string must NOT match.** A JSON
  Schema `not: { pattern }` for each rule under `allOf`, a zod `refine`, a pydantic
  `AfterValidator`; the reference lists each with its reason. `PostgresUrl` is the
  first user.
- **A union of types is `anyOf`, and says so.** It always was; the choice over
  `oneOf` is now documented in the JSON Schema generator (Pkl accepts a value that
  is any member, so the schema must, and where the members cannot overlap, a string
  and a block, the two keywords accept the same documents). Fixtures: a list whose
  items are a name or a block, and two closed classes that the empty object
  conforms to.
- **The decided vocabulary.** Durations, each in the grammar of the system that
  reads it: `Duration` (Go's `time.ParseDuration` subset), `GatewayDuration`
  (GEP-2257), `KarpenterDuration`, `KargoDuration` and `Retention` (`30d`, `12M`).
  `Seconds` and `Days`, for a field that mirrors an upstream integer. `OpenRatio`
  (strictly between 0 and 1). Names: `DnsSubdomain`, `ProjectName`, `InstallName`.
  URLs: `HttpsUrl`, `HttpUrl`, `NatsUrl`, `OciUrl`. Secrets: `SecretKey`,
  `UpstreamSecretKey` (a closed list of the keys an upstream fixes), `SecretRefKey`
  (the two as one string type, because the Kotlin code generator refuses their
  union), the class `SecretRef { secretName; key }`, `SecretName`, `Reload`.
  `ApiVersion`. `NonEmptyObject`, an open object with at least one key.
- **The compatibility check probes every vocabulary type.** `hack/compat.sh`
  generates, from each side's own vocabulary, a module with one property for every
  alias and class (`hack/vocab-probe.pkl`) and compares the schemas generated from
  it, so a change to any type, or a type removed, is classified, not only the ones
  the worked example uses. `uniqueItems` added is breaking. Known limitation,
  documented: a changed pattern is breaking whichever way it moved.

### Fixes

- **The authoring lint no longer mistakes `Listing<X | Y>?` for a union with a
  nullable member.**
- **The test loader reads a union of classes as the member whose properties the
  document's keys are**, not the first class.
- **Stale documentation.** The README and `docs/packaging.md` pinned `v0.1.0`,
  said there were no consumers and no release workflow; they describe the current
  state.

## v0.4.1 — 2026-10-04

### Fixes

- **`OtelProtocol`'s documentation states the right reason for leaving out
  `http/json`.** It said the Go SDK's HTTP exporter always sends protobuf; it
  does not (`otlptracehttp` and `otlpmetrichttp` can send JSON). The reason is
  the Go exporter selection most services use (`autoexport`), which refuses
  `http/json`, and the Python and TypeScript exporters, which are fixed to
  HTTP/protobuf. The type is unchanged.

## v0.4.0 — 2026-10-04

### Features

This minor adds vocabulary and annotation features and narrows one vocabulary type
(see the breaking entry below); a contract that does not use `OtelProtocol` generates
the same schemas as before.

- **Breaking: `OtelProtocol` no longer admits `http/json`.** It is now
  `"grpc" | "http/protobuf"`. The Go SDK's `autoexport` (v0.71.0) refuses any other
  value at startup (`errInvalidOTLPProtocol`) and `otlptracehttp` always sends
  `application/x-protobuf`; the Python and TypeScript exporters are fixed to
  HTTP/protobuf, so a contract that allowed `http/json` allowed a value that
  crashed the service. A consumer that set `http/json` (a `telemetry.protocol` or
  any field of type `OtelProtocol`) must use `http/protobuf` or `grpc`.
- **Exclusive bounds: `@Range { exclusiveMin; exclusiveMax }`.** "Greater than zero"
  is `exclusiveMin = 0`; either end may be exclusive and combined with the other
  side's `min` or `max`, and a range that leaves no value (`exclusiveMin = 1; max = 1`)
  is refused when the contract is reflected. Pkl enforces it through `Check`, JSON
  Schema says `exclusiveMinimum` and `exclusiveMaximum`, zod `.gt()` and `.lt()`, pydantic
  `gt` and `lt`; the probes try the bound itself and one step either side.
- **A rule across fields through blocks: `@RequiredWhen` and the new
  `@RequiredUnless`.** On a class, a module (a document, or a chart's values) or an
  alias of a class; the condition and the required paths are dotted names through
  blocks (`alerts.remote.enabled` decides, `database.owner.passwordSecret` is
  required), a boolean or an enum condition, `in` holding booleans or strings. Every
  path is resolved against the contract when it is generated, and an unknown one, a
  path through a list or a scalar, a condition that is not a boolean or an enum, or one
  whose default would make Pkl and a schema validator disagree is a generation
  error. JSON Schema is `if`/`then` (when) or `if`/`else` (unless) over nested
  `properties` and `required`; zod a `superRefine`; pydantic a `model_validator`
  per class; Pkl enforces it in `Check`, from the annotations of the value's class
  and its bases. A chart's values schema carries the module's rules too (it
  carried none before). A flat `@RequiredWhen` on an alias is unchanged in the
  schema, and zod and pydantic say it through the same code as the new ones.
- **`@DenyKeys { keys }` on a map or an open object.** The keys a `Mapping` or a
  `V.OpenObject` property must not carry: `propertyNames: { not: { enum: [...] } }`,
  a zod `refine`, a pydantic `AfterValidator`, `Check` for Pkl. The compatibility
  diff now reports `propertyNames` added as breaking.
- **New vocabulary types.** `PromDuration` (`^[0-9]+(s|m|h)$`, Prometheus durations;
  no empty form, a field that may be left out is `PromDuration?`), `DnsLabel` (an
  RFC 1123 label of at most 63 characters; an optional one is `DnsLabel?`),
  `StatusCodeList` (`^[A-Z_]+(\|[A-Z_]+)*$`, status code names joined by a bar) and
  `GatewayTlsMode` (`"off" | "permissive"`, distinct from `TlsMode`).
- **The reference lists a class's rules.** A class or alias with rules across fields
  has a "Rules across fields" list in the generated reference.

## v0.3.1 — 2026-10-03

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
