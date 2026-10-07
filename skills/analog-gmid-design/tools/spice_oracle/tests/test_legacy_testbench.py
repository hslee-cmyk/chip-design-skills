"""legacy_testbench.json -- 어댑터가 넣는 테스트벤치 구성값: 스키마 testbench 절에 맞고, 판정 기준(허용오차·포화 여유)은 없다(C11)."""
import json

import jsonschema

from conftest import ORACLE_DIR

TB = json.loads((ORACLE_DIR / "legacy_testbench.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ORACLE_DIR / "oracle_input.schema.json").read_text(encoding="utf-8"))


def test_testbench_conforms_to_schema_section():
    tb = {k: v for k, v in TB.items() if not k.startswith("_")}
    sub = SCHEMA["properties"]["testbench"]
    errs = list(jsonschema.Draft202012Validator(sub).iter_errors(tb))
    assert not errs, [e.message for e in errs]


def test_testbench_has_no_judge_values():
    flat = json.dumps(TB)
    for k in ("tolerances", "sat_margin", "off_current", "_rel", "_abs"):
        assert k not in flat, k
