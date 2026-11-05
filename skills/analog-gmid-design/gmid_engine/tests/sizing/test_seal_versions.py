"""봉인 4 `seal_versions(snapshot, calls)` -- CONTRACT 6절: calls 의 블록마다
fp_of((이름, code_hash, Projection.from_snapshot(snapshot, reads, extras).fp)) == block_version 이고 그 블록 writes 필드의
input_version == block_version. 위반 블록 = detail `blocks`, magnitude = 위반 수, tol 0.

`calls` 형식은 계약에 없다 -- 공개 함수가 받는 ((블록, extras tuple), ...) 를 쓴다(conftest eval_calls, 보고: 모호).
기대 버전은 이 test 가 core `fp_of`·`Projection` 으로 직접 계산한다.
"""
from gmid_engine.core import Projection, fp_of
from gmid_engine.sizing import SealItem, seal_versions

from .conftest import eval_calls, tamper, theta_c


def expected_version(snap, blk, extras):
    return fp_of((blk.name, blk.code_hash, Projection.from_snapshot(snap, blk.reads, extras).fp))


def test_pass_and_independent_version_formula(ctx_c):
    snap, calls = eval_calls(ctx_c[2], theta_c())
    for blk, ex in calls:
        assert snap.block_version(blk.name) == expected_version(snap, blk, ex)
    item = seal_versions(snap, calls, ctx_c[2].base)
    assert isinstance(item, SealItem) and item.item == 4
    assert item.status == "pass"
    assert item.magnitude == 0 and item.tol == 0
    assert dict(item.detail)["blocks"] == ()
    assert dict(item.detail)["n_checked"] == len(calls)


def test_input_changed_after_compute_is_violation(ctx_c):
    """dc_L 를 dc_lengths 자기 버전 그대로 바꿔 넣으면 dc_L 을 읽는 하류(dc_columns·dc_widths)의 투영이 달라진다."""
    snap, calls = eval_calls(ctx_c[2], theta_c())
    bad = tamper(snap, "dc_lengths", "device", "dc_L", {"M1": 2e-6}, version=snap.block_version("dc_lengths"))
    exp = sorted(b.name for b, ex in calls if bad.block_version(b.name) != expected_version(bad, b, ex))
    assert {"dc_columns", "dc_widths"} <= set(exp)
    assert "dc_currents" not in exp
    item = seal_versions(bad, calls, ctx_c[2].base)
    assert item.status == "fail"
    assert tuple(dict(item.detail)["blocks"]) == tuple(exp)
    assert item.magnitude == len(exp) and item.tol == 0


def test_output_written_with_other_version_is_violation(ctx_c):
    """dc_op 를 다른 input_version 으로 다시 쓰면 block_version(dc_widths) 이 계산 버전과 다르다."""
    snap, calls = eval_calls(ctx_c[2], theta_c())
    bad = tamper(snap, "dc_widths", "device", "dc_op", {}, version="tampered")
    item = seal_versions(bad, calls, ctx_c[2].base)
    assert item.status == "fail"
    assert dict(item.detail)["blocks"] == ("dc_widths",)
    assert item.magnitude == 1


def test_empty_calls_pass(ctx_c):
    snap, _ = eval_calls(ctx_c[2], theta_c())
    item = seal_versions(snap, (), snap)       # [승인 20261022-it2a-o94-ext 범위 1] base = 이 test 의 4 호출 뒤 스냅샷 자신
    assert item.status == "pass" and dict(item.detail)["n_checked"] == 0


# =====================================================================================================================
# [IT-2a 20261021-it2a-snapshot-derive, T-L11b] 봉인 4 `seal_versions(snapshot, calls, base)` 단언 (3) coverage·(4) 서로소 (design 41 4.7-3c).
# oracle: (식) 단언 문장 그대로 -- (3) 스냅샷 모든 필드의 writer ∈ base writer ∪ {calls 블록 이름}, 위반 detail ("foreign_writers", 정렬 tuple);
# (4) base writer ∩ {calls 블록 이름} = ∅, 위반 detail ("base_call_overlap", 정렬 tuple). 위반 = status "fail"(SEAL_FAIL).
# 픽스처는 구성으로 정한다: (3) 위반 = 4 호출 뒤 스냅샷에 호출 목록 밖 블록(dc_tolerances)의 필드를 더한 것, (4) 위반 = base 를 4 호출 뒤 스냅샷
# 자체로 준 것(base writer 가 호출 블록 넷을 모두 포함). 통과 픽스처를 먼저 보이고(거부가 실제로 일어남을 대조), 기존 (1)(2) 결과는 그대로여야 한다.
# 피검 함수 출력으로 기대값을 만들지 않는다. base(seal_versions(snapshot, calls) 2 인자): 새 인자 TypeError(존재 부재 red).
# =====================================================================================================================

from .conftest import with_tol  # noqa: E402


def _it2a_names(calls):
    return tuple(sorted(b.name for b, _ex in calls))


def _it2a_extra(item, key):
    return dict(item.detail).get(key, ())


