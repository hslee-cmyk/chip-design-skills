"""WB-1 소스 grep 계약 (interface card §3·§5·§6·§8·§10 D-6 F-4 E-5 R-11 M-4 M-6 G-1 G-2). oracle (식): card 가 적은 grep 규칙.

이 파일은 엔진 소스를 '텍스트·AST 로' 훑는다(엔진 소스 구현을 보고 쓴 것이 아니다). 사라지는 이름은 이 파일 자신이 grep 에 걸리지 않게
조각으로 이어 붙인다. 각 test 는 먼저 훑은 파일 수 >= 1 을 단언한다(공허 통과 방지).
"""
import ast
import pathlib
import re

ENGINE = pathlib.Path(__file__).resolve().parents[2]


def _py(include_tests=False):
    out = []
    for p in sorted(ENGINE.rglob("*.py")):
        rel = p.relative_to(ENGINE).parts
        if "tests" in rel and not include_tests:
            continue
        if "__pycache__" in rel:
            continue
        out.append(p)
    return out


def _text(p):
    return p.read_text(encoding="utf-8", errors="replace")


def _words(names, include_tests):
    hits = {}
    for p in _py(include_tests):
        if p.resolve() == pathlib.Path(__file__).resolve():
            continue
        t = _text(p)
        for n in names:
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])", t):
                hits.setdefault(n, []).append(str(p.relative_to(ENGINE)))
    return hits


def test_wb1_files_scanned():
    assert len(_py()) > 50 and len(_py(True)) > len(_py())


def test_wb1_removed_dc_names_absent_everywhere_including_tests():
    # §3 '없어지는 것': E/ (tests 포함) 단어 grep 0
    names = ["dc_" + "columns", "dc_" + "widths", "dc_drop_" + "current", "pre_layout_lut_" + "access",
             "w_key_" + "of", "kernel_" + "keys"]
    assert _words(names, True) == {}


def test_wb1_input_status_names_absent_in_sources():
    # §8 순서 창: 지워진 이름 grep 0 (소스)
    names = ["INPUT_STATUS_" + "UNSETTLED", "_interior_" + "solution", "INPUT_STATUS_F_COMPONENT_" + "UNDECLARED"]
    assert _words(names, False) == {}
    kept = _words(["INPUT_STATUS_MEASURED", "INPUT_STATUS_UNMEASURED"], False)
    assert set(kept) == {"INPUT_STATUS_MEASURED", "INPUT_STATUS_UNMEASURED"}      # 남기는 이름은 그대로(양성 대조)


def test_wb1_retired_gm_id_inverse_names_absent():
    # M-4: 비-test 소스에서 0
    assert _words(["gm_id_" + "inverse", "branch_" + "targets"], False) == {}


def test_wb1_strong_inversion_root_used_only_in_vgs_root():
    hits = _words(["strong_inversion_root"], False).get("strong_inversion_root", [])
    assert hits, "사용처가 하나도 없다"
    names = {pathlib.PurePath(h).name for h in hits}
    assert names <= {"vgs_root.py"}, hits


def test_wb1_constraints_has_no_w_keys_and_con_inversion_kept():
    t = _text(ENGINE / "search" / "constraints.py")
    assert "CON_INVERSION" in t and "def " in t                    # 남김(양성 대조)
    assert not re.search(r"\bw_keys\b", t)                         # M-6


# [FS-1 G-4 서명 맞춤] 옛 `test_wb1_reachable_slices_calls_have_three_args`(E-5) 삭제 -- `reachable_slices` 가 사라졌다(후보 = `widths(lut, kind)`).
# 대체: `tests/structure/test_fs1_source.py::test_g3_removed_names_zero_in_engine_sources`.


def test_wb1_slice_functions_defined_once():
    """[FS-1 서명 맞춤] 슬라이스 좌표 함수는 `slice_of_finger` 하나 (옛 `finger_slice` 정의는 0)."""
    d = {"finger_slice": [], "slice_of_finger": []}
    for p in _py():
        for node in ast.walk(ast.parse(_text(p))):
            if isinstance(node, ast.FunctionDef) and node.name in d:
                d[node.name].append(str(p))
    assert d["finger_slice"] == [] and len(d["slice_of_finger"]) == 1, d


def test_wb1_residual_read_only_in_realize_front():
    # R-11: FingerGeom.residual 판정 소비자 = realize_front 하나 (속성 읽기)
    readers = set()
    for p in _py():
        for node in ast.walk(ast.parse(_text(p))):
            if isinstance(node, ast.Attribute) and node.attr == "residual" and isinstance(node.ctx, ast.Load):
                readers.add(p.name)
    assert readers == {"realize_front.py"}, readers


