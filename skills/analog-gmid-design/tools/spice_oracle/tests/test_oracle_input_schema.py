"""oracle_input.schema.json -- 스키마 자체 유효성 + 스키마 위반 입력 거부.

거부 test 는 공허하지 않게 세 가지를 같이 본다:
  (a) 변형 입력이 정말 스키마 위반인지 jsonschema 로 먼저 확인(위반이 아니면 test 자체가 무의미),
  (b) 원본(위반 없는) 입력은 같은 진입점에서 받아들여진다(양성 대조),
  (c) 변형 입력은 진입점이 0 이 아닌 코드로 끝나고 산출물(.cir / compare.json)을 쓰지 않는다.
"""
import copy
import json

import jsonschema
import pytest

from conftest import ORACLE_DIR, cs_input, make_lut, rc_input, run_netlist, run_oracle, require_spice

SCHEMA = json.loads((ORACLE_DIR / "oracle_input.schema.json").read_text(encoding="utf-8"))


def validator():
    return jsonschema.Draft202012Validator(SCHEMA)


def test_schema_is_valid_2020_12():
    assert SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


def test_fixture_inputs_conform(tmp_path):
    lut = make_lut(tmp_path / "lut.npz")
    for inp in (cs_input(lut), rc_input(lut)):
        errs = list(validator().iter_errors(inp))
        assert not errs, [e.message for e in errs]


def _set(path, value):
    def f(d):
        cur = d
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = value
    return f


def _del(path):
    def f(d):
        cur = d
        for k in path[:-1]:
            cur = cur[k]
        del cur[path[-1]]
    return f


def _add_constraint(op):
    def f(d):
        d["acceptance"] = {"constraints": [{"name": "g", "measure": "dc_gain_db", "op": op, "limit": 10}]}
    return f


VIOLATIONS = {
    "missing_devices": _del(["devices"]),
    "missing_testbench_choke": _del(["testbench", "dc_choke_H"]),
    "missing_ac_fstart": _del(["testbench", "ac", "fstart_hz"]),
    "device_missing_finger_w": _del(["devices", 0, "finger_w"]),
    "n_fingers_zero": _set(["devices", 0, "n_fingers"], 0),
    "n_fingers_fraction": _set(["devices", 0, "n_fingers"], 2.5),
    "L_is_string": _set(["devices", 0, "L"], "0.5u"),
    "passive_kind_inductor": _set(["passives", 0, "kind"], "inductor"),
    "passive_one_terminal": _set(["passives", 0, "terminals"], ["vdd"]),
    "rails_empty": _set(["rails"], []),
    "schema_tag_wrong": _set(["schema"], "spice_oracle_input/2"),
    "constraint_op_eq": _add_constraint("=="),
    "metric_measure_unknown": _set(["predictions", "metrics"], [{"measure": "gain", "value": 1.0}]),
    "region_unknown": _set(["predictions", "devices"], {"M1": {"region": "linear"}}),
}


@pytest.mark.parametrize("case", sorted(VIOLATIONS))
def test_violation_is_really_a_schema_violation(case, tmp_path):
    inp = cs_input(make_lut(tmp_path / "lut.npz"))
    bad = copy.deepcopy(inp)
    VIOLATIONS[case](bad)
    assert list(validator().iter_errors(bad)), f"{case}: 변형이 스키마 위반이 아님(test 결함)"


def test_valid_input_accepted_by_netlist(tmp_path):
    p, text, meta = run_netlist(cs_input(make_lut(tmp_path / "lut.npz")), tmp_path)
    assert p.returncode == 0, p.stderr[-2000:]
    assert text is not None and meta is not None and meta.get("blockers") == []


@pytest.mark.parametrize("case", sorted(VIOLATIONS))
def test_netlist_rejects_schema_violation(case, tmp_path):
    bad = cs_input(make_lut(tmp_path / "lut.npz"))
    VIOLATIONS[case](bad)
    p, text, meta = run_netlist(bad, tmp_path)
    assert p.returncode != 0 and text is None, (
        f"{case}: oracle_netlist.py 가 스키마 위반 입력을 받아들였다 rc={p.returncode} "
        f"cir_written={text is not None}\n{(p.stdout + p.stderr)[-600:]}")


@pytest.mark.parametrize("case", sorted(VIOLATIONS))
def test_run_rejects_schema_violation(case, tmp_path):
    require_spice()
    bad = cs_input(make_lut(tmp_path / "lut.npz"))
    VIOLATIONS[case](bad)
    p, res = run_oracle(bad, tmp_path / "o")
    assert p.returncode != 0 and res["free"] is None, (
        f"{case}: oracle_run.py 가 스키마 위반 입력으로 비교표를 냈다 rc={p.returncode} "
        f"verdict={(res['free'] or {}).get('summary', {}).get('verdict')}")
