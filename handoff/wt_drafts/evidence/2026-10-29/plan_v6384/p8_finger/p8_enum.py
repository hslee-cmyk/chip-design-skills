"""plan v6.38.4 P8 실측 -- 손가락 선택 (m, w_f)의 자기 정합 해 열거(design 작성자 m4_measure.py 복사본에 열거만 더함; 엔진 import·읽기만).

물리: SPICE는 손가락 폭 w_f로 모델 bin을 고르고, 같은 동작점(VGS·VDS·VSB·L)에서 소자 전류 I = m·w_f·J_s(J_s = 그 bin 슬라이스의 단위 폭 전류 IDu/L 꼴).
그래서 실현 (m, s)가 자기 정합 ⇔ w_f = 격자(I·L/IDu_s / m)가 슬라이스 s를 고름(같은 bin, bin 안 가까운 슬라이스) ∧ w_f ≥ W_min.
열거 = m = 1..M(W_min이 막는 유한 상한), s = 그 kind 슬라이스 전부 -- 반복 없음. 기록: 자기 정합 해 목록, 계획 규칙 의도(w_f ≤ w_hi, 가장 작은 m)의 해,
같은 점의 옛 반복 규칙(fixed_point) 결과. 결과 = p8_enum.out.jsonl append.
"""
"""design v1.15.2 검증 M-4 / 재판정 P5 측정 -- 엔진 무수정(integ/it12 import·읽기만, DEC-104 (1′) (b) 꼴). 판정 기록 아님.

(i) 정적 계수: 노드 풀이가 종속 소자 슬라이스를 읽을 수 있는 회로(Rʳ ≠ ∅ 후보) -- 범위 3a(E-13) 뒤 남는 읽기 =
    순환 SCC 수렴 허용오차 소자(design 40 §3.7-A 2 '되먹임 경로'): VGS writer 식이 있는 SCC는 그 writer 소자,
    없으면 SCC `devices`(단자가 닿는 MOS -- 채널 값 조건은 동적이라 상위집합). 그 가운데 `dc_coord.role` = dependent 인 소자.
(ii) 소자 안 고정점 회차: G-10 흐름(선언 E_B 40, 600 s)으로 find_front 를 돌려 얻은 봉인점(front, 없으면 sealed cache,
    균등 최대 5점)마다 노드 동작점(vgs, vds, vsb, L, ID)을 고정하고, 종속 소자마다 기준 폭 슬라이스 k0에서 출발해
    W(k) = ID·L/IDu_k(op_point, 그 슬라이스) -> 선택 규칙(design 40 §3.7-A 5: w_hi = 기준 슬라이스 W-bin 위 끝,
    m = ceil(W/w_hi), w_f = 격자 반올림, w_f < W_min -> finger_below_min, bin 에 슬라이스 없으면 m 증가, bin 안 가까운 쪽)
    -> k 를 재방문까지 되풀이. 결과 = 소자별 회차 수(수렴/순환/실패 사유). Rʳ 안 키가 바뀐 뒤의 노드 재풀이는 재지 않는다
    (구현 뒤에만 잴 수 있음). 결과 = 회로마다 m4_measure.out.jsonl append.
한계: bin 소속은 as-built `bin_index`(1 ulp 비교 -- D1 정정 전), L 이 그 슬라이스 L bin 지도 밖이면 그 슬라이스 조회 실패로 기록."""
import sys, os, json, math, tempfile, shutil, traceback, collections
sys.dont_write_bytecode = True
SKILL_S = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design"
sys.path.insert(0, SKILL_S)
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
from pathlib import Path
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.lut.point_query import op_point
from gmid_engine.lut._helpers_bins import bin_index
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import SearchSettings, build_search_context, find_front, open_run
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
from gmid_engine.sizing.s2_values import COORD_WRITER, REL_VGS_GATE, REL_VGS_SOURCE

SKILL = Path(SKILL_S); LIBRARY = SKILL / "assets" / "library"
OUT = Path(__file__).parent / "p8_enum.out.jsonl"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds_map = dict(DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds_map[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds_map[e["device"]], float("inf")))
GRID = float(man.get("manufacturing_grid_m", 5e-9))
dm = BoundedLRU(16); pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm); q = dict(pdk.quantities)
W_MIN = float(q["min_finger_w_m"].value_m)
spec_l = LutSpec(GRID, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                 noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec_l, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
rule = read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm)
SL = lut.slice_map
KIND_SLICES = collections.defaultdict(list)
for (kd, key), sl in SL.items():
    wb = sl.l_bins.w_bin if (sl.l_bins and sl.l_bins.bins) else None
    KIND_SLICES[kd].append((key, sl.w_m, wb))


