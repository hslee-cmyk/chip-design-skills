"""measure only: gather per-card numbers for M2..M9 drafts into C:/g226/out/cards_data.json (reads chain/neg/pt3/ei/vtools outputs,
runs E3 (design §10 E3_AST) base/head and plan idempotence at the last head)."""
import collections
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET

O = "C:/g226/out"
K = "C:/g226/kit"
GCX = "C:/g226/cache/tools/gates"
S = "C:/g226/r"
PY = "C:/Python314/python.exe"
N310 = ["gmid_lut", "topology_authoring", "circuit_state_graph", "gmid_sizing_engine", "circuit_metrics", "theta_search",
        "stick_diagram", "sizing_layout_convergence", "instance_report_builder", "gmid_design_pipeline"]
ENV = dict(os.environ, TMP="C:/g226/tmp", TEMP="C:/g226/tmp", PYTHONIOENCODING="utf-8", MP_STMT_KEY="names",
           APPDATA="C:/Users/HSLEE/AppData/Roaming", HOME="C:/Users/HSLEE")
EXCL = re.compile(r'^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)')
chain = [json.loads(l) for l in open(O + "/chain.jsonl", encoding="utf-8")]
neg = [json.loads(l) for l in open(O + "/neg.jsonl", encoding="utf-8")]


def junit(label):
    p = "%s/%s.pt3.junit.xml" % (O, label)
    if not os.path.exists(p):
        return None
    res = {}
    for tc in ET.parse(p).getroot().iter("testcase"):
        tid = "%s::%s" % (tc.get("classname"), tc.get("name"))
        st = "passed"
        for ch in tc:
            if ch.tag in ("failure", "error"):
                st = ch.tag
            elif ch.tag == "skipped":
                st = "xfailed" if "xfail" in (ch.get("type", "") + ch.get("message", "")) else "skipped"
        res[tid] = st
    return res


def pt3_tail(label):
    p = "%s/%s.pt3.txt" % (O, label)
    if not os.path.exists(p):
        return None
    L = [x for x in open(p, encoding="utf-8", errors="replace").read().splitlines() if x.strip()]
    return {"summary": [x for x in L if re.search(r"passed|failed|error", x)][-1:], "exit": L[-1],
            "failed": [x for x in L if x.startswith("FAILED") or x.startswith("ERROR")]}


