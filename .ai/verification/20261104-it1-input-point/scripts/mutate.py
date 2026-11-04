"""IT-1 실제 거부·뮤테이션: 격리 복제본 파일을 바이트로 임시 수정 -> test -> 원 바이트 복원. 커밋 없음. 결과 append."""
import json
import os
import re
import subprocess
import sys

ISO, OUT = sys.argv[1], sys.argv[2]
ROOT = ISO + "/skills/analog-gmid-design"
E = "gmid_engine/"
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")

MUT = [
    ("R1 입력 정지 제거(input_cm_undefined -> 무동작)", "sizing/writer_plan.py",
     '''    raise StructureUnresolvedError(devices=(), detail={"reason": UNSUPPORTED_RULE_BRANCH,
                                                       "rule_branch": BRANCH_INPUT_CM_UNDEFINED,
                                                       "ports": tuple(free_inputs)})''', "    return None",
     ["sizing/test_writer_plan.py"], "t1e"),
    ("R2 판정 role 무시(차동쌍 아닌 두 입력도 묶음)", "sizing/writer_plan.py",
     "if len(free_inputs) == len(_DIFF_ROLES) and set(by_role) == set(_DIFF_ROLES):\n        return by_role[ROLE_DIFFERENTIAL_INPUT_P], by_role[ROLE_DIFFERENTIAL_INPUT_N]",
     "if len(free_inputs) == len(_DIFF_ROLES):\n        return free_inputs[0], free_inputs[1]", ["sizing/test_writer_plan.py"], "t1"),
    ("M3 g=s 칸 읽기 제거(cycle_vgs 로 샘)", "sizing/writer_plan.py", "if name in same_gs or (gate in fixed and source in fixed):", "if (gate in fixed and source in fixed):",
     ["sizing/test_writer_plan.py"], "t5b"),
    ("M4 g=s 칸 기록 제거", "graph/gvgs_cycles.py", "            same.append(name)", "            pass", ["graph/test_gvgs_cycles.py"], "gate_equals_source"),
    ("M5 짝 포트 전압 어긋남(KVL 위반)", "sizing/block_columns.py",
     "if w.relation == REL_INPUT_POINT and w.known is not None:      # 입력 점의 짝 포트 -- 뿌리와 같은 전압(KVL)\n            return values[w.known]",
     "if w.relation == REL_INPUT_POINT and w.known is not None:      # 입력 점의 짝 포트 -- 뿌리와 같은 전압(KVL)\n            return values[w.known] + 0.05", ["sizing/test_block_columns.py"], "t1h"),
    ("M6 n 포트 창 항목 생김", "sizing/block_columns.py", "if net not in c.inputs or w.relation in (REL_WINDOW, REL_INPUT_DC, REL_INPUT_POINT):", "if net not in c.inputs or w.relation in (REL_WINDOW, REL_INPUT_DC):",
     ["sizing/test_block_columns.py"], "t1h"),
    ("M7 DOF 입력 점 변수 공유 제거", "metrics/achievability.py", 'same_point = {n: w.known for n, w in p.column("node", "dc_writer") if w.relation == REL_INPUT_POINT and w.known is not None}', "same_point = {}",
     ["metrics/test_achievability.py"], "t1f"),
    ("M8 평행 판정 입력 점 미적용", "sizing/writer_plan.py", "pair = (kinds[name], canon(gate, point), canon(source, point))", "pair = (kinds[name], gate, source)",
     ["sizing/test_writer_plan.py"], "t1a"),
    ("M9 Kruskal 입력 점 미적용", "sizing/writer_plan.py", "ra = _find(parent, _FIXED if a in fixed else canon(a, point))", "ra = _find(parent, _FIXED if a in fixed else a)",
     ["sizing/test_writer_plan.py"], "t1"),
    ("M10 coupling_vars 둘째 계산 복귀", "graph/coupling_vars.py", 'model = dataclasses.replace(net_index(s1), **{f: s1.value("graph", S1V_KEY, f) for f in DERIVED_FIELDS})', "from .net_model import net_model as _nm; model = _nm(s1)",
     ["graph/test_coupling_vars.py"], "it1"),
    ("M11 θ y 키 입력 점 제외", "sizing/theta_schema.py", "if w.relation in (REL_WINDOW, REL_INPUT_POINT) and w.y_key is not None)", "if w.relation == REL_WINDOW and w.y_key is not None)",
     ["sizing/test_writer_plan.py", "search/test_orbit_ties.py"], "it1"),
    ("M12 SCC 뿌리 짝 포트 의존 제거", "sizing/scc_order.py", "members = {net, *mates.get(net, ())}", "members = {net}", ["sizing/test_scc_order.py", "sizing/test_kernel_context.py", "sizing/test_block_columns.py"], ""),
    ("M13 창 짝 포트 제약 제거", "sizing/block_columns.py", "for mate in self.mates.get(net, ()):\n            found.extend(self.order_terms.get(mate, ()))", "pass", ["sizing/test_block_columns.py", "sizing/test_input_window.py"], ""),
    ("M14 fd y 스텝 입력 점 제외", "search/fd_jacobian.py", "if writers[node].relation in (REL_WINDOW, REL_INPUT_POINT):", "if writers[node].relation == REL_WINDOW:", ["search/test_fd_jacobian.py"], ""),
    ("M15 F 닿는 입력 점 짝 포트 settle 제거", "sizing/writer_plan.py", "        if mate is not None and mate not in plan.writes:", "        if False:", ["sizing/test_writer_plan.py"], "t1c"),
]
RH = ("R16 rule_hash 재기록 되돌림(사실 stale)", "../assets/library/nmcnr_amplifier.structure.json", '"rule_hash": "5c0b84c53d2f350e2d27a2aba8acb2739379a16a6227e042c7761b183fb6906b"', '"rule_hash": "adc91fc87947b00d8d45e1f09337a8965f41fb33faa9f2cb02cdd7c11e45b754"',
      ["graph/test_s1v_build.py"], "rh")
