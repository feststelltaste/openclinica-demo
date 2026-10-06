# Tools for Signals by Ecosystem

This is a memory aid, not a requirement. First check what is already configured or installed in the project (build plugins, CI, `package.json` scripts, `Makefile`, `tox.ini`). Use what is customary for the language and record what is verified and what is only estimated.

| Ecosystem | Direct dependencies (verified) | Implicit / estimate | Coverage | Notes |
|---|---|---|---|---|
| **Java/Kotlin/Scala** | `jdeps -verbose:class`, ArchUnit, jQAssistant, `mvn dependency:tree` (external) | Spring XML/annotation wiring, reflection, JSP/templates via regex | JaCoCo (Maven/Gradle), Kover, scoverage | Needs bytecode, so compile first. Watch the JDK version. |
| **JavaScript/TypeScript** | `madge`, `dependency-cruiser`, `knip`, `ts-prune`, `tsc --listFiles` | dynamic `import()`, `require` with variables, Next/Nuxt/routing conventions | `c8`, `nyc`/Istanbul, Vitest/Jest `--coverage` | Monorepo: workspace boundaries are concept candidates. |
| **Python** | `grimp`, `import-linter`, `pydeps`, `pipdeptree` (external) | `importlib`, plugins/entry points, Django settings and signals | `coverage.py`, `pytest-cov` | High dynamic behavior, coverage and types help as additional evidence. |
| **Go** | `go list -deps -json`, `go mod graph`, `go-callvis` | Interfaces plus dependency injection, codegen | `go test -cover -coverprofile` | Package boundaries are usually clean concept candidates. |
| **Rust** | `cargo tree`, `cargo-modules`, `cargo-deps` | Macros, feature flags, `unsafe` with `cargo-geiger` | `cargo-llvm-cov`, `tarpaulin` | `unsafe` and FFI as a red signal. |
| **C#/.NET** | NDepend, `dotnet list package`, Roslyn analyzer, `dotnet-depends` | DI container, reflection, Razor views | `coverlet`, `dotnet-coverage` | Project boundaries (csproj) as structure. |
| **C/C++** | `gcc -MM`/`clang -MM`, `include-what-you-use`, `cscope`, Doxygen graphs | Macros, conditional compilation, build variants | `gcov`/`lcov`, `llvm-cov` | The include graph is coarse, link boundaries add to it. |
| **PHP** | `deptrac`, `phpmetrics`, `composer depends` | Autoload, container, templates (Twig/Blade) | PHPUnit `--coverage-*` | |
| **Ruby** | `packwerk`, `rubycritic`, Zeitwerk conventions | Metaprogramming, Rails conventions | `simplecov` | Rails: convention instead of import. |
| **SQL/DB** | Schema introspection, `pg_depend`, foreign key graph | Stored procedures, dynamic SQL, triggers | – | Triggers and procedures are implicit logic, often red. |
| **Cross-language** | `tree-sitter`, `ctags`, `semgrep` (custom rules), `ast-grep` | Naming conventions, `grep` on framework IDs | – | Good for cross-cutting topics without a language tool. |

## Always available (language-independent)

- **Size:** `cloc`, `scc`, or counting lines. Per concept, not per package.
- **History:** `git log --name-only --format=...` for commits, authors, last change. First check whether the history is real (many commits, distributed authors). Tools like `code-maat` and `git-of-theseus` offer more but are optional.
- **Ownership:** `CODEOWNERS`, `git shortlog -sn -- <pfad>`. A top-author share (bus factor) says how few people understand it.
- **Markers:** count `TODO|FIXME|HACK|@Deprecated`.
- **Tests:** number of test files per concept, plus coverage from a real run. Check whether the run was complete (skipped tests, missing database or services).
- **Production signals**, if accessible: incident archive, error rates, logs. They belong in the Comprehension Memo, not in the metrics.

## When a tool is missing, or several are possible

Do not silently pick a tool, and do not silently skip a signal. Offer the human a short, justified recommendation.

1. **Check what already exists**: project (CI configuration, build plugins, scripts), then the ecosystem cache (`~/.m2`, `~/.cache`, `node_modules/.bin`), then what is installed (`which`, `--version`). Prefer what the project already uses.
2. **Search the web briefly** for the usual solution in this ecosystem if nothing fits.
3. **Recommend 1 to 3 candidates**, not a long list, as a small table the human can answer in one line:

   | Candidate | Signal it adds | Reliability | Effort / cost | Risks |
   |---|---|---|---|---|
   | e.g. `dependency-cruiser` | import graph (dependents) | verified | `npx`, no install into the project, a minute | misses dynamic imports |
   | e.g. `c8` / `vitest --coverage` | line coverage | verified (needs a full test run) | runs the test suite, may need services | partial run gives a misleading number |

   Mark one as **recommended** and say why (most common in the ecosystem, already half-configured, cheapest, no change to the project). Name what you would give up without it.
4. **Ask before** installing anything, changing project files (build configuration, `pom.xml`, `package.json`), running long test suites, or starting services such as databases. Offer a no-install path when one exists (`npx`, `uvx`, `pipx`, a throw-away virtualenv or container, a command-line plugin invocation instead of editing the build file).
5. **If the human declines or nothing fits**, fall back to a heuristic and label the signal **heuristic**; if there is no sensible heuristic, label it **missing** and leave the column empty rather than guessing.
6. **Write down the decision** (tool, version, command) in `notes` or next to the generated files, so the next run is reproducible.
