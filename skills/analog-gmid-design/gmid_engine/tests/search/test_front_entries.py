"""search/front_entries.py -- `read_front_entries(run_dir) -> tuple[dict, ...]` (설계 40 v1.10 §2.4.3 'front 조회 전용 읽기 경로' 표 '읽기 함수' 행,
U-90 사용자 결정 2026-10-15, xrun interface card C6).

계약: run_dir = <archive_root>/<context_fp>(= S3Archive.dir). runs.jsonl 을 줄 순서대로 읽어 각 줄의 `front`·`pending_front` 항목 dict 를
원래 그대로(키 추가: 그 줄의 `run_id`, `code_fp`) 차례로 낸다. code_fp 로 거르지 않는다. 파일이 없으면 ().

oracle:
- (a) 구성: test 가 손으로 쓴 runs.jsonl(합성 줄) -- 기대값 = 그 줄들의 front·pending_front 항목에 두 키를 더한 dict(계약 문장대로 test 가 조립).
- (a) 구성: 엔진이 find_front 로 쓴 runs.jsonl 을 test 가 json 으로 직접 읽은 내용 -- 피검 함수 출력을 기대값으로 쓰지 않는다.
"""
import json
from pathlib import Path

from gmid_engine.search import find_front, read_front_entries

from .conftest import build_case, circuit_c, theta_r4c

SS_GAIN = (("gain_ss_db", ">=", 10.0, None),)            # test_find_front 의 SS 와 같은 입력(봉인 7 대기 점이 pending_front 로 가는 조건)


def _line(run_id, code_fp, front, pending, unmeasured=()):
    # runs.jsonl 한 줄(6절 형식의 칸 일부 -- 읽기 함수가 보는 칸 + 거르지 않아야 할 칸). 점 항목은 원래 dict 그대로 돌아와야 하므로
    # 계약이 정하지 않은 임의 키(`extra`)도 넣는다.
    return {"run_id": run_id, "code_fp": code_fp, "schema_fp": "s" * 64, "front": list(front), "pending_front": list(pending),
            "unmeasured_front": list(unmeasured), "notes": []}


def _point(pid, ref):
    return {"point_id": pid, "status": "sealed", "theta_hex": [[["current", "M1"], (1e-5).hex()]], "snapshot_ref": ref,
            "extra": {"nested": [1, 2]}}


def _write(run_dir, lines):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "runs.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")


def _expected(lines):
    # 계약 C6 문장 그대로: 줄 순서, 한 줄 안 front 다음 pending_front, 항목 원래 dict + run_id·code_fp. unmeasured_front 는 내지 않는다.
    out = []
    for ln in lines:
        for e in ln["front"] + ln["pending_front"]:
            out.append(dict(e, run_id=ln["run_id"], code_fp=ln["code_fp"]))
    return tuple(out)


def test_missing_file_gives_empty_tuple(tmp_path):
    assert read_front_entries(tmp_path / "no_such_run_dir") == ()
    (tmp_path / "empty_dir").mkdir()
    assert read_front_entries(tmp_path / "empty_dir") == ()


def test_line_order_front_then_pending_with_run_id_and_code_fp(tmp_path):
    lines = [
        _line("r1", "a" * 64, [_point("p1", "snapshots/1.json.gz"), _point("p2", "snapshots/2.json.gz")],
              [_point("q1", "snapshots/3.json.gz")], unmeasured=[_point("u1", "snapshots/9.json.gz")]),
        _line("r2", "a" * 64, [], [_point("q2", "snapshots/4.json.gz")]),
        _line("r3", "a" * 64, [_point("p3", "snapshots/5.json.gz")], []),
    ]
    _write(tmp_path / "ctx", lines)
    got = read_front_entries(tmp_path / "ctx")
    assert isinstance(got, tuple) and all(isinstance(e, dict) for e in got)
    assert got == _expected(lines)
    assert [(e["point_id"], e["run_id"]) for e in got] == [("p1", "r1"), ("p2", "r1"), ("q1", "r1"), ("q2", "r2"), ("p3", "r3")]
    assert "u1" not in {e["point_id"] for e in got}                       # unmeasured_front 는 front 조회 대상이 아니다(계약: front·pending_front)


