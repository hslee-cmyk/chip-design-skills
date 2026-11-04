"""시작점 목록 (설계 design_mod6_search_front 6.1, 계획 N3.5·DEC-54·LR10 (L-c)).

진입점: `start_points(sctx, given, layer0=()) -> (tuple[StartPoint], tuple[dict])`(받아들인 시작점, 시작점마다 확인 기록).

* 출처 순서: ① 층 0 시작점(`layer0` -- `layer0_start` 가 만든 StartPoint, DEC-71 최소형 = 봉인 여유 최대-최소 중심, 그 평가는
  캐시에 있어 여기서 커널 0) ② 부르는 쪽이 넘긴 θ(`given`, 선언 x0). 이전 실행의 S3 front 점은 시작점으로 쓰지 않는다
  (S3 는 출력이다 -- 실행 사이 재사용 없음, NFR-2·U-89). 같은 평가 키는 한 번만.
* 칸 벡터 = L 값마다 그 값을 품는 L 칸 index(칸 경계 1 ulp 포함). 품는 칸이 없으면 `ValueError`(정의역 밖 θ).
* 단일 평가는 평가 전에 탐색 예산을 본다(`search_stop`): 주어진 시작점(`given`)이 예산(또는 벽시계)에 닿으면 그 후보와 그 뒤 후보를 평가하지 않고 기록에 `status` = 정지 사유
  (`eval_budget`)를 남긴다. 층 0 시작점은 `layer0_start` 가 이미 평가해 캐시 적중이라 예산에 닿았어도 커널 0 으로 읽는다(확인하지 않는다).
* 모든 시작점은 평가 1회로 봉인 상태를 확인한다(R K8). 받아들일 상태(봉인 통과·봉인 7 대기)가 아닌 시작점은 목록에서 빼고
  기록에 사유를 남긴다.
"""
import math

from gmid_engine.sizing import THETA_L

from .kernel import evaluate
from .search_stop import search_stop
from .search_values import ACCEPTED_STATUSES, STAGE_START, StartPoint


def _cells_of(sctx, theta):
    values = dict(theta)
    out = []
    for mos, cells in sctx.domain.l_cells:
        L = values[(THETA_L, mos)]
        found = [j for j, (lo, hi) in enumerate(cells) if lo - math.ulp(lo) <= L <= hi + math.ulp(hi)]
        if not found:
            raise ValueError("start_points: L " + repr((mos, L)) + " 을 품는 L 칸이 없다")
        out.append(found[0])
    return tuple(out)


def start_points(sctx, given, layer0=()):
    candidates = [(s.source, s.theta) for s in layer0]
    candidates += [("given", tuple(sorted(dict(t).items()))) for t in given]
    starts, log, seen = [], [], set()
    halted = None          # 주어진 시작점에서 예산에 닿은 사유 -- 이 뒤 후보는 평가하지 않는다
    for n, (source, theta) in enumerate(candidates):
        cells = _cells_of(sctx, theta)
        start_id = "s" + str(n + 1)
        if source == "given":
            halted = halted or search_stop(sctx)
            if halted is not None:
                log.append({"id": start_id, "source": source, "status": halted, "seq": None})
                continue
        res = evaluate(sctx, theta, cells, origin=(("stage", STAGE_START), ("start", start_id)))
        entry = {"id": start_id, "source": source, "status": res.status, "seq": res.seq}
        if res.failure is not None:
            entry["fail"] = res.failure.to_json()
        log.append(entry)
        if res.key in seen or res.status not in ACCEPTED_STATUSES:
            continue
        seen.add(res.key)
        starts.append(StartPoint(start_id, res.theta, cells, source))
    return tuple(starts), tuple(log)
