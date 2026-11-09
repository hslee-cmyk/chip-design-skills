# M1: 칸 0 미정 θ 전류의 물리 분류 -- 어느 MOS 행이 읽고, 그 행에 gm 방정식(블록 입력 소자)이 걸리는가, 미지 수는 몇인가.
# as-built `_state` 호출을 감싸(스크립트 안 monkeypatch, 엔진 파일 무변경) 출발 구간 계산의 ctx·state 를 읽는다. 회로마다 append.
import sys
from pg_common import *

OUT = HERE / os.environ.get("PG_M1_OUT", "m1_current_facts.jsonl")
only = sys.argv[1:] or ALL
lut, pdk, rule = load_env()
capt = {}
orig_state = si._state


def wrap_state(ctx, gm_id, lengths, refine=True):
    st = orig_state(ctx, gm_id, lengths, refine)
    capt["last"] = (ctx, dict(gm_id), dict(lengths), st)
    capt.setdefault("first", capt["last"])
    return st


si._state = wrap_state
for c in only:
    row = {"circuit": c}
    capt.clear()
    t0 = time.time()
    try:
        a, b, sctx = build(c, lut, pdk, rule)
        if sctx is None:
            row["stop"] = "stage"
            app(OUT, row); continue
        variables = [v.component for v in sctx.domain.variables]
        rungs = sctx.rungs or ()
        given = {comp for comp, _v in rungs[0].theta} if rungs else set()
        row["n_theta"] = len(variables)
        row["missing"] = [list(map(str, v)) for v in variables if v not in given]
        schema = sctx.dc.base.value("graph", "kernel", "theta_schema") if False else l0._schema(sctx)
        row["ties"] = [[list(map(str, rep)), [list(map(str, m)) for m in mem]] for rep, mem in sctx.domain.ties]
        row["zeros"] = [list(map(str, z)) for z in sctx.domain.zeros]
        ctx, g, L, st = capt["last"]
        rows = {name: [(t.source, t.num / t.den) for t in terms] for name, terms in ctx.basis.rows}
        row["basis_free"] = list(ctx.basis.free)
        row["basis_fixed"] = [(s, float(v)) for s, v in ctx.basis.fixed]
        row["rows"] = {k: v for k, v in rows.items()}
        row["blocks"] = [{"key": str(bi.key), "inputs": list(bi.inputs), "out": bi.out_net, "in": bi.in_net, "buffer": bi.buffer, "stage": bi.stage} for bi in st.model.blocks]
        row["ff"] = [{"tap": f[0], "merge": f[1]} for f in st.model.ff]
        row["unassigned"] = list(st.model.unassigned)
        row["macro_gm"] = [(str(k), float(v)) for k, v in st.macro.gm] if st.macro.gm else None
        row["macro_records"] = [str(r)[:200] for r in st.macro.records]
        row["macro_failed"] = getattr(st, "macro_failed", None)
        row["elements"] = {k: float(v) for k, v in st.elements.items()}
        row["currents"] = {k: (None if v is None else float(v)) for k, v in st.currents.items()}
        row["refs"] = {k: float(v) for k, v in st.refs.items()}
        row["g"] = {k: float(v) for k, v in g.items()}
        row["L"] = {k: float(v) for k, v in L.items()}
        row["w_min_m"] = float(ctx.w_min_m)
        row["gbw_hz"] = ctx.gbw_hz; row["pm_deg"] = ctx.pm_deg
        row["constraints"] = [list(map(str, x)) for x in ctx.constraints]
        row["device_cls"] = {d.name: {"kind": d.kind, "group": d.group, "owner": d.owner} for d in ctx.devices}
        # 물리 분류: 미정 θ 전류마다 읽는 행
        classify = {}
        input_devs = {n for bi in st.model.blocks for n in bi.inputs}
        known = set(st.elements)
        for s in st.model.unassigned:
            readers = [m for m, ts in rows.items() if any(x == s for x, _c in ts)]
            classify[s] = {"readers": readers, "input_readers": [m for m in readers if m in input_devs],
                           "row_unknowns": {m: [x for x, _c in rows[m] if x not in known] for m in readers}}
        row["classify"] = classify
        row["inputs_no_current"] = [n for n in input_devs if st.currents.get(n) is None]
    except Exception:
        row["error"] = traceback.format_exc()[-1500:]
    row["t_s"] = round(time.time() - t0, 1)
    app(OUT, row)
    print(c, "done", row["t_s"], flush=True)
print("done")
