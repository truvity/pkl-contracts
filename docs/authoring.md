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
(`String(length >= 1)`), no `typealias` and no `@A.Pattern` outside the
vocabulary. Two exceptions, both data a generator can read: a rule across
fields, an alias annotated `@A.RequiredWhen` (the TLS fragment's "a mode other
than `off` needs the whole identity"), and a bound on a property, which is the
next section but one.

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

## A bound on a property: `@A.Range` and `@A.Length`

A field whose only rule is a bound (a minimum of 600, a length of at least 16, a
port that may be zero) is not worth an alias. It takes the vocabulary type it
would have anyway and a **property annotation**:

```pkl
/// How long a signed link lives, in seconds.
@A.Range { min = 600 }
linkSeconds: V.PositiveInt = 3600

/// A generated password.
@A.Length { min = 16 }
password: V.NonEmptyString?

/// A port; zero asks for any free one.
@A.Range { max = 65535 }
port: V.NonNegativeInt?
```

The set is fixed (`@A.Range` for a number, `@A.Length` for a string; a
`@A.Pattern` stays the vocabulary's) and the generators read them exactly as
they read an alias's. The bound is laid over the type's own and **intersected**
with it, because Pkl enforces both: a property can tighten what its type says,
never loosen it, and a bound that leaves no value is refused when the contract is
reflected. The type is then written out in full in zod and pydantic (a reference
to the alias would lose the bound).

*How Pkl enforces it.* Pkl has nowhere to put the rule: a constraint belongs to a
type, and a type cannot read the annotation of the property it types; a class
cannot carry an invariant. So `contracts.vocab.Check` does it by reflection: it
walks a value, reads the annotations on the properties of every object in it, and
compares each property's value with them, failing with the path and the bound.
`ServiceConfig` and `ChartValues` call it in their `output`, so `pkl eval` or
`pkl eval -f yaml` of a document, or of a chart's `values.pkl`, fails on a value
outside its bound; the Helm generator renders that same output; the test loader
(the conformance oracle) calls it on every document. A module that extends
neither writes `output { value = Check.checked(module) }`.

*Checked by:* the probes, which run the same boundaries (at, just below and just
above each bound) for a property as for an alias, against Pkl; and the loader in
the conformance suite.

## Set at install

A value that only an install can give (a bucket name, a database host, the
Secret that holds a password) is **required** by the schema, and **absent** from
the chart's defaults. A default of `""` would be a lie to a non-empty type and
would let an install that forgot it fail somewhere else, later. The contract says
it with an annotation on a property that is a non-empty string and nullable in
Pkl:

```pkl
/// The bucket. Every install names its own.
@A.SetAtInstall
bucket: V.NonEmptyString?
```

Nullable, so that the module that holds the defaults need not set it (and the
rendered `values.yaml` leaves it out); `@A.SetAtInstall`, so that every generator
reads it as required: it is in the JSON Schema's `required` (and the chart's
values schema), the zod and pydantic field is not optional, the reference and the
values table say "Set at install". The test loader refuses a document without it.
It is never combined with a default, and on a string it needs a type that refuses
`""`, so that the requirement is of a real value.

*Checked by:* the model, when it reflects the contract (an annotation on a type
that is not nullable, on a string that may be empty, or beside a default is an
error); `hack/defaults-check.py`, which reads the generated schemas, values,
zod, pydantic and reference and fails on a set-at-install property that is
optional, defaulted or present in `values.yaml`; and the conformance fixtures.

## A default may be an object

A default is any value, an object included: an open object (`V.OpenObject`) with
Kubernetes' resource requests in it, or a class given a default of its own. The
JSON Schema `default`, `values.yaml`, zod, pydantic and the reference carry it
whole. Reflection cannot tell an explicit default from the one Pkl gives every
object, so the model compares them: a default that differs from what the class
declares for itself is explicit, and its property is optional. A default that is
exactly the class's own is none, and such a property stays required, because its
fields carry their own defaults.

*Checked by:* `hack/defaults-check.py`, on the worked example.

## One literal union, one place

An inline union of literals (`"http/protobuf" | "grpc"`) is fine where it is used
in ONE place. When the same union, or one that overlaps it, is used in two places,
it is one concept written twice, and it becomes an enum in the vocabulary
(`OtelProtocol`, `LogLevel`), where it has one name and one list of members. Check
which members every consumer accepts before choosing the list: the vocabulary's
is the union of what they pass through.

*Checked by:* the model, which refuses to generate for modules that have two
such places (the message names both); and `test/LintTest.pkl` over this
repository's modules.

## A nullable union is parenthesised

`X | Y?` is `X | (Y?)`: the `?` binds to the last member alone. Reflection sees a
union with a nullable member, not a nullable union, and a field written that way
is **required** in every generated artifact while Pkl accepts `null` for it.
Write `(X | Y)?`.

*Checked by:* `hack/lint.sh` on the source, and the model, which refuses the
property or alias when it reflects it.

## The semantic rules

Pkl, JSON Schema and each language's validators disagree at the edges, and the
contract picks one meaning:

- **A pattern is a search, and refuses every line break.** A JSON Schema
  `pattern` matches anywhere; Pkl's `String.matches` is a full match, so an alias
  written with it accepts less than its schema says. The vocabulary writes every
  pattern through one helper, `search`, which has search semantics. Regular-
  expression engines also disagree on which characters `$` matches before and
  `.` stops at, so no pattern may rely on either answer: `search` refuses any
  value that contains LF, CR, FF, VT, NEL (U+0085), LS (U+2028) or PS (U+2029),
  and the probes check that each valid example, with each of them added after it
  (and the first with each before it), is refused. A generator must say the same
  in its output, with the guard its target spells: JSON Schema pairs each
  `pattern` with `not: { pattern: "[...]" }` over the seven, zod with a
  refinement, pydantic with a validator.
  *Checked by:* `hack/lint.sh` (no `matches`, one `Regex(`, the alias and its
  annotation name the same constant) and the probes; `test/LintTest.pkl` checks
  that the vocabulary's list and the generators' are the same.
- **A pattern spells no `.`, `\s`, `\d`, `\w` or `\b`.** The engines read them
  differently (Unicode-aware in ECMAScript and Python, ASCII in Java and RE2;
  `\v` means two things). A pattern uses an explicit class: `[0-9]`, `[^\n]` for
  "any character" (a line feed is the one escape they all read alike, and no
  other line break reaches a pattern), and the vocabulary's white-space class
  (space, tab, no-break space and the Unicode space separators: ECMAScript's `\s`
  without the line breaks, so the widest and strictest reading). Characters above
  U+00FF are written in the pattern itself, because no escape for them is common
  to RE2 and the rest.
  *Checked by:* `test/LintTest.pkl`, which scans every `@A.Pattern`, and the
  probes.
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
`examples/service` does both, and is rendered by `just example`. The `service-lib`
key (Helm puts one in the values it validates for every sub-chart) is
`Fragments.ServiceLib`: a product chart that does not extend `ChartValues` uses
it from there.

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
refused). The suite's toolchain (Go, Node, uv, a JDK, Gradle) is its own devbox,
`test/conformance/devbox.json`, so that the other recipes do not install it;
the recipes enter it through `hack/conf.sh`. The Kotlin half is `just conformance-kotlin`, a recipe of its own because
Gradle makes it the slow part.

### Line breaks and white space

Engines used to disagree beyond `\n`: Java (so Pkl) let `$` match before a final
`\r`, NEL, LS or PS, and `.` did not match them; ECMAScript's `.` did not match
`\r`, LS or PS; `\s` was Unicode-aware in ECMAScript and Python (a no-break space
is white space) and ASCII in Java and RE2, which also differ over `\v`. The
suite reported six such strings and did not fail on them. They are closed, not
accepted: the vocabulary refuses every line break and spells white space and
"any character" as explicit classes (the two rules above), and the six strings
are now ordinary fixtures (`fixtures/showcase`) that every engine must refuse.
There is no informational tier; a new split fails the run, and is closed the same
way.
