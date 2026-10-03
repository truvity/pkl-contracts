# Contributing

## Ground rules for a public repository

This repository is public and its history cannot be unpublished. Nothing in
it may name a real organisation, cluster, account, environment, team, person,
incident or internal ticket, in code, documents, tests, commit messages or
pull request text. Say "a consuming estate", "an environment", "the source
estate". Examples use neutral values (`example.com`, `registry.example.com`).

`hack/leak-canary.sh` catches the mechanical half of that and runs on every
commit through lefthook, and again in CI. It cannot read prose, so the rest is
a review rule. Quote a placeholder, never a real value, including in a commit
message: a message is as public as a file and cannot be edited after the push.

## What belongs here

A data contract: a shape that more than one party must agree on, written once
in Pkl (decision 0010 of
[truvity/policy](https://github.com/truvity/policy)). A service's own
configuration, and the chart that deploys it, live with the service and extend
the templates here; what lives here is what more than one of them shares.

- A rule a constraint needs that the vocabulary lacks goes in
  `packages/vocab/Vocab.pkl`, never in a fragment. There are no ad-hoc
  constraints; `hack/lint.sh` refuses one.
- A shape two services spell the same way is a fragment, with its `$id`.
- Every field is documented, and a field with a default is optional
  (`test/LintTest.pkl`).

[docs/authoring.md](docs/authoring.md) has the details and the reasons.

## Changing a package

A pull request that changes what a consumer must do adds its bullet to the
CHANGELOG under `## Unreleased`. A breaking bullet starts with **Breaking:** and
names the step to take. All packages are released together under one version,
so there is no per-package changelog.

A new alias gets a property in `test/Showcase.pkl`, so that the probes cover it.

## Tooling

Tools come from `devbox.json` through direnv. Never hand-roll a PATH; add a
missing tool with `devbox add <pkg>@<version>`. The one exception is Pkl,
which `bin/pkl` fetches and verifies at the pinned version until nixpkgs ships
0.32 or newer; run Pkl through it, never from your own PATH, so that you run
what CI runs.

`just check` is the gate and needs no credentials, no container and no
cluster. `just fmt` formats the Pkl files.

## Commits and pull requests

Small, reviewable pull requests. Pull requests merge by rebase, so a branch
carries no merge commits.
