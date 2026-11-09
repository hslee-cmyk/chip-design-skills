"""D0a v7 필수 합성 단계 `import-time-high` (i)~(v) -- 측정 전용 모의(기대값은 구성이 정한다, 시제품 출력에서 가져오지 않는다).

    C:/Python314/python.exe -B gen_ith.py <작업 디렉터리(C:/g<n>/...)> <G1 시제품 tools/gates 디렉터리> <move_plan 시제품> <출력 JSONL>

가짜 N3.10: MOD1 lowmod.py / MOD2 lmod.py(= split이자 N3.10, s = 2) / MOD3 jmod.py(j = 3) / MOD4 kmod.py(k = 4). 분할 대상 = src.py(N3.10 밖) + lmod.py.
'대표 대상' A-1 토큰으로 배정을 고정한다(`lmod.py` → MOD2 전부, `g0` → MOD1, `Jcls`·`g` → MOD3, `f`·`TABLE` → MOD4).
단계마다 새 git 저장소 하나, 결과는 케이스마다 출력 JSONL에 append(WP-11).
"""
import json
import os
import shutil
import subprocess
import sys

WORK, GATES, TOOL, OUT = sys.argv[1:5]
A = "skills/analog-gmid-design/assets/"
PLAN = """# 가짜 계획

### N3.10 모듈 표

| ID | 파일 | 책임 | 대표 대상 |
|---|---|---|---|
| MOD1 | `lowmod.py` | 낮은 층 | `g0` |
| MOD2 | `lmod.py` | 위쪽 재수출 모듈 | `lmod.py` |
| MOD3 | `jmod.py` | 중간 | `Jcls`, `g` |
| MOD4 | `kmod.py` | 높은 층 | `f`, `TABLE` |

### N3.11 다음 절

본문.
"""
REG = """# 가짜 레지스트리

### src.py

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `f` | 가짜 | kmod.py | |
"""
LMOD = "C = 1\n"
FUT = "from __future__ import annotations\n\n"
STAGES = [
    # (id, src.py 본문, 기대 exit, 기대 import_time_high (unit, name) 목록) -- 구성으로 정한 기대값
    ("i-default-reads-L-const", "from lmod import C\n\n\ndef f(x=C):\n    return x\n", 1, [("src.py::f", "C")]),
    ("ii-body-reads-L-const", "from lmod import C\n\n\ndef f(x):\n    return x + C\n", 0, []),
    ("iii-a-annotation-no-future", "class Jcls:\n    def m(self):\n        return 1\n\n\ndef f(x: Jcls):\n    return x\n", 1,
     [("src.py::f", "Jcls")]),
    ("iii-b-annotation-with-future", FUT + "class Jcls:\n    def m(self):\n        return 1\n\n\ndef f(x: Jcls):\n    return x\n", 0, []),
    ("iv-dict-stmt-reads-mod-j", "def g():\n    return 1\n\n\nTABLE = {\"a\": g}\n", 1, [("src.py::TABLE", "g")]),
    ("v-dict-stmt-reads-below-s", "def g0():\n    return 1\n\n\nTABLE = {\"a\": g0}\n", 0, []),
]


def run(args, cwd=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True)
    if r.returncode != 0:
        raise SystemExit("실패 %s: %s" % (args, r.stderr.decode("utf-8", "replace")))
    return r


def wr(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(t)


if os.path.exists(OUT):
    os.remove(OUT)
ok_all = True
for sid, src, exp_exit, exp_ith in STAGES:
    d = os.path.join(WORK, sid)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)
    shutil.copytree(GATES, os.path.join(d, "tools", "gates"), ignore=shutil.ignore_patterns("redteam", "__pycache__"))
    wr(os.path.join(d, "docs", "plan.md"), PLAN)
    wr(os.path.join(d, "docs", "registry.md"), REG)
    wr(os.path.join(d, A, "src.py"), src)
    wr(os.path.join(d, A, "lmod.py"), LMOD)
    run(["git", "init", "-q", d])
    run(["git", "-C", d, "add", "-A"])
    run(["git", "-C", d, "-c", "user.name=kit", "-c", "user.email=kit@local", "commit", "-q", "-m", "stage"])
    r = subprocess.run([sys.executable, "-B", TOOL, "plan", "--root", d, "--plan", "docs/plan.md", "--registry", "docs/registry.md",
                        "--split", "src.py", "lmod.py"], capture_output=True)
    first = r.stdout.decode("utf-8").splitlines()[0] if r.stdout else ""
    try:
        o = json.loads(first)
    except ValueError:
        o = {"raw": first, "stderr": r.stderr.decode("utf-8", "replace")[-500:]}
    got = sorted((x["unit"], x["name"]) for x in o.get("import_time_high", []))
    others = {k: o.get(k) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch")}
    ok = r.returncode == exp_exit and got == sorted(exp_ith) and not any(others.values())
    ok_all &= ok
    rec = {"stage": sid, "ok": ok, "exit": r.returncode, "expected_exit": exp_exit, "import_time_high": o.get("import_time_high"),
           "expected": exp_ith, "other_lists": others, "assignment": o.get("assignment"), "verdict": o.get("verdict"),
           "error": o.get("error") or o.get("raw")}
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(sid, "ok" if ok else "MISMATCH", "exit", r.returncode, "ith", got)
print("ALL OK" if ok_all else "SOME MISMATCH")