def test_wb1_realize_front_has_no_oracle_import():
    # G-1: oracle 호출 0 -- tools.spice_oracle import 0 (AST)
    p = ENGINE / "search" / "realize_front.py"
    assert p.is_file()
    tree = ast.parse(_text(p))
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods.append(node.module or "")
    assert mods                                                     # import 가 있는 파일을 훑었다
    assert not [m for m in mods if "spice_oracle" in m]


def test_wb1_realize_front_module_has_evaluate_not_finger_slice():
    import importlib
    importlib.import_module("gmid_engine.search")
    import sys
    importlib.import_module("gmid_engine.search.realize_front")      # 부재 = ModuleNotFoundError (신규 심볼)
    m = sys.modules["gmid_engine.search.realize_front"]
    assert hasattr(m, "evaluate")
    assert not hasattr(m, "finger_slice")


def test_wb1_tol_v_metrics_is_id_equivalent_only():
    from gmid_engine.lut import TOL_V_METRICS
    assert tuple(TOL_V_METRICS) == ("id_equivalent",)


# ---------------------------------------------------------------- G-2 (재작성 범위 옛 이름 0, spec card '재작성 범위' 표)
REWRITE_DELETED = ("sizing/block_columns.py", "sizing/block_widths.py", "sizing/pre_layout_widths.py", "convergence/kernel_keys.py")
REWRITE_NEW = ("sizing/block_dc.py", "lut/slice_of_finger.py",      # [FS-1] lut/finger_slice.py 는 삭제(G-4)
 "lut/slice_gap.py", "lut/slice_tables.py",
               "search/realize_front.py", "core/file_sha256.py")


def test_wb1_rewrite_range_deleted_files_gone_and_new_files_present():
    # 커밋 4: 네 파일 삭제 (block_dc.py 로 흡수), 새 파일 + core/file_sha256.py (양성 대조: 새 파일이 있어야 삭제가 의미 있다)
    assert all((ENGINE / r).is_file() for r in REWRITE_NEW), [r for r in REWRITE_NEW if not (ENGINE / r).is_file()]
    assert not [r for r in REWRITE_DELETED if (ENGINE / r).exists()]


def test_wb1_no_import_of_deleted_modules():
    mods = {"block_" + "columns", "block_" + "widths", "pre_layout_" + "widths", "kernel_" + "keys"}
    seen = 0
    bad = []
    for p in _py():
        for node in ast.walk(ast.parse(_text(p))):
            names = []
            if isinstance(node, ast.ImportFrom):
                seen += 1
                names = (node.module or "").split(".") + [a.name for a in node.names]
            elif isinstance(node, ast.Import):
                seen += 1
                names = [part for a in node.names for part in a.name.split(".")]
            if mods & set(names):
                bad.append((str(p.relative_to(ENGINE)), node.lineno))
    assert seen > 100 and bad == []


def test_wb1_w_keys_absent_in_rewritten_value_modules_and_graph():
    # 칸·인자 삭제: LutAccess·LocalInputs·ParamTables 의 w_keys, A-34 의 E/graph grep 0
    files = [ENGINE / r for r in ("metrics/block_param_tables.py", "metrics/achievability.py", "metrics/achievability_types.py",
                                  "search/iv_context.py", "search/constraints.py", "sizing/s2_values.py", "sizing/kernel_context.py",
                                  "sizing/_helpers_lut.py")] + sorted((ENGINE / "graph").glob("*.py"))
    assert len(files) > 10 and all(f.is_file() for f in files)
    names = ["w_" + "keys", "w_key_" + "of"]
    bad = {f.name: n for f in files for n in names if re.search(r"(?<![A-Za-z0-9_])" + n + r"(?![A-Za-z0-9_])", _text(f))}
    assert bad == {}


def test_wb1_ulp_anchor_condition_names_absent():
    # B-7: ulp 조건 비교 grep 0
    assert len(_py()) > 50
    assert _words(["_on_or_" + "inside"], False) == {}


def test_wb1_curve_checks_and_w_tolerance_docs_have_no_retired_names():
    # M-4: metrics/curve_checks.py 에 vgs_for_gm_id 0, layout/w_tolerance.py 에 gm_id_inverse 0
    cc, wt = ENGINE / "metrics" / "curve_checks.py", ENGINE / "layout" / "w_tolerance.py"
    assert cc.is_file() and wt.is_file() and len(_text(cc)) > 100 and len(_text(wt)) > 100
    assert "vgs_for_gm_" + "id" not in _text(cc)
    assert "gm_id_" + "inverse" not in _text(wt)


def test_wb1_param_tables_signature_is_memo_grids_side_z_side():
    # 포락 표는 W 가 없는 단계: 소자 키·기준 폭 키 인자를 받지 않는다 (side·z_side 만)
    import inspect
    from gmid_engine.metrics import ParamTables
    assert list(inspect.signature(ParamTables).parameters) == ["memo", "grids", "side", "z_side"]
