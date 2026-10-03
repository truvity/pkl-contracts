<!-- Generated from a contract by contracts.docs. Do not edit. -->

# Contract reference

## Documents

| Document | Title | `$id` |
|---|---|---|
| `config` | echo | `https://example.com/echo/schemas/config.json` |
| `fragments/drain` | drain | `https://github.com/truvity/policy/schemas/fragments/drain.json` |
| `fragments/listen` | listen | `https://github.com/truvity/policy/schemas/fragments/listen.json` |
| `fragments/log` | log | `https://github.com/truvity/policy/schemas/fragments/log.json` |
| `fragments/platform` | platform | `https://github.com/truvity/policy/schemas/fragments/platform.json` |
| `fragments/postgres` | postgres | `https://github.com/truvity/policy/schemas/fragments/postgres.json` |
| `fragments/probes` | probes | `https://github.com/truvity/policy/schemas/fragments/probes.json` |
| `service` | service | `https://github.com/truvity/policy/schemas/service.json` |

## Types

The constrained types the fields use. A pattern is a search, and never matches a string with a line break in it.

| Type | Kind | Constraints | Description |
|---|---|---|---|
| `HostPort` | string | matches `^[^\t \xA0  -   　]*:[0-9]{1,5}$`, never a line break | host:port as the configuration contract spells it today. It does NOT bound the port at 65535, because the hand-written pattern does not; `Port` is the stricter vocabulary a contract may move to. |
| `PostgresUrl` | string | matches `^postgres(ql)?://`, never a line break | A PostgreSQL connection URL, by its scheme. |
| `NonEmptyString` | string | at least 1 character | A string of at least one character. |
| `PositiveInt` | integer | at least 1 | A whole number of at least one. |
| `OpenObject` | open |  | Kubernetes' own object shape, passed through unchanged. |
| `PromDuration` | string | matches `^[0-9]+(s\|m\|h)$`, never a line break | A duration in Prometheus' spelling: whole seconds, minutes or hours, `90s`, `15m`, `2h`. Narrower than `GoDuration`, which also admits `ns`, `us` and `ms`, units Prometheus' `for`, `interval` and range selectors do not read. Never empty: a duration that may be left out is `PromDuration?`, absent, and not a `""` that means "none" (the rule of every vocabulary type: an optional field is absent or has a value). |
| `StatusCodeList` | string | matches `^[A-Z_]+(\\|[A-Z_]+)*$`, never a line break | A list of status code names joined by a bar, `INTERNAL\|UNAVAILABLE`: upper-case letters and underscores (a gRPC code's spelling), the shape a regular expression alternation of them takes in a query. At least one code, and no empty member. |
| `DnsLabel` | string | at most 63 characters; matches `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`, never a line break | An RFC 1123 DNS label, as Kubernetes spells a namespace: lower-case letters, digits and hyphens, starting and ending with a letter or a digit, at most 63 characters. Never empty, and never dotted (`DnsName` is the dotted one). A field that may be left out (a namespace, a cluster name) is `DnsLabel?`, absent, and not a `""`. |
| `GatewayTlsMode` | one of `off`, `permissive` |  | How a gateway's listener treats mutual TLS: `off` serves cleartext only, `permissive` serves both. Not `TlsMode`: a gateway has no `strict` (a listener that refuses every cleartext client is a different decision, taken by its own setting), so the value must not be spellable. |
| `LogLevel` | one of `debug`, `info`, `warn`, `error` |  | The lowest level a service writes. |
| `ImageDigest` | string | matches `^(sha256:[0-9a-f]{64})?$`, never a line break | An image digest, or empty when there is none. |
| `PullPolicy` | one of `Always`, `IfNotPresent`, `Never` |  | When a container image is pulled. |
| `NonNegativeInt` | integer | at least 0 | A whole number of at least zero. |
| `RootedPath` | string | matches `^/`, never a line break | A path that starts at the root, the root itself included. |
| `AbsPath` | string | matches `^/[^\n]+`, never a line break | An absolute path that is not the root. |
| `OtelProtocol` | one of `grpc`, `http/protobuf` |  | The protocol OpenTelemetry exports over. `http/json` is absent on purpose: it is in the OpenTelemetry specification, but the Go SDK's exporter selection (`autoexport`) refuses it at startup and its HTTP exporter always sends protobuf, and the Python and TypeScript exporters are fixed to HTTP/protobuf, so a contract that admitted it would admit a value that stops a service from starting. |
| `EnvName` | string | matches `^[A-Za-z_][A-Za-z0-9_]*$`, never a line break | The name of an environment variable. |
| `Named` | open | has the keys `name` | An open object that must carry `name`. |
| `Mounted` | open | has the keys `name`, `mountPath` | An open object that must carry `name` and `mountPath`. |

## Classes

### `ServiceConfig`

The envelope every service's configuration carries. A service extends this
module and adds its own properties beside it:

    extends "package://.../contracts.templates@<version>#/ServiceConfig.pkl"

What is in here is what EVERY component has, including a job that exits and
a consumer that answers nothing: somewhere to report health, a log level,
and a shutdown budget. A listener is not one of those, so it is not here.

The module is open so that a service can extend it, and its classes are
closed, so a key that is not declared is refused: a typo must fail.

Document `https://github.com/truvity/policy/schemas/service.json`.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `probes` | Probes | yes |  |  | The health listener. Required: every component can be probed. |  |
| `log` | Log | no |  |  | Structured logging. Absent means the service's own default level. |  |
| `drain` | Drain | no |  |  | The shutdown budget. Absent means the service's own default, which is only correct if nothing external is counting. |  |

### `Config`

An example service that serves one listener and keeps a record in a
PostgreSQL database. Its configuration is the service envelope (probes, log,
drain) and what it needs of its own.

Extends `ServiceConfig`.

Document `https://example.com/echo/schemas/config.json`.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `listen` | Listen | yes |  |  | The listener the service's own traffic is served on. |  |
| `postgres` | Postgres | yes |  |  | The database the service keeps its records in. |  |
| `retention` | ConfigRetention | no | `{"days": 30, "keepForever": false}` |  | How long what the service keeps is kept. A default that is a class, which differs from the class's own in `days`. |  |
| `labels` | OpenObject | no | `{"team": "platform"}` |  | Labels put on what the service writes. A default that is an open object. |  |
| `archive` | ConfigArchive | no |  |  | Where the service archives what it served. Absent means it does not. |  |
| `alerts` | ConfigAlerts | no |  |  | Alerting on the service's own error budget. Absent means no rules. |  |
| `client` | ConfigClient | no | `{"timeoutSeconds": 5, "retry": {"attempts": 3, "idempotentOnly": true}}` |  | How the service calls out. Every field of it has a default, and so has the `retry` block inside it, so the whole block may be left out of a document. |  |

### `Listen`

A TCP listener. `address` is a host:port the service binds; an empty host binds every interface.

Document `https://github.com/truvity/policy/schemas/fragments/listen.json`.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `address` | HostPort | yes |  | matches `^[^\t \xA0  -   　]*:[0-9]{1,5}$`, never a line break | host:port, for example ":8080" or "127.0.0.1:8080". |  |

### `Postgres`

A PostgreSQL connection. The URL carries no password: it names the environment variable that does.

Document `https://github.com/truvity/policy/schemas/fragments/postgres.json`.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `url` | PostgresUrl | yes |  | matches `^postgres(ql)?://`, never a line break | A connection URL without credentials, for example postgres://user@host:5432/dbname?sslmode=require. |  |
| `passwordEnv` | NonEmptyString | no |  | at least 1 character | **Names a secret.** The NAME of the environment variable holding the password. Unset means the connection needs none. |  |
| `maxConnections` | PositiveInt | no | `10` | at least 1 | Pool size for this instance. Sized against the server's limit divided by the number of instances, not guessed. |  |

### `ConfigRetention`

How long what the service keeps is kept.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `days` | PositiveInt | no | `7` | at least 1 | Days before it is deleted. |  |
| `keepForever` | boolean | no | `false` |  | Keep it until somebody deletes it, whatever `days` says. |  |

### `ConfigArchive`

Where the service archives what it served.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `bucket` | NonEmptyString | yes |  | at least 1 character | **Set at install.** The bucket. Every install names its own, so the defaults leave it out and the schema requires it. | yes |
| `prefix` | NonEmptyString | no | `"echo/requests"` | at least 1 character | What every object's key begins with. |  |
| `batchSeconds` | PositiveInt | no | `60` | at least 10 | How often a batch is written, in seconds: not more often than every ten. |  |

### `ConfigAlerts`

Alerting rules for the service. Every threshold is a number or a duration with
a rule of its own, and the receiver is needed unless the install only renders
the rules for another cluster to evaluate.

Rules across fields:

- Unless `remote.enabled` is `true`, `receiver.url` are required.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `remote` | ConfigAlertsRemote | no |  |  | Where the rules are evaluated. Absent means in this cluster. |  |
| `holdFor` | PromDuration | no | `"10m"` | matches `^[0-9]+(s\|m\|h)$`, never a line break | How long a condition holds before it fires. |  |
| `errorRatio` | Ratio | no | `0.05` | greater than 0 and at most 1 | The share of requests that may fail before it fires: more than none, at most all of them. |  |
| `latencySeconds` | number | no | `0.5` | greater than 0 | The slowest a request may be, in seconds: more than zero. |  |
| `codes` | StatusCodeList | no | `"INTERNAL\|UNAVAILABLE"` | matches `^[A-Z_]+(\\|[A-Z_]+)*$`, never a line break | The status codes that count as failures, joined by a bar. |  |
| `namespace` | DnsLabel | no |  | at most 63 characters; matches `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`, never a line break | The namespace the rules are evaluated in. Absent means the install's own. |  |
| `tls` | GatewayTlsMode | no | `"off"` |  | How the rules' gateway treats mutual TLS. |  |
| `alertLabels` | map of NonEmptyString | no | `{}` | never has the keys `severity` | Labels put on every alert. `severity` is the rules' own and may not be set here. |  |
| `receiver` | ConfigAlertsReceiver | no |  |  | Who is told. Needed unless the rules are only rendered. |  |

### `ConfigAlertsRemote`

Where the rules are evaluated.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `enabled` | boolean | no | `false` |  | Whether the install only renders the rules, for another cluster to evaluate. |  |

### `ConfigAlertsReceiver`

Who is told.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `url` | NonEmptyString | no |  | at least 1 character | The receiver's URL. |  |

### `ConfigClient`

How the service calls out.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `timeoutSeconds` | PositiveInt | no | `5` | at least 1 | How long one call may take, in seconds. |  |
| `retry` | ConfigRetry | no | `{"attempts": 3, "idempotentOnly": true}` |  | What is tried again. |  |
| `proxy` | NonEmptyString | no |  | at least 1 character | A proxy to go through; absent means none. |  |

### `ConfigRetry`

What is tried again, and how often.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `attempts` | PositiveInt | no | `3` | at least 1 | How many attempts in all. |  |
| `idempotentOnly` | boolean | no | `true` |  | Whether a call that is not safe to repeat is repeated too. |  |

### `Probes`

The health listener. Separate from the service's own traffic, so that readiness is answerable when the service's listener is saturated, and so that a probe is not reachable from outside.

Document `https://github.com/truvity/policy/schemas/fragments/probes.json`.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `address` | HostPort | yes |  | matches `^[^\t \xA0  -   　]*:[0-9]{1,5}$`, never a line break | host:port for /health/live and /health/ready. |  |

### `Log`

Structured logging. One level for the whole service: per-package levels are deliberately not part of the contract.

Document `https://github.com/truvity/policy/schemas/fragments/log.json`.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `level` | LogLevel | no | `"info"` |  | The lowest level that is written. |  |

### `Drain`

How long the service may take to finish in-flight work after SIGTERM. It is one number shared with whatever deploys the service: the grace period granted to the process and the pre-stop delay before it are derived from this, so that a draining process is never killed at the moment it would have finished.

Document `https://github.com/truvity/policy/schemas/fragments/drain.json`.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `seconds` | PositiveInt | no | `20` | at least 1 | Seconds to finish in-flight work. Unset means the service's own default, which is only correct if nothing external is counting. |  |

### `Platform`

What the platform provides one component of a service chart: the image, the replicas, the account it runs as, how it is probed, where its identity is mounted, which secrets reach it as environment variables, and how it exports telemetry. The shape of the `platform` block of a chart's values, read by the library chart (decision 0009 of the policy repository). Nothing here is the service's own configuration: that is the chart's `config` block, which is the service's schema and nothing else.

Document `https://github.com/truvity/policy/schemas/fragments/platform.json`.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `image` | PlatformImage | no |  |  | Where the image is. A digest when there is one; a tag only when there is not. Left out, the library reads the chart's own top-level `images.<component>`, the map a release stamps and refuses to publish with an empty digest. |  |
| `imagePullPolicy` | PullPolicy | no |  |  | Defaults to IfNotPresent. |  |
| `replicas` | NonNegativeInt | no |  | at least 0 | Defaults to 1. A service that must survive a rollout runs more than one: one instance cannot be replaced without a gap whatever the strategy says. |  |
| `strategy` | PlatformStrategy | no |  |  | The rolling update. The defaults make a rollout gapless: the replacement is READY before the incumbent is touched. |  |
| `resources` | OpenObject | no |  |  | Kubernetes' own resource requirements. Open: it is passed through unchanged. |  |
| `podSecurity` | PlatformPodSecurity | no |  |  | Who the process is. Every field defaults to 65532, the unprivileged user the runtime images run as; `fsGroup` is the one that matters, because a CSI driver writes what it mounts owned by root. |  |
| `serviceAccount` | PlatformServiceAccount | no |  |  | The account this component runs as. EVERY component has its own, always; `default` is refused. The library grants nothing: annotations are where a platform binds the account to rights outside the cluster, and which mechanism does that is the platform's. |  |
| `service` | PlatformService | no |  |  | A component that listens has a Service on the ports of its own `config.listen`; one that does not has none. |  |
| `probes` | PlatformProbes | no |  |  | How the component is probed, on the listener its own `config.probes` binds. Liveness is nothing but the process: a probe that checks a dependency restarts a healthy process and makes an outage worse. |  |
| `drain` | PlatformDrain | no |  |  | The service's own shutdown budget is `config.drain.seconds`; the library derives the grace period from it and this delay, so the three numbers cannot disagree. |  |
| `tls` | PlatformTls | no |  |  | Where the platform mounts the workload identity. The files the component's own `config.tls` names must be under `mountPath`; the render refuses a file that is not. |  |
| `telemetry` | PlatformTelemetry | no |  |  | OpenTelemetry's own environment variables (decision 0006 of the policy repository): they leave the chart as variables, never as configuration keys. No endpoint means do not export. |  |
| `secrets` | map of PlatformSecret | no |  |  | **Names a secret.** The environment variables that carry SECRETS, and nothing else (decision 0002 of the policy repository): variable name to the Secret and key its value comes from. The configuration file names the VARIABLE; the value never appears in a values file or a render. |  |
| `env` | list of PlatformEnvVar | no |  |  | Environment a platform CLIENT LIBRARY reads (a database client's connection variables, for example), never the service's own configuration: a service takes no other structural input than its file (decision 0002 of the policy repository). A secret does not belong here; declare it in `secrets`. |  |
| `volumes` | list of Named | no |  |  | Extra pod volumes, in Kubernetes' own shape, for what a client library mounts (a trust bundle, a password file). Open: passed through unchanged. |  |
| `volumeMounts` | list of Mounted | no |  |  | The mounts for `volumes`, in Kubernetes' own shape. |  |
| `config` | PlatformConfig | no |  |  | How the file reaches the process. The path is ONE argument or ONE environment variable, never both (decision 0002 of the policy repository). |  |
| `configMap` | PlatformConfigMap | no |  |  | The ConfigMap the file is rendered into. |  |

### `PlatformImage`

Where the image is. A digest when there is one; a tag only when there is not. Left out, the library reads the chart's own top-level `images.<component>`, the map a release stamps and refuses to publish with an empty digest.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `registry` | string | no |  |  | The registry host. Left out, the repository is read as the whole name. |  |
| `repository` | NonEmptyString | yes |  | at least 1 character | The repository path, without the registry and without a tag. |  |
| `tag` | string | no |  |  | The tag. Empty or absent when there is a digest. |  |
| `digest` | ImageDigest | no |  | matches `^(sha256:[0-9a-f]{64})?$`, never a line break | The content digest, `sha256:` and 64 hex digits; empty when there is none. |  |

### `PlatformStrategy`

The rolling update. The defaults make a rollout gapless: the replacement is READY before the incumbent is touched.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `maxUnavailable` | integer \| string | no |  |  | Defaults to 0. |  |
| `maxSurge` | integer \| string | no |  |  | Defaults to 1. |  |

### `PlatformPodSecurity`

Who the process is. Every field defaults to 65532, the unprivileged user the runtime images run as; `fsGroup` is the one that matters, because a CSI driver writes what it mounts owned by root.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `runAsUser` | PositiveInt | no |  | at least 1 | The user ID the process runs as. Never zero. |  |
| `runAsGroup` | PositiveInt | no |  | at least 1 | The group ID the process runs as. Never zero. |  |
| `fsGroup` | PositiveInt | no |  | at least 1 | The group that owns what a CSI driver mounts. Never zero. |  |

### `PlatformServiceAccount`

The account this component runs as. EVERY component has its own, always; `default` is refused. The library grants nothing: annotations are where a platform binds the account to rights outside the cluster, and which mechanism does that is the platform's.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `create` | boolean | no |  |  | False where the platform creates the accounts; they must then exist. Defaults to true. |  |
| `name` | NonEmptyString | no |  | at least 1 character | Defaults to `<release>-<component>`. |  |
| `annotations` | map of string | no |  |  | Annotations put on the account, where a platform binds it to rights outside the cluster. |  |

### `PlatformService`

A component that listens has a Service on the ports of its own `config.listen`; one that does not has none.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `enabled` | boolean | no |  |  | Defaults to whether `config.listen` exists. Enabling one for a component that listens on nothing is refused. |  |

### `PlatformProbes`

How the component is probed, on the listener its own `config.probes` binds. Liveness is nothing but the process: a probe that checks a dependency restarts a healthy process and makes an outage worse.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `liveness` | PlatformProbe | no |  |  | The liveness probe: the process and nothing else. |  |
| `readiness` | PlatformProbe | no |  |  | The readiness probe: this instance can serve now. |  |
| `startup` | PlatformProbe | no |  |  | Absent means no startup probe. Present, it needs at least one field. |  |

### `PlatformProbe`

One probe's timing. Every field has the library's own default.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `path` | RootedPath | no |  | matches `^/`, never a line break | The path on the probe listener. Defaults to the contract's own. |  |
| `periodSeconds` | PositiveInt | no |  | at least 1 | How often to probe, in seconds. |  |
| `initialDelaySeconds` | NonNegativeInt | no |  | at least 0 | How long to wait after the start before the first probe, in seconds. |  |
| `timeoutSeconds` | PositiveInt | no |  | at least 1 | How long one probe may take, in seconds. |  |
| `successThreshold` | PositiveInt | no |  | at least 1 | Consecutive successes that make the probe pass again. |  |
| `failureThreshold` | PositiveInt | no |  | at least 1 | Consecutive failures that make the probe fail. |  |

### `PlatformDrain`

The service's own shutdown budget is `config.drain.seconds`; the library derives the grace period from it and this delay, so the three numbers cannot disagree.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `preStopSeconds` | NonNegativeInt | no |  | at least 0 | Fail readiness, then wait this long before the drain starts, so that whatever routes traffic has removed this endpoint first. Defaults to 5. |  |

### `PlatformTls`

Where the platform mounts the workload identity. The files the component's own `config.tls` names must be under `mountPath`; the render refuses a file that is not.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `csiDriver` | NonEmptyString | no |  | at least 1 character | The driver that mounts the identity. The platform's, so there is no default; required once the identity is mounted. |  |
| `mountPath` | AbsPath | no |  | matches `^/[^\n]+`, never a line break | Defaults to /var/run/identity. |  |
| `mount` | boolean | no |  |  | Defaults to whether `config.tls.mode` is permissive or strict. True mounts the identity into a component that presents none of its own, because the release does; false never mounts it. |  |

### `PlatformTelemetry`

OpenTelemetry's own environment variables (decision 0006 of the policy repository): they leave the chart as variables, never as configuration keys. No endpoint means do not export.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `serviceName` | NonEmptyString | no |  | at least 1 character | Defaults to `<release>-<component>`. |  |
| `endpoint` | string | no |  |  | The collector to export to. Absent means do not export. |  |
| `protocol` | OtelProtocol | no |  |  | The protocol to export over. |  |
| `tracesSampler` | string | no |  |  | OpenTelemetry's `OTEL_TRACES_SAMPLER`. |  |
| `sampleRatio` | string \| number | no |  |  | The sampler's argument: a ratio, as a number or a string. |  |
| `resourceAttributes` | map of string | no |  |  | Attributes that describe the resource, name to value. |  |

### `PlatformSecret`

Where an environment variable's value comes from: a key of a Secret. Never the value.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `secretName` | NonEmptyString | yes |  | at least 1 character | The name of the Secret. |  |
| `key` | NonEmptyString | yes |  | at least 1 character | The key within it. |  |

### `PlatformEnvVar`

A plain environment variable. Never a secret.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `name` | NonEmptyString | yes |  | at least 1 character | The variable's name. |  |
| `value` | string | yes |  |  | Its value. |  |

### `PlatformConfig`

How the file reaches the process. The path is ONE argument or ONE environment variable, never both (decision 0002 of the policy repository).

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `fileName` | NonEmptyString | no |  | at least 1 character | Defaults to `<component>.yaml`. |  |
| `mountPath` | AbsPath | no |  | matches `^/[^\n]+`, never a line break | The directory the ConfigMap is mounted at. Defaults to `/etc/<chart name>`. |  |
| `pathFlag` | NonEmptyString | no |  | at least 1 character | The argument that carries the path. Defaults to `-config`. |  |
| `pathEnv` | NonEmptyString | no |  | at least 1 character | **Names a secret.** When set, the path is passed in this environment variable instead of an argument. |  |

### `PlatformConfigMap`

The ConfigMap the file is rendered into.

| Field | Type | Required | Default | Constraints | Description | Set at install |
|---|---|---|---|---|---|---|
| `annotations` | map of string | no |  |  | For a ConfigMap that must be a hook resource: a pre-install job cannot mount one the release has not created yet. |  |

## Secrets

These fields hold the NAME of a secret, never its value: the environment variable that holds it, or the Secret and key it comes from.

| Field | Description |
|---|---|
| `Postgres.passwordEnv` | The NAME of the environment variable holding the password. Unset means the connection needs none. |
| `Platform.secrets` | The environment variables that carry SECRETS, and nothing else (decision 0002 of the policy repository): variable name to the Secret and key its value comes from. The configuration file names the VARIABLE; the value never appears in a values file or a render. |
| `PlatformConfig.pathEnv` | When set, the path is passed in this environment variable instead of an argument. |
