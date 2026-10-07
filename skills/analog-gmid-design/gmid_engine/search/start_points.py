"""시작점 목록 (설계 design_mod6_search_front 6.1, 계획 N3.5·DEC-54·LR10 (L-c)).

진입점: `start_points(sctx, given, layer0=()) -> (tuple[StartPoint], tuple[dict])`(받아들인 시작점, 시작점마다 확인 기록).

* 출처 순서: ① 층 0 시작점(`layer0` -- `layer0_start` 가 만든 StartPoint, DEC-71 최소형 = 봉인 여유 최대-최소 중심, 그 평가는
  캐시에 있어 여기서 커널 0) ② 같은 S0·스키마·코드
  지문의 S3 이전 실행 front 점(`runs.jsonl`, 비지배 순위 1 = 설계 '상위' 정렬의 첫 단) ③ 부르는 쪽이 넘긴 θ(`given`, 선언 x0).
  ② 가 ③ 보다 앞이다(설계 순서). 같은 평가 키는 한 번만.
* 칸 벡터 = L 값마다 그 값을 품는 L 칸 index(칸 경계 1 ulp 포함). 품는 칸이 없으면 `ValueError`(정의역 밖 θ).
* 모든 시작점은 평가 1회로 봉인 상태를 확인한다(R K8). 받아들일 상태(봉인 통과·봉인 7 대기)가 아닌 시작점은 목록에서 빼고
  기록에 사유를 남긴다.
"""
import math

from gmid_engine.sizing import THETA_L

from .kernel import evaluate
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


def _s3_thetas(sctx):
    if sctx.archive is None:
        return ()
    out = []
    for run in sctx.archive.load_runs():
        if run.get("schema_fp") != sctx.schema_fp:
            continue
        for point in run.get("front", ()) + run.get("pending_front", ()):
            out.append(tuple((tuple(k), float.fromhex(h)) for k, h in point["theta_hex"]))
    return tuple(out)


def start_points(sctx, given, layer0=()):
    candidates = [(s.source, s.theta) for s in layer0]
    candidates += [("s3", t) for t in _s3_thetas(sctx)]
    candidates += [("given", tuple(sorted(dict(t).items()))) for t in given]
    starts, log, seen = [], [], set()
    for n, (source, theta) in enumerate(candidates):
        cells = _cells_of(sctx, theta)
        start_id = "s" + str(n + 1)
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
