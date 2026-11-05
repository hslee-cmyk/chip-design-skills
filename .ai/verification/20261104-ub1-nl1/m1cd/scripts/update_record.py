"""M-1c·M-1d 재판정: 판정 기록 갱신(BOM 없는 UTF-8), 증거 복사."""
import json
import pathlib
import shutil
import subprocess

R = pathlib.Path("C:/Users/HSLEE/AppData/Local/Temp/la1s_ub1_audit/run6")
W = pathlib.Path("C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-ub1-nl1-audit")
V = W / ".ai/verification/20261104-ub1-nl1/m1cd"
(V / "scripts").mkdir(parents=True, exist_ok=True)
for n in ("probe_m1d.jsonl", "probe_m1b.jsonl", "probe_a107.jsonl", "probe_phys.jsonl", "probe_row.jsonl", "probe_library.jsonl", "mut_m1d.json"):
    shutil.copy(R / "out" / n, V / n)
for n in ("probe_m1d.py", "probe_extra.py", "probe_m1b.py", "probe_library.py", "mut_m1d.py", "update_record.py", "runpt.sh"):
    shutil.copy(R / n, V / "scripts" / n)


def full(rev):
    return subprocess.run(["git", "-C", str(W), "rev-parse", rev], capture_output=True, text=True, check=True).stdout.strip()


fp = W / ".ai/verification/20261104-ub1-nl1.json"
r = json.loads(fp.read_text(encoding="utf-8"))
r["test_commit"], r["code_commit"] = full("f766580b"), full("44d3e8aa")
c = r["checks"]
c["V1"]["basis"] += " [M-1c·M-1d 재판정, 새 복제본 iso6, 머리 a115c714] card test + test_s2_values + test_canonical_order 325 통과 1 deselected / 소비자 9파일 99 통과 / tests/structure 171 통과 1 deselected / 연기 g10 2, stage_b 10, s0 11 통과. 안 돌린 것(전체 test, ngspice, 다른 11회로)은 통과로 세지 않는다."
c["V3"]["basis"] += " [M-1c·M-1d] 뮤턴트 6: 죽음 4(확장을 소자 capacitors 만, _structure C 조건 없이, block_local_gain C 재조립, charge_seeded 늘 거짓), 생존 2(charge_seeded 늘 참, 고정 행도 봄 -- 값은 같고 조립만 늘어 nodal_of·view_factor 호출 수를 세는 test 가 없다, minor). 대조 108 통과."
c["V6"]["basis"] += " [머리 a115c714] 171 통과 1 deselected, new 0, stale 같은 2."
c["V7"] = {"verdict": "PASS", "basis": c["V7"]["basis"] + " [M-1d 해소] 전하 넷 0: C 조립 0(nodal_of, view_factor 기준 일치·다른 고정 집합 씨앗 없음, block_local_gain, block_residual, library_case folded·two_stage_ota·ngcc 앞 판정 1·2·12 -> 0). 전하 넷 있음: block_local_gain 1회당 1, 같은 C 를 확장·독자·전하 행이 읽음. c_full 은 _structure 지역값을 호출자 지역 변수로 돌려줄 뿐 저장 자리·값 사본 아님(block_model 밖 소비 0, BlockGain 칸 0). 두 호출 줄(nodal_of, view_factor)의 같은 조건식은 graph 위반 아님: 공식 하나(capacitance_matrix·charge_seeded), 필드 쓰기 없음. 잔여 minor: 전하 넷이 있는 회로에서 C 는 필드가 아니라 호출마다 조립한다(nodal_of 1, view_factor 다른 고정 집합 1, block_local_gain 블록마다 1, 같은 ss). library 9/13 전하 넷 0 이라 발동 0, 앞 판정 view_factor minor 와 같은 항목, 줄이려면 NodalSystem 칸이 필요해 interface 밖."}
c["V9"] = {"verdict": "PASS", "basis": "M-1c 해소: a -6.46551724, b -7.5, c -6.46551724 = 손·전회로 일치(앞 -6.25). 앞 재현 전부 유지: case 2·case 6 117.1875, 두 단 사슬, 전하 섬 rel 0, 옛 막다른 경우 468.75, 무관한 Rd 제외, 용량 섬 -18.75, 행 모드 fail-closed. 고립 섬(기준 없음)은 singular_dc. charge_seeded 손 확인: 씨앗 없음 = 모든 비고정 행 g_row 참 -> nodal_factor 의 floating 조건 not g_row 거짓, charge 조건 not g_row 거짓, limit_matrix 행 교체 0 -> 행렬 = G 라 C 가 값·분류를 바꿀 길이 없다(G 행이 0 이 아닌 넷의 ω -> 0 극한은 G 행). 판정 조건도 nodal_factor 의 g.any(axis=1) 과 같은 술어. 무작위 800(부호 있는 MOS 용량, 다른 고정 집합, 씨앗 있음 405): 엔진 factor 와 진짜 C 를 넣은 factor 비트 동일 800/800, 씨앗 거짓인데 행 0 은 0. O-179: 0 행렬 대체는 nodal_factor 인자뿐이고 capacitance_matrix 소비자는 nodal_of·view_factor·_structure 셋, GBW·PM 경로(mna_build·stamp_mos·stamp_two_terminal)는 2f60222a 대비 diff 0 이라 닿지 않는다. pencil·mna·stamp 소비자 test 통과. library 구조 9/13 앞 판정과 행별 차이 0, 4회로 미측정."}
r["reproduced_numbers"] += [{"name": a, "value": b, "command": d} for a, b, d in (
    ("M-1cd card test 통과", 325, "m1cd/scripts/runpt.sh card1"), ("M-1cd 소비자 통과", 99, "consumers"), ("M-1cd structure 통과", 171, "structure"), ("M-1cd 연기 g10 통과", 2, "smoke_g10"), ("M-1cd 연기 stage_b 통과", 10, "smoke_stageb"), ("M-1cd 연기 s0 통과", 11, "smoke_s0"),
    ("M-1c a 블록 gain", -6.46551724137931, "m1cd/probe_m1b.jsonl"), ("M-1c b 블록 gain", -7.5, "m1cd/probe_m1b.jsonl"), ("M-1d ngcc C 조립(전하 넷 0)", 0, "m1cd/probe_m1b.jsonl"), ("charge_seeded 비트 동일", 800, "m1cd/probe_m1d.jsonl"), ("뮤턴트 생존", 2, "m1cd/mut_m1d.json"))]
r["auditor_run"]["commands"].append("격리: git clone --no-hardlinks --no-local <audit worktree> iso6, remote remove origin, 머리 a115c714 (M-1c·M-1d 재판정); git archive HEAD -> mut6")
r["auditor_run"]["time"] = subprocess.run(["date", "+%Y-%m-%dT%H:%M:%S+09:00"], capture_output=True, text=True).stdout.strip()
fp.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
import jsonschema
jsonschema.validate(r, json.loads((W / ".ai/verification/_schema.json").read_text(encoding="utf-8")))
print("schema ok", {k: v["verdict"] for k, v in c.items()})
