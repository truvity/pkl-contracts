# Instructions for an agent working here

Short on purpose: the order to read things in and the traps that are not
obvious from the files. Human-readable too.

## What this repository is

Pkl source, in three packages released together: `contracts.vocab`,
`contracts.fragments`, `contracts.templates`, under `packages/`. It contains no
generator (the next piece of work) and no program: Pkl is a build tool and
nothing here runs at run time.

## Read first

1. [docs/authoring.md](docs/authoring.md): the rules a contract is held to.
2. [docs/packaging.md](docs/packaging.md): how a package is named, versioned and
   published, before you touch a `PklProject` or `packages/Release.pkl`.
3. The module you are changing, in full. Its doc comments are the reference.

## The gate

`just check` is the gate: tests, lint, the worked example, the packages built
and their metadata checked, and the leak canary. It needs the network only for
the first run (devbox, and the Pkl release `bin/pkl` caches).

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
  `@A.Length`, from the same constant) and a property in `test/Showcase.pkl`.
- **`matches` is a full match; a pattern is a search.** Use the vocabulary's
  `search` helper, which also refuses a newline. `$` means different things in
  different engines, and the probes check that none is admitted.
- **Reflection cannot see a constraint.** That is why a constraint is stated as
  an annotation too. A lambda and an annotation that disagree fail
  `test/ProbesTest.pkl`; do not "fix" the test.
- **Annotations stay in `Annotations.pkl`.** A language generator that wants
  only the types would otherwise have to generate them.
- **`pkl format` is part of the gate.** Run `just fmt` before committing.
- **The templates do not evaluate bare.** `ServiceConfig` has a required field;
  evaluate it through the example or the tests.
- **A hand-written change to `examples/service/values.yaml` is a bug**; it is
  the render of `values.pkl`, regenerate it:
  `bin/pkl eval --project-dir examples/service -f yaml examples/service/values.pkl > examples/service/values.yaml`.

## Commits

Never name a real organisation, account, cluster or ticket in a commit message:
the repository is public, and a message cannot be edited after the push.
