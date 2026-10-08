# Architecture

OpenClinica follows a cloud-native microservice architecture. Each service owns its data, is deployed independently on Kubernetes and communicates asynchronously through Kafka. See the [architecture documentation](arc42/) for more information.

## System context

```mermaid
C4Context
    title OpenClinica system context
    Person(cdm, "Data Manager", "Builds studies and eCRFs")
    Person(site, "Site Staff", "Captures patient data")
    Person(mon, "Monitor", "Reviews and queries data")
    System(oc, "OpenClinica Platform", "EDC and CDM")
    System_Ext(idp, "Identity Provider", "OIDC / SAML")
    System_Ext(an, "Analytics", "Statistics tooling")
    Rel(cdm, oc, "Designs studies")
    Rel(site, oc, "Enters data")
    Rel(mon, oc, "Reviews data")
    Rel(oc, idp, "Authenticates via")
    Rel(oc, an, "Exports to")
```

## Services

```mermaid
flowchart TB
    subgraph Edge
        GW[API Gateway]
        AUTH[auth-service]
    end
    subgraph Domain
        ST[study-service]
        SU[subject-service]
        CR[crf-service]
        EV[event-service]
        RU[rules-service]
    end
    subgraph Platform
        AU[audit-service]
        EX[export-service]
        NO[notification-service]
        RP[reporting-service]
    end
    GW --> AUTH
    GW --> ST & SU & CR & EV & RU & RP
    ST & SU & CR & EV & RU --> BUS{{Kafka event bus}}
    BUS --> AU & EX & NO & RP
```

| Service | Responsibility | Datastore |
| --- | --- | --- |
| study-service | Study and site configuration | PostgreSQL |
| subject-service | Subject enrollment and status | PostgreSQL |
| crf-service | eCRF definitions and versions | PostgreSQL |
| event-service | Visit scheduling | PostgreSQL |
| rules-service | Edit checks and rule evaluation | Redis |
| audit-service | Immutable audit trail | Append-only store |
| export-service | Dataset extraction | Object storage |
| notification-service | E-mail and in-app messages | Kafka |
| reporting-service | Dashboards and reports | Read replica |
| auth-service | Authentication, roles, e-signatures | PostgreSQL |
| API Gateway | Routing, rate limiting, TLS | – |

## Data entry flow

```mermaid
sequenceDiagram
    actor S as Site Staff
    participant G as API Gateway
    participant C as crf-service
    participant R as rules-service
    participant K as Kafka
    participant A as audit-service
    S->>G: Submit eCRF
    G->>C: POST /crf-data
    C->>R: Validate edit checks
    R-->>C: Result
    C->>K: DataEntered event
    K->>A: Append audit record
    C-->>G: 201 Created
    G-->>S: Confirmation
```

## Deployment

```mermaid
flowchart LR
    DEV[Commit] --> CI[CI pipeline]
    CI --> T[Unit, integration, e2e tests]
    T --> Q{Quality gate A?}
    Q -- yes --> IMG[Container images]
    IMG --> STG[Staging]
    STG --> CAN[Canary 5%]
    CAN --> PROD[Production]
    Q -- no --> DEV
```

## Quality assurance

Every service is covered by unit, integration and end-to-end tests. The overall line coverage is 79.4%, and merges are blocked when the quality gate drops below "A".
