# Generated from a contract by contracts.python. Do not edit.
from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


def _no_line_break(value: str) -> str:
    # Every character that ends a line in some engine: LF, CR, FF, VT, NEL, LS, PS.
    if any(c in value for c in "\n\r\f\v\x85\u2028\u2029"):
        raise ValueError("a line break is not allowed")
    return value


def _integral(value: Any) -> Any:
    # An integral float is an integer (20.0 is 20); a bool, a string or a
    # float with a fractional part is not.
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _at(value: Any, path: list[str]) -> Any:
    # The value at a path through blocks; absent on the way is absent.
    for key in path:
        if value is None:
            return None
        value = getattr(value, key, None)
    return value


def _deny_keys(keys: list[str]):
    def check(value: dict[str, Any]) -> dict[str, Any]:
        found = [k for k in keys if k in value]
        if found:
            raise ValueError(f"must not have the key {found}")
        return value

    return check


def _has_keys(keys: list[str]):
    def check(value: dict[str, Any]) -> dict[str, Any]:
        missing = [k for k in keys if k not in value]
        if missing:
            raise ValueError(f"missing {missing}")
        return value

    return check


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @model_validator(mode="before")
    @classmethod
    def _optional_is_absent_not_null(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                if value is None:
                    raise ValueError(f"{key}: null is not a value; omit the key")
        return data

HostPort = Annotated[str, StringConstraints(pattern=r"^[^\t \xA0  -   　]*:[0-9]{1,5}$"), AfterValidator(_no_line_break)]
PostgresUrl = Annotated[str, StringConstraints(pattern=r"^postgres(ql)?://"), AfterValidator(_no_line_break)]
NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
PositiveInt = Annotated[int, BeforeValidator(_integral), Field(ge=1)]
OpenObject = dict[str, Any]
PromDuration = Annotated[str, StringConstraints(pattern=r"^[0-9]+(s|m|h)$"), AfterValidator(_no_line_break)]
StatusCodeList = Annotated[str, StringConstraints(pattern=r"^[A-Z_]+(\|[A-Z_]+)*$"), AfterValidator(_no_line_break)]
DnsLabel = Annotated[str, StringConstraints(max_length=63, pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"), AfterValidator(_no_line_break)]
GatewayTlsMode = Literal["off", "permissive"]
LogLevel = Literal["debug", "info", "warn", "error"]
ImageDigest = Annotated[str, StringConstraints(pattern=r"^(sha256:[0-9a-f]{64})?$"), AfterValidator(_no_line_break)]
PullPolicy = Literal["Always", "IfNotPresent", "Never"]
NonNegativeInt = Annotated[int, BeforeValidator(_integral), Field(ge=0)]
RootedPath = Annotated[str, StringConstraints(pattern=r"^/"), AfterValidator(_no_line_break)]
AbsPath = Annotated[str, StringConstraints(pattern=r"^/[^\n]+"), AfterValidator(_no_line_break)]
OtelProtocol = Literal["grpc", "http/protobuf", "http/json"]
EnvName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$"), AfterValidator(_no_line_break)]
Named = Annotated[dict[str, Any], AfterValidator(_has_keys(["name"]))]
Mounted = Annotated[dict[str, Any], AfterValidator(_has_keys(["name", "mountPath"]))]


class ServiceConfig(_Closed):
    """The envelope every service's configuration carries. A service extends this
module and adds its own properties beside it:

    extends "package://.../contracts.templates@<version>#/ServiceConfig.pkl"

What is in here is what EVERY component has, including a job that exits and
a consumer that answers nothing: somewhere to report health, a log level,
and a shutdown budget. A listener is not one of those, so it is not here.

The module is open so that a service can extend it, and its classes are
closed, so a key that is not declared is refused: a typo must fail."""
    model_config = ConfigDict(extra="allow")
    #: The health listener. Required: every component can be probed.
    probes: Probes
    #: Structured logging. Absent means the service's own default level.
    log: Log | None = None
    #: The shutdown budget. Absent means the service's own default, which is only
    #: correct if nothing external is counting.
    drain: Drain | None = None


class Config(ServiceConfig):
    """An example service that serves one listener and keeps a record in a
PostgreSQL database. Its configuration is the service envelope (probes, log,
drain) and what it needs of its own."""
    model_config = ConfigDict(extra="forbid")
    #: The listener the service's own traffic is served on.
    listen: Listen
    #: The database the service keeps its records in.
    postgres: Postgres
    #: How long what the service keeps is kept. A default that is a class, which
    #: differs from the class's own in `days`.
    retention: ConfigRetention = Field(default_factory=lambda: ConfigRetention.model_validate({"days": 30, "keepForever": False}))
    #: Labels put on what the service writes. A default that is an open object.
    labels: OpenObject = Field(default={"team": "platform"})
    #: Where the service archives what it served. Absent means it does not.
    archive: ConfigArchive | None = None
    #: Alerting on the service's own error budget. Absent means no rules.
    alerts: ConfigAlerts | None = None
    #: How the service calls out. Every field of it has a default, and so has the
    #: `retry` block inside it, so the whole block may be left out of a document.
    client: ConfigClient = Field(default_factory=lambda: ConfigClient.model_validate({"timeoutSeconds": 5, "retry": {"attempts": 3, "idempotentOnly": True}}))


class Listen(_Closed):
    """A TCP listener. `address` is a host:port the service binds; an empty host binds every interface."""
    #: host:port, for example ":8080" or "127.0.0.1:8080".
    address: HostPort


class Postgres(_Closed):
    """A PostgreSQL connection. The URL carries no password: it names the environment variable that does."""
    #: A connection URL without credentials, for example postgres://user@host:5432/dbname?sslmode=require.
    url: PostgresUrl
    #: The NAME of the environment variable holding the password. Unset means the connection needs none.
    passwordEnv: NonEmptyString | None = None
    #: Pool size for this instance. Sized against the server's limit divided by the number of instances, not guessed.
    maxConnections: PositiveInt = Field(default=10)


class ConfigRetention(_Closed):
    """How long what the service keeps is kept."""
    #: Days before it is deleted.
    days: PositiveInt = Field(default=7)
    #: Keep it until somebody deletes it, whatever `days` says.
    keepForever: bool = Field(default=False)


class ConfigArchive(_Closed):
    """Where the service archives what it served."""
    #: The bucket. Every install names its own, so the defaults leave it out and the
    #: schema requires it.
    bucket: NonEmptyString
    #: What every object's key begins with.
    prefix: NonEmptyString = Field(default="echo/requests")
    #: How often a batch is written, in seconds: not more often than every ten.
    batchSeconds: Annotated[int, BeforeValidator(_integral), Field(ge=10)] = Field(default=60)


class ConfigAlerts(_Closed):
    """Alerting rules for the service. Every threshold is a number or a duration with
a rule of its own, and the receiver is needed unless the install only renders
the rules for another cluster to evaluate."""
    #: Where the rules are evaluated. Absent means in this cluster.
    remote: ConfigAlertsRemote | None = None
    #: How long a condition holds before it fires.
    holdFor: PromDuration = Field(default="10m")
    #: The share of requests that may fail before it fires: more than none, at most
    #: all of them.
    errorRatio: Annotated[float, Field(le=1, gt=0)] = Field(default=0.05)
    #: The slowest a request may be, in seconds: more than zero.
    latencySeconds: Annotated[float, Field(gt=0)] = Field(default=0.5)
    #: The status codes that count as failures, joined by a bar.
    codes: StatusCodeList = Field(default="INTERNAL|UNAVAILABLE")
    #: The namespace the rules are evaluated in. Absent means the install's own.
    namespace: DnsLabel | None = None
    #: How the rules' gateway treats mutual TLS.
    tls: GatewayTlsMode = Field(default="off")
    #: Labels put on every alert. `severity` is the rules' own and may not be set here.
    alertLabels: Annotated[dict[str, NonEmptyString], AfterValidator(_deny_keys(["severity"]))] = Field(default={})
    #: Who is told. Needed unless the rules are only rendered.
    receiver: ConfigAlertsReceiver | None = None

    @model_validator(mode="after")
    def _conditional_ConfigAlerts(self) -> "ConfigAlerts":
        if _at(self, ["remote", "enabled"]) not in [True]:
            missing = [".".join(p) for p in [["receiver", "url"]] if _at(self, p) is None]
            if missing:
                raise ValueError("unless `remote.enabled` is `true`, `receiver.url` are required: missing " + ", ".join(missing))
        return self


class ConfigAlertsRemote(_Closed):
    """Where the rules are evaluated."""
    #: Whether the install only renders the rules, for another cluster to evaluate.
    enabled: bool = Field(default=False)


class ConfigAlertsReceiver(_Closed):
    """Who is told."""
    #: The receiver's URL.
    url: NonEmptyString | None = None


class ConfigClient(_Closed):
    """How the service calls out."""
    #: How long one call may take, in seconds.
    timeoutSeconds: PositiveInt = Field(default=5)
    #: What is tried again.
    retry: ConfigRetry = Field(default_factory=lambda: ConfigRetry.model_validate({"attempts": 3, "idempotentOnly": True}))
    #: A proxy to go through; absent means none.
    proxy: NonEmptyString | None = None


class ConfigRetry(_Closed):
    """What is tried again, and how often."""
    #: How many attempts in all.
    attempts: PositiveInt = Field(default=3)
    #: Whether a call that is not safe to repeat is repeated too.
    idempotentOnly: bool = Field(default=True)


class Probes(_Closed):
    """The health listener. Separate from the service's own traffic, so that readiness is answerable when the service's listener is saturated, and so that a probe is not reachable from outside."""
    #: host:port for /health/live and /health/ready.
    address: HostPort


class Log(_Closed):
    """Structured logging. One level for the whole service: per-package levels are deliberately not part of the contract."""
    #: The lowest level that is written.
    level: LogLevel = Field(default="info")


class Drain(_Closed):
    """How long the service may take to finish in-flight work after SIGTERM. It is one number shared with whatever deploys the service: the grace period granted to the process and the pre-stop delay before it are derived from this, so that a draining process is never killed at the moment it would have finished."""
    #: Seconds to finish in-flight work. Unset means the service's own default, which is only correct if nothing external is counting.
    seconds: PositiveInt = Field(default=20)


class Platform(_Closed):
    """What the platform provides one component of a service chart: the image, the replicas, the account it runs as, how it is probed, where its identity is mounted, which secrets reach it as environment variables, and how it exports telemetry. The shape of the `platform` block of a chart's values, read by the library chart (decision 0009 of the policy repository). Nothing here is the service's own configuration: that is the chart's `config` block, which is the service's schema and nothing else."""
    #: Where the image is. A digest when there is one; a tag only when there is not. Left out, the library reads the chart's own top-level `images.<component>`, the map a release stamps and refuses to publish with an empty digest.
    image: PlatformImage | None = None
    #: Defaults to IfNotPresent.
    imagePullPolicy: PullPolicy | None = None
    #: Defaults to 1. A service that must survive a rollout runs more than one: one instance cannot be replaced without a gap whatever the strategy says.
    replicas: NonNegativeInt | None = None
    #: The rolling update. The defaults make a rollout gapless: the replacement is READY before the incumbent is touched.
    strategy: PlatformStrategy | None = None
    #: Kubernetes' own resource requirements. Open: it is passed through unchanged.
    resources: OpenObject | None = None
    #: Who the process is. Every field defaults to 65532, the unprivileged user the runtime images run as; `fsGroup` is the one that matters, because a CSI driver writes what it mounts owned by root.
    podSecurity: PlatformPodSecurity | None = None
    #: The account this component runs as. EVERY component has its own, always; `default` is refused. The library grants nothing: annotations are where a platform binds the account to rights outside the cluster, and which mechanism does that is the platform's.
    serviceAccount: PlatformServiceAccount | None = None
    #: A component that listens has a Service on the ports of its own `config.listen`; one that does not has none.
    service: PlatformService | None = None
    #: How the component is probed, on the listener its own `config.probes` binds. Liveness is nothing but the process: a probe that checks a dependency restarts a healthy process and makes an outage worse.
    probes: PlatformProbes | None = None
    #: The service's own shutdown budget is `config.drain.seconds`; the library derives the grace period from it and this delay, so the three numbers cannot disagree.
    drain: PlatformDrain | None = None
    #: Where the platform mounts the workload identity. The files the component's own `config.tls` names must be under `mountPath`; the render refuses a file that is not.
    tls: PlatformTls | None = None
    #: OpenTelemetry's own environment variables (decision 0006 of the policy repository): they leave the chart as variables, never as configuration keys. No endpoint means do not export.
    telemetry: PlatformTelemetry | None = None
    #: The environment variables that carry SECRETS, and nothing else (decision 0002 of the policy repository): variable name to the Secret and key its value comes from. The configuration file names the VARIABLE; the value never appears in a values file or a render.
    secrets: dict[EnvName, PlatformSecret] | None = None
    #: Environment a platform CLIENT LIBRARY reads (a database client's connection variables, for example), never the service's own configuration: a service takes no other structural input than its file (decision 0002 of the policy repository). A secret does not belong here; declare it in `secrets`.
    env: list[PlatformEnvVar] | None = None
    #: Extra pod volumes, in Kubernetes' own shape, for what a client library mounts (a trust bundle, a password file). Open: passed through unchanged.
    volumes: list[Named] | None = None
    #: The mounts for `volumes`, in Kubernetes' own shape.
    volumeMounts: list[Mounted] | None = None
    #: How the file reaches the process. The path is ONE argument or ONE environment variable, never both (decision 0002 of the policy repository).
    config: PlatformConfig | None = None
    #: The ConfigMap the file is rendered into.
    configMap: PlatformConfigMap | None = None


class PlatformImage(_Closed):
    """Where the image is. A digest when there is one; a tag only when there is not. Left out, the library reads the chart's own top-level `images.<component>`, the map a release stamps and refuses to publish with an empty digest."""
    #: The registry host. Left out, the repository is read as the whole name.
    registry: str | None = None
    #: The repository path, without the registry and without a tag.
    repository: NonEmptyString
    #: The tag. Empty or absent when there is a digest.
    tag: str | None = None
    #: The content digest, `sha256:` and 64 hex digits; empty when there is none.
    digest: ImageDigest | None = None


class PlatformStrategy(_Closed):
    """The rolling update. The defaults make a rollout gapless: the replacement is READY before the incumbent is touched."""
    #: Defaults to 0.
    maxUnavailable: Annotated[int, BeforeValidator(_integral)] | str | None = None
    #: Defaults to 1.
    maxSurge: Annotated[int, BeforeValidator(_integral)] | str | None = None


class PlatformPodSecurity(_Closed):
    """Who the process is. Every field defaults to 65532, the unprivileged user the runtime images run as; `fsGroup` is the one that matters, because a CSI driver writes what it mounts owned by root."""
    #: The user ID the process runs as. Never zero.
    runAsUser: PositiveInt | None = None
    #: The group ID the process runs as. Never zero.
    runAsGroup: PositiveInt | None = None
    #: The group that owns what a CSI driver mounts. Never zero.
    fsGroup: PositiveInt | None = None


class PlatformServiceAccount(_Closed):
    """The account this component runs as. EVERY component has its own, always; `default` is refused. The library grants nothing: annotations are where a platform binds the account to rights outside the cluster, and which mechanism does that is the platform's."""
    #: False where the platform creates the accounts; they must then exist. Defaults to true.
    create: bool | None = None
    #: Defaults to `<release>-<component>`.
    name: NonEmptyString | None = None
    #: Annotations put on the account, where a platform binds it to rights outside the cluster.
    annotations: dict[str, str] | None = None


class PlatformService(_Closed):
    """A component that listens has a Service on the ports of its own `config.listen`; one that does not has none."""
    #: Defaults to whether `config.listen` exists. Enabling one for a component that listens on nothing is refused.
    enabled: bool | None = None


class PlatformProbes(_Closed):
    """How the component is probed, on the listener its own `config.probes` binds. Liveness is nothing but the process: a probe that checks a dependency restarts a healthy process and makes an outage worse."""
    #: The liveness probe: the process and nothing else.
    liveness: PlatformProbe | None = None
    #: The readiness probe: this instance can serve now.
    readiness: PlatformProbe | None = None
    #: Absent means no startup probe. Present, it needs at least one field.
    startup: PlatformProbe | None = None


class PlatformProbe(_Closed):
    """One probe's timing. Every field has the library's own default."""
    #: The path on the probe listener. Defaults to the contract's own.
    path: RootedPath | None = None
    #: How often to probe, in seconds.
    periodSeconds: PositiveInt | None = None
    #: How long to wait after the start before the first probe, in seconds.
    initialDelaySeconds: NonNegativeInt | None = None
    #: How long one probe may take, in seconds.
    timeoutSeconds: PositiveInt | None = None
    #: Consecutive successes that make the probe pass again.
    successThreshold: PositiveInt | None = None
    #: Consecutive failures that make the probe fail.
    failureThreshold: PositiveInt | None = None


class PlatformDrain(_Closed):
    """The service's own shutdown budget is `config.drain.seconds`; the library derives the grace period from it and this delay, so the three numbers cannot disagree."""
    #: Fail readiness, then wait this long before the drain starts, so that whatever routes traffic has removed this endpoint first. Defaults to 5.
    preStopSeconds: NonNegativeInt | None = None


class PlatformTls(_Closed):
    """Where the platform mounts the workload identity. The files the component's own `config.tls` names must be under `mountPath`; the render refuses a file that is not."""
    #: The driver that mounts the identity. The platform's, so there is no default; required once the identity is mounted.
    csiDriver: NonEmptyString | None = None
    #: Defaults to /var/run/identity.
    mountPath: AbsPath | None = None
    #: Defaults to whether `config.tls.mode` is permissive or strict. True mounts the identity into a component that presents none of its own, because the release does; false never mounts it.
    mount: bool | None = None


class PlatformTelemetry(_Closed):
    """OpenTelemetry's own environment variables (decision 0006 of the policy repository): they leave the chart as variables, never as configuration keys. No endpoint means do not export."""
    #: Defaults to `<release>-<component>`.
    serviceName: NonEmptyString | None = None
    #: The collector to export to. Absent means do not export.
    endpoint: str | None = None
    #: The protocol to export over.
    protocol: OtelProtocol | None = None
    #: OpenTelemetry's `OTEL_TRACES_SAMPLER`.
    tracesSampler: str | None = None
    #: The sampler's argument: a ratio, as a number or a string.
    sampleRatio: str | float | None = None
    #: Attributes that describe the resource, name to value.
    resourceAttributes: dict[str, str] | None = None


class PlatformSecret(_Closed):
    """Where an environment variable's value comes from: a key of a Secret. Never the value."""
    #: The name of the Secret.
    secretName: NonEmptyString
    #: The key within it.
    key: NonEmptyString


class PlatformEnvVar(_Closed):
    """A plain environment variable. Never a secret."""
    #: The variable's name.
    name: NonEmptyString
    #: Its value.
    value: str


class PlatformConfig(_Closed):
    """How the file reaches the process. The path is ONE argument or ONE environment variable, never both (decision 0002 of the policy repository)."""
    #: Defaults to `<component>.yaml`.
    fileName: NonEmptyString | None = None
    #: The directory the ConfigMap is mounted at. Defaults to `/etc/<chart name>`.
    mountPath: AbsPath | None = None
    #: The argument that carries the path. Defaults to `-config`.
    pathFlag: NonEmptyString | None = None
    #: When set, the path is passed in this environment variable instead of an argument.
    pathEnv: NonEmptyString | None = None


class PlatformConfigMap(_Closed):
    """The ConfigMap the file is rendered into."""
    #: For a ConfigMap that must be a hook resource: a pre-install job cannot mount one the release has not created yet.
    annotations: dict[str, str] | None = None


SCHEMAS: dict[str, type[BaseModel]] = {
    "config": Config,
    "fragments/drain": Drain,
    "fragments/listen": Listen,
    "fragments/log": Log,
    "fragments/platform": Platform,
    "fragments/postgres": Postgres,
    "fragments/probes": Probes,
    "service": ServiceConfig,
}
