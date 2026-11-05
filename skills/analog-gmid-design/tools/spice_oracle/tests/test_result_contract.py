"""OP-3 결과 계약 + 기간 동작 + 손 값 -- interface §6 T3-8a~d, T3-12a~d, T3-13~T3-15, §5 '기간 동작 [D-1]', design §11.5·§11.7.

oracle 출처:
  (a) T3-8: `record_id` 정의(D §11.7) 대로 test 가 손으로 만든 정규 JSON 해시(키 정렬, 구분자 (",", ":"), ensure_ascii=False)와 대조.
  (a) T3-13~T3-15: stub MNA 의 닫힌 식 -- 공통소스 한 단: 이득 = gm / (1/RL + gds), 출력 저항 = 1 / (1/RL + gds). 손 대입:
      gm = 6e-4, RL = 2e4 -> 1/RL = 5e-5, gds = 1/60000 = 1.66667e-5, 합 = 6.66667e-5, 이득 = 6e-4 / 6.66667e-5 = 9.0,
      dB = 20·log10(9) = 19.0848502, 출력 저항 = 1 / 6.66667e-5 = 15000.
  (a) T3-12d: 단극점 증폭기 PM. 극점 fp = 1/(2π·(RL||ro)·CL) with RL||ro = 15000, CL = 1e-12 -> fp = 1.06103e7 Hz,
      A0 = 9, 단위 이득 교차 f_u = fp·sqrt(A0² - 1) = fp·sqrt(80), 위상 이동 atan(sqrt(80)) = 90 - atan(1/sqrt(80)) = 90 - 6.3794 = 83.6206 deg,
      PM = 180 - 83.6206 = 96.3794 deg (README 측정 정의 `PM = 180 - (DC 위상 - UGF 위상)`).
  (d) T3-12a/b/c: 사용자 선언 기간 동작 [D-1] -- 능력 없는 측정은 거부, PM 은 P = 0 증명 없이 정의 불가(stability_unverified).
해석: 진입점 `oracle_run.main`, 결과 파일 `<stem>.compare.json`·`<stem>.sim.json`(D §11.7), sim.json 의 `ac.gain_dc`·`ac.dc_gain_db`·
`ac.pm_deg_raw`·`ac.pm_deg`·`ac.pm_undefined`·`ac.stability`. 코어는 시뮬레이터를 부르지 않는다(stub).
"""
import hashlib
import json
from pathlib import Path

import pytest

from op23_support import World, deep, read_json_glob, read_reject
from stub_adapter import StubAdapter

DEV = {"M1": {"gm": 6e-4, "gds": 1.0 / 60000.0}}


