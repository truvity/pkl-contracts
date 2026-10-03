# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately via
[GitHub Security Advisories](https://github.com/truvity/pkl-contracts/security/advisories/new).

Do NOT open a public issue for security vulnerabilities.

## Supported Versions

Only the latest release is supported with security updates.

## What is in scope

This repository publishes Pkl packages: a vocabulary of constrained types,
shared configuration fragments and the templates a service's own contract
starts from. Reports that matter most:

- A constraint that admits what its documentation says it refuses (a pattern
  that accepts a newline, a range that is off by one), because a contract built
  on it validates a value it should have refused.
- A default that is unsafe for anyone who follows it.
- Anything in `bin/pkl`, which downloads and runs a binary: a checksum that
  does not match the asset it names, or a way to run something that was not
  verified.

Nothing here runs at run time: Pkl is a build tool, and what ships from a
contract is JSON Schema and ordinary types. This repository holds no
credentials, and its CI runs on hosted runners with no access to any private
infrastructure. A finding that depends on a particular deployment belongs with
that deployment's owner.
