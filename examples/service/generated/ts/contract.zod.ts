// Generated from a contract by contracts.typescript. Do not edit.
import { z } from "zod";

const noLineBreak = (s: string): boolean => !/[\n\r\f\v\u0085\u2028\u2029]/.test(s);

/** host:port as the configuration contract spells it today. It does NOT bound the port at 65535, because the hand-written pattern does not; `Port` is the stricter vocabulary a contract may move to. */
export const HostPort = z.string().regex(/^[^\t \xA0  -   　]*:[0-9]{1,5}$/).refine(noLineBreak);
export type HostPort = z.infer<typeof HostPort>;
/** A PostgreSQL connection URL, by its scheme. */
export const PostgresUrl = z.string().regex(/^postgres(ql)?:\/\//).refine(noLineBreak);
export type PostgresUrl = z.infer<typeof PostgresUrl>;
/** A string of at least one character. */
export const NonEmptyString = z.string().min(1);
export type NonEmptyString = z.infer<typeof NonEmptyString>;
/** A whole number of at least one. */
export const PositiveInt = z.number().int().min(1);
export type PositiveInt = z.infer<typeof PositiveInt>;
/** Kubernetes' own object shape, passed through unchanged. */
export const OpenObject = z.looseObject({});
export type OpenObject = z.infer<typeof OpenObject>;
/** The lowest level a service writes. */
export const LogLevel = z.enum(["debug", "info", "warn", "error"]);
export type LogLevel = z.infer<typeof LogLevel>;
/** An image digest, or empty when there is none. */
export const ImageDigest = z.string().regex(/^(sha256:[0-9a-f]{64})?$/).refine(noLineBreak);
export type ImageDigest = z.infer<typeof ImageDigest>;
/** When a container image is pulled. */
export const PullPolicy = z.enum(["Always", "IfNotPresent", "Never"]);
export type PullPolicy = z.infer<typeof PullPolicy>;
/** A whole number of at least zero. */
export const NonNegativeInt = z.number().int().min(0);
export type NonNegativeInt = z.infer<typeof NonNegativeInt>;
/** A path that starts at the root, the root itself included. */
export const RootedPath = z.string().regex(/^\//).refine(noLineBreak);
export type RootedPath = z.infer<typeof RootedPath>;
/** An absolute path that is not the root. */
export const AbsPath = z.string().regex(/^\/[^\n]+/).refine(noLineBreak);
export type AbsPath = z.infer<typeof AbsPath>;
/** The protocol OpenTelemetry exports over. */
export const OtelProtocol = z.enum(["grpc", "http/protobuf", "http/json"]);
export type OtelProtocol = z.infer<typeof OtelProtocol>;
/** The name of an environment variable. */
export const EnvName = z.string().regex(/^[A-Za-z_][A-Za-z0-9_]*$/).refine(noLineBreak);
export type EnvName = z.infer<typeof EnvName>;
/** An open object that must carry `name`. */
export const Named = z.looseObject({}).refine((o) => ["name"].every((k) => k in o));
export type Named = z.infer<typeof Named>;
/** An open object that must carry `name` and `mountPath`. */
export const Mounted = z.looseObject({}).refine((o) => ["name", "mountPath"].every((k) => k in o));
export type Mounted = z.infer<typeof Mounted>;

/** The envelope every service's configuration carries. A service extends this module and adds its own properties beside it:      extends "package://.../contracts.templates@<version>#/ServiceConfig.pkl"  What is in here is what EVERY component has, including a job that exits and a consumer that answers nothing: somewhere to report health, a log level, and a shutdown budget. A listener is not one of those, so it is not here.  The module is open so that a service can extend it, and its classes are closed, so a key that is not declared is refused: a typo must fail. */
export const ServiceConfig_shape = {
  /** The health listener. Required: every component can be probed. */
  probes: z.lazy(() => Probes),
  /** Structured logging. Absent means the service's own default level. */
  log: z.lazy(() => Log).optional(),
  /** The shutdown budget. Absent means the service's own default, which is only correct if nothing external is counting. */
  drain: z.lazy(() => Drain).optional(),
};
export const ServiceConfig = z.looseObject(ServiceConfig_shape);
export type ServiceConfig = z.infer<typeof ServiceConfig>;

/** An example service that serves one listener and keeps a record in a PostgreSQL database. Its configuration is the service envelope (probes, log, drain) and what it needs of its own. */
export const Config_shape = {
  ...ServiceConfig_shape,
  /** The listener the service's own traffic is served on. */
  listen: z.lazy(() => Listen),
  /** The database the service keeps its records in. */
  postgres: z.lazy(() => Postgres),
  /** How long what the service keeps is kept. A default that is a class, which differs from the class's own in `days`. */
  retention: z.lazy(() => ConfigRetention).default({"days": 30, "keepForever": false}),
  /** Labels put on what the service writes. A default that is an open object. */
  labels: OpenObject.default({"team": "platform"}),
  /** Where the service archives what it served. Absent means it does not. */
  archive: z.lazy(() => ConfigArchive).optional(),
  /** How the service calls out. Every field of it has a default, and so has the `retry` block inside it, so the whole block may be left out of a document. */
  client: z.lazy(() => ConfigClient).default({"timeoutSeconds": 5, "retry": {"attempts": 3, "idempotentOnly": true}}),
};
export const Config = z.strictObject(Config_shape);
export type Config = z.infer<typeof Config>;

/** A TCP listener. `address` is a host:port the service binds; an empty host binds every interface. */
export const Listen_shape = {
  /** host:port, for example ":8080" or "127.0.0.1:8080". */
  address: HostPort,
};
export const Listen = z.strictObject(Listen_shape);
export type Listen = z.infer<typeof Listen>;

/** A PostgreSQL connection. The URL carries no password: it names the environment variable that does. */
export const Postgres_shape = {
  /** A connection URL without credentials, for example postgres://user@host:5432/dbname?sslmode=require. */
  url: PostgresUrl,
  /** The NAME of the environment variable holding the password. Unset means the connection needs none. */
  passwordEnv: NonEmptyString.optional(),
  /** Pool size for this instance. Sized against the server's limit divided by the number of instances, not guessed. */
  maxConnections: PositiveInt.default(10),
};
export const Postgres = z.strictObject(Postgres_shape);
export type Postgres = z.infer<typeof Postgres>;

/** How long what the service keeps is kept. */
export const ConfigRetention_shape = {
  /** Days before it is deleted. */
  days: PositiveInt.default(7),
  /** Keep it until somebody deletes it, whatever `days` says. */
  keepForever: z.boolean().default(false),
};
export const ConfigRetention = z.strictObject(ConfigRetention_shape);
export type ConfigRetention = z.infer<typeof ConfigRetention>;

/** Where the service archives what it served. */
export const ConfigArchive_shape = {
  /** The bucket. Every install names its own, so the defaults leave it out and the schema requires it. */
  bucket: NonEmptyString,
  /** What every object's key begins with. */
  prefix: NonEmptyString.default("echo/requests"),
  /** How often a batch is written, in seconds: not more often than every ten. */
  batchSeconds: z.number().int().min(10).default(60),
};
export const ConfigArchive = z.strictObject(ConfigArchive_shape);
export type ConfigArchive = z.infer<typeof ConfigArchive>;

/** How the service calls out. */
export const ConfigClient_shape = {
  /** How long one call may take, in seconds. */
  timeoutSeconds: PositiveInt.default(5),
  /** What is tried again. */
  retry: z.lazy(() => ConfigRetry).default({"attempts": 3, "idempotentOnly": true}),
  /** A proxy to go through; absent means none. */
  proxy: NonEmptyString.optional(),
};
export const ConfigClient = z.strictObject(ConfigClient_shape);
export type ConfigClient = z.infer<typeof ConfigClient>;

/** What is tried again, and how often. */
export const ConfigRetry_shape = {
  /** How many attempts in all. */
  attempts: PositiveInt.default(3),
  /** Whether a call that is not safe to repeat is repeated too. */
  idempotentOnly: z.boolean().default(true),
};
export const ConfigRetry = z.strictObject(ConfigRetry_shape);
export type ConfigRetry = z.infer<typeof ConfigRetry>;

/** The health listener. Separate from the service's own traffic, so that readiness is answerable when the service's listener is saturated, and so that a probe is not reachable from outside. */
export const Probes_shape = {
  /** host:port for /health/live and /health/ready. */
  address: HostPort,
};
export const Probes = z.strictObject(Probes_shape);
export type Probes = z.infer<typeof Probes>;

/** Structured logging. One level for the whole service: per-package levels are deliberately not part of the contract. */
export const Log_shape = {
  /** The lowest level that is written. */
  level: LogLevel.default("info"),
};
export const Log = z.strictObject(Log_shape);
export type Log = z.infer<typeof Log>;

/** How long the service may take to finish in-flight work after SIGTERM. It is one number shared with whatever deploys the service: the grace period granted to the process and the pre-stop delay before it are derived from this, so that a draining process is never killed at the moment it would have finished. */
export const Drain_shape = {
  /** Seconds to finish in-flight work. Unset means the service's own default, which is only correct if nothing external is counting. */
  seconds: PositiveInt.default(20),
};
export const Drain = z.strictObject(Drain_shape);
export type Drain = z.infer<typeof Drain>;

/** What the platform provides one component of a service chart: the image, the replicas, the account it runs as, how it is probed, where its identity is mounted, which secrets reach it as environment variables, and how it exports telemetry. The shape of the `platform` block of a chart's values, read by the library chart (decision 0009 of the policy repository). Nothing here is the service's own configuration: that is the chart's `config` block, which is the service's schema and nothing else. */
export const Platform_shape = {
  /** Where the image is. A digest when there is one; a tag only when there is not. Left out, the library reads the chart's own top-level `images.<component>`, the map a release stamps and refuses to publish with an empty digest. */
  image: z.lazy(() => PlatformImage).optional(),
  /** Defaults to IfNotPresent. */
  imagePullPolicy: PullPolicy.optional(),
  /** Defaults to 1. A service that must survive a rollout runs more than one: one instance cannot be replaced without a gap whatever the strategy says. */
  replicas: NonNegativeInt.optional(),
  /** The rolling update. The defaults make a rollout gapless: the replacement is READY before the incumbent is touched. */
  strategy: z.lazy(() => PlatformStrategy).optional(),
  /** Kubernetes' own resource requirements. Open: it is passed through unchanged. */
  resources: OpenObject.optional(),
  /** Who the process is. Every field defaults to 65532, the unprivileged user the runtime images run as; `fsGroup` is the one that matters, because a CSI driver writes what it mounts owned by root. */
  podSecurity: z.lazy(() => PlatformPodSecurity).optional(),
  /** The account this component runs as. EVERY component has its own, always; `default` is refused. The library grants nothing: annotations are where a platform binds the account to rights outside the cluster, and which mechanism does that is the platform's. */
  serviceAccount: z.lazy(() => PlatformServiceAccount).optional(),
  /** A component that listens has a Service on the ports of its own `config.listen`; one that does not has none. */
  service: z.lazy(() => PlatformService).optional(),
  /** How the component is probed, on the listener its own `config.probes` binds. Liveness is nothing but the process: a probe that checks a dependency restarts a healthy process and makes an outage worse. */
  probes: z.lazy(() => PlatformProbes).optional(),
  /** The service's own shutdown budget is `config.drain.seconds`; the library derives the grace period from it and this delay, so the three numbers cannot disagree. */
  drain: z.lazy(() => PlatformDrain).optional(),
  /** Where the platform mounts the workload identity. The files the component's own `config.tls` names must be under `mountPath`; the render refuses a file that is not. */
  tls: z.lazy(() => PlatformTls).optional(),
  /** OpenTelemetry's own environment variables (decision 0006 of the policy repository): they leave the chart as variables, never as configuration keys. No endpoint means do not export. */
  telemetry: z.lazy(() => PlatformTelemetry).optional(),
  /** The environment variables that carry SECRETS, and nothing else (decision 0002 of the policy repository): variable name to the Secret and key its value comes from. The configuration file names the VARIABLE; the value never appears in a values file or a render. */
  secrets: z.record(EnvName, z.lazy(() => PlatformSecret)).optional(),
  /** Environment a platform CLIENT LIBRARY reads (a database client's connection variables, for example), never the service's own configuration: a service takes no other structural input than its file (decision 0002 of the policy repository). A secret does not belong here; declare it in `secrets`. */
  env: z.array(z.lazy(() => PlatformEnvVar)).optional(),
  /** Extra pod volumes, in Kubernetes' own shape, for what a client library mounts (a trust bundle, a password file). Open: passed through unchanged. */
  volumes: z.array(Named).optional(),
  /** The mounts for `volumes`, in Kubernetes' own shape. */
  volumeMounts: z.array(Mounted).optional(),
  /** How the file reaches the process. The path is ONE argument or ONE environment variable, never both (decision 0002 of the policy repository). */
  config: z.lazy(() => PlatformConfig).optional(),
  /** The ConfigMap the file is rendered into. */
  configMap: z.lazy(() => PlatformConfigMap).optional(),
};
export const Platform = z.strictObject(Platform_shape);
export type Platform = z.infer<typeof Platform>;

/** Where the image is. A digest when there is one; a tag only when there is not. Left out, the library reads the chart's own top-level `images.<component>`, the map a release stamps and refuses to publish with an empty digest. */
export const PlatformImage_shape = {
  /** The registry host. Left out, the repository is read as the whole name. */
  registry: z.string().optional(),
  /** The repository path, without the registry and without a tag. */
  repository: NonEmptyString,
  /** The tag. Empty or absent when there is a digest. */
  tag: z.string().optional(),
  /** The content digest, `sha256:` and 64 hex digits; empty when there is none. */
  digest: ImageDigest.optional(),
};
export const PlatformImage = z.strictObject(PlatformImage_shape);
export type PlatformImage = z.infer<typeof PlatformImage>;

/** The rolling update. The defaults make a rollout gapless: the replacement is READY before the incumbent is touched. */
export const PlatformStrategy_shape = {
  /** Defaults to 0. */
  maxUnavailable: z.union([z.number().int(), z.string()]).optional(),
  /** Defaults to 1. */
  maxSurge: z.union([z.number().int(), z.string()]).optional(),
};
export const PlatformStrategy = z.strictObject(PlatformStrategy_shape);
export type PlatformStrategy = z.infer<typeof PlatformStrategy>;

/** Who the process is. Every field defaults to 65532, the unprivileged user the runtime images run as; `fsGroup` is the one that matters, because a CSI driver writes what it mounts owned by root. */
export const PlatformPodSecurity_shape = {
  /** The user ID the process runs as. Never zero. */
  runAsUser: PositiveInt.optional(),
  /** The group ID the process runs as. Never zero. */
  runAsGroup: PositiveInt.optional(),
  /** The group that owns what a CSI driver mounts. Never zero. */
  fsGroup: PositiveInt.optional(),
};
export const PlatformPodSecurity = z.strictObject(PlatformPodSecurity_shape);
export type PlatformPodSecurity = z.infer<typeof PlatformPodSecurity>;

/** The account this component runs as. EVERY component has its own, always; `default` is refused. The library grants nothing: annotations are where a platform binds the account to rights outside the cluster, and which mechanism does that is the platform's. */
export const PlatformServiceAccount_shape = {
  /** False where the platform creates the accounts; they must then exist. Defaults to true. */
  create: z.boolean().optional(),
  /** Defaults to `<release>-<component>`. */
  name: NonEmptyString.optional(),
  /** Annotations put on the account, where a platform binds it to rights outside the cluster. */
  annotations: z.record(z.string(), z.string()).optional(),
};
export const PlatformServiceAccount = z.strictObject(PlatformServiceAccount_shape);
export type PlatformServiceAccount = z.infer<typeof PlatformServiceAccount>;

/** A component that listens has a Service on the ports of its own `config.listen`; one that does not has none. */
export const PlatformService_shape = {
  /** Defaults to whether `config.listen` exists. Enabling one for a component that listens on nothing is refused. */
  enabled: z.boolean().optional(),
};
export const PlatformService = z.strictObject(PlatformService_shape);
export type PlatformService = z.infer<typeof PlatformService>;

/** How the component is probed, on the listener its own `config.probes` binds. Liveness is nothing but the process: a probe that checks a dependency restarts a healthy process and makes an outage worse. */
export const PlatformProbes_shape = {
  /** The liveness probe: the process and nothing else. */
  liveness: z.lazy(() => PlatformProbe).optional(),
  /** The readiness probe: this instance can serve now. */
  readiness: z.lazy(() => PlatformProbe).optional(),
  /** Absent means no startup probe. Present, it needs at least one field. */
  startup: z.lazy(() => PlatformProbe).optional(),
};
export const PlatformProbes = z.strictObject(PlatformProbes_shape);
export type PlatformProbes = z.infer<typeof PlatformProbes>;

/** One probe's timing. Every field has the library's own default. */
export const PlatformProbe_shape = {
  /** The path on the probe listener. Defaults to the contract's own. */
  path: RootedPath.optional(),
  /** How often to probe, in seconds. */
  periodSeconds: PositiveInt.optional(),
  /** How long to wait after the start before the first probe, in seconds. */
  initialDelaySeconds: NonNegativeInt.optional(),
  /** How long one probe may take, in seconds. */
  timeoutSeconds: PositiveInt.optional(),
  /** Consecutive successes that make the probe pass again. */
  successThreshold: PositiveInt.optional(),
  /** Consecutive failures that make the probe fail. */
  failureThreshold: PositiveInt.optional(),
};
export const PlatformProbe = z.strictObject(PlatformProbe_shape);
export type PlatformProbe = z.infer<typeof PlatformProbe>;

/** The service's own shutdown budget is `config.drain.seconds`; the library derives the grace period from it and this delay, so the three numbers cannot disagree. */
export const PlatformDrain_shape = {
  /** Fail readiness, then wait this long before the drain starts, so that whatever routes traffic has removed this endpoint first. Defaults to 5. */
  preStopSeconds: NonNegativeInt.optional(),
};
export const PlatformDrain = z.strictObject(PlatformDrain_shape);
export type PlatformDrain = z.infer<typeof PlatformDrain>;

/** Where the platform mounts the workload identity. The files the component's own `config.tls` names must be under `mountPath`; the render refuses a file that is not. */
export const PlatformTls_shape = {
  /** The driver that mounts the identity. The platform's, so there is no default; required once the identity is mounted. */
  csiDriver: NonEmptyString.optional(),
  /** Defaults to /var/run/identity. */
  mountPath: AbsPath.optional(),
  /** Defaults to whether `config.tls.mode` is permissive or strict. True mounts the identity into a component that presents none of its own, because the release does; false never mounts it. */
  mount: z.boolean().optional(),
};
export const PlatformTls = z.strictObject(PlatformTls_shape);
export type PlatformTls = z.infer<typeof PlatformTls>;

/** OpenTelemetry's own environment variables (decision 0006 of the policy repository): they leave the chart as variables, never as configuration keys. No endpoint means do not export. */
export const PlatformTelemetry_shape = {
  /** Defaults to `<release>-<component>`. */
  serviceName: NonEmptyString.optional(),
  /** The collector to export to. Absent means do not export. */
  endpoint: z.string().optional(),
  /** The protocol to export over. */
  protocol: OtelProtocol.optional(),
  /** OpenTelemetry's `OTEL_TRACES_SAMPLER`. */
  tracesSampler: z.string().optional(),
  /** The sampler's argument: a ratio, as a number or a string. */
  sampleRatio: z.union([z.string(), z.number()]).optional(),
  /** Attributes that describe the resource, name to value. */
  resourceAttributes: z.record(z.string(), z.string()).optional(),
};
export const PlatformTelemetry = z.strictObject(PlatformTelemetry_shape);
export type PlatformTelemetry = z.infer<typeof PlatformTelemetry>;

/** Where an environment variable's value comes from: a key of a Secret. Never the value. */
export const PlatformSecret_shape = {
  /** The name of the Secret. */
  secretName: NonEmptyString,
  /** The key within it. */
  key: NonEmptyString,
};
export const PlatformSecret = z.strictObject(PlatformSecret_shape);
export type PlatformSecret = z.infer<typeof PlatformSecret>;

/** A plain environment variable. Never a secret. */
export const PlatformEnvVar_shape = {
  /** The variable's name. */
  name: NonEmptyString,
  /** Its value. */
  value: z.string(),
};
export const PlatformEnvVar = z.strictObject(PlatformEnvVar_shape);
export type PlatformEnvVar = z.infer<typeof PlatformEnvVar>;

/** How the file reaches the process. The path is ONE argument or ONE environment variable, never both (decision 0002 of the policy repository). */
export const PlatformConfig_shape = {
  /** Defaults to `<component>.yaml`. */
  fileName: NonEmptyString.optional(),
  /** The directory the ConfigMap is mounted at. Defaults to `/etc/<chart name>`. */
  mountPath: AbsPath.optional(),
  /** The argument that carries the path. Defaults to `-config`. */
  pathFlag: NonEmptyString.optional(),
  /** When set, the path is passed in this environment variable instead of an argument. */
  pathEnv: NonEmptyString.optional(),
};
export const PlatformConfig = z.strictObject(PlatformConfig_shape);
export type PlatformConfig = z.infer<typeof PlatformConfig>;

/** The ConfigMap the file is rendered into. */
export const PlatformConfigMap_shape = {
  /** For a ConfigMap that must be a hook resource: a pre-install job cannot mount one the release has not created yet. */
  annotations: z.record(z.string(), z.string()).optional(),
};
export const PlatformConfigMap = z.strictObject(PlatformConfigMap_shape);
export type PlatformConfigMap = z.infer<typeof PlatformConfigMap>;

export const schemas = {
  "config": Config,
  "fragments/drain": Drain,
  "fragments/listen": Listen,
  "fragments/log": Log,
  "fragments/platform": Platform,
  "fragments/postgres": Postgres,
  "fragments/probes": Probes,
  "service": ServiceConfig,
} as const;
