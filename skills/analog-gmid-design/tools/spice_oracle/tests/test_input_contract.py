"""OP-3 입력 계약 `spice_oracle_input/2` -- interface §6 '입력 계약'(D §11.3 E1~E18), '게이트 전용 넷' T3-3a~f, 'LUT 읽기' T3-4a~h.

oracle (a)(d): 예시 입력 I 에서 한 곳만 바꾼 깨진 변형이 D §11.3 표의 코드로 거부된다는 구성 + 사용자 선언 규칙(닫힌 키 집합,
조용한 기본값 0). 양성 대조(예시 I 는 1a~2b 를 통과)와 짝. 모든 변형은 stub 로 돌고 시뮬레이터 호출 0.
해석: 진입점 `oracle_run.main(argv, adapters=...)`, 거부 기록 `<circuit>.reject.json` = {schema, code, detail, stage, input_path,
input_sha256}(D §11.7); `check_input_cross`·`read_lut_files` 는 interface §5 시그니처, LutRead 는 `corner`·`temp_c`·`meta_json` 속성.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from core.build_circuit import circuit_ir
from core.input_check import check_input_cross, read_lut_files
from core.results import OracleError

from op23_support import World, deep, lf_of, make_lut_toy, read_json_glob, read_reject, sha, M_LIB, write
from stub_adapter import StubAdapter

DEV = {"M1": {"gm": 6e-4, "gds": 1.0 / 60000.0}}


@pytest.fixture
def w(tmp_path):
    return World(tmp_path)


def run(w, inp, **kw):
    stub = StubAdapter(DEV)
    rc, out = w.run(stub, inp=inp, **kw)
    return rc, out, stub


def reject(w, inp, **kw):
    rc, out, stub = run(w, inp, **kw)
    rec = read_reject(out)
    assert rc == 2
    assert stub.calls == []                                              # 시뮬레이터 호출 0
    assert sorted(p.name for p in out.iterdir()) == ["cs_toy.reject.json"]    # 산출물은 거부 기록 하나
    return rec


def rules(rec):
    return {(d["pointer"], d["rule"]) for d in rec["detail"]}


def test_positive_control_example_passes_1a_to_2b(w):
    rc, out, stub = run(w, w.inp)
    assert not (out / "cs_toy.reject.json").exists()


def test_reject_record_shape(w):
    inp = deep(w.inp)
    inp["schema"] = "spice_oracle_input/1"
    rec = reject(w, inp)
    assert rec["schema"] == "oracle_reject/1" and rec["code"] == "oracle_input_format_old"
    raw = (Path(rec["input_path"])).read_bytes()
    assert rec["input_sha256"] == hashlib.sha256(raw).hexdigest()         # 입력 파일 raw sha256 (손으로 잰 값)


# ------------------------------------------------------------------ E1 ~ E7 스키마·옛 형식
def test_e1_schema_key_missing(w):
    inp = deep(w.inp); del inp["schema"]
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_schema_invalid" and ("/schema", "required") in rules(rec)


def test_e2_old_schema_value(w):
    inp = deep(w.inp); inp["schema"] = "spice_oracle_input/1"
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_format_old" and "schema" in rec["detail"]["markers"]


def test_e3_process_models_marker(w):
    inp = deep(w.inp); inp["process"]["models"] = {"x": 1}
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_format_old" and "process.models" in rec["detail"]["markers"]


def test_e4_testbench_options_marker(w):
    inp = deep(w.inp); inp["testbench"]["options"] = {"gmin": "1e-15"}
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_format_old" and "testbench.options" in rec["detail"]["markers"]


@pytest.mark.parametrize("marker", ["models", "ngspice_exe", "lut_npz", "diffusion"])
def test_e3b_every_deleted_process_field_is_old_format(w, marker):
    inp = deep(w.inp); inp["process"][marker] = {"x": 1}
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_format_old" and f"process.{marker}" in rec["detail"]["markers"]


def test_e5_unknown_top_level_key(w):
    inp = deep(w.inp); inp["declared_triode"] = []
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_schema_invalid" and ("/declared_triode", "additionalProperties") in rules(rec)


def test_e6_region_enum(w):
    inp = deep(w.inp); inp["predictions"]["devices"]["M1"]["region"] = "linear"
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_schema_invalid" and ("/predictions/devices/M1/region", "enum") in rules(rec)


def test_e7_uppercase_sha(w):
    inp = deep(w.inp); inp["process"]["descriptor"]["sha256"] = inp["process"]["descriptor"]["sha256"].upper()
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_schema_invalid" and ("/process/descriptor/sha256", "pattern") in rules(rec)


def test_two_defects_report_the_earlier_stage_only(w):
    inp = deep(w.inp); inp["schema"] = "spice_oracle_input/1"; inp["declared_triode"] = []     # E2 + E5
    assert reject(w, inp)["code"] == "oracle_input_format_old"


def test_schema_violations_listed_all_sorted(w):
    inp = deep(w.inp); inp["declared_triode"] = []; inp["predictions"]["devices"]["M1"]["region"] = "linear"
    rec = reject(w, inp)
    pairs = [(d["pointer"], d["rule"]) for d in rec["detail"]]
    assert pairs == sorted(pairs) and len(pairs) == 2                    # 위반 전부, (pointer, rule) 사전순


@pytest.mark.parametrize("path", [("process",), ("devices", 0), ("predictions", "devices", "M1"), ("testbench",), ("judge",)],
                         ids=lambda p: "/".join(map(str, p)))
def test_closed_key_set_every_layer(w, path):
    inp = deep(w.inp)
    cur = inp
    for k in path:
        cur = cur[k]
    cur["unknown_key_for_test"] = 1
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_schema_invalid"
    assert any(r == "additionalProperties" and p.endswith("unknown_key_for_test") for p, r in rules(rec))


def test_closed_key_set_judge_tolerances_and_noise(w):
    inp = deep(w.inp); inp["judge"]["tolerances"] = {"ID_rel": 0.1, "unknown_key_for_test": 1}
    rec = reject(w, inp)
    assert any(r == "additionalProperties" and p == "/judge/tolerances/unknown_key_for_test" for p, r in rules(rec))
    inp2 = deep(w.inp); inp2["noise"] = {"f_lo_hz": 1.0, "unknown_key_for_test": 1}
    rec2 = reject(w, inp2)
    assert any(r == "additionalProperties" and p == "/noise/unknown_key_for_test" for p, r in rules(rec2))


def test_provenance_key_is_accepted_open_object(w):
    inp = deep(w.inp); inp["provenance"] = {"producer": "test", "anything": [1, 2]}
    rc, out, stub = run(w, inp)
    assert not (out / "cs_toy.reject.json").exists()


# ------------------------------------------------------------------ E8 ~ E10, E14 ~ E16, E18
def test_e8_input_descriptor_raw_sha_on_crlf_checkout(w):
    w.toy.write_descriptor(crlf=True)
    raw = sha(w.toy.d.read_bytes())
    assert raw != lf_of(w.toy.d.read_bytes())
    inp = deep(w.inp); inp["process"]["descriptor"]["sha256"] = raw
    rec = reject(w, inp)
    assert rec["code"] == "pdk_descriptor_stale" and rec["detail"]["ref"] == "input_descriptor"
    ok = deep(w.inp); ok["process"]["descriptor"]["sha256"] = lf_of(w.toy.d.read_bytes())       # 양성 대조: LF 값은 통과
    rc, out, stub = run(w, ok, out=w.tmp / "ok")
    assert not (out / "cs_toy.reject.json").exists()


def test_e9_lut_file_stale_changed_and_missing(w):
    inp = deep(w.inp); s = inp["process"]["lut_files"][0]["sha256"]
    inp["process"]["lut_files"][0]["sha256"] = ("0" if s[0] != "0" else "1") + s[1:]
    rec = reject(w, inp)
    assert rec["code"] == "lut_file_stale" and rec["detail"]["actual_sha256"] == s
    inp2 = deep(w.inp); Path(inp2["process"]["lut_files"][0]["path"]).unlink()
    rec2 = reject(w, inp2, out=w.tmp / "o2")
    assert rec2["code"] == "lut_file_stale" and rec2["detail"]["actual_sha256"] == "missing"


def test_e10_kind_not_in_descriptor(w):
    inp = deep(w.inp); inp["devices"][0]["kind"] = "xmos"; inp["process"]["lut_files"][0]["kinds"] = {"xmos": None}
    rec = reject(w, inp)
    assert rec["code"] == "descriptor_kind_undeclared" and rec["detail"]["kind"] == "xmos"


def test_e11_lut_kind_coverage(w):
    inp = deep(w.inp); inp["process"]["lut_files"][0]["kinds"] = {"pmos": None}
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_schema_invalid" and any(r == "lut_kind_coverage" for _, r in rules(rec))


def test_e12_flat_meta_with_key_given(w):
    inp = deep(w.inp); inp["process"]["lut_files"][0]["kinds"] = {"nmos": "nfet_01v8"}
    rec = reject(w, inp)
    assert rec["code"] == "lut_meta_shape_mismatch" and rec["detail"]["why"] == "meta_key_given_for_flat"


def test_e13_condition_conflict_two_files(w):
    second = make_lut_toy(w.tmp / "world" / "lut2.npz", model_sha={"m.lib": sha(M_LIB)}, temp_c=30.0)
    inp = deep(w.inp)
    inp["process"]["lut_files"].append({"path": second.as_posix(), "sha256": sha(second.read_bytes()), "kinds": {"nmos": None}})
    rec = reject(w, inp)
    assert rec["code"] == "lut_condition_conflict" and rec["detail"]["key"] == "temp_c"


def test_e14_adapter_unknown(w):
    inp = deep(w.inp); inp["simulator"]["adapter"] = "no_such_adapter"
    rc, out, stub = run(w, inp, cli_simulator=None)                      # CLI 가 입력을 덮지 않게
    rec = read_reject(out)
    assert rc == 2 and rec["code"] == "adapter_unknown" and rec["detail"]["name"] == "no_such_adapter"
    assert "stub" in rec["detail"]["known"] or isinstance(rec["detail"]["known"], list)


def test_e15_exe_missing(w):
    inp = deep(w.inp); del inp["simulator"]["exe"]
    rec = reject(w, inp)
    assert rec["code"] == "simulator_exe_missing"
    inp2 = deep(w.inp); inp2["simulator"]["exe"] = (w.tmp / "nope.exe").as_posix()    # 경로는 있으나 파일 없음
    assert reject(w, inp2, out=w.tmp / "o2")["code"] == "simulator_exe_missing"


def test_e16_reference_rail_voltage_nonzero(w):
    inp = deep(w.inp); inp["rails"][1]["voltage"] = 0.5
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_schema_invalid" and any(r == "reference_rail_voltage" for _, r in rules(rec))


def test_e17_two_reference_rails_is_blocked_not_rejected(w):
    inp = deep(w.inp); inp["rails"][0]["reference"] = True
    rc, out, stub = run(w, inp)
    assert rc == 2 and not (out / "cs_toy.reject.json").exists()
    cj = read_json_glob(out, "*.compare.json")
    assert cj["summary"]["verdict"] == "BLOCKED" and cj["blockers"]
    assert stub.calls == []                                              # 막힘은 벤치를 실행하지 않는다


def test_e18_lut_without_meta_json(w):
    lut = make_lut_toy(w.tmp / "world" / "nometa.npz", with_meta=False)
    w.lut = lut
    inp = deep(w.inp)
    inp["process"]["lut_files"][0].update(path=lut.as_posix(), sha256=sha(lut.read_bytes()))
    rec = reject(w, inp)
    assert rec["code"] == "lut_model_provenance_missing" and rec["detail"]["why"] == "meta_absent"


# ------------------------------------------------------------------ T3-3 게이트 전용 넷 (check_input_cross)
def gate_input(w):
    inp = deep(w.inp)
    inp["devices"] = [
        {"name": "M1", "kind": "nmos", "drain": "o", "gate": "pb", "source": "gnd", "bulk": "gnd", "L": 5e-7,
         "finger_w": 1e-6, "n_fingers": 2, "W": 2e-6, "diffusion": inp["devices"][0]["diffusion"]},
        {"name": "M2", "kind": "nmos", "drain": "o", "gate": "in", "source": "gnd", "bulk": "gnd", "L": 5e-7,
         "finger_w": 1e-6, "n_fingers": 2, "W": 2e-6, "diffusion": inp["devices"][0]["diffusion"]}]
    inp["passives"] = [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "o"], "value": 20000.0}]
    inp["ports"] = {"input": "in", "output": "o"}
    inp["predictions"] = {"nodes": {"in": 0.6, "o": 0.9}, "devices": {}, "metrics": []}
    inp.pop("bias_voltages", None)
    return inp


def cross_rules(inp):
    circuit, _blockers = circuit_ir(inp, "free")
    return [e["rule"] for e in check_input_cross(inp, circuit)]


def test_t3_3a_no_bias_declaration(w):
    assert "bias_gate_nets_mismatch" in cross_rules(gate_input(w))


def test_t3_3b_declared_exactly(w):
    inp = gate_input(w); inp["bias_voltages"] = [{"net": "pb", "value": 0.5}]
    assert "bias_gate_nets_mismatch" not in cross_rules(inp)             # 양성 대조


def test_t3_3c_extra_declared_non_gate_only_net(w):
    inp = gate_input(w); inp["bias_voltages"] = [{"net": "pb", "value": 0.5}, {"net": "o", "value": 0.5}]
    assert "bias_gate_nets_mismatch" in cross_rules(inp)


def test_t3_3d_rail_net_needs_no_declaration(w):
    inp = gate_input(w); inp["rails"].append({"net": "pb", "voltage": 0.5})
    assert "bias_gate_nets_mismatch" not in cross_rules(inp)


def test_t3_3e_net_with_other_terminal_is_not_gate_only(w):
    inp = gate_input(w)
    inp["passives"].append({"name": "Rb", "kind": "resistor", "terminals": ["pb", "gnd"], "value": 1e5})
    assert "bias_gate_nets_mismatch" not in cross_rules(inp)


def test_t3_3f_prediction_does_not_replace_declaration(w):
    inp = gate_input(w); inp["predictions"]["nodes"]["pb"] = 0.5          # 예측 노드전압만 있고 선언 없음
    assert "bias_gate_nets_mismatch" in cross_rules(inp)
    circuit, _ = circuit_ir(inp, "free")
    touching = [e for e in circuit.elements if type(e).__name__ == "VSource" and "pb" in (e.p, e.n)]
    assert touching == []                                                # 예측값 전압원 0개 (옛 동작은 pb 에 전압원을 만들었다)


def test_t3_3_pipeline_rejects_with_oracle_input_schema_invalid(w):
    inp = gate_input(w)
    rec = reject(w, inp)
    assert rec["code"] == "oracle_input_schema_invalid" and any(r == "bias_gate_nets_mismatch" for _, r in rules(rec))


def test_check_input_cross_collects_all_sorted(w):
    inp = gate_input(w); inp["rails"][1]["voltage"] = 0.5                 # reference_rail_voltage + bias_gate_nets_mismatch
    circuit, _ = circuit_ir(inp, "free")
    errs = check_input_cross(inp, circuit)
    pairs = [(e["pointer"], e["rule"]) for e in errs]
    assert pairs == sorted(pairs) and {r for _, r in pairs} >= {"reference_rail_voltage", "bias_gate_nets_mismatch"}


# ------------------------------------------------------------------ T3-4 LUT 읽기 (read_lut_files)
def lut_input(w, tmp_path, files):
    """files = [(npz 경로, kinds)]"""
    inp = deep(w.inp)
    inp["process"]["lut_files"] = [{"path": Path(p).as_posix(), "sha256": sha(Path(p).read_bytes()), "kinds": k}
                                   for p, k in files]
    return inp


def mk(tmp_path, name, **kw):
    kw.setdefault("model_sha", {"p": "S" * 1})
    return make_lut_toy(tmp_path / name, **kw)


def read(w, tmp_path, files, **proc):
    inp = lut_input(w, tmp_path, files)
    inp["process"].update(proc)
    return read_lut_files(inp, tmp_path)


def shape_err(w, tmp_path, files):
    with pytest.raises(OracleError) as ei:
        read(w, tmp_path, files)
    assert ei.value.code == "lut_meta_shape_mismatch"
    return ei.value.detail["why"]


def test_t3_4a_flat_table_with_null_kind(w, tmp_path):
    r = read(w, tmp_path, [(mk(tmp_path, "a.npz"), {"nmos": None})])
    assert r.corner == "tt" and r.temp_c == 27.0


def test_t3_4b_flat_table_with_key_given(w, tmp_path):
    assert shape_err(w, tmp_path, [(mk(tmp_path, "a.npz"), {"nmos": "k"})]) == "meta_key_given_for_flat"


def test_t3_4c_flat_table_multi_kind(w, tmp_path):
    assert shape_err(w, tmp_path, [(mk(tmp_path, "a.npz"), {"nmos": None, "pmos": None})]) == "flat_multi_kind"


def test_t3_4d_nested_table(w, tmp_path):
    nested = mk(tmp_path, "n.npz", meta="nested")
    read(w, tmp_path, [(nested, {"nmos": "k"})])                          # 통과
    assert shape_err(w, tmp_path, [(nested, {"nmos": "z"})]) == "nested_key_absent"
    assert shape_err(w, tmp_path, [(nested, {"nmos": None})]) == "meta_key_missing_for_nested"


def test_t3_4e_unknown_shape(w, tmp_path):
    odd = mk(tmp_path, "o.npz", meta_raw={"a": "S", "k": {"p": "S"}})
    assert shape_err(w, tmp_path, [(odd, {"nmos": None})]) == "unknown_shape"


def test_t3_4f_temp_conflict_between_files(w, tmp_path):
    a, b = mk(tmp_path, "a.npz", temp_c=27.0), mk(tmp_path, "b.npz", temp_c=30.0)
    with pytest.raises(OracleError) as ei:
        read(w, tmp_path, [(a, {"nmos": None}), (b, {"nmos": None})])
    e = ei.value
    assert e.code == "lut_condition_conflict" and e.detail["key"] == "temp_c"
    assert {int(k): float(v) for k, v in e.detail["values"].items()} == {0: 27.0, 1: 30.0}


def test_t3_4g_input_temperature_wins(w, tmp_path):
    r = read(w, tmp_path, [(mk(tmp_path, "a.npz", temp_c=27.0), {"nmos": None})], temp_c=40.0)
    assert r.temp_c == 40.0


def test_t3_4h_no_corner_anywhere(w, tmp_path):
    with pytest.raises(OracleError) as ei:
        read(w, tmp_path, [(mk(tmp_path, "a.npz", corner=None), {"nmos": None})])
    assert ei.value.code == "oracle_condition_missing"


def test_t3_4_meta_json_member_is_returned(w, tmp_path):
    r = read(w, tmp_path, [(mk(tmp_path, "a.npz", model_sha={"m.lib": "ab" * 32}), {"nmos": None})])
    metas = r.meta_json if isinstance(r.meta_json, (list, tuple)) else [r.meta_json]
    assert any("ab" * 32 in json.dumps(m, default=str) for m in metas)
