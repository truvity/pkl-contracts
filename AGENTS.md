# Instructions for an agent working here

Short on purpose: the order to read things in and the traps that are not
obvious from the files. Human-readable too.

## What this repository is

Pkl source, in nine packages released together: three that a contract is
written with (`contracts.vocab`, `contracts.fragments`, `contracts.templates`)
and six that read it (`contracts.model`, the reflection every generator shares,
and the generators `contracts.jsonschema`, `contracts.helm`,
`contracts.typescript`, `contracts.python` and `contracts.docs`), under
`packages/`. It contains no program: Pkl is a build tool and nothing here runs
at run time.

## Read first

1. [docs/authoring.md](docs/authoring.md): the rules a contract is held to.
2. [docs/packaging.md](docs/packaging.md): how a package is named, versioned and
   published, before you touch a `PklProject` or `packages/Release.pkl`.
3. The module you are changing, in full. Its doc comments are the reference.

## The gate

`just check` is the gate: tests, lint, the worked example, the packages built
and their metadata checked (and the generators run as packages), the leak
canary, the generated example against its committed copy, the compatibility
diff against the last release tag, and the cross-language conformance suite
(Kotlin is its own recipe, `conformance-kotlin`: Gradle is slow). It needs the network only for
the first run (devbox, and the Pkl release `bin/pkl` caches).

The root devbox is lean on purpose (just, lefthook, jq, editorconfig-checker,
Python for the package smoke test), because every CI job installs it. Go, Node,
uv, a JDK and Gradle live in `test/conformance/devbox.json` (with its own
`devbox.lock`); `just conformance` and `just conformance-kotlin` reach them
through `hack/conf.sh`, and devbox installs them on first use. To run something
by hand in that toolchain: `hack/conf.sh <command>`.

## Traps

- **Run Pkl as `bin/pkl`**, never a `pkl` from the machine. It is pinned to
  0.32.1 and verified; devbox's is older. Pkl is pre-1.0 and breaks between
  minors.
- **A project needs `--project-dir`.** `pkl eval x.pkl` does not find the
  `PklProject` of the directory it is in, and a module that imports `@vocab/...`
  fails with "no project found". Use `bin/pkl eval --project-dir <dir> <file>`,
  or a `just` recipe.
- **`PklProject.deps.json` is committed and must be current.** After a version
  or a dependency change run `just resolve`; `just lint` fails on a stale one.
  It records the version, so every release bump touches all of them.
- **The version is written once**, in `packages/Release.pkl`. Never type a
  version into a `PklProject` or a module; `hack/lint.sh` refuses it.
- **A constraint is written once, in the vocabulary.** A fragment that wants a
  new rule adds an alias to `Vocab.pkl` (with its `@A.Pattern`, `@A.Range` or
  `@A.Length`, from the same constant) and a property in `test/Showcase.pkl`. A
  rule that is only a bound is `@A.Range` or `@A.Length` on the property itself,
  over a vocabulary type; Pkl enforces it through `contracts.vocab.Check`, which
  the templates call in their `output`.
- **`@A.SetAtInstall` is nullable and required at once.** The Pkl type is `T?`
  (so the module of defaults can leave it out), the annotation makes every
  generator and the test loader require it. Never beside a default.
- **`X | Y?` is a trap.** Write `(X | Y)?`; the lint and the model refuse the
  other. And a literal union used in two places is an enum in the vocabulary.
- **`matches` is a full match; a pattern is a search.** Use the vocabulary's
  `search` helper, which also refuses every line break (`lineBreaks`: LF, CR, FF,
  VT, NEL, LS, PS) and is written with no `.`, `\s`, `\d`, `\w` or `\b`. `$` means different things in
  different engines, and the probes check that none is admitted.
- **Reflection cannot see a constraint.** That is why a constraint is stated as
  an annotation too. A lambda and an annotation that disagree fail
  `test/ProbesTest.pkl`; do not "fix" the test.
- **Annotations stay in `Annotations.pkl`.** A language generator that wants
  only the types would otherwise have to generate them.
- **`pkl format` is part of the gate.** Run `just fmt` before committing.
- **The templates do not evaluate bare.** `ServiceConfig` has a required field;
  evaluate it through the example or the tests.
- **A hand-written change to `examples/service/generated/` is a bug**; it is
  what the generators write for the example, and `just generate` rewrites it.
  `just generated` fails when it is stale.
- **Recognise annotations by name, never with `is`.** A class has one identity
  per package URI, and a consumer and a generator may each depend on the
  vocabulary through their own route. `packages/model/Model.pkl` matches by
  class and module name; `hack/package-smoke.sh` runs the generators as packages
  to keep it so.
- **A package whose content changed needs a new version.** `just package` is
  refused by Pkl for a version already published with other contents: the
  vocabulary, fragments and templates of a released version are frozen until the
  next release.
- **A module you hand to a generator must be inside the project directory.**
  `@dependency` is not a path, and a file outside the project cannot resolve its
  own imports. Use `--project-dir`, and a `projectpackage://` URI for a module
  inside a package.
- **A hand-written change to `examples/service/values.yaml` is a bug**; it is
  the render of `values.pkl`, regenerate it:
  `bin/pkl eval --project-dir examples/service -f yaml examples/service/values.pkl > examples/service/values.yaml`.

## Commits

Never name a real organisation, account, cluster or ticket in a commit message:
the repository is public, and a message cannot be edited after the push.
