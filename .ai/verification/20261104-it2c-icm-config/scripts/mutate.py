"""손 뮤턴트(복제본 임시 수정, 커밋 없음): 한 개씩 바꾸고 관련 test 를 -x 로 돌린 뒤 원복. 인자: 복제본 루트, 결과 jsonl. 메모리 < 2 GB 면 멈춤."""
import ctypes, json, subprocess, sys, time, os

ROOT, OUT = sys.argv[1], sys.argv[2]
E = ROOT + "/skills/analog-gmid-design/gmid_engine/"
ICM = "metrics/test_icm_config.py metrics/test_ss_evaluate.py".split()
SW = "metrics/test_icm_config.py sizing/test_input_window.py sizing/test__helpers_dc_solve.py".split()
AUX = "metrics/test_offset_analysis.py metrics/test_offset_systematic.py metrics/test_block_residual.py metrics/test__helpers_view.py metrics/test_metrics_aux.py metrics/test_icm_config.py".split()
SYM = "search/test_canonical_order.py graph/test_s1_symmetry.py graph/test_canonical_form.py".split()
MUT = [
 ("M1 sat 행 여유 +tol", "sizing/_helpers_dc_solve.py", "rows.append((d, s, sign, vds - sat, _ROW_SAT))", "rows.append((d, s, sign, vds - sat - 0.001, _ROW_SAT))", SW),
 ("M2 triode 행 여유 +tol", "sizing/_helpers_dc_solve.py", "rows.append((d, s, -sign, sat - vds, _ROW_TRIODE))", "rows.append((d, s, -sign, sat - vds - 0.001, _ROW_TRIODE))", SW),
 ("M3 건너뛴 행 slack<0 무시(fail-open)", "sizing/input_window.py", "            if slack < 0:\n                return None\n", "", SW),
 ("M4 레일 자름 삭제", "metrics/icm_config.py", "        if s != 0:\n            a, b = (circuit.lo", "        if False:\n            a, b = (circuit.lo", ICM),
 ("M5 servo 보정 삭제", "metrics/icm_config.py", "slope = {net: float(volt_x[i]) - float(volt_e[i]) / span * ratio for net, i in index.items()}", "slope = {net: float(volt_x[i]) for net, i in index.items()}", ICM),
 ("M6 용량 전용 노드 갈래 삭제", "metrics/icm_config.py", "    if floating:\n", "    if False:\n", ICM),
 ("M7 기본 뷰 거름 삭제", "metrics/icm_config.py", "if view.kind == VIEW_TRANSFER and view.default_port)", "if view.kind == VIEW_TRANSFER)", ICM + ["graph/test_views.py"]),
 ("M8 tol_v 최댓값", "metrics/icm_config.py", "return min(found) if found else None", "return max(found) if found else None", ICM),
 ("M9 V_cm 첫 포트 감도", "metrics/icm_config.py", "mean_slope = sum(slope[net] for net in inputs) / len(inputs)", "mean_slope = slope[inputs[0]]", ICM),
 ("M10 g_bound 셋째 항 삭제", "metrics/_helpers_nodal.py", "                             + _gamma(size + 1, unit_roundoff) * abs(g[row, col]))", "                             )", ["metrics/test__helpers_nodal.py"] + ICM),
 ("M11 view_factor 고정 집합 무시", "metrics/_helpers_view.py", "return base.factor if fixed == base.fixed else nodal_factor(base.g, fixed)", "return base.factor", AUX),
 ("M12 default_port 늘 True", "graph/views.py", "default_port=key in default_keys", "default_port=True", ["graph/test_views.py"] + ICM),
 ("M13 icm_config 호출 삭제", "metrics/ss_evaluate.py", "        snapshot = icm_config_window(snapshot, ctx.lut, frozenset(ctx.inputs.linear_devices), **keys)", "        pass  #", ICM),
 ("M14 피벗 판정 분해능 삭제", "metrics/icm_config.py", "if abs(a_e) * span <= delta:", "if abs(a_e) * span <= 0:", ICM),
 ("M15 용량 결측도 Undefined", "metrics/ss_nodal.py", "missing = tuple(name for name in ss.missing if is_dc_conducting_passive(kinds[name]))", "missing = tuple(ss.missing)", ICM),
 ("M16 입력 넷 고정 제외", "metrics/ss_nodal.py", "tuple(ss.ground_nets) + tuple(ss.input_nets)", "tuple(ss.ground_nets)", ICM),
 ("M17 p 포트 정준화 삭제", "graph/s1_symmetry.py", "    if len(p_ports) == 1:\n", "    if False:\n", SYM),
 ("M18 h 대신 위치 맞바꿈(비자기동형)", "graph/s1_symmetry.py", "    return {v: position[h.get(v, v)] for v in position}", "    return {**position, p_port: position[best], best: position[p_port]}", SYM),
 ("M19 archive 옛 item", "search/archive.py", 'if hasattr(value, "tolist"):', 'if hasattr(value, "item"):', ["search/test_archive.py"] + ICM),
 ("M20 차동 출력 감지 부호", "metrics/icm_config.py", "return ((plus[0], 1.0), (minus[0], -1.0))", "return ((plus[0], 1.0), (minus[0], 1.0))", ICM),
 ("M21 NodalSystem 잠금 삭제", "metrics/aux_types.py", "            array.flags.writeable = False\n", "            pass\n", ICM),
 ("M22 빈 창 통과", "metrics/icm_config.py", "return None if lo > hi else (lo, hi)", "return (lo, hi)", ICM),
 ("M23 structure rule_hash 되돌림", "../assets/library/nmcnr_amplifier.structure.json", "87455b1b2c661149768cbdf83b1539763a7a0d3433081d9ccc691622c1d13f68", "ca0fde40c5599facc08b18d3fd94036b7fd8b242580edf5db1fd0eb54ad04347", ["graph/test_s1v_build.py"]),
 ("M24 g_ops MOS 항목 0", "metrics/stamp_mos.py", None, None, ["metrics/test_stamp_mos.py"]),
]


class M(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong),
                ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong)]


def free():
    m = M(); m.l = ctypes.sizeof(M); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.a / 2**30


env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
for name, rel, old, new, tests in MUT:
    if old is None:
        continue
    while free() < 3.7:
        time.sleep(15)
    p = E + rel
    raw = open(p, "rb").read()
    src = raw.decode("utf-8")
    crlf = "\r\n" in src
    needle = old.replace("\n", "\r\n") if crlf else old
    repl = new.replace("\n", "\r\n") if crlf else new
    row = {"mut": name, "file": rel}
    if src.count(needle) != 1:
        row["error"] = "needle count %d" % src.count(needle)
    else:
        open(p, "wb").write(src.replace(needle, repl).encode("utf-8"))
        try:
            t = time.time()
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "--tb=line"] + ["gmid_engine/tests/" + x for x in tests],
                               cwd=ROOT + "/skills/analog-gmid-design", env=env, capture_output=True, encoding="utf-8", errors="replace")
            lines = r.stdout.strip().splitlines()
            row.update(killed=r.returncode != 0, rc=r.returncode, secs=round(time.time() - t), tail=[x[:200] for x in lines[-3:]])
        finally:
            open(p, "wb").write(raw)
    with open(OUT, "ab") as f:
        f.write((json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8"))
    if free() < 2.0:
        with open(OUT, "ab") as f:
            f.write(b'{"stop":"mem<2"}\n')
        sys.exit(3)
with open(OUT, "ab") as f:
    f.write(b'{"done":true}\n')
