#!/usr/bin/env python3
"""Collects signals per concept (see concepts.yaml) and writes zones.yaml, zones.md and treemap.html.

Language-neutral core: path/text matches, size, git history, output. Language-specific
(dependency graph, coverage, template edges) is only the adapter in ../adapters/<adapter>.py.

The agent does NOT draw zones. The fields zone/rationale/owner/notes in zones.yaml
are filled in by a human; they are preserved on re-runs.

Usage:  python3 -I zones_signals.py --adapter java|python|php [--repo <path>] [--out <folder>] [--concepts <file>] [--detail]
Default = manageable: per concept only files, LOC, line coverage, dependents, dependent templates, test files.
--detail adds branch coverage, core/text matches, git churn, authors, TODO counter, hotspots.
Default output: <repo>/temp/zones.  Concept catalog: <out>/concepts.yaml, otherwise ../examples/<adapter>/concepts.yaml.
"""
import argparse, collections, copy, datetime as dt, importlib, json, re, subprocess, sys
sys.dont_write_bytecode = True
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent          # scripts and template
SKILL = HERE.parent
OUT = HERE                                          # output folder, set in main() via --out
DETAIL = False                                      # --detail: emit additional signals
AD = None                                           # language adapter, loaded in main()
HUMAN_FIELDS = {"zone": None, "reviewed": False, "rationale": "", "owner": "", "allowed_verbs": "", "promote_when": "", "notes": "",
                "observability": {"level": None, "evidence": ""}, "recoverability": {"level": None, "evidence": ""},
                "implicit_dependencies": [], "memo": ""}
MARKERS = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b|@Deprecated", re.I)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


_KIND = {**dict.fromkeys(["java", "groovy", "kt", "scala", "py", "php", "go", "rs", "rb", "cs", "ts", "tsx", "c", "cpp", "h"], "code"),
         **dict.fromkeys(["jsp", "tag", "html", "twig", "phtml", "jinja", "jinja2", "j2", "js"], "view"),
         **dict.fromkeys(["xml", "properties", "yaml", "yml", "ini", "cfg", "toml", "json"], "config"), "sql": "sql"}


def kind(p):
    return _KIND.get(p.rsplit(".", 1)[-1] if "." in p else "", "other")


def module(p):
    """Top-level directory (module/package/workspace); files directly in the root count as '.'."""
    return p.split("/", 1)[0] if "/" in p else "."


