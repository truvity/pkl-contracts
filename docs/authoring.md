# Authoring a contract

The rules a shape in these packages is held to, and why. They come from
decision 0010 of [truvity/policy](https://github.com/truvity/policy), which
says that a data contract is written once, in Pkl, and everything that
restates it is generated. The generators are in this repository, and the rules
are what they rely on.

Everything here is checked mechanically. Where, is named at each rule.

## There are no ad-hoc constraints

Every constraint comes from the vocabulary, `packages/vocab/Vocab.pkl`: a
constrained alias (`Port`, `GoDuration`, `HostPort`, `ImageDigest`, an enum
such as `LogLevel`). A field that needs a rule the vocabulary lacks adds the
alias there, where it is reviewed once and used by every contract.

*Checked by:* `hack/lint.sh`, on the source: no `Regex(`, no constrained type
(`String(length >= 1)`) and no `typealias` outside the vocabulary. The one
exception is a rule across fields, an alias annotated `@A.RequiredWhen` (the
TLS fragment's "a mode other than `off` needs the whole identity"), because a
generator can read that annotation.

## A constraint is written twice, and cannot drift

Pkl's reflection does not expose a constraint, only that one exists. So an
alias states its constraint as the expression Pkl enforces, and again as an
annotation a generator reads (`@A.Range`, `@A.Length`, `@A.Pattern`), both
built from the same named constants (`portMin`, `durationRe`). Small literals
(`>= 1`) are written twice; the kind of the constraint is too.

What covers the remainder is the probes, `test/Probes.pkl`: generated from the
annotations, one set per alias (at and just outside a range, at and under a
minimum length, a pattern's own valid and invalid examples, every enum member
and a non-member, a value of the wrong type), and run against Pkl's own
enforcement in `test/ProbesTest.pkl`. An alias whose expression and annotation
disagree fails there.

A new alias therefore needs three things: the alias with its annotation, a
property of that type in `test/Showcase.pkl` (the test refuses an alias with
none), and, for a pattern, valid and invalid examples in its `@A.Pattern`.

## The semantic rules

Pkl, JSON Schema and each language's validators disagree at the edges, and the
contract picks one meaning:

- **A pattern is a search, and refuses a newline.** A JSON Schema `pattern`
  matches anywhere; Pkl's `String.matches` is a full match, so an alias written
  with it accepts less than its schema says. The vocabulary writes every pattern
  through one helper, `search`, which has search semantics. Regular-expression
  engines also disagree on whether `$` matches before a final `\n`, so no
  pattern may rely on either answer: `search` refuses any value that contains a
  newline, and the probes check that each valid example, with a newline added
  before or after it, is refused. A generator must say the same in its output:
  JSON Schema pairs each `pattern` with `not: { pattern: "\\n" }`, zod with a
  refinement, pydantic with a validator.
  *Checked by:* `hack/lint.sh` (no `matches`, one `Regex(`, the alias and its
  annotation name the same constant) and the probes.
- **A field with a default is optional.** Pkl cannot say both "required" and
  "has a default", and a default on a required field documented nothing.
- **`null` is not a value for an optional field.** An optional field is absent,
  or present with a value. Pkl's own evaluation is lenient about `null`, so a
  contract never writes one and a field is never both nullable and defaulted.
  zod's `.optional()` and JSON Schema's types refuse `null`; pydantic needs a
  validator that runs first and refuses it; the test loader (`test/Load.pkl`),
  which asks Pkl "is this document valid", refuses it too.
  *Checked by:* `hack/lint.sh` (no `= null`) and `test/LintTest.pkl` (no
  nullable field with a default).
- **An integral float is an integer.** `20.0` is valid where an integer is
  asked for, as JSON Schema says. Pkl's own `Int` does not accept it; a
  generated validator decides, and the vocabulary does not try to. JSON Schema
  says `integer`, zod `.int()` (JavaScript has one number type), pydantic reads an
  integer through a validator that turns a float with no fractional part into
  one (strict mode would refuse it, and lax mode would also take `"3"`).

## Every field is documented

A field's doc comment is its reference documentation; a generator publishes it.
A class, an alias and a module are documented the same way.

*Checked by:* `test/LintTest.pkl`, by reflection, over every module in the
packages. The test also refuses a module it does not know, so a new one is
added to the list in the test.

## Annotations are a module of their own

`Annotations.pkl` holds the annotation classes and nothing else. A generator for
a language that wants only the types (Go, Kotlin) then need not generate them:
`pkl-codegen-kotlin` otherwise demands a generated `pkl:base`.

## A shape that is a document carries its `$id`

A class, alias or module annotated `@A.Schema` is a standalone JSON Schema
document, and its `$id` is the one the hand-written schema it was written from
has, so that during the shadow phase a generated schema and its hand-written
original are compared document by document. A shape that is only a part of one
(the TLS peer, a probe's timings) has no `$id`.

## Templates

`ServiceConfig` is the envelope every service's configuration carries: `probes`
(required), `log` and `drain`. A service's own contract `extends` it and adds
what it needs; a listener is not in the envelope, because a job that exits has
none. `ChartValues` is the values of a service chart: `platform`, `config` and
the image map. A chart's own contract extends it and narrows `config` to its
service's contract and `images` to the components it has. The worked example in
`examples/service` does both, and is rendered by `just example`.

## Not here yet

A fragment, template or alias for a shape that nothing in the policy repository
has written down is not invented here. These are missing for that reason, and
are added when their source shape exists:

- `LambdaArgs`, `SystemdUnit` and `Secrets` fragments;
- `LambdaValues` and `UnitValues` templates.

## Generating

Each generator is a package with a `pkl:Command` entry point, `Generate.pkl`,
and takes the modules of a contract as arguments. Reflection cannot enumerate a
module graph, so the modules are named: a module that is itself a document, and
each class or alias in one that is annotated `@Schema`, becomes a document, and
so does every document those refer to (a fragment, a base).

```console
$ pkl run --project-dir . package://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.jsonschema@<version>#/Generate.pkl \
    -- --dir schemas Config.pkl
```

| Package | Entry point | Writes (into `--dir`) |
|---|---|---|
| `contracts.jsonschema` | `Generate.pkl` | `<key>.json`, one document per shape; the key is the tail of the `$id` after `/schemas/` |
| `contracts.jsonschema` | `Compat.pkl` | a report of what changed between two directories of schemas (`--before`, `--after`) |
| `contracts.helm` | `Generate.pkl` | `values.schema.json` (platform and config, every document embedded under `$defs` so that Helm validates offline), `README.md` (a values table), and `values.yaml` when the module amends the chart |
| `contracts.typescript` | `Generate.pkl` | `contract.zod.ts`: a zod schema and a type for every shape |
| `contracts.python` | `Generate.pkl` | `contract_pydantic.py`: pydantic v2 models |
| `contracts.docs` | `Generate.pkl` | `reference.md`: fields, types, defaults, constraints, secrets |

For Helm, give the chart's values module (the one that `amends` the chart
contract): the contract gives the schema and the table, the values give
`values.yaml`, and a default that breaks a rule fails when the module is
evaluated. The generated `values.yaml` of `examples/service` is the render
`just example` compares with.

Go and Kotlin come from the official generators, behind `hack/codegen.sh go ...`
and `hack/codegen.sh kotlin ...` (versions and a digest pinned there). Their types
are shapes: none of the contract's constraints survives into a Go struct or a
Kotlin class, so a service validates against the generated JSON Schema, and the
type says only what the fields are. Kotlin cannot generate a module with a union
type (`Int | String`), which is why the platform block has no Kotlin class.

The secrets column of the reference lists a field that names a secret, by the
contract's own convention (a name ending in `Env`, or a `Secret` class), because
the vocabulary has no annotation for it yet.

`just generate` writes the worked example's artifacts to
`examples/service/generated`; `just generated` regenerates and fails if they
differ, so a change to a generator or to the contract cannot leave them stale.

A generator package must not recognise the vocabulary's annotations with `is`:
a class has one identity per package URI, so a consumer that depends on the
vocabulary as a package would show a generator that depends on it by path none.
`packages/model/Model.pkl` matches by class and module name, and
`hack/package-smoke.sh` runs the generators as packages to keep it so.

## Compatibility

`just compat` generates the schemas of the example from the last release tag
(in a temporary worktree, with this checkout's generators laid over it) and
compares them with this checkout's. A change is breaking when a document valid
before may be invalid now, or a new demand is made: a property or document
removed, a property newly required, a narrowed type, enum, range or length, an
object closed that was open, a pattern added or changed (whether one regular
expression is narrower than another is not decidable in general, so a changed
pattern is flagged and a reviewer overrules it), an `anyOf` alternative no longer
covered. A property added, a type or enum widened, a range relaxed and a pattern
removed are compatible and only reported. The rules are in
`packages/jsonschema/Compatibility.pkl` and are tested on synthetic pairs in
`test/CompatTest.pkl`. A breaking change that is meant passes when the
CHANGELOG's `## Unreleased` section has an entry that begins `- **Breaking`.

## Conformance

`just conformance` is the proof that the generators say the same thing. It
generates every artifact for the contracts in `test/conformance/contract` and
asks every validator about every fixture (`test/conformance/fixtures`), every
probe the vocabulary's annotations generate, and every chart's generated values
against its generated values schema (compiled alone, so that a reference that
needed fetching would fail):

| Validator | What it is |
|---|---|
| `ajv`, `santhosh`, `pyjsonschema`, `networknt` | four JSON Schema engines (ECMAScript, RE2, Python `re`, Java) on the generated schemas |
| `zod`, `pydantic` | the generated TypeScript and Python |
| `go`, `kotlin` | the schema's verdict and the document decoded into the official generator's type (types are shapes, the schema is the validator; Kotlin's classes are bound from what Pkl evaluates) |
| `pkl` | Pkl's own enforcement, through `test/Load.pkl`: the oracle |

They must all give the verdict the fixture's name says (`ok-` accepted, `bad-`
refused). The Kotlin half is `just conformance-kotlin`, a recipe of its own because
Gradle makes it the slow part.

### What the engines still disagree on

The rules above settle `\n`. The engines also disagree on the other characters
a pattern's `.`, `\s` and `$` treat as a line break or as white space: Java (so
Pkl) lets `$` match before a final `\r`, `\u0085`, `\u2028` or `\u2029`, and
`.` does not match them; ECMAScript's `.` does not match `\r`, `\u2028` or
`\u2029`; Python's and RE2's `.` match all but `\n`; `\s` is Unicode-aware in
ECMAScript and Python (a no-break space is white space) and ASCII in Java and
RE2, which also differ over `\v`. `test/conformance/edge` holds six such
strings, and the suite reports, without failing on them, that the engines
split. They are findings, not accepted behaviour: closing them takes a
vocabulary decision (refuse every line-break character as `search` refuses
`\n`, and spell `\s` and `.` as explicit classes), which is a change to the
published vocabulary and is not made here.
