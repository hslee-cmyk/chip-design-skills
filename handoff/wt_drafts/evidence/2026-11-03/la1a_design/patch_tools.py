# q8_run.py(검증 60 사본)·p4_uncovered.py(v6.38.4 P4 측정)를 이 card design 측정용으로 고친다. 엔진 소스 수정 0.
import pathlib, shutil
H = pathlib.Path(__file__).parent
E = H.parent
shutil.copyfile(E / 'plan_v6387_v60' / 'q8_run.py', H / 'q8_la1a.py')
shutil.copyfile(E.parent / '2026-10-29' / 'plan_v6384' / 'p4_start' / 'p4_uncovered.py', H / 'la1a_uncovered.py')
p = H / 'q8_la1a.py'
s = p.read_bytes().decode('utf-8')
s = s.replace('SKILL = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")', 'SKILL = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/skills/analog-gmid-design")')
s = s.replace('OUT = HERE / "q8_engine_gainL.jsonl"', 'OUT = HERE / "q8_la1a.jsonl"')
new = '''
# ---- LA-1a design g60-2 측정 모드 (측정 도구만, 엔진 소스 0)
#  da1  : g = G*found_i/sum_all(문언 그대로), 버퍼 블록(DEC-63) 목표 없음 -> 이득 L 하한 없음, 매크로도 버퍼 A_i 없음(A_intr)
#  da1m : 같은 L 처리, 매크로는 버퍼 몫을 A_i로 유지(요인 분리)
#  da2  : 버퍼 블록도 목표 유지, 미달이면 DEC-105 (1) 최선 앵커(as-built 마지막 앵커 대체)
#  da3  : 합을 이득 블록만으로(sum_gain), 버퍼 목표 없음
def _blocks_of(p, views, lut, constraints):
    gain = dict(p.column("graph", "gain_checks")).get(ACH_KEY)
    view = next((v for v in views if v.kind == "transfer"), None)
    return gain, view

def gain_inputs_da(p, views, lut, constraints):
    if not any(m == "gain_ss_db" and op == ">=" for m, op, _v in constraints):
        return None, (("gain_l", "constraint_not_declared"),)
    gain, view = _blocks_of(p, views, lut, constraints)
    found = [b.found_db for b in gain.blocks] if gain is not None else []
    goal = max(float(v) for m, op, v in constraints if m == "gain_ss_db" and op == ">=")
    kinds_ = [b.kind for b in view.blocks] if view is not None else []
    rec = {"case": "da_target", "G_db": goal, "found_db": found, "kinds": kinds_}
    if gain is None or view is None or not gain.blocks or len(view.blocks) != len(gain.blocks) or any(f is None for f in found):
        rec["undefined"] = True
        CAPT["gain_inputs"].append(rec)
        return None, (("gain_l", "found_db_missing(la1a)"),)
    if MODE == "da3":
        total = sum(f for f, k in zip(found, kinds_) if k != "buffer")
    else:
        total = float(sum(found))
    targets = [goal * f / total for f in found]
    rec["g1"] = targets; rec["sum_all"] = float(sum(found)); rec["total_used"] = total
    CAPT["gain_inputs"].append(rec)
    local = p.value("graph", ACH_KEY, "local_inputs").view
    pairs = [(block_spec(view, b, local), t, b.kind) for b, t in zip(view.blocks, targets)]
    keep = [x for x in pairs if MODE in ("da2", "da1m") or x[2] != "buffer"]
    CAPT["buffer_members"] = [m for sp, _t, k in pairs if k == "buffer" for m in sp.members]
    return GainInputs(local, ParamTables(lut.memo, local.w_keys, local.grids), tuple((sp, t) for sp, t, _k in keep)), ()

_q8_wrap_prev = None
def gain_l_da(ctx, elements, resistors, gm_id_lo):
    res = _q8_wrap_prev(ctx, elements, resistors, gm_id_lo)
    if MODE == "da1m":
        drop = set(CAPT.get("buffer_members", ()))
        return ivg.GainLBounds({m: b for m, b in res.bounds.items() if m not in drop},
                               tuple(c for c in res.conflicts if c.device not in drop), res.inactive)
    if MODE == "da2" and ctx.gain is not None:
        bounds = dict(res.bounds); conflicts = list(res.conflicts)
        anchors = [float(a) for a in ctx.gain.local.grids[0]]
        for spec, target in ctx.gain.blocks:
            model, _r = block_gain_model_of(ctx.gain.local, spec)
            if model is None:
                continue
            table = []
            for j, L in enumerate(anchors):
                row = ivg._row(ctx, ctx.gain, model, j, gm_id_lo, elements, resistors)
                db = None if row is None else ivg._gain_db(model, ctx.gain, row)
                if db is not None:
                    table.append((db, L))
            if table and max(t[0] for t in table) < target:
                best = max(table, key=lambda t: (t[0], -t[1]))
                members = [m for m in spec.members if m in bounds]
                old = bounds[members[0]][0]
                for m in members:
                    bounds[m] = (dataclasses.replace(old, value=best[1]),)
                CAPT.setdefault("best_anchor", []).append({"members": list(spec.members), "best_db": best[0], "best_L": best[1], "target": target})
                conflicts = [c for c in conflicts if c.device not in spec.members] + [ivg.StartConflict(members[0], ivg.QUANTITY_L, ((ivg.SRC_GAIN_L, target),), target - best[0])]
        return ivg.GainLBounds(bounds, tuple(conflicts), res.inactive)
    return res
'''
s = s.replace('si.gain_l_bounds = gain_l_wrap\n', new + '\nsi.gain_l_bounds = gain_l_wrap\nif MODE in ("da1","da1m","da2","da3"):\n    _q8_wrap_prev = gain_l_wrap\n    si.gain_l_bounds = gain_l_da\n    ivc._gain_inputs = gain_inputs_da\n')
s = s.replace('app({"case": "captured", "gain_inputs": CAPT["gain_inputs"],', 'app({"case": "captured", "best_anchor": CAPT.get("best_anchor"), "gain_inputs": CAPT["gain_inputs"],')
p.write_bytes(s.encode('utf-8'))

