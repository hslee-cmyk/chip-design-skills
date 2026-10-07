"""공정-무관 회귀 검증 러너 test 도구.

`sizing_recipe.py`에서 이관됐다(spec card 20260930-d-move-tests, 운영 호출 0 -- self-test 전용).
본문은 바이트 그대로이며 엔진 이름은 전부 `from sizing_recipe import ...`로 가져온다.
"""
import json
import os
import sys
from dataclasses import dataclass

import numpy as np

_ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ASSETS not in sys.path:
    sys.path.insert(0, _ASSETS)

from sizing_recipe import (  # noqa: E402
    SemiEmpiricalGmIdLUT, _COMPENSATION_REGISTRY, optimize_multistage)


# ---------------------------------------------------------------------------
# 6.6) 공정-무관 회귀 검증 러너 — "무엇을 검증할지"는 전부 reference JSON이 선언하고, 이
#      함수는 그 선언을 읽어 실행·대조만 한다. 새 공정을 추가해도 이 함수는 한 글자도
#      안 바뀐다(<process>_regression_reference.json 파일만 새로 만들면 됨) — 새 회로/새
#      engine 타입을 추가할 때도 _REGRESSION_ENGINES에 등록만 하면 된다(_COMPENSATION_
#      REGISTRY/_METRICS_REGISTRY와 같은 패턴). 배경: analog-topology-json-library.do.md
#      배치 7-1 — sky130 전용 숫자를 이 파일(공정-무관 엔진)에 직접 박았다가(2026-07-31)
#      사용자 지적으로 이 구조로 재설계함.
# ---------------------------------------------------------------------------

@dataclass
class RegressionVerdict:
    ok: bool
    case_key: str
    detail: str
    actual: dict | None = None


def _run_optimize_multistage_case(case: dict, luts_by_kind: dict) -> dict:
    """`"engine": "optimize_multistage"` case를 실제로 실행해 gms/stages를 반환한다.
    `case`는 reference JSON의 한 case 항목 그대로(`topology_fn`/`topology_fn_kwargs`/
    `lut_kinds`/`search`/`constraints`)."""
    fn_name = case["topology_fn"]
    if fn_name not in _COMPENSATION_REGISTRY:
        raise ValueError(
            f"regression case가 참조하는 topology_fn '{fn_name}'이 _COMPENSATION_REGISTRY에 "
            f"없다 -- {sorted(_COMPENSATION_REGISTRY)} 중 하나여야 한다")
    topology_fn = _COMPENSATION_REGISTRY[fn_name](**case["topology_fn_kwargs"])
    luts = [luts_by_kind[k] for k in case["lut_kinds"]]
    search = case["search"]
    constraints = case.get("constraints", {})
    result = optimize_multistage(
        topology_fn, luts,
        L_candidates=search["L_candidates"], VDS_candidates=search["VDS_candidates"],
        gm_id_grid=search["gm_id_grid"],
        objective=constraints.get("objective", "power"),
        gain_min=constraints.get("gain_min"), w_max=constraints.get("w_max"))
    if result is None:
        raise ValueError("optimize_multistage()가 실행가능점을 못 찾음 -- case의 격자/제약 확인")
    return {"gms": result["gms"],
            "stages": [{"L": s["L"], "VDS": s["VDS"], "gm_id": s["gm_id"], "W": s["W"]}
                       for s in result["stages"]]}


_REGRESSION_ENGINES = {
    "optimize_multistage": _run_optimize_multistage_case,
    # 새 engine 타입(예: "run_topology_pipeline", "optimize_full_circuit_budget")을 추가할
    # 때는 여기 한 줄만 등록하면 된다 -- run_regression_case() 자체는 수정하지 않는다.
}


