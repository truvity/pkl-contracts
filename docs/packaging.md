# Packaging, naming and releasing

## One version

The whole repository has one version, `vX.Y.Z`, and the packages are released
together: a tag releases all of them (nine). The version is written once, in
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
package://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.vocab@<version>
   GET https://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.vocab@<version>
   GET https://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.vocab@<version>.zip
```

So `baseUri` is `package://github.com/truvity/pkl-contracts/releases/download/v<version>/<name>`
and `packageZipUrl` is `https://github.com/truvity/pkl-contracts/releases/download/v<version>/<name>@<version>.zip`.
The metadata asset is named `<last path element>@<version>`, nothing more.

A release therefore carries thirty-six assets, four per package:

| asset | what |
|---|---|
| `contracts.vocab@<version>` | the package metadata (JSON, no extension) |
| `contracts.vocab@<version>.sha256` | its checksum |
| `contracts.vocab@<version>.zip` | the package |
| `contracts.vocab@<version>.zip.sha256` | its checksum |

(and the same for every other package). This is the
shape Pkl's own `pkl-go` publishes its `pkl.golang` package in, behind a
redirect.

A consumer pins the exact URIs, and `pkl project resolve` records their
checksums in its `PklProject.deps.json`:

```pkl
dependencies {
  ["vocab"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.vocab@<version>" }
  ["fragments"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.fragments@<version>" }
  ["templates"] { uri = "package://github.com/truvity/pkl-contracts/releases/download/v<version>/contracts.templates@<version>" }
}
```

## How it is verified before a release is published

`just package` builds the packages with `pkl project package` exactly as a
release will publish them (into `.out/`), and `hack/package-check.sh` checks
what it produced: the four assets of each package are named `<name>@<version>`
as Pkl will ask for them, the metadata's `packageUri` and `packageZipUrl` point
into the release `v<version>`, the version is the repository's, every
dependency is a sibling package at the same version, and the zip's checksum is
the one the metadata records. The zips are reproducible: the same sources give
the same checksum.

That the URIs resolve is proved by serving `.out/` from a local web server that
answers `/truvity/pkl-contracts/releases/download/v<version>/<asset>` with a
redirect, as GitHub does, and pointing a consumer at it with
`--http-rewrite https://github.com/=http://127.0.0.1:<port>/`: Pkl asks for
the metadata and the zip at exactly the GitHub paths above, resolves the
dependency graph and evaluates a module that imports all three.

`hack/package-smoke.sh` then does what a consumer does with the generators:
it serves `.out/` that way, resolves a throwaway project that depends on the
vocabulary, fragments and templates as packages, runs every generator as a
package (`pkl run package://...#/Generate.pkl`) on the example's contract, and
compares the output with the committed copy. It exists because the tests
cannot see a class that has one identity per package URI: a generator that
recognised the vocabulary's annotations with `is` wrote nothing for such a
consumer.

## Releasing

A release is two things in order: a pull request that names it, and a tag.

1. **The heading pull request** changes `packages/Release.pkl` to the new version,
   runs `just resolve` (every `PklProject.deps.json` records the version) and gives
   `CHANGELOG.md` its `## vX.Y.Z` heading, in place of `## Unreleased`. While the
   change is under review, `just compat` also accepts a breaking entry under that
   heading.
2. **The tag `vX.Y.Z`** on the commit that declares the version. Pushing it runs
   `.github/workflows/release.yaml`, which calls the shared `release-pkl` workflow
   of the organisation's CI repository: it refuses a tag that is not `v` and the
   version in `packages/Release.pkl`, or that has no `## vX.Y.Z` heading in the
   CHANGELOG; runs `just package` (which also runs the metadata check); creates the
   GitHub release and uploads the thirty-six assets under their exact names (a name
   is part of the URI, so none is renamed or zipped again); and resolves each
   package from github.com itself, evaluating a module that imports the vocabulary,
   the fragments and the templates, to prove a consumer can. Its token is
   `contents: write` and nothing wider.

Between a release and the next, the packages differ from the tag's, and Pkl refuses
to package a version already published with other contents. `just package` knows:
while the declared version is released and `packages/` differs from its tag, the
comparison is skipped and the CHANGELOG must say what is Unreleased instead. A change
to a package therefore never bumps the version itself; the heading pull request does.

Minors and majors are always cut by hand. The patch tag can be cut by
`.github/workflows/auto-release.yaml` when merged changes have moved master past the
latest release: it is off unless the repository variable `AUTO_RELEASE` is `true` and
the token issuer is configured, it only ever cuts patches, and its heading pull
request carries the version bump (`version-bump-command` rewrites
`packages/Release.pkl` and re-resolves the projects).

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
