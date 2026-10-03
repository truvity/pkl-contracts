# Changelog

What changed for someone consuming these packages, newest first, one heading
per tag. The prose bullets are written for a consumer; the commit subjects under
them are the GitHub Release's own list. All packages are released together
under one version, so a heading covers all of them.

## Unreleased

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
