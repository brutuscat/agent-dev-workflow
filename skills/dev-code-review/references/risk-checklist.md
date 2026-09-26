# Review risk checklist

Load only the sections that match the diff. These are prompts for investigation, not automatic findings. Report a problem only after establishing a reachable trigger and consequence.

## Trust boundaries

- Validate untrusted input before it reaches SQL, commands, file paths, internal URLs, deserializers, or privileged operations.
- Keep authentication, authorization, tenant, and ownership checks on trusted boundaries.
- Do not expose credentials, tokens, PII, private paths, or raw sensitive payloads through logs, errors, client bundles, fixtures, or examples.

## Data integrity and concurrency

- Make check-then-act sequences atomic when concurrent calls can race.
- Use transactions, version checks, locks, or atomic updates when read-modify-write can lose data.
- Make retryable writes idempotent or duplicate-safe.
- Define recovery for partial writes and migrations. Do not claim an irreversible migration has a lossless rollback.

## Failure and resource handling

- Handle or deliberately propagate fallible I/O, parsing, network, and database operations.
- Bound background work and give it cancellation or a clear lifetime.
- Release files, streams, sockets, database handles, timers, subscriptions, and other owned resources.

## Performance and dependencies

- Look for new N+1 queries, unbounded collections, blocking work in hot paths, and avoidable repeated network calls.
- Check cache scope and invalidation when stale or cross-tenant data matters.
- Treat new dependencies, registries, CDNs, disabled certificate checks, or weakened pinning as supply-chain changes that need justification.
