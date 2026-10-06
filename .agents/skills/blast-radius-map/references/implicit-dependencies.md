# Finding Implicit Dependencies

A dependency graph (import, bytecode, `use`) only sees what is referenced in the code. In most frameworks, a large part of the coupling runs through **conventions, configuration and strings**. The blast radius from the graph is therefore a lower bound.

## Procedure

1. **Identify frameworks and concepts**: build files (`pom.xml`, `build.gradle`, `package.json`, `pyproject.toml`, `composer.json`, `go.mod`, `Cargo.toml`, `*.csproj`), configuration files, annotations/decorators, directory structure. Note the list (e.g. "Spring 4 with XML wiring, Hibernate, Quartz, JSP").
2. **Take the typical implicit couplings** of these frameworks and concepts from the catalog below.
3. **Search specifically**: with `grep`/`rg`, `ast-grep`, `semgrep` or a custom rule. Count hits per concept and note 1 to 2 pieces of evidence (file:line).
4. **Report separately**: implicit dependencies are **heuristic**, never "verified". Enter them as `implicit_dependencies` in the YAML (mechanism, evidence, count), not in the "Dependents" column.
5. **Include them in the rationale**: high implicit coupling is a reason to choose a stricter zone. If there is no trace at all, write which mechanisms you checked, so the human knows what was not searched.
6. **Not too much**: only concepts where the zone is uncertain or red-suspect get the deep search. At most 3 to 5 mechanisms per concept, with evidence.

## Framework-independent concepts (always check)

| Concept | How to recognize it | Search |
|---|---|---|
| **Dependency injection / container** | Classes are not created with `new` but supplied by the container | Annotations/decorators (`@Autowired`, `@Inject`, `@Service`), container configuration, provider registration |
| **Events / pub-sub / signals** | Sender does not know the receiver | `publish`, `emit`, `dispatch`, `@EventListener`, `signals.connect`, `Event::listen`, topic and queue names |
| **String keys** | Coupling via names: config keys, i18n keys, feature flags, cache keys, route names, queue/topic names, SQL tables and columns | Compare definition and use of the string (only one side = dead or external entry) |
| **Reflection / dynamic loading** | Class is loaded by name | `Class.forName`, `importlib`, `__import__`, `new $class`, `Activator.CreateInstance`, `require(variable)` |
| **Inheritance / template method / hooks** | Base class calls subclasses or vice versa | Base classes with many subclasses, abstract methods, callbacks |
| **AOP, proxies, middleware, filters, interceptors** | Cross-cutting behavior without a call | Aspect definitions, middleware lists, filter chains, `@Transactional`/`@Cacheable` |
| **Code generation / build time** | Source code is created during the build | Generator configuration, `generated` folder, annotation processors, macros |
| **Shared state** | Session, globals, thread-local, static fields, singletons | `HttpSession`, `$_SESSION`, `ThreadLocal`, `static`, singleton pattern, request attributes |
| **Database as interface** | Triggers, views, stored procedures, foreign keys, sequences, other applications on the same DB | Schema introspection, migrations, SQL files |
| **Outside world** | Files, HTTP endpoints, queues, cron, batch jobs, email | Paths and URLs as constants, scheduler configuration, crontabs |

## Catalog per framework

### Java: Spring, Servlet/JSP, Hibernate, Quartz
- **Spring wiring in XML** (`applicationContext*.xml`, `<bean class="…">`, `ref=`): beans that are referenced nowhere in the code.
- **Component scan and stereotypes** (`@Component`, `@Service`, `@Repository`, `@Controller`), `@Autowired`, `@Qualifier`, `@Resource` (name-based).
- **AOP and proxies**: `@Transactional`, `@Cacheable`, `@Async`, aspects (`@Aspect`, `<aop:config>`).
- **Configuration keys**: `@Value("${…}")`, `Environment.getProperty`, `*.properties`, custom `CoreResources`-style classes with string keys.
- **Servlet container**: `web.xml` (servlet mappings, filters, listeners, session config), URL patterns to classes, JNDI lookups.
- **Forwards and views**: `forward("…")`, `setViewName`, enum or constant classes with JSP paths, `RequestDispatcher`.
- **Hibernate/JPA**: mapping in `hbm.xml` or annotations, HQL/JPQL and named queries as strings, lazy loading and cascade, entities that are imported nowhere but mapped.
- **Quartz/scheduler**: job classes in XML or properties, cron expressions, `@Scheduled`.
- **Security**: URL patterns in `security-config.xml`, `@PreAuthorize`, roles as strings.
- **JSP/taglibs**: `<%@ taglib %>`, EL expressions on request/session attributes (`request.setAttribute("name", …)` in the servlet, `${name}` in the JSP).