q = H / 'la1a_uncovered.py'
s = q.read_bytes().decode('utf-8')
s = s.replace('ENG = Path("C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design")', 'ENG = Path("C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/skills/analog-gmid-design")')
s = s.replace('OUT = Path(__file__).parent / "out.jsonl"', 'OUT = Path(__file__).parent / "uncovered.jsonl"')
s = s.replace('p4_uncovered_runs', 'la1a_uncovered_runs')
s = s.replace('''        donors, counters = open_run()
        a = run_stage_a(T.LIBRARY / (c + ".topology.json"), T.LIBRARY / (c + ".sizing_spec.json"), lut, output_dir=env.root / c,
                        donors=donors, counters=counters)''', '''        donors, counters = open_run()
        kw = {}
        if c == "ngcc_3stage_ff":  # O-216 선언 내용을 TEMP 사본으로만(파일 작성 = card data 커밋)
            from gmid_engine.authoring import load_topology
            from gmid_engine.graph import structure_rule_fp
            topo = load_topology(str(T.LIBRARY / (c + ".topology.json")))
            st = {"schema_version": "1", "topology_hash": topo.connectivity_fp, "rule_hash": structure_rule_fp(), "facts": [
                {"concept": "dc_role", "subject": m, "value": "signal", "status": "ratified",
                 "evidence": {"rule": "TEMP O-216 content", "nets": ["V1", "gnd"]}, "approval_id": "TEMP-la1a-design"} for m in ("M8", "M14")]}
            (env.root / c).mkdir(parents=True, exist_ok=True)
            sp = env.root / c / (c + ".structure.json"); sp.write_text(json.dumps(st), encoding="utf-8")
            kw = {"structure_path": sp}
        a = run_stage_a(T.LIBRARY / (c + ".topology.json"), T.LIBRARY / (c + ".sizing_spec.json"), lut, output_dir=env.root / c,
                        donors=donors, counters=counters, **kw)
        row["stage_a"] = a.status
        if a.status != "ok":
            row["stop"] = repr(a.report.get("stop_reasons"))[:300]
            with OUT.open("ab") as fh:
                fh.write((json.dumps(row, ensure_ascii=False, default=repr) + "\\n").encode("utf-8"))
            continue''')
s = s.replace('''        row["n_theta_vars"] = len(variables)''', '''        row["n_theta_vars"] = len(variables)
        row["kinds"] = sorted({str(v[0]) for v in variables})
        row["r_vars"] = [str(v[1]) for v in variables if str(v[0]) == "resistance"]
        row["c_vars"] = [str(v[1]) for v in variables if str(v[0]) == "capacitance"]''')
s = s.replace('''    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=repr) + "\\n")''', '''    with OUT.open("ab") as fh:
        fh.write((json.dumps(row, ensure_ascii=False, default=repr) + "\\n").encode("utf-8"))''')
q.write_bytes(s.encode('utf-8'))

# 드라이버: 회로·모드마다 하위 프로세스, 결과는 각 jsonl에 append
drv = H / 'run_all.py'
drv.write_text('''import os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
def log(t):
    with open(os.path.join(H, "run_all.log"), "ab") as f:
        f.write((t + "\\n").encode("utf-8"))
for m in ("base", "ga", "da1", "da1m", "da2", "da3"):
    try:
        r = subprocess.run([sys.executable, "q8_la1a.py", "two_stage_ota_sf", m, "--front"], cwd=H, env=env, capture_output=True, timeout=500)
        open(os.path.join(H, "q8_sf_%s.stdout.txt" % m), "wb").write(r.stdout + r.stderr)
        log("two_stage_ota_sf %s rc=%s" % (m, r.returncode))
    except subprocess.TimeoutExpired:
        log("two_stage_ota_sf %s timeout" % m)
try:
    r = subprocess.run([sys.executable, "la1a_uncovered.py"], cwd=H, env=env, capture_output=True, timeout=900)
    open(os.path.join(H, "uncovered.stdout.txt"), "wb").write(r.stdout + r.stderr)
    log("uncovered rc=%s" % r.returncode)
except subprocess.TimeoutExpired:
    log("uncovered timeout")
''', encoding='utf-8')
print('patched')