def ej(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return {"__missing__": str(e)}


def e3(rev):
    r = subprocess.run([PY, "-B", K + "/e3_ast.py", S, rev], capture_output=True, text=True, encoding="utf-8", env=ENV)
    L = [x for x in r.stdout.replace("\r", "").splitlines() if x]
    files = sorted({re.sub(r":\d+$", "", re.sub(r"^[A-Za-z-]+ ", "", x)) for x in L})
    return {"rc": r.returncode, "stmt": sum(1 for x in L if x.startswith("stmt ")), "call": sum(1 for x in L if x.startswith("call ")),
            "outside": [f for f in files if not EXCL.match(f)]}


out = {}
prev_label = "base"
for i, r in enumerate(chain):
    c = r["card"]
    d = {k: r[k] for k in ("base", "head", "plan", "assigned", "rules", "units", "gen", "check_verdict", "check_findings", "moved_units",
                          "moved_defs", "v3_static", "import_any", "import_layering", "e3b", "w2_acf_foreign_load", "t_check", "sec")}
    d["rule_counts"] = dict(collections.Counter(r["rules"].values()))
    d["src_counts"] = dict(collections.Counter(u.split("::")[0] for u in r["rules"]))
    # W-1 filtered: shim-import reads of names bound by a NON-N3.10 import (re-exports from N3.10 modules are kept by SHIM (c))
    sr = ej("%s/%s/shim_reads.json" % (O, c))
    hits = [h for h in sr.get("hits", []) if not (h["bound_by"].startswith("from ") and h["bound_by"][5:] in N310)]
    d["w1_nonreexport_reads"] = len(hits)
    d["w1_sample"] = hits[:5]
    # plan idempotence: next card's base plan vs this card's base plan (mapping)
    pb = ej("%s/%s/plan_base.json" % (O, c))["assignment"]
    nxt = chain[i + 1]["card"] if i + 1 < len(chain) else None
    if nxt:
        pn = ej("%s/%s/plan_base.json" % (O, nxt))
    else:
        pr = subprocess.run([PY, "-B", K + "/move_plan_sim.py", "plan", "--root", S, "--rev", r["head"]] + json.load(open(K + "/mp_args.json")),
                            capture_output=True, text=True, encoding="utf-8", env=ENV)
        pn = json.loads([x for x in pr.stdout.splitlines() if x.startswith("{")][0])
    pa = pn["assignment"]
    kb = collections.Counter((k.split("::", 1)[1], v["mod"]) for k, v in pb.items())
    ka = collections.Counter((k.split("::", 1)[1], v["mod"]) for k, v in pa.items())
    moved_keys = {u.split("::", 1)[1] for u in r["rules"]}
    d["plan_head"] = {"lists": {k: len(pn[k]) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high", "import_conflicts")},
                      "map_diff": sum(((kb - ka) + (ka - kb)).values()),
                      "moved_rule": dict(collections.Counter(v["rule"] for k, v in pa.items() if k.split("::", 1)[0] == c + ".py" and k.split("::", 1)[1] in moved_keys)),
                      "n_assign": len(pa)}
    # vtools
    v3 = ej("%s/v3_%s.json" % (O, c))
    d["V3"] = {k: v3.get(k) for k in ("verdict", "defs", "mutants", "survivors", "move_rejected", "targets", "error")}
    d["V3"]["moved_n"] = len(v3.get("moved", []) or [])
    v6 = ej("%s/v_source_lint_%s.json" % (O, c))
    d["V6"] = {k: v6.get(k) for k in ("verdict", "findings", "move_rejected", "error")}
    v7 = ej("%s/v_reachability_%s.json" % (O, c))
    d["V7"] = {k: v7.get(k) for k in ("verdict", "new_defs", "move_rejected", "error")}
    d["V7"]["moved_n"] = len(v7.get("moved", []) or [])
    # PT3 id-by-id vs previous state
    jb, jh = junit(prev_label), junit(c)
    if jb is not None and jh is not None:
        d["pt3"] = {"ids_base": len(jb), "ids_head": len(jh), "same_ids": set(jb) == set(jh),
                    "diff": sorted("%s %s->%s" % (t, jb.get(t), jh.get(t)) for t in set(jb) | set(jh) if jb.get(t) != jh.get(t)),
                    "base": pt3_tail(prev_label), "head": pt3_tail(c)}
    # E-LIB / E-INST vs previous state
    ei = {}
    eb = ej("%s/ei/%s.elib.json" % (O, prev_label))
    eh = ej("%s/ei/%s.elib.json" % (O, c))
    ei["elib_equal"] = (eb == eh) and "__missing__" not in eb
    ei["elib_hash"] = eh.get("hash")
    for cc in ("current_reuse_telescopic_ota", "folded_cascode"):
        b = ej("%s/ei/%s.%s.einst.json" % (O, prev_label, cc))
        h = ej("%s/ei/%s.%s.einst.json" % (O, c, cc))
        diff = sorted(k for k in set(b) | set(h) if b.get(k) != h.get(k))
        eo = h.get("engine_origin")
        ei[cc] = {"n_keys": len(h), "diff_keys": diff, "raw_sha256": h.get("raw_sha256"),
                  "without_topology_ref_sha256": h.get("without_topology_ref_sha256"),
                  "origin_has_mod": (c in json.dumps(eo)) if eo is not None else None,
                  "origin_in_iso": all("g226/ei" in str(p).replace("\\", "/") for p in (eo.values() if isinstance(eo, dict) else (eo or []))) if eo is not None else None}
    d["einst"] = ei
    d["e3"] = {"base": e3(r["base"]), "head": e3(r["head"])}
    d["e3"]["same_outside"] = d["e3"]["base"]["outside"] == d["e3"]["head"]["outside"]
    d["e3"]["n_outside"] = len(d["e3"]["head"]["outside"])
    del d["e3"]["base"]["outside"], d["e3"]["head"]["outside"]
    # unit list (name, span, rule) from gen.json, and re-export line positions at head
    gj = ej("%s/%s/gen.json" % (O, c))
    d["unit_rows"] = [{"uid": u, "span": s, "rule": r["rules"].get(u.split("#")[0], r["rules"].get(u))} for u, s in zip(gj.get("units", []), gj.get("spans", []))]
    pos = {}
    for f in (gj.get("reexports") or {}):
        txt = subprocess.run(["git", "-C", S, "show", "%s:skills/analog-gmid-design/assets/%s" % (r["head"], f)], capture_output=True).stdout.decode("utf-8").replace("\r\n", "\n").split("\n")
        for i, line in enumerate(txt, 1):
            if line.startswith("from %s import " % c):
                prev = next((txt[j] for j in range(i - 2, -1, -1) if txt[j].strip()), "")
                nxt = next((txt[j] for j in range(i, len(txt)) if txt[j].strip()), "<EOF>")
                pos[f] = {"line": i, "n_lines": len(txt) - (1 if txt[-1] == "" else 0), "prev": prev[:120], "next": nxt[:120]}
    d["reexport_pos"] = pos
    modtxt = subprocess.run(["git", "-C", S, "show", "%s:skills/analog-gmid-design/assets/%s.py" % (r["head"], c)], capture_output=True).stdout.decode("utf-8")
    d["mod_file_lines"] = modtxt.count("\n")
    # V4 (subjects = first two def/class units) / V5 on base..head
    subs = []
    for u in gj.get("units", []):
        nm = u.split("::", 1)[1].split("#")[0]
        if "," not in nm and not nm.startswith("<"):
            sp = [s for s in gj["spans"] if True]
        subs.append(nm)
    import ast as _ast
    subj = []
    for u, s in zip(gj.get("units", []), gj.get("spans", [])):
        if s.endswith("FunctionDef") or s.endswith("ClassDef"):
            subj.append("%s:%s" % (c, u.split("::", 1)[1]))
        if len(subj) == 2:
            break
    v4 = subprocess.run([PY, "-B", GCX + "/test_lint.py", "--root", S] + sum((["--subject", x] for x in subj), []) + ["--base", r["base"], "--head", r["head"]],
                        capture_output=True, text=True, encoding="utf-8", env=dict(ENV, PYTHONPATH=GCX))
    v5 = subprocess.run([PY, "-B", GCX + "/weakening_diff.py", "--root", S, "--base", r["base"], "--head", r["head"]],
                        capture_output=True, text=True, encoding="utf-8", env=dict(ENV, PYTHONPATH=GCX))
    d["V4"] = {"subjects": subj, "exit": v4.returncode, "out": v4.stdout.strip()[:300]}
    d["V5"] = {"exit": v5.returncode, "out": v5.stdout.strip()[:300]}
    last = {}
    for n in neg:   # later line for the same variant wins (R-6 v2 rerun with same-__future__ candidate preference)
        if n["card"] == c:
            last[n["variant"]] = n
    d["neg"] = [{k: n.get(k) for k in ("variant", "what", "check_exit", "check_findings", "v3_static_g1", "import_any", "w2_foreign_load", "ERROR")}
                for n in last.values()]
    out[c] = d
    prev_label = c
json.dump(out, open(O + "/cards_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", list(out))
