# pkl-contracts

Pkl packages for data contracts: the vocabulary, the shared fragments and the
templates from which a service's configuration schema and a chart's values are
written once.

| Package | What it is | Published as |
|---|---|---|
| `contracts.vocab` | the constrained aliases (a port, a duration, a host and port, an image digest, the enums) and the annotations a generator reads | a GitHub release asset, `package://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.vocab@<version>` |
| `contracts.fragments` | the shapes shared between services: listener, probes, log, drain, TLS, PostgreSQL, NATS, object store, and the `platform` block of a chart | the same, `contracts.fragments` |
| `contracts.templates` | what a service's own contract starts from: `ServiceConfig` and `ChartValues` | the same, `contracts.templates` |

| `contracts.model` | the intermediate form every generator reads: a contract's modules reflected into classes, properties, types and constraints | the same, `contracts.model` |
| `contracts.jsonschema` | **generator:** JSON Schema draft 2020-12, one document per shape, composed by `$ref`; and the compatibility diff between two sets of schemas (`Generate.pkl`, `Compat.pkl`) | the same, `contracts.jsonschema` |
| `contracts.helm` | **generator:** a chart's `values.schema.json` (platform and config composed), `values.yaml` defaults and a README values table | the same, `contracts.helm` |
| `contracts.typescript` | **generator:** TypeScript types and zod schemas | the same, `contracts.typescript` |
| `contracts.python` | **generator:** pydantic v2 models | the same, `contracts.python` |
| `contracts.docs` | **generator:** a Markdown reference: fields, types, defaults, constraints, secrets | the same, `contracts.docs` |

