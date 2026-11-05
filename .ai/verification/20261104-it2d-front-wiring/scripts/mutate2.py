"""IT-2d·2e 손 뮤턴트(복제본 임시 수정, 커밋 없음). 인자: 복제본 루트, 결과 jsonl."""
import ctypes, json, os, subprocess, sys, time

ROOT, OUT = sys.argv[1], sys.argv[2]
E = ROOT + "/skills/analog-gmid-design/gmid_engine/"
D = "metrics/test_icm_window.py metrics/test_metrics_aux.py metrics/test_ls_swing.py metrics/test_registry.py".split()
DF = D + ["metrics/test_ss_evaluate.py"]
K = "sizing/test_kernel_run.py sizing/test_size_and_seal.py sizing/test_seal_versions.py".split()
MUT = [
 ("D1 dc 결측 판정이 ss 와 같게", "metrics/metrics_aux.py", "        return isinstance(nodal, Undefined)\n", "        return bool(ss.missing)\n", D),
 ("D2 dc 결측 판정 항상 False(저항 결측 통과)", "metrics/metrics_aux.py", "        return isinstance(nodal, Undefined)\n", "        return False\n", D),
 ("D3 ss 결측 판정 삭제", "metrics/metrics_aux.py", "        return bool(ss.missing)\n", "        return False\n", D),
 ("D4 어휘 밖 영역 통과", "metrics/metrics_aux.py", '    raise ValueError("metrics_aux: 결측 판정 영역 %r 은 (%r, %r) 밖이다" % (domain, DOMAIN_DC, DOMAIN_SS))\n', "    return False\n", D),
 ("D5 전달 뷰 보고 결측 때도", "metrics/metrics_aux.py", "for view in () if ss.missing else transfer_views:", "for view in transfer_views:", D),
 ("D6 input_dc 뒤집음", "metrics/metrics_aux.py", '"pending" if input_dc_v is None else "declared"', '"declared" if input_dc_v is None else "pending"', D),
 ("D7 포트 상태 안 봄", "metrics/metrics_aux.py", "if found is None or found.input_status != INPUT_STATUS_MEASURED:", "if found is None:", D),
 ("D8 undefined 합치기 스윙만", "metrics/metrics_aux.py", "undefined=swing.undefined + icm.undefined)", "undefined=swing.undefined)", D),
 ("D9 margin 을 lo·hi 로", "metrics/icm_window.py", "min(centre - low, high - centre)", "min(centre - ports[0].lo, ports[0].hi - centre)", D),
 ("D10 미측정 포트 통과", "metrics/icm_window.py", "    if lacking is not None:\n", "    if False:\n", D),
 ("D11 구성 None code 교체", "metrics/icm_window.py", "return _undefined((first.code, first.category, first.detail))", 'return _undefined(("x", "numeric", first.detail))', D),
 ("D12 ff_gm_ratio dc", "metrics/registry.py", '("ff_gm_ratio", "ratio", "ss",', '("ff_gm_ratio", "ratio", "dc",', D),
 ("D13 offset ss", "metrics/registry.py", '("offset_sys_mv", "mv", "dc",', '("offset_sys_mv", "mv", "ss",', D),
 ("D14 ls_swing 출력 넷 전압 검사 삭제", "metrics/ls_swing.py", "    if lacking:\n", "    if False:\n", D),
 ("D15 구성 불일치 ValueError 삭제", "metrics/icm_window.py", '    if None in (config.vcm0, config.vcm_lo, config.vcm_hi):\n        raise ValueError("icm_window_metrics: 포트는 모두 측정됐는데 V_cm 칸이 None -- icm_config 불일치")\n', "", D),
 ("E1 커널 부착 옛 꼴", "sizing/kernel_run.py", "attach_partial(exc, snapshot.derive_child(writers_in_scope(ctx.base, before)))", "attach_partial(exc, snapshot)", K),
 ("E2 봉인 항목 부착 옛 꼴", "sizing/seal.py", "attach_partial(exc, snapshot.derive_child(writers_in_scope(base, (b for b, _ in calls))))      # 봉인", "attach_partial(exc, snapshot)      # 봉인", K),
 ("E3 위반 부착 보고서 뺌", "sizing/seal.py", "[b for b, _ in calls] + [dc_seal_report]", "[b for b, _ in calls]", K),
 ("E4 base None 통과", "sizing/seal_versions.py", '    if base is None:\n        raise TypeError("writers_in_scope: base 는 필수다(ctx.base)")\n', "", K),
 ("E5 앞 블록 기록 안 함", "sizing/kernel_run.py", "        snapshot = _call_block(ctx, block, snapshot, extras, done)\n        done.append(block)\n    steps = tuple(steps + later)", "        snapshot = _call_block(ctx, block, snapshot, extras, done)\n    steps = tuple(steps + later)", K),
 ("E6 coverage 인라인 재구현", "sizing/seal_versions.py", "foreign = tuple(sorted(used - writers_in_scope(base, (block for block, _extras in calls))))", "foreign = tuple(sorted(used - base_writers - called))", K),
 ("E7 보고서 블록 실패 부착 옛 꼴", "sizing/seal.py", "        snapshot = dc_seal_report(snapshot, item4, item5, donors=donors, counters=counters)\n    except CANDIDATE_FAILURE_CLASSES as exc:\n        attach_partial(exc, snapshot.derive_child(writers_in_scope(base, (b for b, _ in calls))))", "        snapshot = dc_seal_report(snapshot, item4, item5, donors=donors, counters=counters)\n    except CANDIDATE_FAILURE_CLASSES as exc:\n        attach_partial(exc, snapshot)", K),
]


class M(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong),
                ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong)]


def free():
    m = M(); m.l = ctypes.sizeof(M); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.a / 2**30


env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
for name, rel, old, new, tests in MUT:
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
