# Packaging, naming and releasing

## One version

The whole repository has one version, `vX.Y.Z`, and the packages are released
together: a tag releases all three. The version is written once, in
`packages/Release.pkl`; each package's `PklProject` takes its metadata from
`Release.metadata`, and `hack/lint.sh` refuses a version typed anywhere else.

The version is also recorded in every `PklProject.deps.json` (a project
dependency is resolved to a package URI, which has the version in it), so a
version change is `packages/Release.pkl` plus `just resolve`; `just lint` fails
on a stale one.

## Package URIs are GitHub release paths

A package is not an OCI artifact. Pkl resolves `package://<host>/<path>@<version>`
by an HTTPS GET of `https://<host>/<path>@<version>` (the metadata), then of the
`packageZipUrl` the metadata names. These packages use GitHub releases for both,
and the version appears in the tag directory and after the `@`:

```
package://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.vocab@0.1.0
   GET https://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.vocab@0.1.0
   GET https://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.vocab@0.1.0.zip
```

So `baseUri` is `package://github.com/truvity/pkl-contracts/releases/download/v<version>/<name>`
and `packageZipUrl` is `https://github.com/truvity/pkl-contracts/releases/download/v<version>/<name>@<version>.zip`.
The metadata asset is named `<last path element>@<version>`, nothing more.

A release therefore carries twelve assets, four per package:

| asset | what |
|---|---|
| `contracts.vocab@0.1.0` | the package metadata (JSON, no extension) |
| `contracts.vocab@0.1.0.sha256` | its checksum |
| `contracts.vocab@0.1.0.zip` | the package |
| `contracts.vocab@0.1.0.zip.sha256` | its checksum |

(and the same for `contracts.fragments` and `contracts.templates`). This is the
shape Pkl's own `pkl-go` publishes its `pkl.golang` package in, behind a
redirect.

A consumer pins the exact URIs, and `pkl project resolve` records their
checksums in its `PklProject.deps.json`:

```pkl
dependencies {
  ["vocab"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.vocab@0.1.0" }
  ["fragments"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.fragments@0.1.0" }
  ["templates"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v0.1.0/contracts.templates@0.1.0" }
}
```

## How it is verified before a release exists

`just package` builds the packages with `pkl project package` exactly as a
release will publish them (into `.out/`), and `hack/package-check.sh` checks
what it produced: the three assets of each package are named `<name>@<version>`
as Pkl will ask for them, the metadata's `packageUri` and `packageZipUrl` point
into the release `v<version>`, the version is the repository's, every
dependency is a sibling package at the same version, and the zip's checksum is
the one the metadata records. The zips are reproducible: the same sources give
the same checksum.

That the URIs resolve is proved by serving `.out/` from a local web server that
answers `/truvity/pkl-contracts/releases/download/v0.1.0/<asset>` with a
redirect, as GitHub does, and pointing a consumer at it with
`--http-rewrite https://github.com/=http://127.0.0.1:<port>/`: Pkl asks for
the metadata and the zip at exactly the GitHub paths above, resolves the
dependency graph and evaluates a module that imports all three.

## What a release needs, and what is not yet built

There is no `release.yaml` or `auto-release.yaml` yet. The shared
`release-public.yaml` in `truvity/ci-workflows` runs goreleaser and publishes
charts, neither of which is here, so a release workflow for this repository
needs its own steps, on a tag `v*`:

1. refuse a tag that is not `v` and the version in `packages/Release.pkl`, and
   one that has no `## vX.Y.Z` heading in the CHANGELOG (component contract C5);
2. `just package`, which also runs the metadata check;
3. create the GitHub release for the tag and upload the twelve assets in
   `.out/` under their exact names (a name is part of the URI, so none may be
   renamed or zipped again);
4. smoke-test the published URIs: resolve a throwaway project that depends on
   the three, and evaluate a module that imports them, against github.com itself;
5. permissions `contents: write` only (the caller grants them: a reusable
   workflow cannot widen them), and `concurrency` that never cancels a publish.

Auto-release (a patch tag when only dependencies moved) stays off until a
release has been cut by hand. Minors and majors are always manual. Moving the
version is a pull request that changes `packages/Release.pkl`, runs
`just resolve`, and adds the CHANGELOG heading.

## Pinning Pkl

Pkl is pre-1.0 and breaks between minors, so a consumer pins the Pkl version as
well as the package versions, and a bump is a reviewed change. This repository
pins 0.32.1 in `bin/pkl`, which fetches the release asset for the host, checks a
pinned sha256 against it, caches it under
`${XDG_CACHE_HOME:-$HOME/.cache}/pkl-contracts/pkl/<version>/`, and runs it. It
is temporary: nixpkgs has only 0.31.1, and when it ships 0.32 or newer Pkl moves
back to `devbox.json` and `bin/pkl` is deleted. To bump meanwhile, change the
version and the four checksums together, and run `just vuln`, which compares
them with the digests GitHub publishes for that release.
