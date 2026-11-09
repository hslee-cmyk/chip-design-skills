# O-268 / O-269 실현 가능성 실측 (측정 도구 -- 엔진 code 수정 0, 저장소 쓰기 0).
# 엔진 인용 용도 = 엔진 밖 사실 측정 + 재작성 범위 확인(원칙 8). as-built 값은 근거가 아니라 측정 입력.
# 대상 = 격리 복제본 C:/o268_iso (master bbcc83a0). 회로는 하나씩 별도 프로세스(worker)로 돌리고
# driver 가 여유 메모리를 지켜본다(착수 대기 < 3.7 GB, 실행 중 < 1 GB 면 그 PID 만 멈추고 '미측정').
#
# 사용: python o268_measure.py driver            -- 13회로 전부, 결과 o268_measure.jsonl 에 회로마다 append
#       python o268_measure.py worker <회로> <출력 json>   (driver 가 부름)
#
# 읽는 엔진 산출(READS 만, 새 계산법 없음):
#   * 출발점 = layer0_start 가 처음 받아들인 평가(사다리 칸/보정/Halton) -- `_maxmin` 에 들어가는 `first`.
#     최대-최소 단계는 출발점 확정 뒤라 측정에 필요 없어 `_maxmin` 진입에서 멈춘다(측정 도구 안 대체, 엔진 무변경).
#   * node.dc_v (출발점 노드 전압), node.dc_window (W4 뿌리 KVL 순서 창: VDS >= 0, VDSAT 항 없음),
#     graph.icm_config (ICMR 측정 구성 창 vcm_lo/vcm_hi, VDS = VDSAT), node.dc_writer (입력 점 관계),
#     metrics_aux 의 swing_icmr 보고(ls_swing 경로 합 -- 계획상 삭제 대상, 참고용, spec 이 swing/icmr 를 요청한 회로만 존재).
#   * 계획 정의 출력 스윙 창(card DE-1, N6.8) 생산자 = master 에 없음 -> '정의 자리 없음'.
import os, sys, json, pathlib, tempfile, time, traceback, subprocess

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
SKILL = pathlib.Path("C:/o268_iso/skills/analog-gmid-design")
LIB = SKILL / "assets" / "library"
HERE = pathlib.Path(__file__).parent
OUT_JSONL = HERE / "o268_measure.jsonl"
TEMP_ROOT = pathlib.Path(tempfile.gettempdir()) / "o268_measure_work"
WAIT_FREE_GB = 3.7
STOP_FREE_GB = 1.0


def circuits():
    return sorted(p.name[: -len(".sizing_spec.json")] for p in LIB.glob("*.sizing_spec.json"))


def app(path, row):
    with open(path, "ab") as fh:
        fh.write((json.dumps(row, ensure_ascii=False, default=lambda o: repr(o)[:600]) + "\n").encode("utf-8"))


# ---------------------------------------------------------------- 1. spec 선언 현황 (파일만)
SWING_ICMR_WORDS = ("icmr", "icm_", "swing", "out_range", "output_range", "input_range")