def collect_history(repo, since):
    """Single pass over git log -> per file: commits (total/window), authors, last change."""
    out = git(repo, "log", "--name-only", "--no-renames", "--format=\x01%H|%an|%aI")
    stat = collections.defaultdict(lambda: {"c": 0, "cw": 0, "auth": collections.Counter(), "authw": set(), "last": ""})
    cur = None
    for line in out.splitlines():
        if line.startswith("\x01"):
            h, an, d = line[1:].split("|", 2)
            cur = (an, d)
        elif line.strip() and cur:
            s = stat[line.strip()]
            s["c"] += 1
            s["auth"][cur[0]] += 1
            if not s["last"] or cur[1] > s["last"]:
                s["last"] = cur[1]
            if cur[1] >= since:
                s["cw"] += 1
                s["authw"].add(cur[0])
    return stat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True, choices=sorted(x.stem for x in (SKILL / "adapters").glob("*.py") if not x.stem.startswith("_")))
    ap.add_argument("--concepts", default=None, help="concept catalog (default: <out>/concepts.yaml or examples/<adapter>/concepts.yaml)")
    ap.add_argument("--detail", action="store_true", help="additional signals (churn, authors, branch coverage, hotspots)")
    ap.add_argument("--repo", default=str(SKILL.parents[2]))
    ap.add_argument("--out", default=None, help="output folder (default: <repo>/temp/zones)")
    a = ap.parse_args()
    repo = Path(a.repo)
    global OUT, AD, DETAIL
    DETAIL = a.detail
    OUT = Path(a.out) if a.out else repo / "temp" / "zones"
    OUT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(SKILL / "adapters"))
    AD = importlib.import_module(a.adapter)
    cpath = Path(a.concepts) if a.concepts else (OUT / "concepts.yaml" if (OUT / "concepts.yaml").exists() else SKILL / "examples" / a.adapter / "concepts.yaml")
    cfg = yaml.safe_load(cpath.read_text())
    print(f"Adapter: {a.adapter}, catalog: {cpath}")
    st = cfg["settings"]
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30 * st["since_months"])).isoformat()
    excl = [re.compile(x) for x in st.get("exclude_paths", [])]
    exts = tuple("." + e for e in (st.get("extensions") or AD.EXTENSIONS))

    files = [f for f in git(repo, "ls-files").splitlines()
             if f.endswith(exts) and not any(x.search(f) for x in excl)]
    hist = collect_history(repo, since)
    # read files once
    info = {}
    for f in files:
        try:
            txt = (repo / f).read_text(errors="replace")
        except OSError:
            continue
        info[f] = {"txt": txt, "loc": txt.count("\n") + 1, "markers": len(MARKERS.findall(txt))}

    cov = AD.load_coverage(repo, info, OUT)                       # {file: {lc, lm, bc, bm}}
    deps = AD.load_deps(repo, info, OUT)                          # {file: {dependencies}} or None
    dependents = collections.defaultdict(set)
    for x, ys in (deps or {}).items():
        for y in ys:
            dependents[y].add(x)
    code_to_tpl, tpl_to_code, tpl_to_tpl = AD.load_extra_edges(repo, info, OUT)   # code <-> templates
    tpl_users = collections.defaultdict(set)                      # code file -> templates that use it
    for t, cs in tpl_to_code.items():
        for c in cs:
            tpl_users[c].add(t)
    include_count = collections.Counter(t for ts in tpl_to_tpl.values() for t in ts)

    memberships = collections.defaultdict(list)   # file -> concept indices (core only)
    concept_list = []
    result = {}
    for lens_key, lens in cfg["lenses"].items():
        for ckey, c in lens["concepts"].items():
            pres = [re.compile(x) for x in c.get("path", [])]
            cres = [re.compile(x, re.I) for x in c.get("content", [])]
            core, touch = set(), set()
            for f, d in info.items():
                if any(r.search(f) for r in pres):
                    core.add(f)
                elif cres and any(r.search(d["txt"]) for r in cres):
                    touch.add(f)
            members = core | touch
            cidx = len(concept_list); concept_list.append({"key": ckey, "title": c["title"], "lens": lens_key})
            for f in core:
                memberships[f].append(cidx)
            if c.get("include_tests"):
                prod, tests = list(members), []
            else:
                prod = [f for f in members if not AD.is_test(f)]
                tests = [f for f in members if AD.is_test(f)]
            loc = sum(info[f]["loc"] for f in prod)
            ch = collections.Counter()
            auth = collections.Counter()
            authw = set()
            last = ""
            c_total = c_win = 0
            for f in prod:
                h = hist.get(f)
                if not h:
                    continue
                c_total += h["c"]; c_win += h["cw"]; auth.update(h["auth"]); authw |= h["authw"]
                last = max(last, h["last"])
                ch[f] = h["cw"]
            hot = sorted(prod, key=lambda f: (ch[f] * info[f]["loc"], info[f]["loc"]), reverse=True)[:5]
            top_share = round(auth.most_common(1)[0][1] / sum(auth.values()), 2) if auth else 0
            bymod = collections.Counter(module(f) for f in prod)
            bykind = collections.Counter(kind(f) for f in prod)
            lc = sum(cov[f]["lc"] for f in prod if f in cov); lm = sum(cov[f]["lm"] for f in prod if f in cov)
            bc = sum(cov[f]["bc"] for f in prod if f in cov); bm = sum(cov[f]["bm"] for f in prod if f in cov)
            cov_files = [f for f in prod if f in cov]
            core_code = {f for f in core if f in cov or AD.is_code(f)} & set(prod)
            verified = set()
            if deps is not None:
                for f in core_code:
                    verified |= dependents.get(f, set())
                verified -= core
            verified_tpl = set()
            for f in core_code:
                verified_tpl |= code_to_tpl.get(f, set()) | tpl_users.get(f, set())
            # one level of includes, but without shared layout fragments (included by >10 templates)
            for j in list(verified_tpl):
                verified_tpl |= {t for t in tpl_to_tpl.get(j, ()) if include_count[t] <= 10}
            verified_tpl -= core
            signals = {
                "files": len(prod), "loc": loc,
                "line_coverage_pct": round(100 * lc / (lc + lm), 1) if lc + lm else None,
                "dependents": (len(verified) if deps is not None and core_code else None),
                "dependents_templates": len(verified_tpl) if core_code else None,
                "test_files": len(tests),
            }
            if DETAIL:
                signals.update({
                    "core_files": len(core & set(prod)), "touching_text": len(touch & set(prod)),
                    "by_module": dict(bymod), "by_kind": dict(bykind),
                    "branch_coverage_pct": round(100 * bc / (bc + bm), 1) if bc + bm else None,
                    "files_with_zero_line_coverage": sum(1 for f in cov_files if cov[f]["lc"] == 0),
                    "files_with_coverage_data": len(cov_files),
                    "dependents_by_module": dict(collections.Counter(module(f) for f in verified)) if verified else {},
                    f"commits_{st['since_months']}m": c_win, "commits_total": c_total,
                    "authors_total": len(auth), f"authors_{st['since_months']}m": len(authw),
                    "top_author_share": top_share, "last_change": last[:10],
                    "markers_todo_deprecated": sum(info[f]["markers"] for f in prod),
                    "hotspots": [{"file": f, "loc": info[f]["loc"], f"commits_{st['since_months']}m": ch[f]} for f in hot],
                })
            result[ckey] = {
                "lens": lens_key, "title": c["title"],
                "signals": signals,
            }

    # preserve human fields from existing zones.yaml
    out_yaml = OUT / "zones.yaml"
    old = {}
    if out_yaml.exists():
        prev = yaml.safe_load(out_yaml.read_text()) or {}
        old = prev.get("concepts") or prev.get("concerns") or {}      # "concerns": old key name, still readable
    for k, v in result.items():
        for hf, default in HUMAN_FIELDS.items():
            v[hf] = copy.deepcopy(old.get(k, {}).get(hf, default))   # deepcopy: no shared objects, otherwise YAML writes anchors

    meta = {"flat_history": sum(h["cw"] for h in hist.values()) < 100,
            "generated": dt.datetime.now().isoformat(timespec="seconds"),
            "commit": git(repo, "rev-parse", "--short", "HEAD").strip(),
            "files_scanned": len(info),
            "zone_values": {"green": "safe / well tested / isolated -> tight agent loop",
                            "yellow": "mixed -> characterization tests first, then change",
                            "red": "sensitive / poorly understood -> human pairs at every step"}}
    out_yaml.write_text("# Signals from the script; a HUMAN fills in the fields zone/rationale/owner/...\n" +
                        yaml.safe_dump({"meta": meta, "concepts": result}, sort_keys=False, allow_unicode=True, width=120))
    render_md(OUT / "zones.md", meta, result, cfg, st)
    for cl in concept_list:
        cl["zone"] = result[cl["key"]]["zone"]
    render_treemap(OUT / "treemap.html", info, memberships, concept_list, cfg, meta)
    print(f"{len(info)} files, {len(result)} concepts -> {out_yaml.name}, zones.md")


