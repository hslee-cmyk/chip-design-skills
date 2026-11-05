"""감도 게이트 실행 -- 분해가 읽지 않는 소자의 θ 성분을 FD 스텝만큼 섭동해 분해 변화와 MNA 변화를 대조 (설계 40 §3.8-2, 체크리스트 D-SG).

진입점: `run_sensitivity_gate(sctx, base, origin=()) -> GateResult | None`.

* 기준 점 `base`(`EvalResult`, 봉인 점)의 블록 잔차 보고(`metrics_aux` 필드, 41 §2.2)에서 분해 이득·전회로 이득·풀이 잔차·**분해가 읽는 소자**(`read_devices`)를 읽는다.
  보고가 없으면(구조 입력 없음 -- S0 수준 필드 `graph/s1v: metric_structure` 가 None(S1v 를 만들지 않은 컨텍스트)이거나 전달 뷰 제약이 없다) 게이트를 돌리지 않는다(None).
* 섭동 방향 = 탐색 변수(`sctx.domain.variables`) 중 **영향을 주는 소자가 모두 읽는 소자 밖**인 것: L·ln IDu·수동소자 성분은 그 소자 하나, 전류 성분은 KCL 원뿔에서 그 원천을 항으로 가진 MOS 들,
  W4 자유 노드 전압 y 는 모든 MOS 의 동작점을 움직이므로 읽는 쪽이다(섭동 안 함).
  스텝과 섭동 점 평가는 `fd_jacobian` 이 하는 그대로다(그 좌표의 LUT 해상도 스텝, parent = 기준 점 -- 바뀐 성분을 읽는 블록만 다시 계산, 같은 키는 캐시 적중). 읽는 소자를 건드리는
  변수는 `skip` 으로 평가하지 않는다.
* 묶음 `ceiling` = `e_total(sctx)`(게이트 예산 = E_total, 탐색 예산이 아니다). `FdBudgetShortfall` 은 잡지 않는다 -- 게이트 예약 R 이 지켜졌다면 나지 않으므로 나면 결함으로 실행이 멈춘다.
  게이트 시작 뒤 `search_ceiling`·`search_stop` 을 부르지 않는다(게이트는 탐색 예산을 다 써도 언제나 돈다).
* 섭동 점의 보고를 metrics `sensitivity_gate` 에 넘겨 판정한다(ε = 풀이 상대 잔차 × 이득 dB 의 감도). 섭동 점이 받아들일 상태가 아니거나 보고가 없으면 그 방향은 검사하지 못한 것.
"""
from gmid_engine.metrics import REPORT_BLOCK_RESIDUAL, sensitivity_gate
from gmid_engine.sizing import KERNEL_KEY, METRICS_KEY, THETA_CURRENT, THETA_Y

from ._helpers_ceiling import e_total
from .fd_jacobian import fd_jacobian
from .theta_coords import ThetaCoords

AUX_FIELD = "metrics_aux"


def _report(result):
    """평가 결과의 블록 잔차 보고 dict 또는 None(전달 뷰가 둘 이상이면 첫 보고)."""
    if result is None or result.evaluation is None:
        return None
    try:
        bundle = result.evaluation.snapshot.value("graph", METRICS_KEY, AUX_FIELD)
    except KeyError:
        return None
    found = next((dict(rep) for name, rep in bundle.reports if name == REPORT_BLOCK_RESIDUAL), None)
    return found


def _affected(sctx, var, everything):
    kind, key = var.component
    if kind == THETA_Y:
        return everything                    # W4 자유 노드 전압(출력·입력 공통모드)은 모든 소자의 동작점을 움직인다
    if kind != THETA_CURRENT:
        return {key}
    return {mos for mos, terms in sctx.dc.base.value("graph", KERNEL_KEY, "theta_schema").current_cone for t in terms if t.source == key}


def run_sensitivity_gate(sctx, base, origin=()):
    report = _report(base)
    if report is None or report["decomposed_gain_db"] is None or report["full_gain_db"] is None:
        return None
    read = set(report["read_devices"])
    variables = sctx.domain.variables
    everything = {m for m, _ in base.evaluation.snapshot.column("device", "dc_op")}
    skip = frozenset(i for i, v in enumerate(variables) if _affected(sctx, v, everything) & read)
    if len(skip) == len(variables):
        return None
    coords = ThetaCoords.start(variables, dict(base.theta))      # 시작 좌표 원값 보존 정본. 자르지 않는다(X-14: fd_jacobian 이 움직이는 좌표만 상자 안으로 맞춘다)
    columns = fd_jacobian(sctx, variables, list(coords.x0), base, base.key.cells, coords.to_theta, origin, skip, ceiling=e_total(sctx))
    runs = []
    for i, (var, (res, _step)) in enumerate(zip(variables, columns)):
        if i in skip or res is None or res is base:
            continue
        found = _report(res)
        if found is None:
            continue
        runs.append((var.component[0] + ":" + str(var.component[1]), found["decomposed_gain_db"], found["full_gain_db"], found["solve_residual"]))
    return sensitivity_gate((report["decomposed_gain_db"], report["full_gain_db"], report["solve_residual"]), tuple(runs))