def test_it2a_seal_4_passes_when_fields_are_base_or_call_writers(ctx_c):
    """통과 대조: 4 호출 뒤 스냅샷, base = ctx.base -> pass, (1)(2) blocks 비어 있음, 새 detail 은 없거나 빈 tuple."""
    ctx = ctx_c[2]
    snap, calls = eval_calls(ctx, theta_c())
    item = seal_versions(snap, calls, ctx.base)
    assert item.item == 4 and item.status == "pass"
    assert dict(item.detail)["blocks"] == ()
    assert _it2a_extra(item, "foreign_writers") == ()
    assert _it2a_extra(item, "base_call_overlap") == ()


def test_it2a_seal_4_rejects_field_of_writer_outside_base_and_calls(ctx_c):
    """(3) coverage 위반: 호출 목록 밖 블록 dc_tolerances 의 필드가 스냅샷에 있다 -> 'fail', detail foreign_writers = ('dc_tolerances',).
    실제 거부를 먼저 확인(통과면 red)."""
    ctx = ctx_c[2]
    snap, calls = eval_calls(ctx, theta_c())
    assert seal_versions(snap, calls, ctx.base).status == "pass"            # 대조: 위반 없는 픽스처는 통과
    snap_tol, _ = with_tol(ctx, theta_c())                                  # 호출 넷 + dc_tolerances(호출 목록 밖)
    assert snap_tol.block_version("dc_tolerances") is not None              # 전제: 호출 밖 writer 의 필드가 실제로 있다
    assert "dc_tolerances" not in ctx.base.block_versions                   # 전제: base writer 도 아니다
    item = seal_versions(snap_tol, calls, ctx.base)
    assert item.status == "fail"
    assert _it2a_extra(item, "foreign_writers") == ("dc_tolerances",)
    assert _it2a_extra(item, "base_call_overlap") == ()
    assert dict(item.detail)["blocks"] == ()                                # 기존 (1)(2) 는 따로 위반 없음 -- 새 단언만이 거부한다


def test_it2a_seal_4_rejects_base_writer_that_is_also_a_call(ctx_c):
    """(4) 서로소 위반: base 스냅샷의 writer 가 호출 블록과 겹친다 -> 'fail', detail base_call_overlap = 겹치는 이름의 정렬 tuple.
    base = 4 호출 뒤 스냅샷 자체 -> base writer ⊇ 호출 블록 넷 -> 겹침 = 호출 블록 넷 전부(손 읽기)."""
    ctx = ctx_c[2]
    snap, calls = eval_calls(ctx, theta_c())
    assert seal_versions(snap, calls, ctx.base).status == "pass"            # 대조
    item = seal_versions(snap, calls, snap)
    assert item.status == "fail"
    assert _it2a_extra(item, "base_call_overlap") == ("dc_columns", "dc_currents", "dc_lengths", "dc_widths")
    assert _it2a_extra(item, "foreign_writers") == ()
    assert dict(item.detail)["blocks"] == ()


def test_it2a_seal_4_existing_checks_still_reject_with_base_argument(ctx_c):
    """기존 (1)(2) 는 그대로 -- dc_op 를 다른 input_version 으로 다시 쓰면 base 인자가 있어도 blocks = ('dc_widths',) 로 fail."""
    ctx = ctx_c[2]
    snap, calls = eval_calls(ctx, theta_c())
    bad = tamper(snap, "dc_widths", "device", "dc_op", {}, version="tampered")
    item = seal_versions(bad, calls, ctx.base)
    assert item.status == "fail"
    assert dict(item.detail)["blocks"] == ("dc_widths",)


# =====================================================================================================================
# [IT-2e 20261104-it2e-partial-snapshot, T-E5·T-E6] `writers_in_scope(base, blocks)` -- 합집합식 정의 자리 하나.
# oracle (손, T-E5): 반환 = base.block_versions 키 ∪ {블록 .name}. 기대는 손 집합 -- 호출 블록 이름은 리터럴, 겹침 사례는 구성(base = 4 호출 뒤
#   스냅샷, 블록 = 같은 4개 -> 합집합이 base 키와 같다). 신규 함수라 import 는 test 안에서 한다(없으면 이 test 들만 ImportError red).
# oracle (독립, T-E6): 엔진 소스의 AST 를 이 test 가 직접 훑는다 -- 'block_versions 읽기와 .name 읽기를 함께 담은 합집합 연산' 자리가 정의 한 곳
#   (함수 writers_in_scope)뿐이고, 호출 자리는 keep(kernel_run)·coverage(seal_versions)·부착(kernel_run·seal) 파일뿐.
# =====================================================================================================================

import ast  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

from .conftest import SKILL_DIR  # noqa: E402

IT2E_CALL_NAMES = ("dc_columns", "dc_currents", "dc_lengths", "dc_widths")


