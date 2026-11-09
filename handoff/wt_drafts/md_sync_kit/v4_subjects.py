"""V4 피검 목록: A/*.py 최상위 def·class 전부를 `--subject <모듈>:<심볼>` 인자로 출력(test-only라 interface card 신규 시그니처가 0행 --
test_lint.py --interface-card 단독은 '피검 심볼이 없다' exit 2. P10 판정 기록 V4와 같은 처리).

    python -B v4_subjects.py <격리 복제본 루트> <출력 파일>
출력 파일 = 한 줄에 `<모듈>:<심볼>` 하나. 0f23786에서 373개.
"""
import ast
import pathlib
import sys

root, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
a = root / "skills" / "analog-gmid-design" / "assets"
rows = []
for p in sorted(a.glob("*.py")):
    for n in ast.parse(p.read_text(encoding="utf-8")).body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            rows.append(f"{p.stem}:{n.name}")
out.write_text("\n".join(rows) + "\n", encoding="utf-8")
print(len(rows))
