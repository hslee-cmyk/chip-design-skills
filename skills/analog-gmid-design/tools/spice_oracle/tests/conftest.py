"""spice_oracle test 공용 도구.

근거: README.md 동작 계약 C1~C12 + oracle_input.schema.json 만. 오라클 소스(oracle_*.py)는 열지 않고
CLI 진입점만 subprocess 로 부른다. 기대값은 (a) 손계산, (b) 이 파일의 `independent_*` 가 손으로 쓴
독립 ngspice 넷리스트를 직접 돌린 결과에서만 만든다(피검 코드 출력으로 기대값을 만들지 않는다).

기본 실행에서 옛 엔진을 새로 돌리는 test(~260 s)는 `legacy_slow` 마커로 빠진다. `--run-legacy` 로 켠다.
독립 기준 실행이 수십 분 걸리는 test 는 `slow` 마커가 붙는다(기본 실행에 포함, 빠른 실행은 `-m "not slow"` 로 뺀다;
전체 검증은 그대로 돌린다).
환경: GMID_NGSPICE(ngspice 실행 파일), GMID_PDK_ROOT(PDK 상위 폴더, 그 아래 sky130_fd_pr).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

ORACLE_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = ORACLE_DIR.parents[1]
if str(ORACLE_DIR) not in sys.path:             # 새 구조 test 가 `core.*`, `adapters.ngspice.*`, `oracle_run` 을 import 한다
    sys.path.insert(0, str(ORACLE_DIR))
PY = sys.executable
NGSPICE = Path(os.environ.get("GMID_NGSPICE", r"C:\ngspice\Spice64\bin\ngspice_con.exe"))      # ngspice 실행 파일 변수 하나(GMID_NGSPICE)
PDK = Path(os.environ.get("GMID_PDK_ROOT") or "C:/pdk") / "sky130_fd_pr"      # PDK 상위 폴더 변수 하나(GMID_PDK_ROOT)에서 도출

NFET = "sky130_fd_pr__nfet_01v8"
PFET = "sky130_fd_pr__pfet_01v8"


# ---------------------------------------------------------------- pytest 설정
def pytest_addoption(parser):
    parser.addoption("--run-legacy", action="store_true", default=False,
                     help="옛 엔진을 새로 돌리는 legacy_adapter test(~260 s) 실행")


def pytest_configure(config):
    config.addinivalue_line("markers", "legacy_slow: 옛 엔진 새 실행이 필요한 느린 test(--run-legacy 로 켬)")
    config.addinivalue_line("markers", "slow: 독립 기준 실행이 기본 시간 한도(600 s)를 넘는 test(빠른 실행은 -m \"not slow\" 로 뺌)")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-legacy"):
        return
    skip = pytest.mark.skip(reason="옛 엔진 새 실행(~260 s): --run-legacy 로 켬")
    for it in items:
        if "legacy_slow" in it.keywords:
            it.add_marker(skip)


def require_spice():
    # fail-closed (card 20261104-op23): 시뮬레이터·PDK 가 없으면 skip 으로 넘어가지 않고 실패한다.
    assert NGSPICE.exists() and PDK.exists(), f"ngspice({NGSPICE}) 또는 PDK({PDK}) 없음"


# ---------------------------------------------------------------- 수집에서 뺀 옛 test (card 20261104-op23, 위임 A-80 D-6)
# 계획 D §18.2 이전표의 '이 card 몫을 toy·독립 기준 이동·순수 수학 import 교체로 줄인다'(O-229 기간). 아래 파일은 지워지는 CLI 나 옛 입력 형식
# (`spice_oracle_input/1`)·옛 넷리스트 텍스트·옛 모듈을 쓰므로 새 구조에서 돌 수 없다. **통과로 세지 않는다.** 이전·재작성·폐기는
# LA-1 재점검에서 파일별로 정한다(원래 취지와 다름 X-R13, 기준 약화 소지 표지). 사유와 소유 card:
#   OP4 = 안정성·과도(stability_check, pz, C10), OP5 = noise·offset MC·swing·ICMR·전도 판정, OP3 = 이 card 소유이나 D-6 으로 이전 보류,
#   LT1 = gain-budget card LT-1 순서 3 이 삭제.
IGNORED_OLD_TESTS = {
    "test_oracle_c10_stability.py": ("OP4", "C10 안정성: oracle_simulate.early_unstable 등 옛 모듈 import, run_netlist/run_simulate/run_compare 사용"),
    "test_oracle_u6_stability.py": ("OP4", "U6 C10 최종 안정성·pz: oracle_simulate import, 옛 입력 형식"),
    "test_oracle_transient.py": ("OP4", "C25 슬루·정착 기록 칸: 옛 입력 형식 생성기 + 옛 결과 칸 (슬루 = OP-10 포함)"),
    "test_oracle_noise.py": ("OP5", "noise: oracle_noise import, 옛 입력 형식 (기간 동안 noise 입력은 adapter_capability_missing 로 거부)"),
    "test_oracle_offset_mc.py": ("OP5", "offset MC: oracle_offset_mc import, sky130 변수 집합 기대값 삭제 대상(D §18.2) (기간 동안 mc_method_unsupported)"),
    "test_oracle_swing_icmr.py": ("OP5", "swing·ICMR: 정의를 바꾼 칸(D §18.2), 옛 입력 형식 (기간 동안 adapter_capability_missing)"),
    "test_oracle_conduction.py": ("OP5", "C23 전도 문턱(off_current_A) 단언: OP-5 가 §21.3 식 test 로 바꿈, run_netlist/run_simulate/run_compare 사용"),
    "test_oracle_compare.py": ("OP3->LA1", "코어 compare 이동 test: Case 가 run_netlist/run_simulate/run_compare(지워진 CLI) 사용"),
    "test_oracle_compare_device_tol.py": ("OP3->LA1", "test_oracle_compare.Case 의존"),
    "test_oracle_diagnosis.py": ("OP3->LA1", "run_oracle 경유이나 옛 입력 형식 생성기(cs_input 등)에 의존: 새 형식 생성기는 실제 기술자·LUT 모델 기록이 필요"),
    "test_oracle_input_schema.py": ("OP3", "새 형식 + 옛 형식 거부 test 로 다시 씀 -> tests/test_input_contract.py"),
    "test_oracle_iso.py": ("OP3->LA1", "iso 넷리스트 텍스트 단언: IR 단언은 core/test_build_*.py, 방언 줄은 어댑터 test 로 다시 쓸 대상"),
    "test_oracle_netlist.py": ("OP3->LA1", "넷리스트 텍스트 단언(run_netlist): IR 단언 core/test_build_ir.py, 방언 줄 adapters/ngspice/test_dialect.py 로 이전"),
    "test_oracle_netlist_topology.py": ("OP3->LA1", "C15 topology 대조: IR 기준으로 다시 씀 (core/identity)"),
    "test_oracle_z1.py": ("OP3->LA1", "Z1 omit/short 넷리스트 텍스트 단언: IR 단언은 core/test_build_ir.py"),
    "test_oracle_c27_loop_defs.py": ("OP3->LA1", "C27 루프 정의 넷리스트 텍스트 단언(run_netlist)"),
    "test_oracle_junction_cap.py": ("OP3->LA1", "접합 용량 넷리스트·run_netlist/run_simulate 사용"),
    "test_oracle_cm_loop.py": ("OP3->LA1", "CM 루프 넷리스트 텍스트(run_netlist) + 엔진 대 ngspice 대조"),
    "test_oracle_loop_singular.py": ("OP3->LA1", "루프 특이 판정: 옛 입력 형식 + run_netlist"),
    "test_oracle_ratio_db.py": ("OP3->LA1", "ratio/rout 넷리스트·실행: 옛 입력 형식 + run_netlist"),
    "test_oracle_rout.py": ("OP3->LA1", "C26 rout: 옛 입력 형식 + run_netlist"),
    "test_oracle_run.py": ("OP3->LA1", "진입점 test: 옛 입력 형식 + run_netlist"),
    "test_oracle_simulate.py": ("OP3->LA1", "oracle_simulate CLI(지워짐) 직접 실행"),
    "test_oracle_simulate_cache.py": ("OP3->LA1", "캐시: 새 캐시 키(D §9)로 core/test_cache_key.py 에 toy 로 다시 씀, 옛 입력 형식"),
    "test_oracle_simulate_pm_crosscheck.py": ("OP3->LA1", "pm_crosscheck: run_netlist/run_simulate 사용, 수학은 core.measures_ac 로 이동"),
    "test_legacy_testbench.py": ("LT1", "legacy_testbench.json 의 options 칸은 새 스키마 testbench 에 없음(옛 형식). LT-1 순서 3 이 파일째 삭제"),
}
collect_ignore = sorted(IGNORED_OLD_TESTS)


# ---------------------------------------------------------------- 입력 만들기
def make_lut(path: Path, corner="tt", temp_c=27.0) -> Path:
    """오라클이 메타만 읽는 LUT npz. corner/temp_c 를 None 으로 주면 그 키를 뺀다(C2 막힘용)."""
    kw = {"L": np.array([1e-6])}
    if corner is not None:
        kw["corner"] = np.array(corner)
    if temp_c is not None:
        kw["temp_c"] = np.array(float(temp_c))
    np.savez(path, **kw)
    return path


def process_block(lut: Path, diffusion=True) -> dict:
    p = PDK.as_posix()
    blk = {
        "lut_npz": str(lut),
        "models": {
            "nmos": {"subckt": NFET,
                     "includes": [f"{p}/cells/nfet_01v8/{NFET}__{{corner}}.pm3.spice",
                                  f"{p}/cells/nfet_01v8/{NFET}__mismatch.corner.spice"],
                     "op_probe": "@m.{inst}.m" + NFET + "[{param}]"},
            "pmos": {"subckt": PFET,
                     "includes": [f"{p}/models/parameters/lod.spice",
                                  f"{p}/cells/pfet_01v8/{PFET}__{{corner}}.pm3.spice",
                                  f"{p}/cells/pfet_01v8/{PFET}__mismatch.corner.spice"],
                     "op_probe": "@m.{inst}.m" + PFET + "[{param}]"},
        },
    }
    if diffusion:
        blk["diffusion"] = {"ad_per_w_m": 5e-7, "pd_extra_m": 2e-6}
    return blk


# C22(free 는 확산 기하 필수): 독립 넷리스트(ad/pd 없음 = subckt 기본 0)와 같은 회로를 free 로 돌릴 때 쓰는 명시적 면적 0.
ZERO_DIFFUSION = {"ad_m2": 0.0, "as_m2": 0.0, "pd_m": 0.0, "ps_m": 0.0,
                  "basis": "test: 면적 0 명시(독립 넷리스트에 ad/pd 없음과 같은 회로)"}
# C23(엔진 예측 전도 소자의 문턱 필수): 문턱 0 = 옛 'ID > 0 이면 전도' 규칙을 명시한 값.
OFF_ZERO = {"M1": {"off_current_A": 0.0}, "MP1": {"off_current_A": 0.0}}


def zero_diffusion(inp: dict) -> dict:
    for d in inp["devices"]:
        d["diffusion"] = dict(ZERO_DIFFUSION)
    return inp


def testbench_block() -> dict:
    return {"dc_choke_H": 1e12, "ac_couple_F": 1.0,
            "options": {"gmin": "1e-15", "reltol": "1e-4", "abstol": "1e-14", "vntol": "1e-7"},
            "ac": {"fstart_hz": 0.01, "fstop_hz": 1e10, "points_per_decade": 40, "input_ac": 1.0,
                   "input_p_ac": 0.5, "input_n_ac": -0.5, "diff_feedback_gain": 0.5}}


# 소형 회로 1: NMOS 공통소스 + 저항 부하 + 부하 C, 별도 가지로 PMOS(소스 1.5 V 레일, 바디 vdd) + 저항.
#   pb 는 PMOS 게이트에만 물린 게이트 전용 넷(C6).
CS = dict(vdd=1.8, vsp=1.5, vin=0.7, rload=1e5, cl=1e-12, L=0.5e-6, finger_w=2e-6, n=2,
          pb=0.3, rp=1e4, pL=0.5e-6, pfinger_w=2e-6, pn=3)


def cs_input(lut: Path, *, preds_nodes=None, preds_devices=None, metrics=None, constraints=None,
             judge=None, W=None, bias_voltages="default", diffusion=True, circuit="tcs_nmos_rload",
             n=None) -> dict:
    c = CS
    nfing = c["n"] if n is None else n
    dev_n = {"name": "M1", "kind": "nmos", "drain": "nout", "gate": "nin", "source": "gnd", "bulk": "gnd",
             "L": c["L"], "finger_w": c["finger_w"], "n_fingers": nfing,
             "W": c["finger_w"] * nfing if W is None else W}
    dev_p = {"name": "MP1", "kind": "pmos", "drain": "pout", "gate": "pb", "source": "vsp", "bulk": "vdd",
             "L": c["pL"], "finger_w": c["pfinger_w"], "n_fingers": c["pn"], "W": c["pfinger_w"] * c["pn"]}
    inp = {
        "schema": "spice_oracle_input/1",
        "circuit": circuit,
        "process": process_block(lut, diffusion=diffusion is True),
        "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "vsp", "voltage": c["vsp"]},
                  {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [dev_n, dev_p],
        "sources": [],
        "passives": [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "nout"], "value": c["rload"],
                      "value_basis": "test"},
                     {"name": "CL", "kind": "capacitor", "terminals": ["nout", "gnd"], "value": c["cl"]},
                     {"name": "RP", "kind": "resistor", "terminals": ["pout", "gnd"], "value": c["rp"]}],
        "ports": {"input": "nin", "output": "nout"},
        "predictions": {"nodes": {"nin": c["vin"], **(preds_nodes or {})},
                        "devices": preds_devices or {},
                        "metrics": metrics or []},
        "testbench": testbench_block(),
    }
    if diffusion == "zero":
        zero_diffusion(inp)
    if bias_voltages == "default":
        inp["bias_voltages"] = [{"net": "pb", "value": c["pb"]}]
    elif bias_voltages is not None:
        inp["bias_voltages"] = bias_voltages
    if constraints is not None:
        inp["acceptance"] = {"constraints": constraints}
    if judge is not None:
        inp["judge"] = judge
    return inp


# 소형 회로 2: RC 저역통과 + 저항 분압 출력. rin -Ra- rout, rout -Rb- gnd, rout -C- gnd.
#   손계산: H0 = Rb/(Ra+Rb) = 0.5 (-6.0206 dB), fc = 1/(2 pi (Ra||Rb) C) = 159154.94 Hz.
#   DC: V(rout) = 0.5 V(rin). 레일 vdd 에 R1/R2 분압(3k/1k) -> V(dmid)=0.45.
#   소자 없는 회로는 이 계약의 대상이 아니므로 NMOS 다이오드 가지(vdd -Rd- ndio, MD) 하나를 둔다.
RC = dict(vdd=1.8, ra=2000.0, rb=2000.0, c=1e-9, r1=3000.0, r2=1000.0, vin=0.6, rd=1e5)


def rc_input(lut: Path, circuit="trc_lowpass_div") -> dict:
    c = RC
    return {
        "schema": "spice_oracle_input/1",
        "circuit": circuit,
        "process": process_block(lut),
        "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [{"name": "MD", "kind": "nmos", "drain": "ndio", "gate": "ndio", "source": "gnd", "bulk": "gnd",
                     "L": 1e-6, "finger_w": 1e-6, "n_fingers": 1, "W": 1e-6}],
        "passives": [{"name": "Ra", "kind": "resistor", "terminals": ["rin", "rout"], "value": c["ra"]},
                     {"name": "Rb", "kind": "resistor", "terminals": ["rout", "gnd"], "value": c["rb"]},
                     {"name": "C1", "kind": "capacitor", "terminals": ["rout", "gnd"], "value": c["c"]},
                     {"name": "R1", "kind": "resistor", "terminals": ["vdd", "dmid"], "value": c["r1"]},
                     {"name": "R2", "kind": "resistor", "terminals": ["dmid", "gnd"], "value": c["r2"]},
                     {"name": "Rd", "kind": "resistor", "terminals": ["vdd", "ndio"], "value": c["rd"]}],
        "ports": {"input": "rin", "output": "rout"},
        "predictions": {"nodes": {"rin": c["vin"]}, "devices": {}, "metrics": []},
        "testbench": testbench_block(),
    }


# 소형 회로 3: 단일단 NMOS CS + 저항 되먹임. nout -Rf- nin(게이트), nin -Cin- gnd, nout -RL- vdd, nout -CL- gnd.
#   β 망 = {Rf, Cin}(둘 다 입력 넷 nin 에 물림). 손계산 루프 이득(gm 제어원 기준 return ratio, MOS 용량 무시):
#     Zp = 1/(s Cin + 1/(s Lloop)),  Zo = 1/(1/RL + gds + s CL + 1/(Rf + Zp)),  T = gm Zo Zp/(Rf + Zp).
#   개루프 A(입력 AC 접지 via 결합 C): A = (-gm + 1/Rf) / (1/RL + gds + s CL + 1/Rf).
FB = dict(vdd=1.8, vin=0.7, rload=1e5, cl=10e-12, rf=1e6, cin=10e-12, L=0.5e-6, finger_w=2e-6, n=2,
          loop_choke=1e20)


def fb_input(lut: Path, *, feedback=("Rf", "Cin"), circuit="tfb_cs_rfeedback", loop_choke="default",
             cin=None, cl=None) -> dict:
    c = dict(FB, **{k: v for k, v in (("cin", cin), ("cl", cl)) if v is not None})
    inp = {
        "schema": "spice_oracle_input/1",
        "circuit": circuit,
        "process": process_block(lut, diffusion=False),
        "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [{"name": "M1", "kind": "nmos", "drain": "nout", "gate": "nin", "source": "gnd", "bulk": "gnd",
                     "L": c["L"], "finger_w": c["finger_w"], "n_fingers": c["n"], "W": c["finger_w"] * c["n"]}],
        "passives": [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "nout"], "value": c["rload"]},
                     {"name": "CL", "kind": "capacitor", "terminals": ["nout", "gnd"], "value": c["cl"]},
                     {"name": "Rf", "kind": "resistor", "terminals": ["nout", "nin"], "value": c["rf"]},
                     {"name": "Cin", "kind": "capacitor", "terminals": ["nin", "gnd"], "value": c["cin"]}],
        "ports": {"input": "nin", "output": "nout"},
        "predictions": {"nodes": {"nin": c["vin"]}, "devices": {}, "metrics": []},
        "testbench": testbench_block(),
    }
    zero_diffusion(inp)  # C22: 손계산·독립 넷리스트에 접합 용량이 없으므로 면적 0 을 명시
    if feedback is not None:
        inp["feedback_passives"] = list(feedback)
    if loop_choke == "default":
        inp["testbench"]["loop_dc_choke_H"] = c["loop_choke"]
    elif loop_choke is not None:
        inp["testbench"]["loop_dc_choke_H"] = loop_choke
    return inp


# (`_independent_fb_cached`·`independent_fb` 는 `tests/adapters/ngspice/independent_ref.py` 로 옮겼다 -- card 20261104-op23, D §18.2)


def fb_loop_gain(f, gm, gds, cin=None, cl=None):
    c = dict(FB, **{k: v for k, v in (("cin", cin), ("cl", cl)) if v is not None})
    s = 2j * np.pi * np.asarray(f)
    zp = 1 / (s * c["cin"] + 1 / (s * c["loop_choke"]))
    zo = 1 / (1 / c["rload"] + gds + s * c["cl"] + 1 / (c["rf"] + zp))
    return gm * zo * zp / (c["rf"] + zp)


def fb_open_loop(f, gm, gds):
    c = FB
    s = 2j * np.pi * np.asarray(f)
    return (-gm + 1 / c["rf"]) / (1 / c["rload"] + gds + s * c["cl"] + 1 / c["rf"])


def write_json(path: Path, obj) -> Path:
    path.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    return path


# ---------------------------------------------------------------- 피검 CLI 부르기
def _run(args, cwd):
    return subprocess.run([PY, "-P", *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(cwd))


# (`run_netlist`·`run_simulate`·`run_compare` 는 지워지는 CLI(oracle_netlist·oracle_simulate·oracle_compare)를 부르므로 지웠다 -- D-6, A-80.
#  그것을 쓰던 옛 test 는 아래 `collect_ignore` 에 사유와 함께 있다.)
def run_oracle(inp: dict, out: Path, biases=("free",), judge=None, sat_margin=None, tag=None, name="t", extra=()):
    """oracle_run.py(새 CLI: `--simulator`·`--sim-exe`, D §11.7) -> (proc, {bias: compare.json dict 또는 None})."""
    out.mkdir(parents=True, exist_ok=True)
    ip = write_json(out / f"{name}.input.json", inp)
    args = [ORACLE_DIR / "oracle_run.py", ip, out, "--bias", *biases, "--simulator", "ngspice", "--sim-exe", NGSPICE]
    if judge is not None:
        args += ["--judge", write_json(out / f"{name}.judge.json", judge)]
    if sat_margin is not None:
        args += ["--sat-margin-v", repr(sat_margin)]
    if tag is not None:
        args += ["--tag", tag]
    p = _run([*args, *extra], out)
    res = {}
    for b in biases:
        cj = out / f"{stem_of(inp, b, tag)}.compare.json"
        res[b] = json.loads(cj.read_text(encoding="utf-8")) if cj.exists() else None
    return p, res


def stem_of(inp: dict, bias: str, tag=None) -> str:
    return inp["circuit"] + (f".{tag}" if tag else "") + f".{bias}"


def x_lines(text: str):
    return [ln for ln in text.splitlines() if ln[:1] in "Xx"]


def elem(text: str, name: str):
    """이름이 정확히 name(대소문자 무시)인 소자 줄의 토큰들. 없으면 None."""
    for ln in text.splitlines():
        t = ln.split()
        if t and t[0].lower() == name.lower():
            return t
    return None


def kv(tokens) -> dict:
    """['a=b', 'c=d', ...] -> {a: b}(소문자 키)."""
    return {t.split("=", 1)[0].lower(): t.split("=", 1)[1] for t in tokens if "=" in t}


def dc_value(tokens) -> float:
    """'V... n+ n- DC <v> ...' 의 DC 값."""
    up = [t.upper() for t in tokens]
    return float(tokens[up.index("DC") + 1])


def by_name(rows, key, val):
    hit = [r for r in rows if r.get(key) == val]
    assert hit, f"{key}={val} 없음: {[r.get(key) for r in rows]}"
    return hit[0]


# ---------------------------------------------------------------- 독립 ngspice(손으로 쓴 넷리스트)
# (`_includes`·`run_spice`·`probe`·`PARAMS`·`independent_cs` 는 `tests/adapters/ngspice/independent_ref.py` 로 옮겼다
#  -- card 20261104-op23, D §18.2 '손 넷리스트 독립 기준 이동')
@pytest.fixture(scope="session")
def ref_root(tmp_path_factory):
    require_spice()
    return tmp_path_factory.mktemp("independent")


# ---------------------------------------------------------------- 측정 정의(README "측정 정의"의 독립 구현)
def measure(f, H):
    """gain=|H(fstart)|, UGF=|H|=1 첫 하강 교차(log f 대 dB 선형 보간), PM=180-(DC위상-UGF위상),
    f-3dB=|H|<|H0|/sqrt2 인 첫 주파수 점. |H0|<1 이거나 1 아래로 안 내려가면 UGF/PM=None."""
    mag = np.abs(H)
    ph = np.degrees(np.unwrap(np.angle(H)))
    out = {"dc_gain_db": 20 * math.log10(mag[0]), "ugf_hz": None, "pm_deg": None, "f3db_hz": None}
    below = np.nonzero(mag < mag[0] / math.sqrt(2))[0]
    if below.size:
        out["f3db_hz"] = float(f[below[0]])
    if mag[0] < 1:
        return out
    for i in range(len(f) - 1):
        if mag[i] >= 1 and mag[i + 1] < 1:
            d0, d1 = 20 * math.log10(mag[i]), 20 * math.log10(mag[i + 1])
            t = d0 / (d0 - d1)
            lf = math.log10(f[i]) + t * (math.log10(f[i + 1]) - math.log10(f[i]))
            out["ugf_hz"] = 10 ** lf
            pu = ph[i] + t * (ph[i + 1] - ph[i])
            out["pm_deg"] = 180.0 - (ph[0] - pu)
            break
    return out


def ac_grid(f0, f1, ppd):
    k = np.arange(0, int(round(math.log10(f1 / f0) * ppd)) + 1)
    return f0 * 10.0 ** (k / ppd)


def preds_from_independent(ind) -> dict:
    """독립 ngspice 값을 '엔진 예측'으로 쓴 predictions(크기 규칙: VSB = -vbs, PMOS 도 @ 값 그대로)."""
    devs = {}
    for name in ("M1", "MP1"):
        d = ind[name]
        devs[name] = {"ID": d["id"], "VGS": d["vgs"], "VDS": d["vds"], "VSB": -d["vbs"], "gm": d["gm"],
                      "gds": d["gds"], "gm_id": d["gm"] / d["id"], "region": "sat", "off_current_A": 0.0}
    m = measure(ind["f"], ind["H"])
    metrics = [{"name": k, "measure": k, "value": m[k]} for k in ("dc_gain_db", "ugf_hz", "pm_deg", "f3db_hz")]
    metrics.append({"name": "ivdd", "measure": "supply_current_A", "rail": "vdd",
                    "value": (CS["vdd"] - ind["V"]["nout"]) / CS["rload"]})
    return {"nodes": {"nout": ind["V"]["nout"], "pout": ind["V"]["pout"]}, "devices": devs, "metrics": metrics}


def all_judges(cmp: dict):
    """compare.json 의 모든 판정 문자열(소자 항목별, 노드, 성능, 제약, KCL)."""
    out = []
    for d in cmp.get("devices", []):
        out += [(f"dev:{d['name']}:{k}", v) for k, v in d["judge"].items()]
    out += [(f"node:{n['net']}", n["judge"]) for n in cmp.get("nodes", [])]
    out += [(f"perf:{p.get('name')}", p["judge"]) for p in cmp.get("performance", [])]
    out += [(f"cons:{c.get('name')}", c["judge"]) for c in cmp.get("constraints", [])]
    out += [(f"kcl:{k['net']}", k["judge"]) for k in cmp.get("kcl_residual", [])]
    return out
