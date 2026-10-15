"""다른 실행의 front 항목 조회 -- 출력 조회 전용 (설계 40 §2.4.3 'front 조회 전용 읽기 경로', 계획 U-90).

진입점: `read_front_entries(run_dir) -> tuple[dict, ...]`.

* `run_dir` = `<archive_root>/<context_fp>`(= `S3Archive.dir`). `runs.jsonl` 을 줄 순서대로 읽어 각 줄의 `front` 다음 `pending_front` 항목을
  원래 dict 그대로 돌려주고, 항목마다 그 줄의 `run_id`·`code_fp` 를 더한다. **거르지 않는다**(`code_fp`·`schema_fp` 로도 거르지 않는다 -- 조회 결과를 보는 쪽이 판단).
  파일이 없으면 `()`.
* 이 함수는 엔진 계산 경로가 부르지 않는다(구조 규칙 K 가 엔진 안 호출을 거부한다): 결과는 graph 필드·시작점·실패 캐시·S3 메모리 색인에 들어가지 않는다.
  `node_across_front` 가 파일 front 항목(dict)을 읽을 때 `archive.dir` 의 스냅샷 파일을 따라가는 입력을 만드는 용도다.
"""
import json
from pathlib import Path

_RUNS_FILE = "runs.jsonl"
_FRONT_COLUMNS = ("front", "pending_front")


def read_front_entries(run_dir):
    path = Path(run_dir) / _RUNS_FILE
    if not path.exists():
        return ()
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            for column in _FRONT_COLUMNS:
                out.extend(dict(entry, run_id=row["run_id"], code_fp=row["code_fp"]) for entry in row.get(column, ()))
    return tuple(out)