def _find_keys(obj, words, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = path + "/" + k
            if any(w in k.lower() for w in words):
                hits.append(p)
            hits += _find_keys(v, words, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _find_keys(v, words, path + "[%d]" % i)
    return hits


def spec_facts(c):
    spec = json.loads((LIB / (c + ".sizing_spec.json")).read_text(encoding="utf-8"))["human"]
    topo = json.loads((LIB / (c + ".topology.json")).read_text(encoding="utf-8"))
    sup = spec.get("supplies_v", {}).get("values", {})
    idc = spec.get("input_dc")
    if not isinstance(idc, dict):
        idc_mode = "missing"
    elif "pending" in idc:
        idc_mode = "pending:" + str(idc["pending"])
    elif idc.get("engine"):
        idc_mode = "engine"
    elif "net" in idc:
        idc_mode = "net:" + str(idc["net"])
    elif "value_v" in idc or "value" in idc:
        idc_mode = "value:" + str(idc.get("value_v", idc.get("value")))
    else:
        idc_mode = "other:" + json.dumps(idc, ensure_ascii=False)[:120]
    fb = spec.get("feedback")
    if fb is None:
        fb_mode, fb_elems, fb_rec = "missing", None, None
    elif "pending" in fb:
        fb_mode, fb_elems, fb_rec = "pending:" + str(fb["pending"]), None, None
    else:
        fb_elems = fb.get("elements")
        fb_mode = "declared_elements" if fb_elems else "empty_list(unity_beta_rule)"
        fb_rec = (fb.get("source") or {}).get("record")
    cons = []
    for row in spec.get("constraints", []):
        m = row.get("metric")
        ms = m if isinstance(m, str) else json.dumps(m)
        if any(w in ms.lower() for w in ("icmr", "icm_", "swing", "out")) or ("MOD5" in ms):
            cons.append({"metric": m, "op": row.get("op"), "value": row.get("value"),
                         "view": row.get("view")})
    ports = topo.get("ports", {})
    port_rows = []
    if isinstance(ports, dict):
        for k, v in ports.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict):
                port_rows.append({"net": k, "direction": v.get("direction"), "role": v.get("role")})
            elif isinstance(v, list):
                for e in v:
                    if isinstance(e, dict):
                        port_rows.append({"key": k, **{kk: e.get(kk) for kk in ("net", "direction", "role")}})
    return {
        "supplies_v": sup,
        "rail_mid_v": (max(sup.values()) + min(sup.values())) / 2 if sup else None,
        "input_dc": idc, "input_dc_mode": idc_mode,
        "feedback_mode": fb_mode, "feedback_elements": fb_elems, "feedback_record": fb_rec,
        "swing_icmr_constraints": cons,
        "spec_keys_swing_icmr": _find_keys(spec, SWING_ICMR_WORDS),
        "ports": port_rows,
        "topology_ports_raw_keys": list(ports.keys()) if isinstance(ports, dict) else str(type(ports)),
    }


# ---------------------------------------------------------------- 2. worker (엔진 출발점 READS)
class _Captured(Exception):
    pass


def _jsonable(x):
    try:
        json.dumps(x)
        return x
    except TypeError:
        if hasattr(x, "__dataclass_fields__"):
            return {k: _jsonable(getattr(x, k)) for k in x.__dataclass_fields__}
        if isinstance(x, (tuple, list)):
            return [_jsonable(v) for v in x]
        if isinstance(x, dict):
            return {str(k): _jsonable(v) for k, v in x.items()}
        return repr(x)[:400]


def worker(c, out_path):
    sys.path.insert(0, str(SKILL))
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    res = {"circuit": c, "phase": "start"}

    def dump():
        pathlib.Path(out_path).write_text(json.dumps(res, ensure_ascii=False, default=lambda o: repr(o)[:600]), encoding="utf-8")

    try:
        import gmid_engine.search  # noqa: F401
        from gmid_engine.lut import LutMemo
        from gmid_engine.pipeline import run_stage_a, run_stage_b
        from gmid_engine.search import SearchSettings, build_search_context, open_run
        from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, LutAccess
        from gmid_engine.tests.generality.pipeline import Env      # 저장소 공용 실데이터 LUT·PDK 적재(읽기만)
        l0 = sys.modules["gmid_engine.search.layer0_center"]
        env = Env()
        lut, pdk, rule = env.lut, env.pdk, env.lut_rule

        work = pathlib.Path(tempfile.mkdtemp(prefix="o268_%s_" % c[:8], dir=str(TEMP_ROOT)))
        donors, counters = open_run()
        a = run_stage_a(LIB / (c + ".topology.json"), LIB / (c + ".sizing_spec.json"), lut, output_dir=work / c,
                        donors=donors, counters=counters)
        res["stage_a"] = a.status
        if a.status != "ok":
            res["phase"] = "stage_a_stop"; res["stage_a_detail"] = repr(getattr(a, "reasons", None) or getattr(a, "report", None))[:1500]
            dump(); return
        memo = LutMemo(lut, point=1 << 14, curve=1 << 12, root=1 << 14)
        # 수동소자 상자: spec search.theta_bounds 정본(None) 먼저. 거부되면 앞선 측정 도구(la1a_pg)와 같은 run 단위 상자로 1회 -- 기록.
        bounds_used = "spec_theta_bounds"
        settings = SearchSettings(300.0, 40, None, (("front_budget_s", "o268 measurement"),), None)
        try:
            b = run_stage_b(a, memo, pdk, output_dir=work / c, diagnostic=True, settings=settings)
        except Exception:
            res["stage_b_spec_bounds_error"] = traceback.format_exc()[-800:]
            b = None
        res["stage_b_spec_bounds_status"] = None if b is None else b.status
        if b is None or b.status != "ok":
            bounds_used = "measurement_box(1e2..1e5 ohm, 1e-13..1e-10 F) -- spec 상자 결측으로 거부된 뒤"
            settings = SearchSettings(300.0, 40, (1e2, 1e5), (("front_budget_s", "o268 measurement"),), (1e-13, 1e-10))
            b = run_stage_b(a, memo, pdk, output_dir=work / c, diagnostic=True, settings=settings)
        res["stage_b"] = b.status; res["bounds_used"] = bounds_used
        if b.status != "ok":
            res["phase"] = "stage_b_stop"; dump(); return
        kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), LutAccess(memo), donors=a.donors, counters=a.counters)
        s3 = work / c / "s3"; s3.mkdir(parents=True, exist_ok=True)
        sctx = build_search_context(kctx, a.spec, settings, str(s3), pdk, rule, code_fp=a.code_fp)
        res["phase"] = "sctx_ok"; dump()

        cap = {}

        def _stop_at_maxmin(sctx_, variables, theta, cells, first, tag):
            cap["first"] = first
            raise _Captured()

        l0._maxmin = _stop_at_maxmin     # 측정 도구 안 대체: 출발점 확정 직후 멈춤
        t0 = time.time()
        try:
            r = l0.layer0_start(sctx)
            res["layer0_no_start"] = repr(r)[:3000]
        except _Captured:
            pass
        res["layer0_s"] = round(time.time() - t0, 2)
        first = cap.get("first")
        if first is None:
            res["phase"] = "no_start_point"; dump(); return
        res["phase"] = "start_point"
        res["start_status"] = first.status
        snap = first.evaluation.snapshot
        col = lambda kind, field: dict(snap.column(kind, field))
        dc_v = col("node", "dc_v")
        rails = {n: v for n, v in snap.column("node", "dc_rail_v") if v is not None}
        dirs = col("node", "port_direction"); roles = col("node", "port_role")
        res["ports"] = {n: {"direction": d, "role": roles.get(n)} for n, d in dirs.items()}
        res["rails"] = rails
        res["port_v"] = {n: dc_v.get(n, rails.get(n)) for n in dirs}
        ins = [n for n, d in dirs.items() if d == "input"]
        outs = [n for n, d in dirs.items() if d == "output"]
        vin = [res["port_v"][n] for n in ins if res["port_v"].get(n) is not None]
        res["v_cm_start"] = sum(vin) / len(vin) if vin else None
        res["v_out_start"] = {n: res["port_v"].get(n) for n in outs}
        writers = col("node", "dc_writer")
        res["input_writers"] = {n: _jsonable(writers.get(n)) for n in ins}
        win = col("node", "dc_window")
        res["kernel_w4_window"] = {n: _jsonable(w) for n, w in win.items()}
        try:
            icm = snap.value("graph", "metrics", "icm_config")
            res["icm_config"] = _jsonable(icm)
        except KeyError:
            res["icm_config"] = None
        try:
            cfgw = col("node", "dc_window_cfg")
            res["dc_window_cfg"] = {n: _jsonable(w) for n, w in cfgw.items()}
        except Exception as exc:
            res["dc_window_cfg"] = repr(exc)
        try:
            aux = snap.value("graph", "metrics", "metrics_aux")
            res["ls_swing_report_reference"] = [_jsonable(rep) for name, rep in aux.reports if name == "swing_icmr"]
        except KeyError:
            res["ls_swing_report_reference"] = None
        res["phase"] = "done"
        dump()
    except Exception:
        res["error"] = traceback.format_exc()[-3000:]
        dump()


