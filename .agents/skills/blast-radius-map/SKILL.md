---
name: blast-radius-map
description: Semi-automatically work out zones (red/yellow/green) for an existing codebase, following Brownfield Agentic Engineering. The agent gathers evidence (dependencies, tests, history) with the tools that fit each language and proposes zones with a rationale, a human decides. Use for "write/draw/update zones", "zone map", "which parts may the agent touch", "blast radius of the codebase", "treemap by zone".
---

# Blast Radius Map: Writing Zones

A zone says how much autonomy an agent has in a part of the code. The zone is not a property of the code but a decision made by a human. The agent supplies evidence and a proposal.

## Principles (from the article)

- **A human draws the map.** An agent that chooses for itself starts in the scariest file. You may prefill every field (zone, rationale, observability, recoverability) so the human has something to correct, but everything you enter is a *proposal* (`reviewed: false`) until a human (owner) confirms it.
- **The zone sets the verbs.**
  - Green: tight agent loop, the gate is build and tests.
  - Yellow: tests first (Characterization Tests, not written by the same session that makes the change), then change.
  - Red: a human pairs at every step. Autonomous work is limited to a read-only Comprehension Memo, otherwise the work does not happen.
- **Zones only move when it is earned.** Yellow becomes green when Characterization Tests exist and the owner has reviewed the agent's first changes. A human decides on promotion.
- **Autonomy follows blast radius, observability and recoverability.** The model's confidence does not count. All three are assessed per concept (step 5).
- **Write only what the code cannot say:** reasons, regulatory or domain constraints, external contracts, history. Metrics sit next to it as evidence and do not replace the rationale.

## Procedure

1. **Explore the ecosystem.** Languages, build system, module structure, existing tests and CI, Git history, CODEOWNERS. Check what is installed and runs offline (`which`, `--version`, build files, local package caches). Ask before installing anything and before long test runs.
2. **Define concepts** (with the human). Zones are not drawn per package but per *concept*, cutting across the code. Four lenses have proven useful:
   - technical cross-cutting topics (security, audit, transactions, logging, i18n, configuration, ...)
   - domain cross-cutting concepts (status/lifecycle, roles, personal data, rules, data exchange formats, ...)
   - technical structures (layers, wiring, DB schema, tests)
   - domain structures (bounded contexts, functional areas)

   A concept has a **core** (path or name matches) and **touched** files (they use the core). Concepts overlap on purpose.
3. **Gather signals.** For each language, look for suitable tools, see `references/signal-tools.md`. There is no prescribed tool: use what is common and available in the ecosystem. If a tool is missing or several fit, check the project and installed tools first, then **recommend 1 to 3 candidates to the human with a short comparison and one marked as recommended** (see "When a tool is missing" in `references/signal-tools.md`). Ask before installing anything. Without agreement, fall back to a simple heuristic and label it. Describe what each number proves (see Reliability).
4. **Find implicit dependencies.** The graph from step 3 only sees what is referenced in the code. First identify the **frameworks and programming concepts in use** (build files, configuration, annotations), then search specifically for the implicit couplings typical of them (DI and wiring, events, string keys, reflection, conventions, database logic, shared state). Procedure and catalog per framework: `references/implicit-dependencies.md`. Only for concepts with an uncertain or red-suspect zone, and reported separately as **heuristic**.
5. **Assess observability and recoverability.** Per concept, one level (`good | partial | poor | unknown`) and one line of evidence each.
   - *Observability*: can a wrong change be noticed quickly? Look for logging configuration, metrics and health checks, error tracking, alerting, audit trails, and whether the concept's behaviour is visible in production at all.
   - *Recoverability*: can a wrong change be undone cheaply? Look for reversible migrations (rollback blocks), feature flags, deploy and rollback procedures, backups and restore, idempotent operations, and whether data written by the concept can be repaired.
   - Use `unknown` when you did not check. Do not guess. Poor observability or poor recoverability moves the zone one step stricter.
6. **Ask what the code cannot say.** For red and borderline concepts, ask the human at most five questions: why is it built this way, which external or regulatory constraints apply, what went wrong here before, who understands it, what must never change. Put the answers into `rationale` and `notes`, marked as human-supplied. If nobody is available, say that the rationale is inferred from the code only.
7. **Propose zones** and enter them in `zones.yaml` (schema below), with `reviewed: false`.
8. **Human review.** Show the view, let the human correct it, enter `owner` and, if needed, `notes`. Set `reviewed: true` only after a human confirmed that concept. Changing the zone or rationale afterwards resets it to `false`.
9. **Generate the view** (Markdown table, optionally a treemap by zone). The tool for this is described below (core, adapters, example catalogs).
10. **Make the map seen.** A map nobody reads has no effect. Offer the human to add one line to the agent instructions file (`AGENTS.md` or `CLAUDE.md`) that points to `zones.yaml` and states the rule "check the zone of the concept before changing code; red means ask". Offer path-based deny rules for red zones as an option (see Maintenance). Do not create or edit these files without asking.