def test_it2e_writers_in_scope_value(ctx_c):
    """T-E5 값: base = ctx.base(S1·계획 writer), 블록 = 평가 4 호출 -> base 키 + 호출 블록 넷 이름 정확히. 블록 없음 -> base 키 그대로."""
    from gmid_engine.sizing.seal_versions import writers_in_scope
    ctx = ctx_c[2]
    _snap, calls = eval_calls(ctx, theta_c())
    base_keys = set(ctx.base.block_versions)
    got = writers_in_scope(ctx.base, [b for b, _ex in calls])
    assert isinstance(got, frozenset)
    assert got - base_keys == set(IT2E_CALL_NAMES)                          # 손: 호출 블록 이름이 더해진다
    assert base_keys <= got and not (set(IT2E_CALL_NAMES) & base_keys)      # 전제: 호출 블록은 base writer 가 아니다
    assert writers_in_scope(ctx.base, ()) == frozenset(base_keys)


def test_it2e_writers_in_scope_overlap_and_iterable(ctx_c):
    """T-E5: base 가 이미 호출 블록을 writer 로 가지면 합집합은 중복 없이 base 키와 같다. blocks 는 iterable 이면 된다(generator)."""
    from gmid_engine.sizing.seal_versions import writers_in_scope
    ctx = ctx_c[2]
    snap, calls = eval_calls(ctx, theta_c())
    assert set(IT2E_CALL_NAMES) <= set(snap.block_versions)                 # 전제: 4 호출 뒤 스냅샷의 writer 는 호출 블록을 포함
    got = writers_in_scope(snap, (b for b, _ex in calls))
    assert got == frozenset(snap.block_versions)


def test_it2e_writers_in_scope_rejects_none_base(ctx_c):
    """T-E5 거부: base 가 None 이면 TypeError (존재하는 base 로는 거부되지 않는다 -- 대조)."""
    from gmid_engine.sizing.seal_versions import writers_in_scope
    ctx = ctx_c[2]
    _snap, calls = eval_calls(ctx, theta_c())
    writers_in_scope(ctx.base, [b for b, _ex in calls])                      # 대조: 정상 입력은 통과
    with pytest.raises(TypeError):
        writers_in_scope(None, [b for b, _ex in calls])


def test_it2e_coverage_violation_still_fails(ctx_c):
    """T-E5: 합집합 정의가 한 자리로 모여도 봉인 4 coverage 위반 픽스처는 FAIL 유지(호출 목록 밖 블록 dc_tolerances 의 필드) -- 통과 대조 먼저."""
    ctx = ctx_c[2]
    snap, calls = eval_calls(ctx, theta_c())
    assert seal_versions(snap, calls, ctx.base).status == "pass"
    snap_tol, _ = with_tol(ctx, theta_c())
    item = seal_versions(snap_tol, calls, ctx.base)
    assert item.status == "fail"
    assert dict(item.detail).get("foreign_writers") == ("dc_tolerances",)


def _it2e_engine_modules():
    root = Path(SKILL_DIR) / "gmid_engine"
    out = []
    for p in sorted(root.rglob("*.py")):
        if "tests" in p.relative_to(root).parts:
            continue
        out.append((p, ast.parse(p.read_text(encoding="utf-8"))))
    return out


def _it2e_attr_names(node):
    return {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}


def _it2e_union_sites(tree):
    """합집합 연산(`a | b`, `a |= b`, `x.union(...)`, `x.update(...)`)이면서 부분식에 `block_versions` 와 `name` 속성 읽기를 함께 담은 노드를
    감싼 가장 안쪽 함수 이름들."""
    sites = []

    def visit(node, fn):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn = node.name
        hit = False
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            hit = True
        elif isinstance(node, ast.AugAssign) and isinstance(node.op, ast.BitOr):
            hit = True
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("union", "update"):
            hit = True
        elif isinstance(node, (ast.Tuple, ast.List, ast.Set)) and any(isinstance(e, ast.Starred) for e in node.elts):
            hit = True                                                      # (*a, *b) 꼴 합집합
        if hit:
            names = _it2e_attr_names(node)
            if "block_versions" in names and "name" in names:
                sites.append(fn)
        for ch in ast.iter_child_nodes(node):
            visit(ch, fn)

    visit(tree, None)
    return sites


def test_it2e_union_definition_site_is_single():
    """T-E6: 'base writer ∪ 블록 이름' 합집합식의 정의 자리는 함수 writers_in_scope 하나, 모듈 seal_versions 안. 그 밖 재구현 0."""
    mods = _it2e_engine_modules()
    assert len(mods) > 10                                                   # 전제: 엔진 소스를 실제로 훑었다
    sites = [(p.name, fn) for p, tree in mods for fn in _it2e_union_sites(tree)]
    assert sites == [("seal_versions.py", "writers_in_scope")], sites


def test_it2e_writers_in_scope_call_sites():
    """T-E6: writers_in_scope 호출 자리 = 파생 keep(kernel_run)·봉인 4 coverage(seal_versions)·실패 부착(kernel_run·seal) 파일뿐이고 셋 모두 있다."""
    files = set()
    for p, tree in _it2e_engine_modules():
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
                if nm == "writers_in_scope":
                    files.add(p.stem)
    assert files == {"kernel_run", "seal_versions", "seal"}, files
