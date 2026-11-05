"""M-1b 재판정: 과잉 제외 뮤턴트 1개 측정 후 판정 기록 갱신(BOM 없는 UTF-8), 증거 복사."""
import json
import os
import pathlib
import shutil
import subprocess
import sys

BASE = pathlib.Path("C:/Users/HSLEE/AppData/Local/Temp/la1s_ub1_audit")
R = BASE / "run5"
W = pathlib.Path("C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-ub1-nl1-audit")
V = W / ".ai/verification/20261104-ub1-nl1/m1b"
(V / "scripts").mkdir(parents=True, exist_ok=True)

root = BASE / "mut4/skills/analog-gmid-design"
S5 = BASE / "iso5/skills/analog-gmid-design"
for rel in ("gmid_engine/metrics/block_model.py", "gmid_engine/tests/metrics/test_block_model.py"):
    shutil.copy(S5 / rel, root / rel)
path = root / "gmid_engine/metrics/block_model.py"
text = path.read_bytes().decode("utf-8")
old = "for o in charge for t in numpy.flatnonzero(c_pairs[o])"
assert old in text
path.write_bytes(text.replace(old, "for o in range(len(ss.nodes)) for t in numpy.flatnonzero(c_pairs[o])", 1).encode("utf-8"))
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONUTF8="1", APPDATA="C:/Users/HSLEE/AppData/Roaming", USERPROFILE="C:/Users/HSLEE", PYTHONPYCACHEPREFIX=str(BASE / "pyc_mut"))
p = subprocess.run([sys.executable, "-m", "pytest", "gmid_engine/tests/metrics/test_block_model.py", "-q", "--tb=line", "-p", "no:cacheprovider", "-W", "ignore"], cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
mres = {"name": "read 를 모든 C 넷으로 넓힘(과잉 제외)", "rc": p.returncode, "last": ((p.stdout.strip().splitlines() or [p.stderr[-160:]])[-1])[:160], "failed": [l[:120] for l in p.stdout.splitlines() if l.startswith("FAILED")]}
print(mres)
(R / "out/mut_over.json").write_text(json.dumps(mres, ensure_ascii=False, indent=0), encoding="utf-8")

for n in ("probe_m1b.jsonl", "probe_a107.jsonl", "probe_row.jsonl", "probe_phys.jsonl", "probe_library.jsonl", "mut_over.json"):
    shutil.copy(R / "out" / n, V / n)
for n in ("probe_m1b.py", "update_record.py", "runpt.sh"):
    shutil.copy(R / n, V / "scripts" / n)


def full(rev):
    return subprocess.run(["git", "-C", str(W), "rev-parse", rev], capture_output=True, text=True, check=True).stdout.strip()


fp = W / ".ai/verification/20261104-ub1-nl1.json"
r = json.loads(fp.read_text(encoding="utf-8"))
r["test_commit"], r["code_commit"] = full("292c7172"), full("1090e177")
c = r["checks"]
c["V1"]["basis"] += " [M-1b 재판정, 새 복제본 iso5, 머리 abd06526] card test + test_s2_values + test_canonical_order 323 통과 1 deselected / tests/structure 171 통과 1 deselected / 연기 g10 2, stage_b 10, s0 11 통과. 머리에서 다시 돈 것은 이것뿐이다."
c["V3"]["basis"] += " [M-1b] 과잉 제외 뮤턴트(read 를 모든 C 넷으로): rc %d, %s." % (mres["rc"], mres["last"])
c["V6"]["basis"] += " [M-1b, 머리 abd06526] 171 통과 1 deselected, new 0, stale 같은 2."
c["V7"] = {"verdict": "FAIL", "basis": c["V7"]["basis"] + " [M-1b] M-1d 같은 입력 재계산·A-4 위반: _structure 가 capacitance_matrix 를 조건 없이 조립한다(c_pairs). 전하 넷 0 회로에서 호출 수 folded block_residual 1, two_stage_ota 2, ngcc_3stage_ff 12(library_case 합성 값, 전하 넷 0), 전하 넷 있는 block_local_gain 1회에 _structure 1 + block_local_gain 1 = 같은 입력 2번(m1b/probe_m1b.jsonl). 앞 판정 측정은 @block_local_gain 0 이었다. 새 필드·cache 0, graph 밖 저장 0. read 는 capacitance_matrix 를 읽어 둘째 공식은 없지만 확장 루프는 소자 capacitors 만 읽어 '용량으로 이어짐' 의 정의가 함수 안에 둘이다(V9 M-1c)."}
c["V9"] = {"verdict": "FAIL", "basis": "M-1b case 6 해소: 블록 gain 117.1875 = 손·전회로. 앞 재현 유지: case 2·두 단 사슬·옛 막다른 경우 468.75·무관한 Rd 제외·용량 섬 -18.75·전하 섬 손 일치, 행 모드 fail-closed(charge_node_row_mode, n 이 노드 안이면 unknown/axis_range_empty), gate 비유한 입력 ok 0. 구조 측정 9/13 앞 판정과 행별 차이 0. M-1c 물리 정합 위반: 전하 넷 확장 루프가 소자 capacitors 만 봐서 MOS 단자 용량으로 이어진 전하 넷을 놓친다. 회로 in -C1 2p- n1 -C2 3p- gnd, M1(d out, g n1), RL, M3(d vdd, s gnd, g n1, b n2, cgb 1p, 스탬프 안 됨). n2 -C3 4p- gnd 일 때 손·전회로 gain -6.46551724, 블록 -6.25(3.3 %), C3 없을 때 손·전회로 -7.5, 블록 -6.25(16.7 %), g·b 를 바꿔도 -6.25 대 -6.46551724. undefined 없음. n2 를 0 V 로 고정한 결과이고 옛 0 V 처리와 같은 부류다(m1b/probe_m1b.jsonl case a·b·c). library 전하 넷 0/9 라 발동 없음."}
r["reproduced_numbers"] += [{"name": a, "value": b, "command": d} for a, b, d in (
    ("M-1b card test 통과", 323, "m1b/scripts/runpt.sh card1"), ("M-1b structure 통과", 171, "structure"), ("M-1b 연기 g10 통과", 2, "smoke_g10"), ("M-1b 연기 stage_b 통과", 10, "smoke_stageb"), ("M-1b 연기 s0 통과", 11, "smoke_s0"),
    ("case 6 블록 gain", 117.1875, "m1b/probe_a107.jsonl"), ("M-1c 블록 gain(C3 있음)", -6.25, "m1b/probe_m1b.jsonl a"), ("M-1c 손 gain(C3 있음)", -6.46551724137931, "m1b/probe_m1b.jsonl a"),
    ("M-1c 손 gain(C3 없음)", -7.5, "m1b/probe_m1b.jsonl b"), ("M-1d ngcc block_residual 1회 C 조립(전하 넷 0)", 12, "m1b/probe_m1b.jsonl"))]
r["auditor_run"]["commands"].append("격리: git clone --no-hardlinks --no-local <audit worktree> iso5, remote remove origin, 머리 abd06526 (M-1b 재판정); mut4 에 block_model·test_block_model 덮어 뮤턴트")
r["auditor_run"]["time"] = subprocess.run(["date", "+%Y-%m-%dT%H:%M:%S+09:00"], capture_output=True, text=True).stdout.strip()
fp.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
import jsonschema
jsonschema.validate(r, json.loads((W / ".ai/verification/_schema.json").read_text(encoding="utf-8")))
print("schema ok")
