"""`sizing/_helpers_dc_solve.py` -- 커널·다듬은 창이 같이 쓰는 노드 풀이 helper(card IT-2b, design 41 v1.12.8 4.7-3a·4.7-4).

옛 `block_columns._Circuit`·`_solve`·`_FAILURES` 를 이 모듈의 공개 이름 `Circuit`·`solve`·`FAILURES` 로 옮기고 `Circuit.saturation_rows` 를
`region_rows`(5원소 행 `(a, b, sign, slack, kind)`)로 넓힌다. `kind` ∈ {"sat", "triode"}(S4-나: EO-1 이 늦게 병합 -- `off` 행·V_on 호출 없음).

oracle:
- (손) triode 행 영 교차 = 창 끝: toy 연결의 닫힌 식 + conftest 의 r4 LUT 열 직접(`r4_vdsat_at`·`r4_tol_vdsat` = npz 열 독립 계산). 피검 함수로 기대값을 만들지 않는다.
- (독립) 모듈 소스의 AST 부재 단언(`git grep` 과 같은 뜻 -- 문자열·주석이 아니라 식별자·상수를 본다).
이 파일은 `Circuit` 생성자 서명을 모른다(interface card 에 없음): 행동은 공개 진입점 `dc_columns`(`run_blocks`)를 거쳐 본다.
"""
import ast
from pathlib import Path

import pytest

import gmid_engine

from .conftest import build_ctx, free_currents, kschema, mos, node_voltages, r4_ln_idu, r4_tol_vdsat, r4_vdsat_at, topo

ENGINE = Path(gmid_engine.__file__).resolve().parent

VIN = 0.8                  # 입력 DC 선언 값(손으로 정한 입력)
VGS1 = 0.8                 # M1(triode 선언) 의 VGS
VGS3 = 0.6                 # M3(in 을 받치는 풀다운) 의 VGS


def _toy_doc():
    """M1 nmos (d = out, g = vb, s = in, b = gnd) -- triode 선언 소자, source 가 입력 포트 in. M2 pmos (out, pb, vdd) 부하(포화).
    M3 nmos (in, vc, gnd) 가 in 노드의 전류 경로를 닫는다. vb·pb·vc = 외부 바이어스(게이트 전용). out = W4 뿌리(y).
    손계산: V(out) = lo + y·(hi − lo), lo = V(in)(M1 은 out 쪽 드레인이 흐름 나가는 단자 -> 소스 쪽 이웃이 아래 끝), hi = V(vdd)."""
    return topo("it2b_triode", [mos("M1", "nmos", "out", "vb", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd"),
                                mos("M3", "nmos", "in", "vc", "gnd")],
                {"in": ("input", "x"), "out": ("output", "y")}, bias=["vb", "pb", "vc"])


def _columns(ctx, theta):
    """`dc_columns` 를 커널과 같은 호출로 부른다: 5번째 extras = 선언 영역 소자 tuple(비어 있지 않을 때만, sizing CONTRACT 5.4). conftest `run_blocks` 는
    이 extras 를 주지 않아 triode 선언이 커널 창에 닿지 않으므로 이 파일의 triode toy 는 이 함수로 부른다. (이 파일 앞 커밋은 `run_blocks` 를 썼다 -- 정정)"""
    from gmid_engine.sizing import dc_columns, dc_currents, dc_lengths
    from .conftest import kfixed, kres
    run = dict(donors=ctx.donors, counters=ctx.counters)
    th = dict(theta)
    snap = dc_currents(ctx.base, tuple(sorted((k, v) for (t, k), v in th.items() if t == "current")), **run)
    snap = dc_lengths(snap, tuple(sorted((k, v) for (t, k), v in th.items() if t == "L")), **run)
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    extras = (kfixed(ctx), kres(ctx), ctx.lut)
    if ctx.inputs.linear_devices:
        extras += (tuple(ctx.inputs.linear_devices),)
    return dc_columns(snap, items, *extras, **run)


def _toy_ctx(tmp_path, access):
    return build_ctx(tmp_path, _toy_doc(), access, input_dc_v=VIN, linear_devices=("M1",))[2]


def _toy_theta(ctx, y, vsg2):
    out = VIN + y * (1.8 - VIN)
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6,
          ("ln_idu", "M1"): r4_ln_idu("nmos", VGS1, out - VIN, VIN),
          ("ln_idu", "M2"): r4_ln_idu("pmos", vsg2, 1.8 - out, 0.0),
          ("ln_idu", "M3"): r4_ln_idu("nmos", VGS3, VIN, 0.0), ("y", "out"): y}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th


