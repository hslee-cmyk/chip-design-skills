"""`_helpers_loo` -- CONTRACT 5절 [r6]·5.1·5.2 공용 틀, 공개 API 경유(`tol_v_table`·`tol_vdsat_table`·`TolVTable.at`).

r5 `tolerance.py` 안 helper(l_interior·l_loo_report·external_by_model·loo·cell_max·targets·with_external·opt·at)를 옮긴 것이라
식·순서·오류는 r5 와 같다(test_tolerance 의 r5 test 가 그대로 지난다). 여기서는 r6 에서 바뀐/더해진 공용 동작을 본다:
- [결정 A] 외부 L 값은 **셀 단위**: 값 칸 = VDS 격자점마다의 수열(길이 len(vds_grid), 원소 float/None), 그 bin 두 앵커 행의 셀 (i, k) 에는
  k 번째 원소만. 수 하나 = 모든 k 같은 값, None = 모든 k None(`per_vds` 정규화), 길이 다르면 ValueError.
  정규화 형식 = (model, (k 별 tuple)) model 정렬 [WB-1: 값 칸 id_equivalent 하나] -> memo 키(수 하나와 그 수를 모든 VDS 에 둔 수열은 같은 키).
- 상태 이름·오류 규칙은 tol_v_table·tol_vdsat_table 가 같다(같은 helper).
"""
import pytest

from gmid_engine.lut import tol_v_table, tol_vdsat_table

from .conftest import BIN_L, MID_L_SOURCE, mid_point_arrays, new_memo

M = "toyn__model."


def test_tol_v_per_vds_elements_go_to_their_cell_only(bin_memo):
    base = tol_v_table(bin_memo, "nmos", 100, ())
    t = tol_v_table(bin_memo, "nmos", 100, ((M + "1", (0.5, None)),))
    for i in range(len(BIN_L)):
        for k in range(2):
            b, c = base.cells[i][k], t.cells[i][k]
            assert c.id_equivalent_loo_v == b.id_equivalent_loo_v
            eq = b.id_equivalent_v
            if i in (3, 4) and k == 0 and eq is not None:
                eq = max(eq, 0.5)
            assert c.id_equivalent_v == eq, (i, k)
    assert any(t.cells[i][0].id_equivalent_v == 0.5 for i in (3, 4))                 # 실제로 올라갔다
    assert all(t.cells[i][1].id_equivalent_v == base.cells[i][1].id_equivalent_v for i in (3, 4))   # k = 1 (원소 None) 은 그대로
    assert tuple(t.l_bin_checks) == ((M + "1", (0.5, None)),)


def test_tol_v_scalar_equals_broadcast_sequence_same_key(bin_memo):
    a = tol_v_table(bin_memo, "nmos", 100, ((M + "3", 0.25), (M + "1", 0.5)))
    b = tol_v_table(bin_memo, "nmos", 100, ((M + "1", (0.5, 0.5)), (M + "3", [0.25, 0.25])))
    assert a is b
    assert tuple(a.l_bin_checks) == ((M + "1", (0.5, 0.5)), (M + "3", (0.25, 0.25)))
    c = tol_v_table(bin_memo, "nmos", 100, ((M + "1", (0.5, 0.4)), (M + "3", 0.25)))
    assert c is not a                                                                   # 한 원소만 달라도 다른 키


@pytest.mark.parametrize("checks", [
    ((M + "1", (0.1, 0.2, 0.3)),),               # id_equivalent 수열 길이 3 ≠ VDS 2
    ((M + "1", (0.1,)),),                        # 수열 길이 1
    ((M + "1", ()),),                            # 빈 수열
])
def test_tol_v_length_mismatch_valueerror(bin_memo, checks):
    with pytest.raises(ValueError):
        tol_v_table(bin_memo, "nmos", 100, checks)


def test_all_none_values_change_nothing(bin_memo):
    base = tol_v_table(bin_memo, "nmos", 100, ())
    t = tol_v_table(bin_memo, "nmos", 100, ((M + "1", None),))
    assert all(t.cells[i][k] == base.cells[i][k] for i in range(len(BIN_L)) for k in range(2))


def test_status_names_shared_between_tables(mid_toy_build):
    """같은 LUT·같은 외부 bin 집합이면 tol_v_table 과 tol_vdsat_table 의 l_loo·l_loo_bins·l_bins 가 같다(같은 helper)."""
    lut = mid_toy_build("shared", mid=mid_point_arrays((3.5e-6, 7.5e-6), l_source=MID_L_SOURCE)).load()
    m = new_memo(lut)
    tv, td = tol_v_table(m, "nmos", 100), tol_vdsat_table(m, "nmos", 100)
    assert tuple(tv.l_loo) == tuple(td.l_loo) and tuple(tv.l_loo_bins) == tuple(td.l_loo_bins)
    assert tv.l_bins == td.l_bins
    tv0, td0 = tol_v_table(m, "nmos", 100, ()), tol_vdsat_table(m, "nmos", 100, ())
    assert tuple(tv0.l_loo) == tuple(td0.l_loo)
    assert tuple(tv0.l_loo) != tuple(tv.l_loo)                                          # 외부 값이 상태를 바꿨다
    # 200 폭(중점 폭 아님) -> 둘 다 외부 값 없음
    assert tuple(tol_v_table(m, "nmos", 200).l_bin_checks) == () == tuple(tol_vdsat_table(m, "nmos", 200).l_bin_checks)


@pytest.mark.parametrize("fn,checks", [
    (tol_v_table, ((M + "1", 0.1), (M + "1", 0.2))),
    (tol_vdsat_table, ((M + "1", 0.1), (M + "1", 0.2))),
    (tol_v_table, ((M + "0", 0.1),)),
    (tol_vdsat_table, ((M + "0", 0.1),)),
])
def test_error_rules_shared(mid_toy_build, fn, checks):
    m = new_memo(mid_toy_build("err").load())
    with pytest.raises(ValueError):
        fn(m, "nmos", 100, checks)
