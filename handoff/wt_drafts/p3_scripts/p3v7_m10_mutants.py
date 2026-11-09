"""Phase 3 design v7 -- M10 V3 생존 추정(4차 검토 S3). 읽기 전용 측정(초안 측정 -- M10 test 기대값·판정의 근거가 아니다, 작성자 != 검증자).

M10은 하네스 `run()`의 파이프라인 몸통을 새 진입점 `run_gmid_design_pipeline`으로 옮긴다(새 def = 본문 전체가 V3 대상, 범위 정책 계약 3).
옮긴 문장은 지금 `run()`의 문장과 같으므로, 지금 `run()`의 변이를 실제로 하나씩 실행해 '어떤 test 모양이 무엇을 죽이는가'를 잰다.
* 변이 생성 = 복제본 `tools/gates/mutate_changed.mutants`(게이트와 같은 연산자·경로).
* 실행 = `.ai/verification/20260930-p9-kcl-edges/scripts/e_inst_df36.py`와 같은 방식(하네스가 경로를 `__file__`에서 유도 -- 복제본 run_harness.py 경로로 exec,
  산출은 복제본 workspaces 아래, 실행 전 이전 산출 삭제, 엔진이 복제본 밖에서 import되면 중단). 변이마다 새 프로세스, 시간 제한 600초(B28 `--timeout`과 같은 값).
* 기록: instance.json 키 정렬 sha256(E-INST), stdout sha256, report.html sha256, 예외.
  죽음 판정 모양 (i) E-INST 해시만 (ii) (i) + stdout 대조 (iii) (ii) + report.html 해시.
* 기준 실행은 LINE 이벤트로 `run()`의 실행된 줄을 센다(회로별 도달 분기).
사용:
  python -P p3v7_m10_mutants.py trace  <root> <circuit> <ws> <out.json>
  python -P p3v7_m10_mutants.py mutant <root> <circuit> <ws> <out.json> <k>
  python -P p3v7_m10_mutants.py all    <root> <circuit> <workdir> <out.json>      (trace 2회 + 변이 전부, 케이스마다 <out>.partial.jsonl에 append)
  python -P p3v7_m10_mutants.py list   <root> <out.json>                          (변이 목록·줄·연산자만)
"""
import ast
import contextlib
import hashlib
import json
import os
import subprocess
import sys
import time
import types

MODE = sys.argv[1]
MAIN_ROOT = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"


def load_src(root, ws):
    """a796468의 하네스는 경로를 __file__에서 유도한다(DF-35) -- 치환 없이 <root>/workspaces/run_harness.py 경로로 exec.
    산출은 <root>/workspaces/<report_dir>/(스크래치 복제본). ws는 stdout 사본 위치로만 쓴다."""
    A = os.path.join(root, "skills", "analog-gmid-design", "assets")
    H = os.path.abspath(os.path.join(root, "workspaces", "run_harness.py"))
    src = open(H, encoding="utf-8").read()
    if MAIN_ROOT in src:
        sys.exit("main-checkout literal in run_harness")
    return A, H, src


def run_fn(src):
    t = ast.parse(src)
    for n in t.body:
        if isinstance(n, ast.FunctionDef) and n.name == "run":
            return t, n
    sys.exit("run def 없음")


def mutant_list(root):
    sys.path.insert(0, os.path.join(root, "tools", "gates"))
    import mutate_changed as mc
    src = open(os.path.join(root, "workspaces", "run_harness.py"), encoding="utf-8").read()
    _, fn = run_fn(src)
    out = []
    for op, path, f in mc.mutants(fn, src):
        try:
            node = mc._get(fn, path) if path else fn
            line = getattr(node, "lineno", fn.lineno)
            seg = ast.get_source_segment(src, node) if hasattr(node, "lineno") else ""
        except Exception:
            line, seg = fn.lineno, ""
        out.append({"op": op, "path": path, "line": line, "seg": (seg or "").splitlines()[0][:100] if seg else "", "fn": f})
    return out