MUT.append(RH)
MUT.append(("M17 coupling_vars 가 네 필드 값을 안 씀(READS 유지)", "graph/coupling_vars.py", 'model = dataclasses.replace(net_index(s1), **{f: s1.value("graph", S1V_KEY, f) for f in DERIVED_FIELDS})', "model = net_index(s1)", ["graph/test_coupling_vars.py", "integration/test_stage_a_library.py"], ""))
MUT.append(("M10b coupling_vars 둘째 계산 복귀(net_model 호출)", "graph/coupling_vars.py", 'model = dataclasses.replace(net_index(s1), **{f: s1.value("graph", S1V_KEY, f) for f in DERIVED_FIELDS})', "from .net_model import net_model; model = net_model(s1)", ["graph/test_coupling_vars.py"], "it1"))
only = sys.argv[3].split(",") if len(sys.argv) > 3 else None


def run(test):
    p = subprocess.run([sys.executable, "-m", "pytest", E + "tests/" + test, "-q", "-p", "no:cacheprovider", "--tb=line", "--deselect",
                        "gmid_engine/tests/sizing/test_writer_plan.py::test_it2b_os_k_no_same_dc_edge_between_input_ports"], cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
    fails = re.findall(r"^(?:FAILED|ERROR) \S*::(\S+)", p.stdout, re.M)
    return p.returncode, fails, p.stdout.strip().splitlines()[-1:]


for name, path, old, new, tests, kw in MUT:
    if only and name.split()[0] not in only:
        continue
    full = ROOT + "/" + E + path
    orig = open(full, "rb").read()
    if old.encode("utf-8") not in orig and bytes([13, 10]) in orig:
        old, new = old.replace(chr(10), chr(13) + chr(10)), new.replace(chr(10), chr(13) + chr(10))
    if old.encode("utf-8") not in orig:
        open(OUT, "ab").write((json.dumps({"mut": name, "error": "old 없음"}, ensure_ascii=False) + "\n").encode("utf-8"))
        continue
    open(full, "wb").write(orig.replace(old.encode("utf-8"), new.encode("utf-8")))
    try:
        res = []
        for t in tests:
            rc, fails, tail = run(t)
            res.append({"test": t, "rc": rc, "n_fail": len(fails), "fails": fails[:12], "tail": tail})
    finally:
        open(full, "wb").write(orig)
    open(OUT, "ab").write((json.dumps({"mut": name, "killed": any(r["rc"] != 0 for r in res), "kw_hit": any(kw in f for r in res for f in r["fails"]) if kw else None, "res": res}, ensure_ascii=False) + "\n").encode("utf-8"))
