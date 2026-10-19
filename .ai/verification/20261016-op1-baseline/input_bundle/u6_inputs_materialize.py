# -*- coding: utf-8 -*-
"""OP-1a (5): N4-1 기준선 입력 묶음 가운데 u6 자체 점검 회로(smoke/u6_selfchecks.py) 입력을 JSON으로 고정한다.

검증자(gmid-verification-auditor) 작성. u6 점검은 입력을 메모리에서 만들고 파일로 남기지 않았다(base `5fea301`
`O/smoke/u6_selfchecks.py:37-60, :63-68, :82-87, :91-93, :130-133`). B-20(OP-3)이 그 파일을 지운 뒤 OP-5의 N4 비교가 쓸 수 있게
base 판 생성 함수를 **그대로 불러** 입력 dict를 만들고 JSON으로 쓴다(시뮬레이터 실행 없음 -- `write_netlists`만 부른다).
확인: 같은 생성 경로로 쓴 넷리스트(.cir)와 LUT npz가 기준선 원자료 `u6/`의 같은 이름 파일과 바이트 동일한지 sha256으로 잰다.

사용: python -I u6_inputs_materialize.py <base 판 spice_oracle 폴더> <작업 폴더> <기준선 files 루트> <결과 json>
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ORACLE, WORK, BASE_FILES, OUT = sys.argv[1:5]
sys.path.insert(0, os.path.join(ORACLE, "smoke"))
sys.path.insert(0, ORACLE)
sys.path.insert(0, os.path.join(ORACLE, "tests"))
import conftest  # noqa: E402
import oracle_netlist as on  # noqa: E402
import u6_selfchecks as u6  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


work = Path(WORK)
work.mkdir(parents=True, exist_ok=True)
cases = {}
# noise_rc (u6_selfchecks.py:63-68)
lut = conftest.make_lut(work / "lut_rc.npz")
inp = conftest.rc_input(lut)
inp["noise"] = {"f_lo_hz": 1.0, "points_per_decade": 5}
inp["testbench"]["ac"]["fstop_hz"] = 1e8
cases["noise_rc"] = (inp, "rc.free.cir", "lut_rc.npz")
# 5T OTA (u6_selfchecks.py:82-87) -- pz_5t는 블록 없음, swing_5t는 swing_icmr, mc_5t는 offset_mc(r = --mc-r 기본 0.05, seed 7)
for key, extra in (("pz_5t", {}), ("swing_5t", {"swing_icmr": {"swing": True, "icmr": True}}),
                   ("mc_5t", {"offset_mc": {"rel_resolution": 0.05, "seed": 7}})):
    lut = conftest.make_lut(work / "lut_5t.npz")
    inp = u6.ota5t_input(lut)
    inp.update(extra)
    cases[key] = (inp, "t5t.free.cir", "lut_5t.npz")
res = {"oracle_dir": ORACLE.replace("\\", "/"), "cases": {}}
for key, (inp, cir_name, lut_name) in cases.items():
    d = work / key
    d.mkdir(exist_ok=True)
    cir = d / cir_name
    meta = on.write_netlists(inp, "free", str(cir))
    jp = d / f"{key}.input.json"
    jp.write_text(json.dumps(inp, ensure_ascii=False, indent=1), encoding="utf-8")
    b_cir = Path(BASE_FILES) / "u6" / cir_name
    b_meta = Path(BASE_FILES) / "u6" / (cir_name + ".meta.json")
    b_lut = Path(BASE_FILES) / "u6" / lut_name
    res["cases"][key] = {
        "input_json": jp.name, "input_sha256": sha(jp),
        "lut_npz_in_input": str(inp["process"]["lut_npz"]).replace("\\", "/"),
        "lut_npz_sha256": sha(work / lut_name), "baseline_lut_sha256": sha(b_lut), "lut_bit_identical": sha(work / lut_name) == sha(b_lut),
        "cir_sha256": sha(cir), "baseline_cir_sha256": sha(b_cir), "cir_bit_identical": sha(cir) == sha(b_cir),
        "meta_sha256": sha(str(cir) + ".meta.json"), "baseline_meta_sha256": sha(b_meta),
        "meta_bit_identical": sha(str(cir) + ".meta.json") == sha(b_meta),
        "blockers": meta.get("blockers"),
    }
Path(OUT).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: {x: v[x] for x in ("lut_bit_identical", "cir_bit_identical", "meta_bit_identical")} for k, v in res["cases"].items()}))