def test_original_dict_preserved_plus_two_keys(tmp_path):
    p = _point("p1", "snapshots/1.json.gz")
    lines = [_line("r1", "b" * 64, [p], [])]
    _write(tmp_path / "ctx", lines)
    (e,) = read_front_entries(tmp_path / "ctx")
    assert set(e) == set(p) | {"run_id", "code_fp"}
    assert {k: v for k, v in e.items() if k not in ("run_id", "code_fp")} == p
    assert (e["run_id"], e["code_fp"]) == ("r1", "b" * 64)


def test_lines_with_other_code_fp_are_not_filtered(tmp_path):
    # 계약 C6 '거르지 않는다 -- 조회 결과를 보는 쪽이 판단한다'(옛 S3 읽기 API 는 code_fp 가 같은 줄만 냈다).
    lines = [_line("r1", "a" * 64, [_point("p1", "snapshots/1.json.gz")], []),
             _line("r2", "0" * 64, [_point("p2", "snapshots/2.json.gz")], [_point("q2", "snapshots/3.json.gz")]),
             _line("r3", "f" * 64, [], [_point("q3", "snapshots/4.json.gz")])]
    _write(tmp_path / "ctx", lines)
    got = read_front_entries(tmp_path / "ctx")
    assert got == _expected(lines)
    assert [e["code_fp"] for e in got] == ["a" * 64, "0" * 64, "0" * 64, "f" * 64]


def _file_lines(run_dir):
    return [json.loads(x) for x in (Path(run_dir) / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def test_engine_written_runs_file_read_back_in_order(tmp_path, lut_sealed, short_root):
    # 엔진이 같은 입력의 새 컨텍스트 두 개로 find_front 를 한 번씩 돌려 같은 S3 실행 폴더에 쓴 runs.jsonl 두 줄을 그대로 읽는다.
    # 기대값 = test 가 같은 파일을 json 으로 직접 읽은 줄(oracle (a)) -- 피검 함수를 부르지 않고 만든다.
    a = build_case(tmp_path / "a", circuit_c(), lut_sealed, eval_budget=30, archive_root=short_root, constraints=SS_GAIN)
    fa = find_front(a.sctx, [theta_r4c()])
    b = build_case(tmp_path / "b", circuit_c(), lut_sealed, eval_budget=30, archive_root=short_root, constraints=SS_GAIN)
    fb = find_front(b.sctx, [theta_r4c()])
    assert a.sctx.archive.dir == b.sctx.archive.dir                       # 전제: 같은 context_fp -> 같은 S3 실행 폴더
    lines = _file_lines(a.sctx.archive.dir)
    assert [ln["run_id"] for ln in lines] == [fa.run_id, fb.run_id]
    got = read_front_entries(a.sctx.archive.dir)
    assert got == _expected(lines)
    assert len(got) == len(fa.front) + len(fa.pending_front) + len(fb.front) + len(fb.pending_front) >= 1
    assert [e["point_id"] for e in got] == [p.point_id for p in tuple(fa.front) + tuple(fa.pending_front)
                                            + tuple(fb.front) + tuple(fb.pending_front)]


def test_engine_written_pending_front_entries_included(tmp_path, lut_pending, short_root):
    # 봉인 7 대기 LUT(VDSAT 열 없음)는 front 가 비고 pending_front 에 점이 든다(test_find_front I-6) -- 그 항목도 낸다.
    c = build_case(tmp_path, circuit_c(), lut_pending, eval_budget=30, archive_root=short_root, constraints=SS_GAIN)
    fr = find_front(c.sctx, [theta_r4c()])
    assert tuple(fr.front) == () and len(fr.pending_front) >= 1           # 전제
    got = read_front_entries(c.sctx.archive.dir)
    assert got == _expected(_file_lines(c.sctx.archive.dir))
    assert [e["point_id"] for e in got] == [p.point_id for p in fr.pending_front]
    assert all(e["run_id"] == fr.run_id and e["code_fp"] == c.sctx.code_fp for e in got)