def test_it2b_d_triode_row_zero_crossing_is_the_window_end(tmp_path, r4_access):
    """oracle 대조: (손) D -- `triode` 선언 소자가 훑기 중 포화로 가는 toy: 그 점이 창 끝. 행 `(d, s, −부호, VDsat − VDS − tol_VDsat, "triode")` 의 영 교차.
    y = 0.4: V(out) = 0.8 + 0.4·(1.8 − 0.8) = 1.2 (뿌리 식), 소스 in 이 움직이면 s_out = 1 − y = 0.6.
    M1(triode): VDS = out − in = 0.4, VDsat = r4_vdsat_at(vgs 0.8, vsb 0.8); 여유 = VDsat − VDS − tol, 율 = −(s_out − s_in) = y -> Δ ≥ −여유/y (아래 끝).
    M2(pmos 포화): VSD = 1.8 − out = 0.6; 여유 = VSD − VDsat(vsg 0.4, vsb 0) − tol_p, 율 = −s_out -> Δ ≤ 여유/(1 − y) (위 끝).
    M3(nmos 포화, d = in, s = gnd): VDS = in; 여유 = in − VDsat(vgs 0.6, 0) − tol, 율 +1 -> Δ ≥ −여유 (더 느슨).
    base 는 선언 소자를 행에서 빼서 M1 아래 끝을 놓친다(아래 끝이 M3 의 −0.4965 가 되어 다르다 -- red)."""
    y, vsg2 = 0.4, 0.4
    ctx = _toy_ctx(tmp_path, r4_access)
    snap = _columns(ctx, _toy_theta(ctx, y, vsg2))
    V = node_voltages(snap)
    out = VIN + y * (1.8 - VIN)
    assert abs(V["out"] - out) <= 1e-9 and V["in"] == VIN                                       # 전제: 뿌리 식 손계산
    tol_n, tol_p = r4_tol_vdsat("nmos"), r4_tol_vdsat("pmos")
    s_out = 1.0 - y
    slack1 = r4_vdsat_at("nmos", 1e-6, VGS1, VIN) - (out - VIN) - tol_n
    slack2 = (1.8 - out) - r4_vdsat_at("pmos", 1e-6, vsg2, 0.0) - tol_p
    slack3 = VIN - r4_vdsat_at("nmos", 1e-6, VGS3, 0.0) - tol_n
    assert slack1 > 0 and slack2 > 0 and slack3 > 0                                              # 전제: 세 소자 모두 선언 영역 안
    dlo = max(-slack1 / y, -slack3)
    dhi = slack2 / s_out
    assert dlo == -slack1 / y                                                                    # 전제: 아래 끝은 triode 행에서 나온다
    w = dict(snap.column("node", "dc_window"))["in"]
    assert w.input_status == "measured"
    assert abs(w.lo - (VIN + dlo)) <= 1e-9 and abs(w.hi - (VIN + dhi)) <= 1e-9, (w, VIN + dlo, VIN + dhi)


def test_it2b_d_no_operating_point_mismatch_vocabulary_in_engine_sources():
    """oracle 대조: (독립) 계획 v6.33 (9)(d), 사용자 결정 O-98·O-101. (S4-나) 에서 동작점 불일치 묶음(블록 `op_mismatch` 판정·`Window.status_detail`·
    metric code)은 EO-1 card 몫이다 -- 죽은 코드를 두지 않는다. 비test 엔진 소스(tests 폴더 제외 모든 .py)에서 문자열 `op_mismatch`,
    `status_detail`, `input_window_operating_point_mismatch` (정의·상수 이름·문자열 모두, `git grep` 과 같은 텍스트 검색) 가 0 이다.
    옛 `test_it2b_d_operating_point_mismatch_status_and_detail` 단언은 EO-1 card 의 test 로 옮겨졌다(범위 이동, 약화 아님)."""
    hits = []
    for path in ENGINE.rglob("*.py"):
        if "tests" in path.relative_to(ENGINE).parts:
            continue
        text = path.read_text(encoding="utf-8")
        for word in ("op_mismatch", "status_detail", "input_window_operating_point_mismatch"):
            if word in text:
                hits.append((str(path.relative_to(ENGINE)), word))
    assert hits == [], hits


def test_it2b_d_helper_module_public_names_replace_block_columns_privates():
    """oracle 대조: (d) 사용자 선언 스펙값 -- interface card: `gmid_engine.sizing._helpers_dc_solve` 가 `Circuit`·`solve`·`FAILURES` 를 공개 이름으로
    갖고(`Circuit.region_rows` 포함) 옛 `block_columns._Circuit`·`_solve`·`_FAILURES` 는 없어진다. `_refine_ends` 삭제는 IT-2d 몫이라 보지 않는다."""
    from gmid_engine.sizing import _helpers_dc_solve as helper
    from gmid_engine.sizing import block_columns
    for name in ("Circuit", "solve", "FAILURES"):
        assert hasattr(helper, name), name
    assert hasattr(helper.Circuit, "region_rows")
    for old in ("_Circuit", "_solve", "_FAILURES"):
        assert not hasattr(block_columns, old), old


def _identifiers_and_strings(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names, strings = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.alias):
            names.add((node.asname or node.name).split(".")[-1])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    return names, strings


def test_it2b_d_s4_na_region_kinds_are_sat_and_triode_without_conduction_helper():
    """oracle 대조: (독립) D (S4-나) -- EO-1 이 늦게 병합되므로 이 card 의 `region_rows` 는 `off` 행·V_on 호출이 없다: 모듈의 문자열 상수에 행 종류
    "sat"·"triode" 가 있고 "off" 는 없으며, 공용 전도 판정 함수·V_on 역함수를 가리키는 식별자(이름에 conduct 또는 v_on)를 쓰지 않는다
    (AST 로 식별자·상수만 본다 -- 주석·docstring 의 말은 세지 않는다)."""
    names, strings = _identifiers_and_strings(ENGINE / "sizing" / "_helpers_dc_solve.py")
    assert {"sat", "triode"} <= strings
    assert "off" not in strings
    suspect = sorted(n for n in names if "conduct" in n.lower() or "v_on" in n.lower())
    assert suspect == [], suspect