### Python: Django, Flask, SQLAlchemy, Celery
- **Django**: `INSTALLED_APPS`, `MIDDLEWARE`, `ROOT_URLCONF` and `include("app.urls")` (strings), models via string reference (`ForeignKey("app.Model")`), signals (`@receiver`), management commands, template tags and filters, `AppConfig.ready()`, admin registration, `settings.X` as global state, `GenericForeignKey`.
- **Flask**: blueprints (`register_blueprint`), extensions (`init_app`), `before_request`/`after_request`, `current_app`, `g`, `session`.
- **SQLAlchemy**: `relationship("Name")` via string, events (`@event.listens_for`), declarative registry.
- **Celery/RQ**: tasks by name (`send_task("pkg.task")`), `CELERY_BEAT_SCHEDULE`, routing configuration.
- **Plugins and entry points**: `pyproject.toml` `[project.entry-points]`, `pkg_resources`, `importlib.metadata`.
- **pytest**: `conftest.py` and fixtures (test coupling via names), `pytest-django` settings.

### PHP: Laravel, Symfony, Doctrine/Eloquent
- **Laravel**: service providers (`register`/`boot`, `bind`, `singleton`), facades (`DB::`, `Cache::`, `Auth::`), events and listeners (`EventServiceProvider`, `$listen`), observers, policies and gates, routes (`Route::get('…', [Controller::class, 'm'])`, string controllers), Eloquent relations and morph maps, `config('a.b')` and `env()`, Blade components and `@include`, middleware aliases, jobs by class name.
- **Symfony**: `services.yaml` (autowiring, tags, `_defaults`), event subscribers, compiler passes, routes (YAML, attributes), messenger handlers, Twig extensions, form types, voters, Doctrine mapping (XML, attributes), parameters (`%param%`).
- **Doctrine/Eloquent**: lifecycle callbacks, query builder with table/column strings, global scopes.

### JavaScript/TypeScript: Node, React, Angular, Nest, Next
- **Dynamic imports** (`import()`, `require(variable)`), barrel files (`index.ts` with `export *`), path aliases (`tsconfig paths`, Webpack/Vite alias).
- **DI frameworks**: Angular (`providers`, modules), Nest (`@Injectable`, `@Module`), Inversify.
- **File conventions**: Next/Nuxt/Remix routing from the file system, `pages/` and `app/`, middleware files.
- **State and context**: React context, global stores (Redux, Pinia), `window.*`, `localStorage`.
- **Environment**: `process.env.*`, `.env` files, build-time substitution.
- **Monorepo**: workspace dependencies in `package.json`, build order.

### Go
- **Interfaces are satisfied implicitly**: the compiler does not show who implements an interface. Search for implementations via method signatures (`gopls implementations`).
- **`init()` and blank imports** (`import _ "pkg"`) for side effects (drivers, registration).
- **Build tags**, code generation (`go generate`, wire, mockgen), reflection via struct tags (`json:`, `db:`).

### Rust
- **Traits and generics**: implementations spread across crates. **Macros** (`macro_rules!`, proc macros) generate code. **Feature flags** (`cfg(feature)`) change what gets compiled.

### .NET/C#
- **DI registrations** (`services.AddScoped<…>()`), `appsettings.json` keys and `IOptions<T>`, reflection (`Activator`, `Assembly.GetTypes`), attributes and filters, MediatR handlers (request to handler by type), EF conventions and `OnModelCreating`, Razor views and view components.

### Ruby on Rails
- **Conventions instead of references**: controller↔view↔helper↔model by name, Zeitwerk autoloading, callbacks (`before_action`, `after_save`), concepts, `routes.rb` to controllers, engines, `config/initializers`, ActiveRecord associations via symbol.

### Database (all languages)
- **Triggers, views, stored procedures, constraints** that contain logic. **Multiple applications** on the same database. **ETL and reporting jobs** that read tables directly. Check the schema and migrations for logic that the application code does not show.

## How to record the findings

In `zones.yaml` per concept (only if relevant):

```yaml
implicit_dependencies:
  - mechanism: Spring-XML-Wiring
    count: 41            # beans in the concept that are wired only via XML
    evidence: ["web/src/main/resources/applicationContext-core-security.xml:12"]
    confidence: heuristic
  - mechanism: Request-Attribute (Servlet → JSP)
    count: ~120
    evidence: ["…/AddNewSubjectServlet.java:207"]
    confidence: heuristic
```

What matters is **what was searched**, even with zero hits ("events/signals checked, none found"), so nobody mistakes a gap for an all-clear.