## When work starts in a yellow or red concept

Before an agent changes code there, produce a **Comprehension Memo** in a separate, read-only pass: entry points, owners, callers, existing abstractions, tests, production signals, relevant history and open questions, each claim with a reference (file, issue, ownership record or dashboard). Template and rules: `references/comprehension-memo.md`. Save it to `<out>/memos/<concept-key>.md` and link it in `memo:`. Planning starts afterwards with a clean context. Implementation stops if it finds the map was wrong, and the zone is corrected first.

## Manageability (requirement)

A human must be able to walk through and correct the map in one session. Otherwise it is not reviewed, and then it does not count.

- **One page per lens.** Rule of thumb: 15 to 25 concepts in total, never more than 10 per lens. If there are more, merge concepts instead of adding columns. Better to start coarse and refine later.
- **Few signals, the default is exactly these six:** files, LOC, line coverage, dependents (blast radius), dependent templates (only if present), test files. Everything else (branch coverage, churn, authors, TODO counts, hotspots) only on explicit request (`--detail`).
- **Every signal needs a decision it influences.** If a signal cannot move a zone, it does not go into the default view. Leave out signals that yield nothing in this codebase (e.g. churn with a flat Git history) and say so.
- **One to two sentences of rationale per concept**, no more. Long texts are not read.
- **Red candidates and borderline cases first.** Do not have the human go through all concepts as equals: sort by "zone uncertain" and "highest blast radius", and ask for corrections on at most 10 entries at a time.
- **Output in three files:** `zones.yaml` (data, completed by the human), `zones.md` (table for reading), `treemap.html` (overview). No other artifacts in the default run.
- **Implicit dependencies sparingly:** only for uncertain or red-suspect concepts, at most 3 to 5 mechanisms with one piece of evidence each. A negative finding ("events checked, nothing found") belongs there too.
- **Observability and recoverability: one level and one evidence line each.** Not a report.
- **One number, one source.** Do not mix metrics from different tools in one column.

## Reliability of signals

Label every number with its quality and do not mix them:

| Quality | Example |
|---|---|
| **verified** | Dependency from bytecode/AST/import graph, coverage from a test run |
| **heuristic** | Text matching (regex) on file content, naming conventions |
| **missing** | Tool not available, language not covered (e.g. templates, XML wiring, reflection) |

Typical pitfalls:
- Text matching produces chance hits. A hit in the content does not prove a dependency on the core.
- Coverage can come from a partial run (e.g. integration tests with the database skipped). Check the test results before interpreting coverage as a level.
- A flat Git history (import state, squash) makes churn and authors worthless.
- Several concepts per file are condensed to the worst zone in the view. This makes a lot look red. Offer the view per lens.
- No graph tool sees implicit dependencies (DI, reflection, XML/annotation wiring, dynamic imports, templates, forwards via strings). Search for them specifically using the conventions of the framework in question (step 4, `references/implicit-dependencies.md`). The blast radius from the graph is only a lower bound.

## Which zone when (proposal rules)

These are starting points, not formulas.

- **Red**, if at least one applies: security, permissions, billing, audit or regulatory duty (e.g. GxP, finance); personal data; irreversible data or schema migration; consistency across transactions; very high coupling with missing tests; few people understand it; or the behaviour is only really understood by production traffic (no honest test suite and no stand-in such as replayed traffic or a synthetic journey) until a stand-in exists.
- **Yellow**, if domain logic is affected but the impact is limited or verifiable, or tests are thin but Characterization Tests are feasible. External contracts without tests (API, formats) are yellow.
- **Green** only with a gate: isolated, low coupling, a test or build gate exists. If tests are missing everywhere, green only means "low risk, with smoke test", not "safeguarded". Say so openly.
- Poor observability or poor recoverability: one step stricter than the other signals suggest.
- Unsure between two zones: enter the stricter one and state the uncertainty in `notes`.

## zones.yaml

One file per repo (default: `temp/zones/zones.yaml`, versioned would be better if the team uses it).