def settings():
    return SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "xrunf1b B-T22 fixture"),), (1e-13, 1e-10))


def emit(rec):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def gridr(x):
    return round(x / GRID) * GRID


def select(kind, W, ref_key):
    """design 40 §3.7-A 5 선택 규칙(측정용 재현). 반환 (key, m, w_f, reason)."""
    ref_wb = SL[(kind, ref_key)].l_bins.w_bin
    w_hi = ref_wb[1]
    m = max(1, math.ceil(W / w_hi * (1 - 1e-12)))
    bins = sorted({wb for _k, _w, wb in KIND_SLICES[kind] if wb is not None})
    first = True
    while True:
        w_f = gridr(W / m)
        if w_f < W_MIN - GRID / 2:
            return None, m, w_f, ("finger_below_min" if first else "slice_missing")
        j = bin_index(bins, w_f)
        if j is not None:
            cands = [(abs(w - w_f), w, k) for k, w, wb in KIND_SLICES[kind] if wb == bins[j] and w >= W_MIN - GRID / 2]
            if cands:
                cands.sort()
                return cands[0][2], m, w_f, None
        m += 1; first = False


def w_of(op, kind, key):
    p = op_point(lut_memo, kind, key, op.L, op.vgs, op.vds, op.vsb)
    return op.current * op.L / p.IDu


def fixed_point(op, ref_key):
    seen, k, seq = [], ref_key, []
    while True:
        try:
            W = w_of(op, op.kind, k)
        except Exception as exc:
            return dict(rounds=len(seen) + 1, status="lut_fail", detail="%s" % type(exc).__name__, seq=seq)
        nk, m, w_f, reason = select(op.kind, W, ref_key)
        seq.append([k, round(W * 1e6, 4), m, round(w_f * 1e6, 4), nk])
        if reason:
            return dict(rounds=len(seq), status=reason, seq=seq)
        if nk == k:
            return dict(rounds=len(seq), status="converged", final=k, changed=(k != ref_key), seq=seq)
        seen.append(k)
        if nk in seen:
            return dict(rounds=len(seq), status="slice_cycle", seq=seq)
        k = nk


def enumerate_fit(op, ref_key):
    """자기 정합 (m, 슬라이스) 전부 + 규칙 의도 해(w_f ≤ w_hi 가운데 가장 작은 m, 동률은 w_f 큰 쪽)."""
    kind = op.kind
    ref_wb = SL[(kind, ref_key)].l_bins.w_bin
    w_hi = ref_wb[1]
    bins = sorted({wb for _k, _w, wb in KIND_SLICES[kind] if wb is not None})
    fits, fails, w_by_slice = [], collections.Counter(), {}
    for key, w_s, wb in KIND_SLICES[kind]:
        if wb is None or w_s < W_MIN - GRID / 2:
            continue
        try:
            W = w_of(op, kind, key)
        except Exception as exc:
            fails[type(exc).__name__] += 1
            continue
        w_by_slice[str(key)] = [round(w_s * 1e6, 4), [round(b * 1e6, 4) for b in wb], W * 1e6]
        m = 1
        while True:
            w_f = gridr(W / m)
            if w_f < W_MIN - GRID / 2:
                break
            j = bin_index(bins, w_f)
            if j is not None and bins[j] == wb:
                cands = sorted((abs(w - w_f), w, k) for k, w, b in KIND_SLICES[kind] if b == wb and w >= W_MIN - GRID / 2)
                if cands and cands[0][2] == key:
                    fits.append([m, round(w_f * 1e6, 4), key, round(W * 1e6, 4)])
            m += 1
    fits.sort()
    intent = [f for f in fits if f[1] * 1e-6 <= w_hi + GRID / 2]
    pick = min(intent, key=lambda f: (f[0], -f[1])) if intent else None
    return dict(n_fits=len(fits), fits=fits[:12], w_by_slice=w_by_slice, w_hi_um=round(w_hi * 1e6, 4), intent_pick=pick,
                n_intent=len(intent), lut_fail=dict(fails))


