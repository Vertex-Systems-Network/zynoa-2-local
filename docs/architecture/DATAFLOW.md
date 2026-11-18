# End-to-end Dataflow Contracts

## System data graph

```mermaid
flowchart TD
  A[Desktop GUI] --> B[Typed IPC]
  B --> C[Native Policy Broker]
  C --> D[Durable Job Controller]
  D --> E[AI Model Router]
  E --> F[Ollama or llama.cpp]
  D --> G[Authorized Tool Workers]
  G --> H[Code / Browser / Design / Research]
  D --> I[SQLite Events and Artifacts]
  I --> J[Docs and Evidence]
  I --> K[Incident Normalizer]
  K --> L{Reporting enabled?}
  L -->|No| M[Local Incident History]
  L -->|Yes| N[Sanitizing Relay]
  N --> O[GitHub Issue Dedupe / Create]
```

## Event envelope

```json
{"schema_version":1,"event_id":"ulid","trace_id":"ulid","project_id":"opaque","module_id":"Mxx","phase_id":"Pxx","type":"module.event","sequence":1,"occurred_at":"UTC ISO8601","payload":{"typed":"module-specific"},"origin":"UI|worker|runtime","policy_decision_id":"optional"}
```

Safety: origin metadata is not permission. Native broker verifies actual process identity, scope and operation. State changes are replayable; external side effects need idempotency safeguards. Batch UI events with backpressure, separate render/inference workers. Every module dossier lists its event vocabulary.