def run_regression_case(reference_json_path: str, case_key: str, rel_tol: float = 0.01) -> RegressionVerdict:
    """`reference_json_path`(공정별 1개 JSON, 예: `sky130_regression_reference.json`)에서
    `case_key`로 지정된 검증 케이스를 로드해 실제로 실행하고 `expected`와 대조한다.

    이 함수 자체는 어느 공정·어느 topology_fn·어느 회로에도 하드코딩되지 않는다 — 전부
    reference JSON의 `case["engine"]`(어느 harness 함수를 돌릴지, `_REGRESSION_ENGINES`로
    조회)과 `case["expected"]`(무엇과 대조할지)가 선언한다. `lut_file`은 `reference_json_
    path`와 같은 디렉터리에서 찾는다(공정 데이터를 reference JSON과 나란히 두는 관례).

    반환: `RegressionVerdict(ok, case_key, detail, actual)` — `ok=False`면 `detail`에
    첫 번째로 어긋난 값을 명시한다."""
    with open(reference_json_path, "r", encoding="utf-8") as f:
        ref = json.load(f)
    if case_key not in ref["cases"]:
        return RegressionVerdict(ok=False, case_key=case_key, detail=(
            f"case_key '{case_key}'가 {reference_json_path}에 없다 -- "
            f"{sorted(ref['cases'])} 중 하나여야 한다"))
    case = ref["cases"][case_key]

    engine = _REGRESSION_ENGINES.get(case["engine"])
    if engine is None:
        return RegressionVerdict(ok=False, case_key=case_key, detail=(
            f"engine '{case['engine']}'이 _REGRESSION_ENGINES에 없다 -- "
            f"{sorted(_REGRESSION_ENGINES)} 중 하나여야 한다"))

    import os as _os_mod
    lut_path = _os_mod.path.join(
        _os_mod.path.dirname(_os_mod.path.abspath(reference_json_path)), ref["lut_file"])
    d = np.load(lut_path)
    luts_by_kind = {
        "n": SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"],
                                   d["ID_n"], d["GM_n"], d["GDS_n"], d["CGG_n"], W_ref=5e-6),
        "p": SemiEmpiricalGmIdLUT(d["L"], d["VGS"], d["VDS"], d["VS"],
                                   d["ID_p"], d["GM_p"], d["GDS_p"], d["CGG_p"], W_ref=5e-6),
    }
    search = dict(case.get("search", {}))
    if search.get("L_candidates") == "lut.L":
        search["L_candidates"] = [float(v) for v in d["L"]]
    if search.get("VDS_candidates") == "lut.VDS":
        search["VDS_candidates"] = [float(v) for v in d["VDS"]]
    case = dict(case, search=search)

    try:
        actual = engine(case, luts_by_kind)
    except (ValueError, KeyError) as e:
        return RegressionVerdict(ok=False, case_key=case_key, detail=f"실행 실패: {e}")

    expected = case["expected"]
    for i, (a_gm, e_gm) in enumerate(zip(actual["gms"], expected["gms"])):
        if abs(a_gm - e_gm) / e_gm > rel_tol:
            return RegressionVerdict(ok=False, case_key=case_key, actual=actual, detail=(
                f"gms[{i}] 불일치: 실제 {a_gm} vs 기대 {e_gm}(상대오차 {rel_tol:.0%} 초과)"))
    for i, (a_st, e_st) in enumerate(zip(actual["stages"], expected["stages"])):
        for key in ("L", "VDS", "gm_id", "W"):
            a_val, e_val = a_st[key], e_st[key]
            if abs(a_val - e_val) / max(abs(e_val), 1e-15) > rel_tol:
                return RegressionVerdict(ok=False, case_key=case_key, actual=actual, detail=(
                    f"stages[{i}].{key} 불일치: 실제 {a_val} vs 기대 {e_val}"
                    f"(상대오차 {rel_tol:.0%} 초과)"))
    return RegressionVerdict(ok=True, case_key=case_key, actual=actual,
                              detail=f"{ref.get('source', reference_json_path)}와 일치")