def render_treemap(path, info, memberships, concept_list, cfg, meta):
    data = {"lenses": {k: v["title"] for k, v in cfg["lenses"].items()},
            "concepts": concept_list,
            "files": [[f, d["loc"], memberships.get(f, [])] for f, d in sorted(info.items())]}
    tpl = (HERE / "treemap_template.html").read_text()
    tpl = (tpl.replace("__META__", f"{meta['generated'][:10]}, commit {meta['commit']}")
              .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
    cdn = '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>'
    # Artifact version: without its own skeleton, d3 via CDN
    path.with_name("treemap.artifact.html").write_text(tpl.replace("__D3TAG__", cdn))
    # Standalone file: d3 embedded, works offline
    d3f = OUT / "cache" / "d3.min.js"
    if not d3f.exists():
        import urllib.request
        d3f.parent.mkdir(exist_ok=True)
        d3f.write_bytes(urllib.request.urlopen("https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js", timeout=30).read())
    d3 = d3f.read_text()
    top, rest = tpl.split("</style>", 1)
    path.write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width, initial-scale=1">' + top + "</style></head><body>"
                    + rest.replace("__D3TAG__", "<script>" + d3 + "</script>") + "</body></html>\n")


def fmt(x):
    return "–" if x is None else x


def render_md(path, meta, result, cfg, st):
    w = st["since_months"]
    has_tpl = any(v["signals"]["dependents_templates"] for v in result.values())
    L = ["# Zone map (signal view)\n",
         f"Generated: {meta['generated']} · Commit `{meta['commit']}` · {meta['files_scanned']} files scanned\n",
         "> **Rev.** = a human has reviewed the zone (✓). **Obs.** / **Rec.** = observability / recoverability (good, partial, poor, unknown), entered with evidence in `zones.yaml`.\n",
         "> The script only provides **signals**. A human enters the zone (green / yellow / red) in `zones.yaml`.\n",
         "> **Cov.** = line coverage from a real test run (– = no report; check whether the run was complete). "
         "**Dependents** = code files outside the concept that, according to the dependency graph, directly use core files (– = no graph)."
         + (" **Templates** = templates that display or use core code." if has_tpl else "") + "\n"]
    if DETAIL and meta.get("flat_history"):
        L.append("> **History:** the git history is mostly flat, churn signals are weak.\n")
    has_or = any((v["observability"] or {}).get("level") or (v["recoverability"] or {}).get("level") for v in result.values())
    head = ["Concept", "Zone", "Rev.", "Files", "LOC", "Cov. %", "Dependents"] + (["Templates"] if has_tpl else []) + ["Tests"] + (["Obs.", "Rec."] if has_or else [])
    if DETAIL:
        head += ["Branch %", "Core/Text", f"Commits {w}M", f"Authors {w}M", "Top author", "TODO", "Last change"]
    for lk, lens in cfg["lenses"].items():
        L.append(f"\n## {lens['title']}\n")
        L.append("| " + " | ".join(head) + " |")
        L.append("|---|---|---|" + "---:|" * (len(head) - 3))
        for k, v in result.items():
            if v["lens"] != lk:
                continue
            s = v["signals"]
            row = [f"**{v['title']}**<br><sub>`{k}`</sub>", v["zone"] or "–", "✓" if v["reviewed"] else "–", s["files"], s["loc"], fmt(s["line_coverage_pct"]), fmt(s["dependents"])]
            row += [fmt(s["dependents_templates"])] if has_tpl else []
            row += [s["test_files"]]
            if has_or:
                row += [(v["observability"] or {}).get("level") or "–", (v["recoverability"] or {}).get("level") or "–"]
            if DETAIL:
                row += [fmt(s["branch_coverage_pct"]), f"{s['core_files']}/{s['touching_text']}", s[f"commits_{w}m"], s[f"authors_{w}m"],
                        f"{int(s['top_author_share'] * 100)} %", s["markers_todo_deprecated"], s["last_change"]]
            L.append("| " + " | ".join(str(x) for x in row) + " |")
    if DETAIL:
        L.append("\n## Hotspots per concept (churn x size)\n")
        for k, v in result.items():
            hs = v["signals"]["hotspots"]
            if hs and hs[0][f"commits_{w}m"] > 0:
                L.append(f"- **{k}**: " + ", ".join(f"`{h['file'].rsplit('/', 1)[-1]}` ({h['loc']} LOC, {h[f'commits_{w}m']} commits)" for h in hs[:3]))
    path.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