def canon(obj) -> str:
    """D §0·§11.7 정규 JSON 해시의 test 쪽 손 구현(oracle: 정의 문장)."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def with_cl(w, ppd=None):
    inp = deep(w.inp)
    inp["passives"].append({"name": "CL", "kind": "capacitor", "terminals": ["out", "gnd"], "value": 1e-12})
    if ppd:
        inp["testbench"]["ac"]["points_per_decade"] = ppd
    return inp


@pytest.fixture
def w(tmp_path):
    return World(tmp_path)


def run(w, inp=None, **kw):
    stub = StubAdapter(DEV)
    rc, out = w.run(stub, inp=inp, **kw)
    return rc, out, stub


# ------------------------------------------------------------------ T3-8
def test_t3_8a_record_id_is_hash_of_body_without_record_id_and_netlist(w):
    rc, out, _ = run(w)
    cj = read_json_glob(out, "*.compare.json")
    body = {k: v for k, v in cj.items() if k not in ("record_id", "netlist")}
    assert cj["record_id"] == canon(body)


def test_t3_8b_record_id_independent_of_output_folder(w):
    rc1, o1, _ = run(w, out=w.tmp / "out_a")
    rc2, o2, _ = run(w, out=w.tmp / "out_b")
    c1, c2 = read_json_glob(o1, "*.compare.json"), read_json_glob(o2, "*.compare.json")
    assert c1["record_id"] == c2["record_id"]
    for c, o in ((c1, o1), (c2, o2)):
        text = json.dumps({k: v for k, v in c.items() if k not in ("record_id", "netlist")}, ensure_ascii=False)
        forms = {o.as_posix(), str(o), json.dumps(str(o))[1:-1]}                         # 경로의 세 표기(JSON 이스케이프 포함)
        assert all(f not in text for f in forms)                                         # 출력 폴더 경로가 다른 칸에 없다


def test_t3_8c_sim_ref_hash_is_canonical_hash_of_sim_json(w):
    rc, out, _ = run(w)
    cj = read_json_glob(out, "*.compare.json")
    sim = read_json_glob(out, "*.sim.json")
    assert cj["sim_ref"]["sha256"] == canon(sim)


def test_t3_8d_compare_json_new_fields_and_deleted_u6(w):
    rc, out, _ = run(w)
    cj = read_json_glob(out, "*.compare.json")
    assert "u6" not in cj["summary"]                                      # X-R5 사본 삭제
    fp = cj["fingerprints"]
    assert set(fp) == {"adapter_fp", "descriptor_fp", "capability_record_id", "compat_sha256"}
    # spec C-6: compat_sha256 = 선언 글 sha. oracle (d): World toy 선언 글 "T" 의 sha256 을 hashlib 로 직접 손 유도(null 인 결과는 없다)
    assert fp["capability_record_id"] is None
    assert fp["compat_sha256"] == hashlib.sha256(b"T").hexdigest()
    assert isinstance(cj["machine_dependent_refs"], list)                 # 빈 목록이어도 칸은 있다
    assert cj["summary"]["conduction_definition"] == "threshold_eps1"
    inp_file = w.tmp / "inputs" / "out.input.json"
    assert cj["input_sha256"] == hashlib.sha256(inp_file.read_bytes()).hexdigest()


def test_t3_8_old_cli_field_names_are_gone(w):
    rc, out, _ = run(w)
    sim = read_json_glob(out, "*.sim.json")
    assert "ngspice_rc" not in sim and "ngspice_runs" not in sim          # 결과 칸 이름에 시뮬레이터 이름 없음(D §6)


# ------------------------------------------------------------------ T3-12 기간 동작 [D-1]
@pytest.mark.parametrize("block,value", [("noise", {"f_lo_hz": 1.0}), ("swing_icmr", {"swing": True})],
                         ids=["noise", "swing_icmr"])
def test_t3_12ab_blocks_without_capability_are_refused(w, block, value):
    inp = deep(w.inp); inp[block] = value
    rc, out, stub = run(w, inp)
    rec = read_reject(out)
    assert rc == 2 and rec["code"] == "adapter_capability_missing" and rec["stage"] == "5"
    assert stub.capabilities().get(rec["detail"]) is False                # detail = stub 에 없는 능력 이름
    assert stub.calls == []
    assert sorted(p.name for p in out.iterdir()) == [f"{inp['circuit']}.reject.json"]


def test_t3_12c_pm_constraint_is_incomplete_never_pass(w):
    inp = with_cl(w)
    inp["acceptance"] = {"constraints": [{"name": "pm", "measure": "pm_deg", "op": ">=", "limit": 45.0}]}
    rc, out, _ = run(w, inp)
    cj = read_json_glob(out, "*.compare.json")
    assert cj["summary"]["verdict"] == "INCOMPLETE" and cj["summary"]["verdict"] != "PASS"
    (row,) = [c for c in cj["constraints"] if c["measure"] == "pm_deg"]
    assert row["judge"] == "N/A(정의 불가: stability_unverified)"


def test_t3_12d_pm_raw_kept_pm_deg_none(w):
    inp = with_cl(w, ppd=200)                                             # 격자 12 decade × 200 = 2400 점: 보간 오차 << 허용
    rc, out, _ = run(w, inp)
    ac = read_json_glob(out, "*.sim.json")["ac"]
    assert ac["pm_deg"] is None and ac["pm_undefined"] == "stability_unverified"
    assert ac["pm_deg_raw"] == pytest.approx(96.3794, abs=0.01)           # 손 유도 값(모듈 docstring), 격자 보간 오차 ~1e-4 deg
    st = ac["stability"]
    assert st["pm_valid"] is None and st["pm_undefined"] == "stability_unverified"
    assert isinstance(st["reason"], str) and st["reason"]


# ------------------------------------------------------------------ T3-13 ~ T3-15 손 값
def test_t3_13_dc_gain(w):
    rc, out, _ = run(w)
    ac = read_json_glob(out, "*.sim.json")["ac"]
    assert ac["gain_dc"] == pytest.approx(9.0, rel=1e-6)                  # 6e-4 / (5e-5 + 1.66667e-5)


def test_t3_14_dc_gain_db(w):
    rc, out, _ = run(w)
    ac = read_json_glob(out, "*.sim.json")["ac"]
    assert ac["dc_gain_db"] == pytest.approx(19.0848502, abs=1e-5)        # 20·log10(9)


def test_t3_15_rout_sense_view(w):
    inp = deep(w.inp)
    inp["acceptance"] = {"constraints": [{"name": "ro", "measure": "rout_ohm", "op": ">=", "limit": 0.0,
                                          "view": {"sense_p": "out", "sense_mode": "single_ended"}}]}
    rc, out, _ = run(w, inp)
    cj = read_json_glob(out, "*.compare.json")
    (row,) = [c for c in cj["constraints"] if c["measure"] == "rout_ohm"]
    assert row["spice"] == pytest.approx(15000.0, rel=1e-6)               # 1 / (5e-5 + 1.66667e-5)

