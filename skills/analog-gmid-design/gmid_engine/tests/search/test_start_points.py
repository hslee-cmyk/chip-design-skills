"""CONTRACT 3.12 `start_points(sctx, given) -> (starts, log)`: 후보 = (층 0 출발점) 다음 given,
칸 = L 마다 [lo − ulp, hi + ulp] 가 품는 첫 칸(없으면 ValueError), 후보마다 evaluate 1회(id s1..), 받아들일 상태이고 처음 보는 키만
StartPoint.
[xrun] 설계 40 v1.10 §2.4.3 'S3' 행·'이전 실행 front 점 시작점' 삭제(사용자 결정 2026-10-15 "나로 해"): 이전 실행의 S3 runs front·pending 점은
후보가 아니다 -- 시작점 기록의 출처는 층 0 과 "given" 뿐(interface card C5)."""
import json
import math
from pathlib import Path

import pytest

from gmid_engine.search import (
    STATUS_FAILED,
    STATUS_OUTSIDE_DOMAIN,
    STATUS_SEALED,
    StartPoint,
    find_front,
    start_points,
)

from .conftest import CELLS_C, build_case, circuit_c, theta_r4c


def test_log_and_starts(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    s = case.sctx
    ok = theta_r4c()
    given = [ok, dict(ok), theta_r4c(i2=-1e-5), theta_r4c(y=0.1, v1=1.5)]
    starts, log = start_points(s, given)
    log = [dict(e) for e in log]
    assert [e["id"] for e in log] == ["s1", "s2", "s3", "s4"]
    assert [e["status"] for e in log] == [STATUS_SEALED, STATUS_SEALED, STATUS_OUTSIDE_DOMAIN, STATUS_FAILED]
    assert all("source" in e and "seq" in e for e in log)
    assert "fail" in log[3]
    assert log[1]["seq"] == log[0]["seq"]                      # 같은 키 -> 캐시 적중(같은 결과)
    assert len(starts) == 1
    (sp,) = starts
    assert isinstance(sp, StartPoint) and sp.start_id == "s1"
    assert tuple(sp.cells) == CELLS_C
    assert tuple(sp.theta) == tuple(sorted(ok.items()))
    c = dict(s.counters)
    assert (c["requests"], c["kernel_calls"], c["outside_domain"]) == (4, 2, 1)


def test_cell_lookup_tolerates_one_ulp(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    th = theta_r4c(l1=math.nextafter(1e-6, 0.0), l2=math.nextafter(2e-6, 1.0))
    starts, log = start_points(case.sctx, [th])
    assert len(starts) == 1 and tuple(starts[0].cells) == (0, 1)


def test_l_outside_every_cell_rejected(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    with pytest.raises(ValueError):
        start_points(case.sctx, [theta_r4c(l1=1.5e-6)])


def _runs(root, ctx_fp):
    p = Path(root) / ctx_fp / "runs.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_previous_run_front_points_are_not_start_candidates(tmp_path, lut_sealed, short_root):
    """[xrun XR-4] interface card C5: 같은 archive_root 로 같은 입력의 find_front 를 두 번 돌리면, 두 번째 실행은 첫 실행의 front 점을
    시작점으로 쓰지 않는다. oracle (a) 구성: 첫 실행은 빈 S3 폴더에서 돈 실행이다 -- 두 번째 실행의 시작점 기록(runs.jsonl 줄 `starts`)은
    출처가 층 0(`SOURCE_LAYER0` = "layer0", test_layer0_center 가 값 고정)과 "given" 뿐이고 시작점 수가 빈 S3 실행과 같다."""
    a = build_case(tmp_path / "a", circuit_c(), lut_sealed, archive_root=short_root, eval_budget=30)
    fa = find_front(a.sctx, [theta_r4c()])
    assert len(fa.front) >= 1                                           # 전제: 첫 실행이 front 점을 S3 에 남겼다
    b = build_case(tmp_path / "b", circuit_c(), lut_sealed, archive_root=short_root, eval_budget=30)
    assert b.sctx.context_fp == a.sctx.context_fp                        # 전제: 같은 S3 실행 폴더(첫 실행 줄이 있다)
    find_front(b.sctx, [theta_r4c()])
    first, second = _runs(short_root, a.sctx.context_fp)
    sources = [dict(e)["source"] for e in second["starts"]]
    assert set(sources) <= {"layer0", "given"}, sources
    assert len(second["starts"]) == len(first["starts"])
    assert [dict(e)["source"] for e in first["starts"]] == sources
