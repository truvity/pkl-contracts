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
fields, an alias annotated `@A.RequiredWhen` or `@A.RequiredUnless` (the TLS
fragment's "a mode other than `off` needs the whole identity"; a class or a module
carries the same annotations with no alias, see "A rule across fields"), and a
bound on a property, which is the next section but one.

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

### Exclusive bounds

`@A.Range` has four ends: `min` and `max` (inclusive) and `exclusiveMin` and
`exclusiveMax` (not). "More than zero" is `exclusiveMin = 0`, which no inclusive
bound can say for a number:

```pkl
/// The share that may fail: more than none, at most all of it.
@A.Range { exclusiveMin = 0 }
ratio: V.Ratio = 0.05

/// A half-open interval: zero up to, and not including, one.
@A.Range { min = 0; exclusiveMax = 1 }
phase: Number?
```

The two ends of one side may both be given, and the stricter holds (a property's
`exclusiveMin = 0` over a type's `min = 0` is "greater than 0"). A range that
leaves no value is refused when the contract is reflected: a lower end above the
upper, or the two meeting where either is exclusive (`exclusiveMin = 1; max = 1`).
Pkl enforces it through `Check`, the JSON Schema says `exclusiveMinimum` and
`exclusiveMaximum`, zod `.gt()` and `.lt()`, pydantic `Field(gt=..., lt=...)`. The
probes try an exclusive bound AT it (refused) and one step either side of it: one
for an integer, a thousandth for a number.

## A map that refuses keys: `@A.DenyKeys`

A `Mapping` or an open object (`V.OpenObject`) whose keys are free except for a few
the platform owns takes `@A.DenyKeys` on the property:

```pkl
/// Labels put on every alert. `severity` is the rules' own.
@A.DenyKeys { keys { "severity"; "k8s_cluster_name" } }
alertLabels: Mapping<String, V.NonEmptyString> = new Mapping {}
```

The property is no longer the vocabulary alias it had, so it is written out in full
in zod and pydantic. JSON Schema says `propertyNames: { not: { enum: [...] } }`
(joined by `allOf` with the key type's own `propertyNames`, for a map keyed by a
pattern or an enum), zod a `refine` on the record, pydantic an `AfterValidator`, Pkl
`Check`. Keys are compared as written: a key is denied by its exact name.

## A count on a list or a map: `@A.Items` and `@A.Properties`

A `Listing` or `List` that must not be empty, or has a most, or holds no item
twice, takes `@A.Items` on the property; a `Mapping` or an open object whose number
of entries is bounded takes `@A.Properties`:

```pkl
/// The actions a policy may take, at least one, no action twice.
@A.Items { min = 1; unique = true }
actions: Listing<V.LogLevel>

/// Labels, at least one.
@A.Properties { min = 1 }
labels: Mapping<String, V.NonEmptyString>
```

They are written as annotations, and not as a constraint on the type
(`Listing<String>(length >= 1)`), because `pkl:reflect` erases a constraint: a
generator would see a plain list and drop the bound without a word. On an alias
they are the alias's own (the vocabulary's `NonEmptyObject` is `@A.Properties
{ min = 1 }`, which is how the items of a list can be required to be non-empty
objects); on a property they narrow the type it has (the larger least, the smaller
greatest, a set stays a set, and a bound that leaves no count is refused when the
contract is reflected). The bound applies to the list itself; the items of a list
get theirs from their own type.

Items are distinct (`unique = true`) when their JSON values are equal, whatever the
order of an object's keys. The numbers `1` and `1.0` are the same value; Pkl would
tell them apart, so a list of floats that holds both is a duplicate to a JSON
Schema validator and to zod, and not to Pkl's own `Check`.

| Rule | Pkl | JSON Schema | zod | pydantic | Docs |
|---|---|---|---|---|---|
| `Items.min`, `Items.max` | `Check` | `minItems`, `maxItems` | `.min()`, `.max()` | `Field(min_length, max_length)` | "at least N items" |
| `Items.unique` | `Check` | `uniqueItems` | `refine(distinct)`, keys sorted | `AfterValidator(_distinct)`, keys sorted | "items are distinct" |
| `Properties.min`, `.max` | `Check` | `minProperties`, `maxProperties` | `refine` on the number of own keys | `Field(min_length, max_length)` on the `dict` | "at least N properties" |

