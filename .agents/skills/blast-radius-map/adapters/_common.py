"""Shared helpers for adapters: Cobertura/Clover parsers and template resolution."""
import collections
import xml.etree.ElementTree as ET
from pathlib import Path


def resolve_by_suffix(path_in_report, files_by_name, roots=()):
    """Maps a path from a report (relative, absolute or with source root) to a repo file."""
    p = path_in_report.replace("\\", "/")
    name = p.rsplit("/", 1)[-1]
    cands = files_by_name.get(name, [])
    if len(cands) == 1:
        return cands[0]
    best = None
    for c in cands:                                   # longest common path suffix
        if p.endswith(c) or c.endswith(p.lstrip("/")) or any((r.rstrip("/") + "/" + p).endswith(c) for r in roots):
            if best is None or len(c) > len(best):
                best = c
    return best


def index_by_name(files):
    idx = collections.defaultdict(list)
    for f in files:
        idx[f.rsplit("/", 1)[-1]].append(f)
    return idx


def parse_cobertura(xml_path, files):
    """Cobertura-XML (coverage.py `coverage xml`, PHPUnit --coverage-cobertura, ...) -> {file: {lc,lm,bc,bm}}.
    Lines are deduplicated per file (Cobertura lists them multiple times per class and method)."""
    import re
    root = ET.parse(xml_path).getroot()
    roots = [s.text.strip() for s in root.iter("source") if s.text]
    idx = index_by_name(files)
    lines = collections.defaultdict(dict)             # file -> {line number: (hit, branches hit, branches total)}
    for cls in root.iter("class"):
        fn = cls.get("filename")
        f = resolve_by_suffix(fn, idx, roots) if fn else None
        if not f:
            continue
        for ln in cls.iter("line"):
            n = ln.get("number")
            if n is None:
                continue
            hit = int(ln.get("hits", "0")) > 0
            m = re.search(r"\((\d+)/(\d+)\)", ln.get("condition-coverage", ""))
            br = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
            old = lines[f].get(n)
            if old:
                hit, br = hit or old[0], max(br, old[1:], key=lambda x: x[1])
            lines[f][n] = (hit, *br)
    out = {}
    for f, ls in lines.items():
        lc = sum(1 for v in ls.values() if v[0])
        bc, bt = sum(v[1] for v in ls.values()), sum(v[2] for v in ls.values())
        out[f] = {"lc": lc, "lm": len(ls) - lc, "bc": bc, "bm": bt - bc}
    return out


def parse_clover(xml_path, files):
    """Clover-XML (PHPUnit --coverage-clover) -> {file: {lc,lm,bc,bm}}."""
    root = ET.parse(xml_path).getroot()
    idx = index_by_name(files)
    out = {}
    for fe in root.iter("file"):
        f = resolve_by_suffix(fe.get("name", ""), idx)
        if not f:
            continue
        c = out.setdefault(f, {"lc": 0, "lm": 0, "bc": 0, "bm": 0})
        for ln in fe.findall("line"):
            if ln.get("type") in ("stmt", "method"):
                if ln.get("type") == "stmt":
                    c["lc" if int(ln.get("count", "0")) > 0 else "lm"] += 1
    return out


def first_existing(repo, names):
    for n in names:
        p = Path(repo) / n
        if p.exists():
            return p
    return None


def template_edges(code_files, texts, tpl_files, ref_res, name_to_candidates):
    """Edges code->template: ref_res yields names from the source text, name_to_candidates(name) yields suffix candidates."""
    by_suffix = index_by_name(tpl_files)
    edges = collections.defaultdict(set)
    for f in code_files:
        for rx in ref_res:
            for name in rx.findall(texts[f]):
                for cand in name_to_candidates(name):
                    for t in by_suffix.get(cand.rsplit("/", 1)[-1], []):
                        if t.endswith("/" + cand) or t == cand:
                            edges[f].add(t)
    return edges
