# Authoring a contract

The rules a shape in these packages is held to, and why. They come from
decision 0010 of [truvity/policy](https://github.com/truvity/policy), which
says that a data contract is written once, in Pkl, and everything that
restates it is generated. Generators are not in this repository yet; the rules
are what they will rely on.

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
  before or after it, is refused. A generator must say the same in its output.
  *Checked by:* `hack/lint.sh` (no `matches`, one `Regex(`, the alias and its
  annotation name the same constant) and the probes.
- **A field with a default is optional.** Pkl cannot say both "required" and
  "has a default", and a default on a required field documented nothing.
- **`null` is not a value for an optional field.** An optional field is absent,
  or present with a value. Pkl's own evaluation is lenient about `null`, so a
  contract never writes one and a field is never both nullable and defaulted.
  *Checked by:* `hack/lint.sh` (no `= null`) and `test/LintTest.pkl` (no
  nullable field with a default).
- **An integral float is an integer.** `20.0` is valid where an integer is
  asked for, as JSON Schema says. Pkl's own `Int` does not accept it; a
  generated validator decides, and the vocabulary does not try to.

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