lut_memo = None
for circuit in sys.argv[1:]:
    rec = {"circuit": circuit}
    out = Path(tempfile.mkdtemp(prefix="m4o")); root = tempfile.mkdtemp(prefix="m4r")
    try:
        donors, counters = open_run()
        a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), lut, output_dir=out,
                        donors=donors, counters=counters)
        memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
        lut_memo = memo
        b = run_stage_b(a, memo, pdk, output_dir=out, diagnostic=True, settings=settings())
        rec["status_ab"] = [a.status, b.status]
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo), donors=a.donors, counters=a.counters)
        sctx = build_search_context(kctx, a.spec, settings(), root, pdk, rule, code_fp=a.code_fp)
        base = sctx.dc.base
        coords = dict(base.column("device", "dc_coord"))
        writers = dict(base.column("node", "dc_writer"))
        order = [v for _k, v in base.column("graph", "dc_scc_order")][0]
        dep = sorted(m for m, c in coords.items() if c.role != COORD_WRITER)
        rset, scc_rows = set(), []
        for entry in order:
            if not entry.cyclic:
                continue
            vw = sorted({writers[n].element for n in entry.nodes if n in writers and writers[n].relation in (REL_VGS_GATE, REL_VGS_SOURCE)})
            tol_devs = vw if vw else sorted(entry.devices)
            dtol = sorted(d for d in tol_devs if d in coords and coords[d].role != COORD_WRITER)
            rset |= set(dtol)
            scc_rows.append(dict(nodes=list(entry.nodes), vgs_writers=vw, tol_devices=tol_devs, dependent_tol=dtol))
        rec.update(dependent_devices=dep, n_dependent=len(dep), cyclic_scc=scc_rows, R_candidates=sorted(rset),
                   R_nonempty=bool(rset))
        if tuple(rec["status_ab"]) != ("ok", "ok"):
            rec["points"] = "탐색 미도달(단계 B review_needed) -- (ii) 측정 불능"
            emit(rec); print(circuit, "static only"); continue
        fr = find_front(sctx, [])
        pts = [p_.result for p_ in fr.front]; pool = "front"
        if not pts:
            pool = "sealed cache"
            pts = sorted((r_ for r_ in sctx.cache.values() if getattr(r_, "status", None) == "sealed" and r_.evaluation is not None),
                         key=lambda r_: r_.seq)
        if len(pts) > 5:
            idx = sorted({round(i * (len(pts) - 1) / 4) for i in range(5)}); pts = [pts[i] for i in idx]
        rec["point_pool"] = pool; rec["n_points"] = len(pts)
        prs = []
        for p in pts:
            ops = dict(p.evaluation.snapshot.column("device", "dc_op"))
            devs = {}
            for m in dep:
                if m not in ops:
                    continue
                op = ops[m]
                devs[m] = dict(iter_rule=fixed_point(op, op.w_key), enum=enumerate_fit(op, op.w_key), I_A=op.current, L_m=op.L)
            prs.append(dict(point=str(p.seq), devices=devs))
        rec["points"] = prs
        agg = collections.Counter(); rmax = 0
        for pr in prs:
            for m, r in pr["devices"].items():
                e = r["enum"]; r = r["iter_rule"]
                agg["enum_nfits_" + ("0" if e["n_fits"] == 0 else ("1" if e["n_fits"] == 1 else "ge2"))] += 1
                agg["enum_intent_" + ("none" if e["intent_pick"] is None else "ok") + "__iter_" + r["status"]] += 1
                agg[r["status"]] += 1; rmax = max(rmax, r["rounds"])
                if r["status"] == "converged" and r.get("changed"):
                    agg["converged_changed"] += 1
                    if m in rset:
                        agg["changed_in_R"] += 1
        rec["summary"] = dict(agg); rec["max_rounds"] = rmax
        emit(rec); print(circuit, dict(agg), rmax)
    except BaseException as exc:
        rec["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:500]); rec["trace"] = traceback.format_exc()[-2000:]
        emit(rec); print(circuit, "ERROR", rec["error"])
    finally:
        shutil.rmtree(out, ignore_errors=True); shutil.rmtree(root, ignore_errors=True)
