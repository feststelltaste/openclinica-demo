"""Python adapter: import graph from `ast` (stdlib only), coverage from coverage.py (Cobertura XML),
template edges for Django/Flask/Jinja.

Prerequisite for coverage: `coverage run --branch --source=<package> -m pytest && coverage xml` (coverage.xml in the repo root).
Without `--source`, never-imported files are missing from the report and appear as "–" instead of 0 %.
Without a report, load_coverage returns {} and the columns stay empty.
Not visible: dynamic imports (importlib, __import__), plugins/entry points, Django settings strings
(INSTALLED_APPS, MIDDLEWARE), signals, Celery task strings.
"""
import ast, collections, re
from pathlib import Path

import _common as C

CODE_EXT = (".py",)
TEMPLATE_EXT = (".html", ".jinja", ".jinja2", ".j2")
EXTENSIONS = ["py", "html", "jinja", "jinja2", "j2", "sql", "yaml", "yml", "toml", "ini", "cfg", "po"]
_TEST = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$")


def is_test(p):
    return bool(_TEST.search(p))


def is_code(p):
    return p.endswith(CODE_EXT)


def is_template(p):
    return p.endswith(TEMPLATE_EXT)


def _module_names(py_files):
    """Module name <-> file. Climbs __init__.py chains, adds namespace packages via the repo path."""
    files = set(py_files)
    pkg_dirs = {f.rsplit("/", 1)[0] if "/" in f else "" for f in files if f.rsplit("/", 1)[-1] == "__init__.py"}
    name_to_file, file_to_name = {}, {}
    for f in sorted(files):
        d, _, base = f.rpartition("/")
        stem = base[:-3]
        chain = []
        while d and d in pkg_dirs:
            chain.insert(0, d.rsplit("/", 1)[-1])
            d = d.rpartition("/")[0]
        name = ".".join(chain + ([] if stem == "__init__" else [stem])) if chain or stem != "__init__" else ""
        dotted = f[:-3].replace("/", ".")
        if dotted.endswith(".__init__"):
            dotted = dotted[: -len(".__init__")]
        for n in {name, dotted, re.sub(r"^(src|lib)\.", "", dotted)}:
            if n and n not in name_to_file:
                name_to_file[n] = f
        file_to_name[f] = name or dotted
    return name_to_file, file_to_name


def _resolve(mod, name_to_file):
    parts = mod.split(".")
    for i in range(len(parts), 0, -1):                 # longest prefix that is a module
        f = name_to_file.get(".".join(parts[:i]))
        if f:
            return f
    return None


def load_deps(repo, info, out):
    py = [f for f in info if f.endswith(".py")]
    if not py:
        return None
    n2f, f2n = _module_names(py)
    deps = collections.defaultdict(set)
    for f in py:
        try:
            tree = ast.parse(info[f]["txt"])
        except SyntaxError:
            continue
        me = f2n[f]
        pkg = me if f.endswith("__init__.py") else me.rpartition(".")[0]
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    up = pkg.split(".") if pkg else []
                    up = up[: len(up) - (node.level - 1)] if node.level > 1 else up
                    base = ".".join([p for p in up + ([base] if base else []) if p])
                targets = [base] + [f"{base}.{a.name}" for a in node.names if a.name != "*"]
            for t in targets:
                g = _resolve(t, n2f) if t else None
                if g and g != f:
                    deps[f].add(g)
    return deps


def load_coverage(repo, info, out):
    x = C.first_existing(repo, ["coverage.xml", "reports/coverage.xml", "build/coverage.xml", "htmlcov/coverage.xml"])
    return C.parse_cobertura(x, [f for f in info if f.endswith(".py")]) if x else {}


_CODE_REFS = [re.compile(p) for p in (
    r"render\(\s*(?:request\s*,\s*)?[\"']([^\"']+\.(?:html|jinja2?|j2))[\"']",
    r"render_template\(\s*[\"']([^\"']+)[\"']",
    r"get_template\(\s*[\"']([^\"']+)[\"']",
    r"TemplateResponse\(\s*(?:request\s*,\s*)?[\"']([^\"']+)[\"']",
    r"template_name\s*=\s*[\"']([^\"']+)[\"']",
)]
_TPL_REFS = [re.compile(r"\{%\s*(?:include|extends)\s+[\"']([^\"']+)[\"']")]


def load_extra_edges(repo, info, out=None):
    code = [f for f in info if is_code(f)]
    tpls = [f for f in info if is_template(f)]
    texts = {f: info[f]["txt"] for f in code + tpls}
    ident = lambda n: [n]
    code_to_tpl = C.template_edges(code, texts, tpls, _CODE_REFS, ident)
    tpl_to_tpl = C.template_edges(tpls, texts, tpls, _TPL_REFS, ident)
    return code_to_tpl, {}, tpl_to_tpl
