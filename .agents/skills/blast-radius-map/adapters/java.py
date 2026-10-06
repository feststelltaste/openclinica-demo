"""Java/Kotlin adapter (Maven): dependencies from `jdeps`, coverage from JaCoCo,
edges between servlets and JSPs (Page enum, import/useBean, include).

Prerequisite for verified signals: compiled classes in */target/classes and
JaCoCo reports (*/target/site/jacoco/jacoco.xml). Otherwise the adapter returns None/{}.
"""
import collections, re, subprocess
from pathlib import Path

CODE_EXT = (".java", ".groovy")
TEMPLATE_EXT = (".jsp", ".tag")
EXTENSIONS = ["java", "groovy", "jsp", "tag", "xml", "properties", "sql", "js"]


def modules(repo):
    """Maven modules = top-level folders with pom.xml (in multi-module projects)."""
    return [d.name for d in sorted(Path(repo).iterdir()) if d.is_dir() and (d / "pom.xml").exists()] or ["."]


def is_code(p):
    return p.endswith(CODE_EXT)


def is_template(p):
    return p.endswith(TEMPLATE_EXT)


def is_test(p):
    return "/src/test/" in p


def load_coverage(repo, info, out):
    """Per source file: {'lc': lines covered, 'lm': missed, 'bc': , 'bm': } from target/site/jacoco/jacoco.xml."""
    import xml.etree.ElementTree as ET
    cov = {}
    for m in modules(repo):
        x = repo / m / "target/site/jacoco/jacoco.xml"
        if not x.exists():
            continue
        for pkg in ET.parse(x).getroot().iter("package"):
            for sf in pkg.findall("sourcefile"):
                rel = f"{m}/src/main/java/{pkg.get('name')}/{sf.get('name')}".removeprefix("./")
                c = {k.get("type"): (int(k.get("covered")), int(k.get("missed"))) for k in sf.findall("counter")}
                l, b = c.get("LINE", (0, 0)), c.get("BRANCH", (0, 0))
                cov[rel] = {"lc": l[0], "lm": l[1], "bc": b[0], "bm": b[1]}
    return cov


def load_deps(repo, info, out):
    """Class edges from jdeps -> {file: set(files it depends on)}; None if no classes are present."""
    cache = out / "cache" / "jdeps.txt"
    dirs = [str(repo / m / "target/classes") for m in modules(repo) if (repo / m / "target/classes").exists()]
    if not dirs:
        return None
    if not cache.exists():
        cache.parent.mkdir(exist_ok=True)
        r = subprocess.run(["jdeps", "--multi-release", "17", "-verbose:class", *dirs], capture_output=True, text=True)
        cache.write_text(r.stdout)
    src_roots = [f"{m}/src/main/java/" for m in modules(repo)]

    def to_file(cls):
        base = cls.split("$", 1)[0].replace(".", "/") + ".java"
        for r in src_roots:
            if (repo / (r + base)).exists():
                return r + base
        return None

    memo, deps = {}, collections.defaultdict(set)
    for line in cache.read_text().splitlines():
        m = re.match(r"^\s+(\S+)\s+->\s+(\S+)\s+(\S+)\s*$", line)
        if not m or not m.group(1).startswith("org.") or m.group(3) in ("java.base", "not", "found"):
            continue
        a, b = m.group(1), m.group(2)
        for k in (a, b):
            if k not in memo:
                memo[k] = to_file(k)
        if memo[a] and memo[b] and memo[a] != memo[b]:
            deps[memo[a]].add(memo[b])
    return deps


PAGE_DEF = re.compile(r'Page\s+([A-Z][A-Z0-9_]*)\s*=\s*new\s+Page\(\s*(?:path\s*\+\s*)?"([^"]+)"', re.S)
PAGE_USE = re.compile(r'\bPage\.([A-Z][A-Z0-9_]*)\b')
JSP_IMPORT = re.compile(r'<%@\s*page[^%]*?\bimport\s*=\s*"([^"]+)"', re.S)
JSP_BEAN = re.compile(r'<jsp:useBean[^>]*?\bclass\s*=\s*"([^"]+)"', re.S)
JSP_INCLUDE = re.compile(r'(?:jsp:include\s+page|c:import\s+url|%@\s*include\s+file)\s*=\s*"([^"$]+)"')


def load_extra_edges(repo, info, out=None):
    """Edges between JSP and Java: servlet->jsp (Page enum), jsp->java (import/useBean), jsp->jsp (include).
    Returns: (java_to_jsp, jsp_to_java, jsp_to_jsp)"""
    jsps = {f for f in info if f.endswith((".jsp", ".tag"))}
    by_suffix = collections.defaultdict(list)
    for f in jsps:
        by_suffix[f.rsplit("/", 1)[-1]].append(f)

    def resolve_page(path):                      # "/WEB-INF/jsp/a/b.jsp" -> repo file
        rel = path.split("?")[0].lstrip("/")
        return [f for f in by_suffix.get(rel.rsplit("/", 1)[-1], []) if f.endswith("/" + rel)]

    pages = {}
    for f in info:
        if f.endswith("/view/Page.java"):
            for name, path in PAGE_DEF.findall(info[f]["txt"]):
                pages.setdefault(name, set()).update(resolve_page(path))

    java_to_jsp = collections.defaultdict(set)
    for f, d in info.items():
        if f.endswith(".java") and "/src/main/" in f and not f.endswith("/view/Page.java"):
            for n in PAGE_USE.findall(d["txt"]):
                java_to_jsp[f] |= pages.get(n, set())

    src_roots = [f"{m}/src/main/java/" for m in modules(repo)]
    java_files = {f for f in info if f.endswith(".java")}

    def cls_file(cls):
        cand = cls.strip().split("$", 1)[0].replace(".", "/") + ".java"
        return next((r + cand for r in src_roots if r + cand in java_files), None)

    jsp_to_java, jsp_to_jsp = collections.defaultdict(set), collections.defaultdict(set)
    for f in jsps:
        txt = info[f]["txt"]
        for imp in JSP_IMPORT.findall(txt):
            for c in imp.split(","):
                t = cls_file(c) if not c.strip().endswith("*") else None
                if t:
                    jsp_to_java[f].add(t)
        for c in JSP_BEAN.findall(txt):
            t = cls_file(c)
            if t:
                jsp_to_java[f].add(t)
        base = f.rsplit("/", 1)[0]
        for inc in JSP_INCLUDE.findall(txt):
            parts = [] if inc.startswith("/") else base.split("/")
            for seg in inc.split("/"):
                if seg == "..":
                    parts and parts.pop()
                elif seg not in ("", "."):
                    parts.append(seg)
            cand = "/".join(parts)
            hit = cand if cand in jsps else next((j for j in by_suffix.get(inc.rsplit("/", 1)[-1], []) if j.endswith("/" + inc.lstrip("/"))), None)
            if hit:
                jsp_to_jsp[f].add(hit)
    return java_to_jsp, jsp_to_java, jsp_to_jsp