def execute(root, circuit, ws, out, k=None, trace=False):
    A, H, src = load_src(root, ws)
    os.makedirs(ws, exist_ok=True)
    mod = types.ModuleType("run_harness_copy")
    mod.__file__ = H
    so = out + ".stdout.txt"
    buf = open(so, "w", encoding="utf-8")
    res = {"circuit": circuit, "k": k}
    lines = set()
    t0 = time.time()
    with contextlib.redirect_stdout(buf):
        code = compile(src, mod.__file__, "exec")
        exec(code, mod.__dict__)
        for m in ("sizing_recipe", "stick_diagram", "design_report"):
            f = os.path.normcase(os.path.abspath(sys.modules[m].__file__))
            if not f.startswith(os.path.normcase(A)):
                raise SystemExit("engine imported outside root: %s" % f)
        if k is not None:
            ml = mutant_list(root)
            mf = ml[k]["fn"]
            res.update({"op": ml[k]["op"], "path": ml[k]["path"], "line": ml[k]["line"]})
            modt = ast.Module(body=[mf], type_ignores=[])
            ast.fix_missing_locations(modt)
            exec(compile(modt, mod.__file__, "exec"), mod.__dict__)
        cfg = mod.SPECS[circuit]
        rd = os.path.join(mod.WORKSPACES_DIR, cfg["report_dir"])
        os.makedirs(rd, exist_ok=True)
        _stem = cfg["topology_file"].removesuffix(".topology.json")
        for _ext in (".instance.json", ".report.html"):
            if os.path.exists(os.path.join(rd, _stem + _ext)):
                os.remove(os.path.join(rd, _stem + _ext))   # 이전 실행 산출을 지운다(저장하지 않는 변이를 구별)
        if trace:
            M = sys.monitoring
            M.use_tool_id(M.PROFILER_ID, "m10")
            target = mod.run.__code__

            def on_line(c, ln):
                if c is target:
                    lines.add(ln)
                    return None
                return M.DISABLE
            M.register_callback(M.PROFILER_ID, M.events.LINE, on_line)
            M.set_local_events(M.PROFILER_ID, target, M.events.LINE)
        try:
            mod.run(circuit)
            res["exc"] = None
        except BaseException as e:  # 변이가 낸 예외도 기록(죽음)
            res["exc"] = "%s: %s" % (type(e).__name__, str(e)[:200])
    buf.close()
    res["elapsed_s"] = round(time.time() - t0, 2)
    stdout_text = open(so, encoding="utf-8").read()
    res["stdout_sha"] = hashlib.sha256(stdout_text.encode("utf-8")).hexdigest()
    stem = cfg["topology_file"].removesuffix(".topology.json")
    inst = os.path.join(rd, stem + ".instance.json")
    rep = os.path.join(rd, stem + ".report.html")
    if os.path.exists(inst):
        obj = json.load(open(inst, encoding="utf-8"))
        res["inst_sha"] = hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    else:
        res["inst_sha"] = None
    res["report_sha"] = hashlib.sha256(open(rep, "rb").read()).hexdigest() if os.path.exists(rep) else None
    res["fail_in_stdout"] = "[FAIL]" in stdout_text
    if trace:
        res["lines"] = sorted(lines)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


if MODE == "list":
    root, out = sys.argv[2], sys.argv[3]
    ml = mutant_list(root)
    json.dump([{k: v for k, v in m.items() if k != "fn"} for m in ml], open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(ml))
elif MODE in ("trace", "mutant"):
    root, circuit, ws, out = sys.argv[2:6]
    k = int(sys.argv[6]) if MODE == "mutant" else None
    r = execute(root, circuit, ws, out, k=k, trace=(MODE == "trace"))
    print(json.dumps({x: r.get(x) for x in ("k", "exc", "inst_sha", "elapsed_s")}))
elif MODE == "all":
    root, circuit, work, out = sys.argv[2:6]
    part = out + ".partial.jsonl"
    if os.path.exists(part):
        os.remove(part)
    me = os.path.abspath(__file__)
    py = [sys.executable, "-P", "-B", me]

    def sub(args, tag):
        o = os.path.join(work, tag + ".json")
        ws = os.path.join(work, "ws_" + tag)
        t0 = time.time()
        try:
            p = subprocess.run(py + [args[0], root, circuit, ws, o] + args[1:], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=600)
            r = json.load(open(o, encoding="utf-8")) if os.path.exists(o) else {"exc": "no output rc=%d %s" % (p.returncode, p.stderr[-300:])}
        except subprocess.TimeoutExpired:
            r = {"exc": "timeout600"}
        r["wall_s"] = round(time.time() - t0, 1)
        r["tag"] = tag
        with open(part, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        return r
    base1 = sub(["trace"], "base1")
    base2 = sub(["trace"], "base2")
    ml = mutant_list(root)
    res = []
    for k in range(len(ml)):
        r = sub(["mutant", str(k)], "m%03d" % k)
        r.update({"op": ml[k]["op"], "path": ml[k]["path"], "line": ml[k]["line"], "seg": ml[k]["seg"]})
        res.append(r)
    det = {x: base1.get(x) == base2.get(x) for x in ("inst_sha", "stdout_sha", "report_sha")}
    reached = set(base1.get("lines", []))

    def killed(r, shape):
        if r.get("exc") or r.get("fail_in_stdout") != base1.get("fail_in_stdout"):
            return True
        if r.get("inst_sha") != base1.get("inst_sha"):
            return True
        if shape >= 2 and r.get("stdout_sha") != base1.get("stdout_sha"):
            return True
        if shape >= 3 and r.get("report_sha") != base1.get("report_sha"):
            return True
        return False
    summ = {"circuit": circuit, "mutants": len(res), "deterministic": det, "base_elapsed_s": [base1.get("elapsed_s"), base2.get("elapsed_s")],
            "base_inst_exists": base1.get("inst_sha") is not None, "base_fail_in_stdout": base1.get("fail_in_stdout"),
            "reached_lines": sorted(reached)}
    for shape in (1, 2, 3):
        sv = [r for r in res if not killed(r, shape)]
        summ["survivors_shape%d" % shape] = len(sv)
        summ["survivor_list_shape%d" % shape] = ["%s L%d %s | %s" % (r["op"], r["line"], r["path"], r["seg"]) for r in sv]
    summ["survivors_shape1_unreached_line"] = sum(1 for r in res if not killed(r, 1) and r["line"] not in reached)
    summ["mutant_wall_s_total"] = round(sum(r.get("wall_s", 0) for r in res), 1)
    json.dump({"summary": summ, "results": res, "base": [base1, base2]}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in summ.items() if not k.startswith("survivor_list") and k != "reached_lines"}, ensure_ascii=False))