What a target cannot say is said here and not dropped silently: a zod type
(`z.infer`) and a TypeScript, Go or Kotlin type are shapes, so none carries a
count or distinctness (zod's validation does; `z.record` and `z.object` have no
size bound of their own, which is why that is a `refine`); the Go and Kotlin
types are the official generators' and validate nothing at all.

*Checked by:* the probes (the count at, under and over each bound, duplicates, the
same object with its keys in another order), `test/VocabTest.pkl`, the
`collections` and `union` fixtures of the conformance suite, and
`test/GeneratorsTest.pkl`.

## A string that must not contain something: `@A.NotPattern`

`@A.Pattern` says what a value looks like. `@A.NotPattern { regex; reason; invalid }`
says what it must never contain, with the reason a person is told: a password in a
connection URL, a TLS parameter that belongs to another setting. An alias carries one
for each rule, beside its `@A.Pattern`, and the Pkl constraint reads the same
expressions from one `local const` list, so the lambda and the annotations cannot
disagree (the probes try each `invalid` example). JSON Schema says `not: { pattern
}` for each, under `allOf` (the schema's own `not` is the line-break guard);
zod a `refine`; pydantic an `AfterValidator` with Python's `re`, where `pattern` is
pydantic's own engine, so the expressions are written in the subset both read. The
semantics are a search, like every pattern.

## A union is `anyOf`

A union of types (`V.NonEmptyString | Entry`, `Listing<X> | X`) is `anyOf` in JSON
Schema, `z.union` in zod and `X | Y` in pydantic, and never `oneOf`. Pkl accepts a
value that conforms to ANY member, and so must the schema. `oneOf` also refuses a
value that conforms to two members. Where the members cannot overlap (a string and
an object, a list and a scalar, objects with a different required key) the two
keywords accept the same documents, and a hand-written schema that says `oneOf`
there is matched, document for document, by the generated `anyOf`. Where they can
(two closed classes whose properties are all optional both admit `{}`) `oneOf`
would refuse what Pkl accepts, so it is not generated. A union of plain scalars is
`type: [...]`. Kotlin's generator refuses a union of a string type and string
literals, so the vocabulary spells such a type as one string alias
(`SecretRefKey`).

*Checked by:* `fixtures/union` (a name or a block, the empty object against two
closed classes, a document that is neither), `test/GeneratorsTest.pkl`.

## A rule across fields: `@A.RequiredWhen` and `@A.RequiredUnless`

"When the install only renders rules, nothing else is needed" is a rule across
fields, and across blocks. It is written once, on the class or the module that
holds the fields (or on an alias of such a class), as the condition and the paths
it requires:

```pkl
@A.RequiredUnless {
  property = "alerts.remote.enabled"
  `in` { true }
  require { "database.host"; "database.owner.passwordSecret"; "events.url" }
}
module my.Chart
```

- `@A.RequiredWhen`: every path of `require` must be present when the value at
  `property` is one of `in`.
- `@A.RequiredUnless`: every path must be present unless it is. A document that
  never says (the block, or the value, is absent) is therefore asked for them.
- A path is dotted names from the annotated class, through blocks (properties of a
  class type): `mode`, `alerts.remote.enabled`. `in` holds booleans for a boolean
  and strings for an enum (an alias or an inline union).
- "Present" is "not absent": the key is in the document. A class may carry several
  rules, and a document its own and its bases'.

Every path is resolved against the contract when it is generated, and what cannot
be is an error, never a rule that quietly never fires: a name that is no property,
a path through a list, a map or a scalar, a condition that is neither a boolean nor
an enum, a value of `in` the property cannot hold, an empty `require` or `in`.

**The limits, each one so that Pkl and a schema validator say the same thing.** A
JSON Schema validator fills no default in, and Pkl always has one, so the rule is
refused where a default would change its meaning:

- a required path ends at a property with no default (nullable, or set at install);
- the condition's property does not default to a value of `in`;
- no block on the way to either has a default of its own (a block Pkl builds from
  its class's defaults is fine: it has nothing the document lacks);
- a rule on a class whose own defaults would break it must not be on a block that a
  document may leave out (a default-complete one): pydantic and Pkl would refuse
  the document that omits it, which the schema and zod accept. Put the rule on a
  class that is not default-complete, or on a nullable block.

A condition on a string or a number that is not an enum is not supported; make it
an enum. A path through a `Listing` or `Mapping` is not supported either.

How each says it. JSON Schema: `allOf` of `if`/`then` (when) or `if`/`else`
(unless), the `if` a nested `properties` that `required`s every step down to the
value, so a document that leaves it out does not match, the other side the same
shape of `required` for each path, with shared steps in one `properties`. zod: one
`superRefine` that reads a path with `at` and reports each missing path at that
path. pydantic: a `model_validator(mode="after")` per class, named for it so that a
subclass adds to its base's. Pkl: `Check` reads the annotations of the value's
class and of every class it extends (a module's class carries the module's), so
`pkl eval` of a document or of a chart's `values.pkl` fails with the paths. An
alias's rule is Pkl's through the alias's own constraint, as it always was.

*Checked by:* the model (every case above is a generation error, `test/LintTest.pkl`),
`Check` against Pkl, and the conformance contract `conditions` (a module and a
class, a boolean and an enum, both branches and the absent one, nested required
paths, fixtures under `fixtures/conditions`).

## The vocabulary's newer types

- **Durations.** Each system that reads a duration has its own grammar, so each
  grammar is its own type, written as a string (Pkl's `Duration` renders as an object
  that no other language reads), and a field takes the type of the system that reads
  it. `Duration`: Go's `time.ParseDuration` subset (one or more `<number><unit>`
  parts, the number whole or `d.d`, the units `ns us µs μs ms s m h`; no sign, no
  bare `0`, no `.5s`). `GoDuration` is the earlier, narrower name, now a deprecated
  alias of it. `PromDuration`: `ms s m h d w y`, compound (`1h30m`, `1d`). `GatewayDuration`: GEP-2257,
  `^([0-9]{1,5}(h|m|s|ms)){1,4}$` (the order of units and a repeated unit are left to
  the API server). `KarpenterDuration`: `h m s`, compound; Karpenter's literal
  `Never` is a union the field declares itself. `KargoDuration`: Go's grammar.
  `Retention`: `30d`, `12M` (capital `M` is months; a lower-case `m` is minutes and
  is refused). There is **no empty variant** of any of them: every vocabulary type
  refuses `""` (a value that may be left out is absent, `PromDuration?`), and a
  consumer that reads an empty string as "none" must read an absent key the same,
  which is the rule of set-at-install blocks and of `Quantity?`.
- **Integers that mirror an upstream field.** `Seconds`, `Days`: at least one.
  Use them only where the upstream field is an integer named `...Seconds` or
  `...Days`; a field of our own takes a duration string. `OpenRatio` is a number
  strictly between zero and one; `Ratio` is zero to one, both included.
- **Names.** `DnsLabel`: an RFC 1123 label, at most 63 characters, never empty and
  never dotted. `DnsSubdomain`: dot-separated labels, at most 253 characters,
  never empty (`DnsName` is the looser, also non-empty since v0.5.0). `ProjectName`:
  2 to 32 characters, starts with a letter. `InstallName`: a `DnsLabel` of at most
  40, which leaves room for the suffixes a chart appends. A name that may be left
  out is `DnsLabel?`, absent rather than `""`; write the `?` on the property (an
  alias that is nullable is read as required, the same trap as `X | Y?`).
- **URLs by scheme.** `HttpsUrl`, `HttpUrl`, `NatsUrl` (`nats://` or `tls://`),
  `OciUrl` (`oci://` and a registry host). Each refuses white space and line
  breaks and needs a host; none is an RFC 3986 parser. `PostgresUrl` needs a host
  and carries no credential and no TLS setting (`NotPattern`, above).
- **Secrets: where they live, never the value.** `SecretRef` is the class
  `{ secretName: DnsSubdomain, key: SecretRefKey }`. A key is kebab-case
  (`SecretKey`, at most 253) or one an upstream fixes (`UpstreamSecretKey`: `tls.key`,
  `tls.crt`, `ca.crt`, `.dockerconfigjson`, the keys a runner controller's GitHub
  App secret reads, the AWS SDK's environment names): a closed list, where a new
  entry is a reviewed change that names the upstream that dictates it. `SecretRefKey`
  is the two as one type; `test/VocabTest.pkl` checks that it admits every
  member of the list. `SecretName` is a relative path of segments joined by `/`
  (`db/password`), none empty, `.` or `..`. `Reload` is `"file" | "restart"`.
- **`ApiVersion`**: `<product>.truvity.github.io/<kind>/v<N>`, N from 1 without a
  leading zero.
- **Earlier additions.** `StatusCodeList`: status code names joined by a bar,
  `INTERNAL|UNAVAILABLE`. `GatewayTlsMode`: `"off" | "permissive"`, a gateway
  listener's mutual TLS; not `TlsMode`, which keeps `strict`. `NonEmptyObject`: an
  open object with at least one key.

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
The same fact is stated as data for a tool: `x-set-at-install: true` on the
property in every JSON Schema (an annotation that no validator reads), and a
`Set at install` column of the reference that says `yes`. The prose stays, but
nothing needs to parse it.
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
declares for itself is explicit, and its property is optional.

## A block nobody sets is Pkl's default, when that is valid

A property of a class type that is not nullable and has no default of its own
(`resources: Resources`) still has one in Pkl: an instance built from the class's
own defaults, which an author may leave out. A document may leave it out too, if
and only if the class is **default-complete**: every property has a default, is
nullable, or is itself of a default-complete class type, recursively (a class
met again on the way down is not complete). Such a property is **optional**, and
its `default` is that instance, rendered whole, nested blocks included. A JSON
Schema `default` is an annotation: a validator does not fill it in, so the
property is out of `required` AND carries the default, which is what
`values.schema.json`, `values.yaml`, zod (`.default(...)`), pydantic
(`Field(default_factory=...)`) and the reference (not required, with its default)
all say. Pkl's own default for a `Listing`, a `Mapping` and a `Dynamic` is the
empty one, and is treated the same way.

A class stays required, and its property too, when it has a property with no
default that is not nullable, when it has a `@SetAtInstall` property (an install
must supply it, so Pkl's own instance would be wrong), when it has a block that is
itself not default-complete, or when it is an open object that must carry keys
(`V.Named`: the empty one is not valid, and Pkl cannot even be asked for its
default, so it is read as having none). What a class inherits counts, including
from a class that is not a document of its own.

*Checked by:* `test/ModelTest.pkl`, the conformance fixtures `blocks` and
`inherit` (a document that omits a default-complete block is accepted by every
validator, Pkl included; one that omits a block that is not is refused by all),
and `hack/defaults-check.py`, on the worked example.

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
Write `(X | Y)?`. A union inside type arguments, `Listing<X | Y>?`, is fine: the
`?` there binds to the whole `Listing`.

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
  "has a default", and a default on a required field documented nothing. A block
  whose class is default-complete (the section above) is optional the same way.
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
type (`Int | String`, or a string type and string literals), which is why the
platform block has no Kotlin class, and why a class in the vocabulary (`SecretRef`)
has no union in it.

A property whose name is not an identifier (`service-lib`) keeps its key in every
artifact. zod quotes it; pydantic declares the attribute under a name Python can
(`service_lib`, `global_` for a keyword, `f_2fa` for a leading digit) with
`Field(alias="service-lib")`, and validates the document's key. A Python name that
two properties would share is refused when the module is generated.

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
object closed that was open, items that must now be distinct, a pattern added or
changed, an `anyOf` alternative no longer covered. A property added, a type or
enum widened, a range relaxed and a pattern removed are compatible and only
reported.

**Known limitation: a changed pattern is breaking, whichever way it moved.** Whether
one regular expression is narrower than another is not decidable in general, so a
pattern that was only WIDENED (a unit added to a duration grammar) is reported
exactly like one that was tightened, and the CHANGELOG entry that declares a break
covers the whole report. The entry's text, not the check, then has to say which of
the reported changes narrow what a document may hold, and which do not.

**The vocabulary is probed type by type.** The worked example uses a handful of the
vocabulary's types, so a change to any other would go unseen. `hack/vocab-probe.pkl`
writes, from the vocabulary of each side of the comparison, a module with one
optional property for every alias and every class (`Port: V.Port?`), and the schemas
generated from it (`probe/vocab-probe.json`) are compared like the example's. A
narrowed pattern, range, length, enum or count of any alias is therefore
classified; an alias removed is a removed property; an alias added is a property
added (compatible). The probe is generated into `examples/service/.compat/`, which
is ignored and removed afterwards. The rules are in
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
