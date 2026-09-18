"""V4 (2) 검출기 예외·정지 전수 확인(review35 M4-03 뒤, 05 design §10).

실제 엔진 모듈(`skills/analog-gmid-design/assets/*.py`)의 모든 최상위 함수를 피검으로 두고, 매개변수 이름을
그대로 인자로 넘긴 합성 test 하나씩을 `v4.judge()`에 넣는다. 확인 대상은 판정 값이 아니라 **예외와 정지**다
(검출기 예외는 게이트 도구 오류 exit 2가 되어 정상 test를 FAIL로 만든다). 결과는 함수마다 파일에 append.
부트스트랩 ①에서 공격 23의 한 케이스(검출기 전수 무예외)로 옮기고 이 파일은 지운다.
"""
import ast
import collections
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
import v4  # noqa: E402

OUT = HERE / "sweep_engine.out.txt"
OUT.write_text("", encoding="utf-8")


def log(line):
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


total, errors, dist, t_all = 0, 0, collections.Counter(), time.time()
for mod in sorted((REPO / "skills/analog-gmid-design/assets").glob("*.py")):
    src = mod.read_text(encoding="utf-8")
    for f in ast.parse(src).body:
        if not isinstance(f, ast.FunctionDef):
            continue
        a = f.args
        names = [p.arg for p in a.posonlyargs + a.args]
        test = f"def test_x():\n    assert {f.name}({', '.join(names)}) == pytest.approx(expected)\n"
        total += 1
        t0 = time.time()
        try:
            r = v4.judge(src, test, {f.name})
            dist[r[0][1]] += 1
        except Exception as e:  # 이 확인의 대상: judge가 예외를 내면 게이트 도구 오류(exit 2)가 된다
            errors += 1
            log(f"EXC {mod.name}:{f.name} {type(e).__name__}: {str(e)[:100]}")
        dt = time.time() - t0
        if dt > 5:
            log(f"SLOW {mod.name}:{f.name} {dt:.1f}s")
log(f"functions {total}, exceptions {errors}, outputs {dict(sorted(dist.items()))}")
