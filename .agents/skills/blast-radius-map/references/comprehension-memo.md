# Comprehension Memo

A short, read-only research result for one concept, written **before** an agent changes code in a yellow or red zone. It exists so the next session does not pay for the same archaeology again. Chat history is not a system of record, especially after compaction.

## Rules

- **Read-only pass.** No changes to code, tests or configuration while writing it.
- **Every claim cites something**: a file and line, an issue, an ownership record, a dashboard, a commit. A claim without a reference goes under "Open questions" or is dropped.
- **Short.** One page. Lists and one-line items, no running text.
- **Say what you did not check.** An empty section is only acceptable with "checked, nothing found" and what was checked.
- **A human picks the path afterwards.** The memo does not recommend an implementation.
- Save to `<out>/memos/<concept-key>.md` and link it from `zones.yaml` (`memo:`).

## Template

```markdown
# Memo: <concept title> (`<concept-key>`)
Zone: <red|yellow>   Date: <date>   Commit: <sha>   Author: <agent or human>

## Purpose
One or two sentences: what this concept does for the business or the system.

## Entry points
- <where execution or requests enter> (<file:line>)

## Owners
- <person/team> (<CODEOWNERS entry / git shortlog / ticket>) or "none found"

## Callers and dependents
- Direct: <n> files, main ones: <file>, <file> (<source: dependency graph tool>)
- Implicit (heuristic): <mechanism>, <n>, e.g. <file:line>

## Existing abstractions
- <class/module that already does part of the job and should be reused> (<file:line>)

## Tests
- <test files / coverage of the concept> and what they really prove, including gaps

## Production signals
- <logs, metrics, alerts, incidents, usage> (<dashboard / log config / ticket>) or "none available"

## Relevant history
- <commit/issue/decision that explains a counter-intuitive implementation> (<ref>)

## Observability and recoverability
- Observability: <level>, <evidence>
- Recoverability: <level>, <evidence>

## Invariants that must be preserved
- <behaviour the business depends on, ugly parts included> (<ref>)

## Open questions
- <question for the human or owner>

## Not checked
- <what was not looked at, and why>
```

## After the memo

1. Planning starts in a clean context. Ask which files the plausible approaches touch, which invariants they preserve, and how each can be reversed.
2. A human picks the path.
3. Implementation stops if it finds the map was wrong (a missing caller, a different owner). Fix the zone and memo first.
4. Review starts fresh and works backwards from the acceptance criteria.
