"""usage: mutants_ub1.py <mut skill root> <out jsonl> <first> <last>   -- 복사본 트리(mut)에서 뮤턴트를 하나씩 적용해 지정 test 를 돌리고 되돌린다. 케이스마다 append."""
import json
import os
import pathlib
import subprocess
import sys
import time

root = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
first, last = int(sys.argv[3]), int(sys.argv[4])
E = root / "gmid_engine"
T = "gmid_engine/tests/"
NODAL = [T + "metrics/test__helpers_nodal.py", T + "metrics/test_dc_limit.py"]
BLOCK = [T + "metrics/test_block_model.py", T + "metrics/test_block_residual.py", T + "metrics/test_ff_gm_ratio.py"]
ROW = [T + "metrics/test_block_gain_model.py", T + "metrics/test_block_gain_bound.py", T + "metrics/test_block_param_tables.py", T + "search/test_iv_gain_l.py"]
GATE = [T + "metrics/test_sensitivity_gate.py", T + "search/test_gate_run.py", T + "search/test_find_front.py"]
M = [
    ("T-10a owners 에서 block.members 뺌", "metrics/block_model.py", "owners = (set(block.members) | set(extra)) - barred", "owners = set(extra) - barred", BLOCK),
    ("metric_structure members 안 채움", "metrics/metric_structure.py", "tuple(sorted(name for name, _role in b.roles)))", "())", [T + "metrics/test_metric_structure.py"] + BLOCK),
    ("block_residual ground 안 넘김", "metrics/block_residual.py", ", ground=vstruct.ac_ground)", ")", BLOCK),
    ("ff_gm_ratio ground 안 넘김", "metrics/ff_gm_ratio.py", ", ground=vstruct.ac_ground)", ")", BLOCK),
    ("limit_matrix 행 교체 없음", "metrics/_helpers_dc.py", "    out[rows, :] = numpy.asarray(c)[rows, :]\n", "", NODAL + BLOCK),
    ("capacitance_matrix MOS 용량 뺌", "metrics/_helpers_nodal.py", " + tuple(mos_stamps(m) for m in circuit.mos), \"c\"", ", \"c\"", NODAL + BLOCK),
    ("capacitance_matrix 커패시터 뺌", "metrics/_helpers_nodal.py", "tuple(two_terminal_stamps(k) for k in circuit.capacitors) + ", "", NODAL + BLOCK),
    ("전하 노드 주입 거부 없앰", "metrics/_helpers_nodal.py", "    if any(node in charge for node in (injection or {})):\n        return None, None\n", "", NODAL),
    ("수반 전하 칸 NaN 없앰", "metrics/_helpers_nodal.py", "    z[list(charge)] = numpy.nan\n", "", NODAL),
    ("floating 에 read 조건 뺌(옛 0 V)", "metrics/_helpers_nodal.py", "not (g_row[i] or c_row[i] or read[i])", "not (g_row[i] or c_row[i])", NODAL + BLOCK),
    ("block_local_gain missing 거부 없앰", "metrics/block_model.py", "    if charge and ss.missing:", "    if False:", BLOCK),
    ("block_local_gain C 늘 조립(A-4)", "metrics/block_model.py", "c = capacitance_matrix(ss.circuit, size) if charge else numpy.zeros((size, size))", "c = capacitance_matrix(ss.circuit, size)", BLOCK),
    ("막다른 규칙 gate 독자 뺌", "metrics/block_model.py", "n not in outputs and n not in touched and count[n] == 1", "n not in outputs and count[n] == 1", BLOCK),
    ("막다른 규칙 출력 예외 뺌", "metrics/block_model.py", "n not in outputs and n not in touched and count[n] == 1", "n not in touched and count[n] == 1", BLOCK),
    ("막다른 가지 안 뺌", "metrics/block_model.py", "        dead = {n for n in unknown if n not in outputs and n not in touched and count[n] == 1}\n", "        dead = set()\n", BLOCK),
    ("비멤버 MOS 스탬프 안 함", "metrics/block_model.py", "stamped_mos = {l for l, m in mos.items() if l not in barred and (m.d in unknown or m.s in unknown)}", "stamped_mos = {l for l, m in mos.items() if l in owners and (m.d in unknown or m.s in unknown)}", BLOCK),
    ("용량 폐포 없앰", "metrics/block_model.py", "            if (a in charge) != (b in charge):\n", "            if False:\n", BLOCK),
    ("남의 블록 넷 F 에서 뺌", "metrics/block_model.py", "set(block.inputs) | outside if n in index}", "set(block.inputs) if n in index}", BLOCK),
    ("행 모드 전하 넷 거부 없앰", "metrics/block_gain_model.py", "    if charge:\n        return None, REASON_CHARGE_NODE_ROW\n", "", ROW),
    ("행 모드 others F 에서 뺌", "metrics/block_gain_model.py", "fixed = set(ground) | set(drive) | (set(spec.others) - set(spec.nodes))", "fixed = set(ground) | set(drive)", ROW),
    ("omitted_load 안 적음", "metrics/block_gain_model.py", "() if reference is None else (reference,), omitted, decomposed)", "() if reference is None else (reference,), (), decomposed)", ROW),
    ("decomposed_only 인증 허용", "metrics/block_gain_bound.py", "    if model.decomposed_only:\n", "    if False:\n", ROW),
    ("E-16 안쪽 찾기 없앰", "metrics/block_gain_bound.py", "    best, values, unchecked, l_rows = _interior(model, tables, idx, best, values)\n", "    unchecked, l_rows = False, 0\n", ROW),
    ("E-16 NaN 끝점 인증", "metrics/block_gain_bound.py", "    if unchecked:\n        return BlockBound", "    if False:\n        return BlockBound", ROW),
    ("E-16 bin 검사 없앰", "metrics/block_gain_bound.py", "if not all(tables.same_l_bin(kind, lo_i, hi_i) for kind in kinds):", "if False:", ROW),
    ("same_l_bin 지도 없으면 참", "metrics/block_param_tables.py", "return bool(bins) and bins[int(i_a)] == bins[int(i_b)]", "return (not bins) or bins[int(i_a)] == bins[int(i_b)]", ROW),
    ("게이트 None 섭동 조용히 생략", "metrics/sensitivity_gate.py", "            unmeasured.append(label)\n", "", GATE),
    ("게이트 base None 판정 없앰", "metrics/sensitivity_gate.py", "    if None in base:\n", "    if False:\n", GATE),
    ("게이트 빈 runs ok", "metrics/sensitivity_gate.py", "    if not runs:\n", "    if False:\n", GATE),
    ("gate_run res None 조용한 생략", "search/gate_run.py", "            runs.append((name, None, None, None))                       # 못 잰 섭동은 조용히 건너뛰지 않고 행으로 남긴다(unmeasured)\n", "", GATE),
    ("gate_run ceiling 안 넘김", "search/gate_run.py", ", ceiling=e_total(sctx))", ")", GATE),
    ("find_front 빈 front 행 없음", "search/find_front.py", "    notes.append({\"verdict\": gate.verdict, \"reason\": gate.reason,", "    if out[\"front\"]: notes.append({\"verdict\": gate.verdict, \"reason\": gate.reason,", GATE),
    ("icm floating 만", "metrics/icm_config.py", "tuple(nodal.factor[4]) + tuple(nodal.factor[5])", "tuple(nodal.factor[4])", [T + "metrics/test_icm_config.py"]),
    ("off_delta 전하 노드 허용", "metrics/ss_off_delta.py", "if i in floating or i in charge)", "if i in floating)", [T + "metrics/test_ss_off_delta.py"]),
    ("ss_nodal missing·전하 거부 없앰", "metrics/ss_nodal.py", "if ss.missing and value.factor[5]:", "if False:", [T + "metrics/test_metrics_aux.py", T + "metrics/test_ss_metrics.py", T + "metrics/test__helpers_nodal.py"]),
    ("view_factor C 영행렬", "metrics/_helpers_view.py", "c=capacitance_matrix(ss.circuit, len(ss.nodes)))", "c=base.g * 0)", BLOCK + [T + "metrics/test_offset_analysis.py"]),
    ("iv_gain_l 사유 행 없앰", "search/iv_gain_l.py", "        if model.omitted_load:", "        if False:", ROW),
]
env = dict(os.environ)
env.update(OPENBLAS_NUM_THREADS="1", PYTHONUTF8="1", APPDATA="C:/Users/HSLEE/AppData/Roaming", USERPROFILE="C:/Users/HSLEE",
           PYTHONPYCACHEPREFIX=str(root.parent / "pyc_mut"))
for n, (name, rel, old, new, tests) in enumerate(M):
    if not first <= n <= last:
        continue
    path = E / rel
    text = path.read_bytes().decode("utf-8")
    crlf_old, crlf_new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    if old not in text and crlf_old in text:
        old, new = crlf_old, crlf_new
    if old not in text:
        rec = {"n": n, "name": name, "status": "NOT_APPLIED"}
    else:
        path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
        existing = [t for t in tests if (root / t).exists()]
        t0 = time.time()
        p = subprocess.run([sys.executable, "-m", "pytest", *existing, "-x", "-q", "--tb=line", "-p", "no:cacheprovider", "-W", "ignore"], cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = [l for l in p.stdout.splitlines() if l.startswith("FAILED") or l.startswith("ERROR")][:2]
        rec = {"n": n, "name": name, "status": "killed" if p.returncode == 1 else ("survived" if p.returncode == 0 else "rc%d" % p.returncode), "tests": [t.split("/")[-1] for t in existing], "secs": round(time.time() - t0, 1), "by": tail}
        path.write_bytes(text.encode("utf-8"))
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(rec["n"], rec["status"], rec["name"], flush=True)
