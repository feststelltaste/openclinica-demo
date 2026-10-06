"""PHP adapter: class dependencies via declaration index plus use resolution (without a PHP runtime),
coverage from PHPUnit (Clover or Cobertura), template edges for Laravel (Blade) and Symfony (Twig).

Prerequisite for coverage: `phpunit --coverage-clover clover.xml` (or --coverage-cobertura) with a coverage driver
(Xdebug or PCOV). Set `<source>` or `<coverage processUncoveredFiles="true">` in phpunit.xml, otherwise
never-loaded files are missing from the report and appear as "–" instead of 0 %.
Not visible: container autowiring (Laravel/Symfony DI), service locator, dynamic class names,
facades, routes and events as strings, Doctrine mapping via annotations/attributes.
"""
import collections, re
import xml.etree.ElementTree as ET

import _common as C

CODE_EXT = (".php",)
TEMPLATE_EXT = (".blade.php", ".twig", ".phtml")
EXTENSIONS = ["php", "twig", "phtml", "sql", "xml", "yaml", "yml", "ini"]
_TEST = re.compile(r"(^|/)tests?/|Test\.php$")


def is_test(p):
    return bool(_TEST.search(p))


def is_template(p):
    return p.endswith(TEMPLATE_EXT)


def is_code(p):
    return p.endswith(".php") and not is_template(p)


_NS = re.compile(r"^\s*namespace\s+([\w\\]+)\s*[;{]", re.M)
_DECL = re.compile(r"^\s*(?:(?:abstract|final|readonly)\s+)*(?:class|interface|trait|enum)\s+(\w+)", re.M)
_USE = re.compile(r"^\s*use\s+(?!function\b|const\b)([^;(]+);", re.M)
_FQ = re.compile(r"(?<![\w\\])\\([A-Za-z_]\w*(?:\\[A-Za-z_]\w*)+)")
_REL = re.compile(r"\bnew\s+([A-Z]\w*)|\b([A-Z]\w*)::")


def _index(info):
    fq = {}
    for f, d in info.items():
        if not is_code(f):
            continue
        ns = _NS.search(d["txt"])
        ns = ns.group(1) if ns else ""
        for name in _DECL.findall(d["txt"]):
            fq.setdefault((ns + "\\" + name) if ns else name, f)
    return fq


def _use_targets(stmt):
    stmt = stmt.strip().lstrip("\\")
    if "{" in stmt:                                    # group use: A\B\{C, D as E}
        prefix, rest = stmt.split("{", 1)
        return [prefix.strip() + p.split(" as ")[0].strip() for p in rest.rstrip("} ").split(",") if p.strip()]
    return [p.split(" as ")[0].strip().lstrip("\\") for p in stmt.split(",") if p.strip()]


def load_deps(repo, info, out):
    fq = _index(info)
    if not fq:
        return None
    deps = collections.defaultdict(set)
    for f, d in info.items():
        if not is_code(f):
            continue
        txt = d["txt"]
        ns = _NS.search(txt)
        ns = ns.group(1) if ns else ""
        names = set()
        for stmt in _USE.findall(txt):
            names.update(_use_targets(stmt))
        names.update(_FQ.findall(txt))
        for a, b in _REL.findall(txt):                 # classes in the own namespace
            n = a or b
            if ns:
                names.add(ns + "\\" + n)
        for n in names:
            g = fq.get(n)
            if g and g != f:
                deps[f].add(g)
    return deps


def load_coverage(repo, info, out):
    x = C.first_existing(repo, ["clover.xml", "build/logs/clover.xml", "build/coverage/clover.xml", "coverage/clover.xml",
                                "coverage.xml", "build/logs/cobertura.xml", "cobertura.xml"])
    if not x:
        return {}
    files = [f for f in info if is_code(f)]
    root = ET.parse(x).getroot()
    return C.parse_clover(x, files) if root.find("project") is not None else C.parse_cobertura(x, files)


_CODE_REFS = [re.compile(p) for p in (
    r"\bview\(\s*['\"]([\w.\-/]+)['\"]",
    r"View::make\(\s*['\"]([\w.\-/]+)['\"]",
    r"\brender(?:View|Response)?\(\s*['\"]([^'\"]+)['\"]",
    r"['\"]template['\"]\s*=>\s*['\"]([^'\"]+)['\"]",
)]
_TPL_REFS = [re.compile(p) for p in (
    r"@(?:include|extends|component|includeIf|each)\(\s*['\"]([\w.\-/]+)['\"]",
    r"\{%\s*(?:include|extends|embed)\s+['\"]([^'\"]+)['\"]",
    r"\binclude\(\s*['\"]([^'\"]+)['\"]",
)]


def _cands(name):
    name = re.sub(r"^@\w+/", "", name)
    if name.endswith((".twig", ".phtml", ".php")):
        return [name]
    p = name.replace(".", "/")
    return [p + ".blade.php", p + ".php"]


def load_extra_edges(repo, info, out=None):
    code = [f for f in info if is_code(f)]
    tpls = [f for f in info if is_template(f)]
    texts = {f: info[f]["txt"] for f in code + tpls}
    return (C.template_edges(code, texts, tpls, _CODE_REFS, _cands), {},
            C.template_edges(tpls, texts, tpls, _TPL_REFS, _cands))