```yaml
meta: {generated: ..., commit: ...}
concepts:
  <concept-key>:
    lens: technical-crosscutting | domain-crosscutting | technical-structure | domain-structure
    title: ...
    zone: green | yellow | red | null      # null = not yet decided
    reviewed: false                        # true only after a human confirmed this concept
    rationale: >                           # Why (number + evidence + domain reason)
    owner: ""                              # Human, never the agent
    allowed_verbs: ""                      # derived from the zone
    promote_when: ""                       # concrete promotion criterion
    notes: ""                              # "Agent proposal, not reviewed", uncertainties
    observability: {level: unknown, evidence: ""}   # good | partial | poor | unknown
    recoverability: {level: unknown, evidence: ""}  # good | partial | poor | unknown
    implicit_dependencies: []              # searched by the agent: mechanism, count, evidence, confidence (heuristic)
    memo: ""                               # path of the Comprehension Memo (yellow/red, when work starts)
    signals: {...}                         # from the tool, with quality
```

Rules for `rationale`:
- State numbers with their source (e.g. "334 dependent files according to the dependency graph, 0.7 % line coverage according to the coverage run").
- Separate **evidence** from **assumption** (e.g. "regulatory relevance" is domain knowledge and belongs to the human).
- One to two sentences. No running text.

## Maintenance

- The file must be regenerable without overwriting human entries (the script keeps `zone`, `reviewed`, `rationale`, `owner`, `allowed_verbs`, `promote_when`, `notes`, `observability`, `recoverability`, `implicit_dependencies`, `memo`).
- Recurring corrections belong in the harness (hook, deny rule, CI check), not in prose. Red zones can be protected mechanically with path rules in `.claude/settings.json` if the human wants that.
- After promotion: update `notes` and `promote_when`, and record date and reason.

## Tool: core, adapters, example catalogs

```
scripts/zones_signals.py    language-neutral core: path/text matches, size, Git history, zones.yaml, zones.md, treemap.html
scripts/treemap_template.html
adapters/<language>.py      dependency graph, coverage, template edges: only this part is language-specific
adapters/_common.py         Cobertura/Clover parser, template resolution
examples/<language>/concepts.yaml   example catalog of concepts
```

Usage:
```
python3 -I .agents/skills/blast-radius-map/scripts/zones_signals.py --adapter java|python|php [--repo <pfad>] [--out <ordner>] [--concepts <datei>] [--detail]
```
Output goes to `<repo>/temp/zones/` by default. The script takes the catalog from `<out>/concepts.yaml`, otherwise from `examples/<adapter>/`. Copy the example catalog to `<out>/concepts.yaml` and adapt it to the project. The domain concepts in the examples are placeholders.

| Adapter | Dependencies (verified) | Coverage | Template edges | Prerequisite |
|---|---|---|---|---|
| `java` | `jdeps` on `*/target/classes` | JaCoCo `jacoco.xml` | Servlet↔JSP (`Page` enum, `import`, `useBean`, `include`) | Maven project, compiled, JaCoCo report |
| `python` | Import graph from `ast` (stdlib, no extra packages) | coverage.py `coverage.xml` | `render`, `render_template`, `{% include/extends %}` | `coverage run --branch --source=... && coverage xml` |
| `php` | Class index plus `use` resolution (without PHP runtime) | PHPUnit Clover or Cobertura | `view()`, `@include/@extends` (Blade), `render`/`include` (Twig) | `phpunit --coverage-clover clover.xml` with Xdebug/PCOV |

`zones.md` has the columns Concept, Zone, Rev. (reviewed), Files, LOC, Cov. %, Dependents, Templates, Tests, and Obs./Rec. once observability or recoverability is filled in. With `--detail` it adds Branch %, Core/Text, Commits {w}M, Authors {w}M, Top author, TODO, Last change.

Every adapter provides the same three things, so the core does not need to know anything about the language: `load_deps(repo, info, out)`, `load_coverage(repo, info, out)` and `load_extra_edges(repo, info, out)`, plus `is_test`, `is_code`, `is_template`, `EXTENSIONS`. For a new language, write another adapter following this pattern (see `signal-tools.md` for tools). If something is missing, the adapter returns `None` or `{}`, and the column stays empty instead of guessing.

Limits of the adapters:
- They only see static imports, not container wiring, reflection, plugins or configuration strings (see adapter header).
- Python and PHP were tested with small synthetic projects (import graph, template edges, coverage parser), not on a large real project. Spot-check the numbers before relying on them.
- The Java adapter grew up on OpenClinica (Maven multi-module, JSP). For other Java projects (Gradle, Spring Boot without JSP) it needs adjustment.
