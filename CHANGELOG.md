# Changelog

What changed for someone consuming these packages, newest first, one heading
per tag. The prose bullets are written for a consumer; the commit subjects under
them are the GitHub Release's own list. All packages are released together
under one version, so a heading covers all three.

## Unreleased

## v0.1.0 — 2026-10-03

### Packages

- **`contracts.vocab`: the constrained vocabulary of a data contract.** Named
  types that mean the same thing wherever they appear (a port, a duration, a
  host and port, an image digest, the enums of a log level and a TLS mode, and
  so on), each stating its constraint twice, as the expression Pkl enforces and
  as an annotation a generator reads, from the same named constants. The
  annotations are their own module (`Annotations.pkl`), so that a language
  generator that wants only the types need not generate them. A pattern has
  JSON Schema search semantics and refuses any value that contains a newline.
- **`contracts.fragments`: the shapes shared between services.** The listener,
  probes, log, drain, TLS, PostgreSQL, NATS (connection and consumer) and
  object-store configuration fragments, and the `platform` block of a service
  chart, written from the hand-written JSON Schemas of `truvity/policy` and
  keeping their `$id`s.
- **`contracts.templates`: what a service's own contract starts from.**
  `ServiceConfig`, the envelope every service's configuration carries
  (`probes`, `log`, `drain`), and `ChartValues`, the values of a service chart
  (`platform`, `config` and the image map).

### Tooling

- **Pkl 0.32.1, pinned.** `bin/pkl` downloads the release, verifies a pinned
  sha256 per platform, and runs it; it is temporary, until nixpkgs ships Pkl
  0.32 or newer.
- **The gate:** the vocabulary's probes against Pkl's own enforcement, an
  authoring lint, the worked example, and the packages built as a release will
  publish them and their metadata checked against the URIs GitHub will serve.

Nothing is released yet. The first release will be v0.1.0.
