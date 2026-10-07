"""S3 탐색 기억 -- 설계점 단위 append-only 기록 (설계 design_mod6_search_front 7.3·8절, 계획 N3.3 S3, 확정 사항 3, WP-11).

진입점: `S3Archive(root, context_fp, code_fp)`.

* 위치 `<root>/<context_fp>/`: `evals.jsonl`(커널 1회 = 1줄, 캐시 적중은 쓰지 않음), `runs.jsonl`(실행 1회 = 1줄),
  `snapshots/<snapshot_fp>.json.gz`(front 점·채택 해의 S2 전체 -- 필드 값·writer·입력 버전). 줄마다 열고-쓰고-닫아 flush 한다
  (강제 종료 뒤에도 마지막 줄까지 남는다). 지문이 다른 디렉터리는 읽지 않는다.
* 디스크 실패 캐시는 별도 파일이 아니라 evals 의 실패 줄에서 재구성한다(`load_evals` -- `code_fp` 가 같은 줄만, REQ E3
  '코드가 바뀌면 자동 무효').
* 값 직렬화: frozen dataclass -> {"__type__": 클래스 이름, 필드...}, tuple -> list, 비유한 float -> 문자열(repr).
"""
import dataclasses
import gzip
import json
import math
from pathlib import Path


def _plain(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        out = {"__type__": type(value).__name__}
        out.update((f.name, _plain(getattr(value, f.name))) for f in dataclasses.fields(value))
        return out
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else repr(value)
    if hasattr(value, "item"):
        return _plain(value.item())
    return repr(value)


class S3Archive:
    """append-only S3 기록기. 상태는 경로뿐이다(쓴 값을 메모리에 들지 않는다 -- 메모리 캐시는 SearchContext 몫)."""

    def __init__(self, root, context_fp, code_fp):
        self.dir = Path(root) / context_fp
        self.code_fp = code_fp
        (self.dir / "snapshots").mkdir(parents=True, exist_ok=True)

    def _append(self, name, record):
        with open(self.dir / name, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(_plain(record), ensure_ascii=False, sort_keys=True) + "\n")
            fh.flush()

    def append_eval(self, record):
        self._append("evals.jsonl", dict(record, code_fp=self.code_fp))

    def append_run(self, record):
        self._append("runs.jsonl", dict(record, code_fp=self.code_fp))

    def load_evals(self):
        """같은 `code_fp` 의 evals 줄(dict) tuple. 파일이 없으면 ()."""
        path = self.dir / "evals.jsonl"
        if not path.exists():
            return ()
        rows = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                if row.get("code_fp") == self.code_fp:
                    rows.append(row)
        return tuple(rows)

    def load_runs(self):
        """같은 `code_fp` 의 runs 줄(dict) tuple(시작점 ②: 이전 실행 front 점). 파일이 없으면 ()."""
        path = self.dir / "runs.jsonl"
        if not path.exists():
            return ()
        with open(path, encoding="utf-8") as fh:
            rows = tuple(json.loads(line) for line in fh)
        return tuple(r for r in rows if r.get("code_fp") == self.code_fp)

    def write_snapshot(self, snapshot):
        """S2 스냅샷 전체를 `snapshots/<fp>.json.gz` 로(이미 있으면 다시 쓰지 않는다). 반환 = 상대 경로 문자열."""
        rel = "snapshots/" + snapshot.fp + ".json.gz"
        path = self.dir / rel
        if not path.exists():
            records = []
            for kind in snapshot.kinds():
                for key in snapshot.keys(kind):
                    rec = snapshot.record(kind, key)
                    fields = {}
                    for name in rec.field_names():
                        fv = rec.get(name)
                        fields[name] = {"value": _plain(fv.value), "writer": fv.writer, "input_version": fv.input_version}
                    records.append({"kind": kind, "key": key, "fields": fields})
            payload = json.dumps({"fp": snapshot.fp, "records": records}, ensure_ascii=False, sort_keys=True)
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                fh.write(payload)
        return rel

    def read_snapshot(self, rel):
        """`write_snapshot` 이 쓴 파일 -> dict(재계산 없음)."""
        with gzip.open(self.dir / rel, "rt", encoding="utf-8") as fh:
            return json.load(fh)