All of them are released together under one version. Each generator is a
`pkl:Command` (`Generate.pkl`): run it with `pkl run` on the modules of a
contract ([docs/authoring.md](docs/authoring.md#generating)). Go and Kotlin
come from the official generators, `pkl-gen-go` and `pkl-codegen-kotlin`,
pinned behind one script, `hack/codegen.sh`.

## Who it is for

People who write a **data contract**: the shape of a service's configuration
file, of a chart's values, or of a deployment fragment, where more than one
party must agree on it. It assumes the estate's rule that such a shape is
written once, in Pkl, and that everything restating it (JSON Schema, a type in
each language, reference documentation) is generated from that one source:
decision 0010 of [truvity/policy](https://github.com/truvity/policy).

It generates, and installs nothing: Pkl is a build-time tool and is never
present at run time. The generated types are shapes; the generated JSON Schema
is what a service validates against. It does not provide Pkl
itself either; pin the Pkl version you build with, because Pkl is pre-1.0 and
breaks between minors (this repository builds with 0.32.1).

## The model

Three nouns.

- **The vocabulary** is a set of named, constrained types that mean the same
  thing wherever they appear. There are no ad-hoc constraints anywhere else: a
  field that needs a rule the vocabulary lacks adds it there. Each type states
  its constraint twice, as the expression Pkl enforces and as an annotation a
  generator reads, from the same constants; probes keep the two honest.
- **A fragment** is a shape two services spell the same way: how a listener, a
  log level, a database, a broker or an object store is described. Each is one
  JSON Schema document, with the `$id` of the hand-written schema it was written
  from, and the `platform` block of a chart is one too.
- **A template** is what a service's own contract extends. `ServiceConfig` is
  the envelope every service's configuration carries (`probes`, `log`, `drain`);
  `ChartValues` is a service chart's values (`platform`, `config`, `images`).

Four rules decide the places where Pkl, JSON Schema and each language's
validators disagree: a pattern is a search and refuses a newline, a field with a
default is optional, `null` is never a value for an optional field, and an
integral float is an integer. [docs/authoring.md](docs/authoring.md) has them
with their reasons.

## Install and a worked example

Pin the packages the contract is written with (the three below), and the generators you run (`contracts.jsonschema` and the others, as `pkl run package://...#/Generate.pkl` or as dependencies), at the exact version, in your `PklProject`, and run
`pkl project resolve` to record their checksums:

```pkl
amends "pkl:Project"

dependencies {
  ["vocab"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.vocab@0.1.0" }
  ["fragments"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.fragments@0.1.0" }
  ["templates"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.templates@0.1.0" }
}
```

A service's configuration extends the envelope and adds what it needs, using the
fragments:

```pkl
@A.Schema { id = "https://example.com/echo/schemas/config.json"; title = "echo" }
module example.Config

extends "@templates/ServiceConfig.pkl"

import "@fragments/Fragments.pkl" as F
import "@vocab/Annotations.pkl" as A

/// The listener the service's own traffic is served on.
listen: F.Listen

/// The database the service keeps its records in.
postgres: F.Postgres
```

A chart's values extend `ChartValues`, narrowing `config` to that contract
(`examples/service/Chart.pkl`), and its defaults are written in the same typed
language, so a wrong one fails when the module is evaluated, naming the rule:

```pkl
amends "Chart.pkl"

config {
  listen { address = ":8080" }
  probes { address = ":7070" }
  postgres { url = "postgres://echo@db.example.com:5432/echo?sslmode=require" }
}

images {
  echo {
    registry = "registry.example.com"
    repository = "example/echo"
    tag = ""
    digest = ""
  }
}
```

```console
$ pkl eval --project-dir . -f yaml values.pkl
config:
  probes:
    address: :7070
  listen:
    address: :8080
  postgres:
    url: postgres://echo@db.example.com:5432/echo?sslmode=require
    maxConnections: 10
images:
  echo:
    registry: registry.example.com
    repository: example/echo
    tag: ''
    digest: ''
```

`--project-dir` is needed: Pkl does not find a `PklProject` by itself. The
files are in [`examples/service`](examples/service), which depends on the
packages by path so that it builds from this checkout; `just example` renders it
and compares the result with the committed `values.yaml`.

## Consumers

None yet outside this repository. The surface is a Pkl project depending on the
three packages and running the generators; the first consumers will be the
repositories that build JSON Schemas, chart values
schemas and language types from a contract, and the repositories that author
one.

## Neighbours

- [truvity/policy](https://github.com/truvity/policy): the decision that makes
  this repository (0010), and the contracts and hand-written schemas the
  fragments were written from. The hand-written schemas stay authoritative
  until a later decision switches.
- [truvity/ci-workflows](https://github.com/truvity/ci-workflows): the shared
  CI this repository's workflows call.
- [apple/pkl](https://github.com/apple/pkl): the language. Its release is what
  `bin/pkl` fetches.

## Documentation

- [docs/authoring.md](docs/authoring.md): the rules a contract is held to, and
  how each is checked.
- [docs/packaging.md](docs/packaging.md): the one version, the package URIs, the
  release assets, how they are verified before a release exists, and what a
  release workflow will need.
- The doc comments in the modules are the reference for every alias, class and
  field.

## The rule that makes this repository public

Mechanism only. A contract describes a shape, never an estate: no real
organisation, cluster, account, environment, hostname or ticket appears in
code, documents, examples, commit messages or pull request text; examples use
`example.com`. `hack/leak-canary.sh` enforces the mechanical half on every
commit and in CI, and reading the rest is a review rule
([CONTRIBUTING.md](CONTRIBUTING.md)).

## Status

Nine packages exist and build, and are tested on Pkl 0.32.1: the vocabulary
with its probes, nine fragments (listener, probes, log, drain, TLS, PostgreSQL,
NATS, NATS consumer, object store) and the platform block, the two templates,
and the generators: JSON Schema, Helm values, TypeScript with zod, Python with
pydantic, and a Markdown reference, plus a compatibility diff of two sets of
schemas. The first three are released as v0.1.0; the generators ship with the
next release, so until then they are run from this checkout.

Generated, and agreed on: the conformance suite (`just conformance`) asks nine
validators about every fixture and probe (four JSON Schema engines, zod,
pydantic, Go and Kotlin decoded through the official generators' types plus the
schema, and Pkl itself), and they must all agree. One known gap is reported
there and not failed: the engines differ on characters other than `\n` that
a pattern's `.`, `\s` and `$` treat as line breaks or white space
([docs/authoring.md](docs/authoring.md#what-the-engines-still-disagree-on)).

What is not here: the fragments `LambdaArgs`, `SystemdUnit` and `Secrets` and
the templates `LambdaValues` and `UnitValues`, which wait for a source shape; a
Go or Kotlin generator of our own (the official ones are used, and their types
are shapes only); and a release workflow of our own beyond what
[docs/packaging.md](docs/packaging.md) describes. Pkl is fetched by `bin/pkl`
rather than devbox until nixpkgs ships 0.32 or newer.

## Development

```bash
devbox shell     # dev environment
just check       # tests, lint, example, packages, leak canary, generated, compat, conformance: must pass before a PR
just generate    # regenerate examples/service/generated after a change to a generator or a contract
just fmt         # format the Pkl files
just resolve     # after a version or dependency change
```

Run Pkl as `bin/pkl`, never from your own PATH. `just --list` shows every recipe.
The worked example's render is the one committed file to regenerate by hand:
`bin/pkl eval --project-dir examples/service -f yaml examples/service/values.pkl > examples/service/values.yaml`.

## Releasing

All packages are released together under one version, `vX.Y.Z`, written once in
`packages/Release.pkl`. The first release will be v0.1.0. Releases are manual
for now, and minors and majors always will be; there is no release workflow and
auto-release is not armed ([docs/packaging.md](docs/packaging.md)).

## Licence

MIT. See [LICENSE](LICENSE).
