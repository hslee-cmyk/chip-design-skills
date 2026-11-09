"""(a) 포트 넷 분류(연결만 + 엔진 쓰기 계획 대조), (b) ls_swing VGS 등식 소자 집합 대 '모든 MOS' 집합. 13회로. 결과 out/ab.jsonl."""
import sys
import tempfile
import traceback
from pathlib import Path

from common import append, circuits, load_env

from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import LutMemo
from gmid_engine.pipeline import run_stage_a
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access

only = sys.argv[1:]
lut, pdk, rule = load_env()
memo = LutMemo(lut, point=200000, curve=200000, root=4096)


def comp_of(adj, start):
    seen, st = {start}, [start]
    while st:
        n = st.pop()
        for m in adj.get(n, ()):
            if m not in seen:
                seen.add(m)
                st.append(m)
    return seen


for group, name, d in circuits():
    if only and name not in only:
        continue
    rec = {"circuit": name, "group": group}
    try:
        tmp = Path(tempfile.mkdtemp(prefix="ab_" + name))
        a = run_stage_a(d / (name + ".topology.json"), d / (name + ".sizing_spec.json"), lut, output_dir=tmp)
        rec["stage_a"] = a.status
        snap = a.s1.snapshot if hasattr(a.s1, "snapshot") else a.s1
        classes = dict(snap.column("device", "element_class"))
        kinds = dict(snap.column("device", "kind"))
        pins = {m: dict(p) for m, p in snap.column("device", "pins")}
        kctx = None
        try:
            kctx = build_kernel_context(a.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo))
        except Exception as exc:  # noqa: BLE001
            rec["kernel_error"] = repr(exc)[:300]
        rsrc = kctx.base if kctx is not None else snap
        rails = {n: v for n, v in rsrc.column("node", "dc_rail_v") if v is not None}
        if not rails:
            import json as _j
            raw = _j.loads((d / (name + ".topology.json")).read_text(encoding="utf-8"))
            rails = {n: None for n in raw["supply_nets"]}
            rec["rails_from"] = "topology supply_nets (kernel ctx 없음)"
        ports = dict(snap.column("node", "port_direction"))
        ports = {n: dd for n, dd in ports.items() if dd is not None}
        rec["rails"] = rails
        rec["classes"] = sorted(set(classes.values()))
        mos = sorted(m for m in pins if set(MOS_TERMINAL_NAMES) <= set(pins[m]))
        # 터미널 접속 목록(연결만)
        touch = {}
        for m, p in pins.items():
            for t, n in p.items():
                touch.setdefault(n, []).append((m, t, classes[m], kinds.get(m)))
        # G_vgs(연결만): MOS (g,s), 저항 두 단자. 용량·전류원 제외.
        adj = {}
        def edge(x, y):
            adj.setdefault(x, set()).add(y)
            adj.setdefault(y, set()).add(x)
        for m, p in pins.items():
            if m in mos:
                edge(p[MOS_TERMINAL_NAMES[1]], p[MOS_TERMINAL_NAMES[2]])
            elif str(kinds.get(m)).lower().startswith("res") or str(classes[m]).lower().startswith("res"):
                ts = list(p.values())
                edge(ts[0], ts[1])
        rec["passive_kinds"] = sorted({str(kinds.get(m)) for m in pins if m not in mos})
        # 엔진 쓰기 계획
        writers = {}
        if kctx is not None:
            writers = dict(kctx.base.column("node", "dc_writer"))
            rec["input_dc_v"] = kctx.inputs.input_dc_v
            rec["node_targets"] = kctx.inputs.node_targets
        rows = []
        for n, dirn in sorted(ports.items()):
            t = touch.get(n, [])
            terms = sorted({(c if c != "mos" else "mos") + ":" + tt for _m, tt, c, _k in t})
            in_gvgs = n in adj
            comp = comp_of(adj, n) if in_gvgs else {n}
            has_rail = bool(comp & set(rails))
            drain_only = all((tt == MOS_TERMINAL_NAMES[0] and c == "mos") or ("cap" in str(c).lower() or "cap" in str(k).lower())
                             for _m, tt, c, k in t)
            if n in rails:
                conn = "rail"
            elif not in_gvgs:
                conn = "HZ:drain/cap-only (not in G_vgs)"
            elif has_rail:
                conn = "KVL:G_vgs comp contains rail"
            else:
                conn = "floating G_vgs comp (no rail) size=%d" % len(comp)
            if conn.startswith("floating") and any(ports.get(x) == "input" for x in comp if x != n):
                conn += " +contains input port"
            chain, cur, guard = [], n, 0
            while cur in writers and guard < 60:
                ww = writers[cur]
                chain.append((cur, ww.relation, ww.element))
                if ww.known is None:
                    break
                cur, guard = ww.known, guard + 1
            w = writers.get(n)
            wdesc = None if w is None else {"tier": w.tier, "rel": w.relation, "elem": w.element, "known": w.known, "y": w.y_key}
            rows.append({"net": n, "dir": dirn, "terms": terms, "drain_only": drain_only, "conn_class": conn,
                         "comp": sorted(comp)[:12], "writer": wdesc, "chain": chain})
        rec["ports"] = rows
        # (b)
        devs = []
        for m in mos:
            p = pins[m]
            dn, gn, sn = (p[t] for t in MOS_TERMINAL_NAMES)
            asbuilt = (sn not in rails) or (gn == dn)
            # source 의 저항 경유 레일 도달(degeneration): source 에 닿은 저항의 다른 끝이 레일
            res_to_rail = []
            for m2, tt, c, k in touch.get(sn, []):
                if m2 not in mos and (str(k).lower().startswith("res") or str(c).lower().startswith("res")):
                    other = [x for x in pins[m2].values() if x != sn]
                    res_to_rail.append((m2, other, any(o in rails for o in other)))
            gate_w = writers.get(gn)
            devs.append({"dev": m, "kind": kinds[m], "d": dn, "g": gn, "s": sn, "s_rail": sn in rails, "diode": gn == dn,
                         "asbuilt_vgs_eq": asbuilt, "gate_is_input": ports.get(gn) == "input", "gate_is_output": ports.get(gn) == "output",
                         "gate_writer": None if gate_w is None else (gate_w.tier, gate_w.relation, gate_w.element),
                         "src_resistors": res_to_rail})
        rec["devices"] = devs
        rec["n_mos"] = len(mos)
        rec["n_asbuilt"] = sum(x["asbuilt_vgs_eq"] for x in devs)
        rec["diff_rail_cs"] = [x["dev"] for x in devs if not x["asbuilt_vgs_eq"]]
        rec["cs_gate_input"] = [x["dev"] for x in devs if not x["asbuilt_vgs_eq"] and x["gate_is_input"]]
        rec["degeneration"] = [x["dev"] for x in devs if any(r[2] for r in x["src_resistors"])]
        rec["src_res_nonrail"] = [x["dev"] for x in devs if x["src_resistors"] and not any(r[2] for r in x["src_resistors"])]
    except Exception as exc:  # noqa: BLE001
        rec["error"] = repr(exc)[:500]
        rec["tb"] = traceback.format_exc()[-1500:]
    append("ab.jsonl", rec)
    print(name, rec.get("stage_a"), rec.get("error", "")[:200], flush=True)