# ---------------------------------------------------------------- 3. driver
def free_gb():
    import psutil
    return psutil.virtual_memory().available / 2 ** 30


def driver(only=None):
    import psutil
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    for c in (only or circuits()):
        row = {"circuit": c, "t": time.strftime("%Y-%m-%d %H:%M:%S")}
        row["spec"] = spec_facts(c)
        while free_gb() < WAIT_FREE_GB:
            time.sleep(30)
        row["free_gb_at_start"] = round(free_gb(), 2)
        out = TEMP_ROOT / ("%s.worker.json" % c)
        if out.exists():
            out.unlink()
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        log = open(TEMP_ROOT / ("%s.worker.log" % c), "wb")
        p = subprocess.Popen([sys.executable, str(pathlib.Path(__file__).resolve()), "worker", c, str(out)],
                             env=env, stdout=log, stderr=subprocess.STDOUT)
        killed, min_free, peak_rss = None, 99.0, 0.0
        t0 = time.time()
        while p.poll() is None:
            f = free_gb(); min_free = min(min_free, f)
            try:
                peak_rss = max(peak_rss, psutil.Process(p.pid).memory_info().rss / 2 ** 30)
            except Exception:
                pass
            if f < STOP_FREE_GB:
                p.kill(); p.wait(); killed = "free_mem_below_1GB(%.2f)" % f
                break
            time.sleep(2)
        log.close()
        row.update({"pid": p.pid, "returncode": p.returncode, "killed": killed, "min_free_gb": round(min_free, 2),
                    "peak_rss_gb": round(peak_rss, 2), "wall_s": round(time.time() - t0, 1)})
        if killed is None and out.exists():
            row["engine"] = json.loads(out.read_text(encoding="utf-8"))
        else:
            row["engine"] = None
            row["unmeasured"] = killed or ("worker_exit_%s_no_output" % p.returncode)
        app(OUT_JSONL, row)


if __name__ == "__main__":
    if sys.argv[1] == "worker":
        worker(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "driver":
        driver(sys.argv[2:] or None)
