"""judge_p3.py e6(및 m-b 판정 줄 보장) 자체 시험 -- v4r(2026-10-07, review_phase3_dod_v4.md S1·m-a·m-b), v4s(review_phase3_dod_v4r.md n-1~n-3).

    python -B judge_e6_selftest.py [<결과 파일>] [<비교용 옛 judge 경로>]

입력은 검토 v4 §2 합성 30가지(R01~R30, 검토 문구로 재구성 -- 원본 파일은 검토 모래상자와 함께 지워짐)와
작성자 §8.v4 13가지(A01~A13)에 m-b 보강 6가지(M01~M05b)를 더한 것. v4s: 검토 v4r의 실패 사례 -- 삭제된 허용 id
(D01~D03, n-1), 거부 확인 깨진 조건 이름(N01~N04, n-3), e01 `findings` 목록 아님(G01~G07, n-2, 가짜 `GC` 모듈) -- 를 더했다. 입력이 두 실행 사이에서 어긋나는지(같은 결함이
허용 없는 실행에도 나오는지)가 판정을 가르므로, 원문이 모호한 경우는 두 변형(…a 어긋남 / …b 두 실행 같음)을 둔다.
기대값은 검토 §3 (c) 규칙에서 나온 것이다: 거부 확인 = exit 1·`changed` ⊇ 허용 두 id(중복 없음)·두 id를 뺀 발견이
허용 있는 실행과 같음, 아니면 INVALID; 성립하면 허용 있는 실행으로 PASS/FAIL. v4s(n-1): 허용 있는 실행이 이미 FAIL 모양
(exit ≠ 0 또는 비지 않은 발견)이면 거부 확인 불성립이어도 FAIL(그래서 R16a·R30a·A11a·A12a·A13a 기대가 INVALID → FAIL).
결과는 케이스마다 결과 파일에 덧붙인다(중간에 끊겨도 남는다). 하나라도 어긋나면 exit 1.
임시 파일은 tempfile(TMP 아래)에만 쓴다.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
JUDGE = os.path.join(HERE, "judge_p3.py")
PY = sys.executable
KINDS = ("move-set", "move-rejected", "changed", "lost", "rebind", "future", "import-dup", "stmt-order", "order", "shim", "cache")
A1 = "workspaces/run_harness.py::run"
A2 = "skills/analog-gmid-design/assets/gmid_design_pipeline.py::run_gmid_design_pipeline"
X = "skills/analog-gmid-design/assets/stick_diagram.py::outside_declared"
L = {"unit": "skills/analog-gmid-design/assets/stick_diagram.py::gone"}
RB = {"unit": "skills/analog-gmid-design/assets/stick_diagram.py::reader", "name": "x"}


def F(drop=(), **over):
    d = {k: [] for k in KINDS if k not in drop}
    for k, v in over.items():
        d[k.replace("_", "-")] = v
    return {"findings": d}


OK_N = F(changed=[A1, A2])
MISSING = object()   # 파일을 만들지 않는다


# (id, 허용 있음 출력, 허용 있음 exit, 허용 없음 출력, 허용 없음 exit, 기대 판정, 기대 문구 조각 또는 None, 옛 판정기 대비 메모)
# 출력: dict → JSON 한 줄, str → 그대로, MISSING → 파일 없음
CASES = [
    ("R01", F(), "0", F(changed=[A2, A1]), "1", "PASS", None, ""),
    ("R02", F(), "0", F(changed=[{"unit": A1, "k": 1}, {"unit": A2, "j": 2}]), "1", "PASS", None, ""),
    ("R03", F(), "0", F(changed=[" " + A1, A2]), "1", "INVALID", "거부 확인", ""),
    ("R04", F(), "0", F(changed=[A1 + "\n", A2]), "1", "INVALID", "거부 확인", ""),
    ("R05", F(), "0", F(changed=[A1, A2, X]), "1", "INVALID", "거부 확인", "허용 없는 쪽에만 셋째 id -- 두 실행 어긋남"),
    ("R06", F(), "0", '{"error": "ERROR boom"}', "2", "INVALID", "거부 확인", ""),
    ("R07", F(), "0", OK_N, "2", "INVALID", "거부 확인", ""),
    ("R08", F(), "0", MISSING, "", "INVALID", "거부 확인", ""),
    ("R09", None, None, None, None, "INVALID", "판정기 예외", "옛 판정기: TypeError traceback, 판정 줄 없음(m-b)"),
    ("R10", F(), "0", OK_N, " 1", "INVALID", "거부 확인", ""),
    ("R11", F(), "0", F(changed=[A1, A1, A2]), "1", "INVALID", "거부 확인", "옛 판정기 PASS(m-a 중복)"),
    ("R12", F(), "0", F(changed=[{"x": A1}, A2]), "1", "INVALID", "모양 모름", ""),
    ("R13", F(), "0", F(changed=[A1]), "1", "INVALID", "거부 확인", ""),
    ("R14", F(), "0", F(), "1", "INVALID", "거부 확인", ""),
    ("R15", F(), "0", F(), "0", "INVALID", "거부 확인", "공허 허용"),
    ("R16a", F(newkind=[1]), "1", OK_N, "1", "FAIL", "거부 확인 불성립(나머지 발견 다른 종류 ['newkind'])",
     "v4s n-1: 두 실행 어긋나도 허용 있는 실행이 FAIL 모양 → FAIL"),
    ("R16b", F(newkind=[1]), "1", F(changed=[A1, A2], newkind=[1]), "1", "FAIL", "'newkind': 1", "두 실행 같음 → 옛과 같은 FAIL"),
    ("R17", F(drop=("import-dup",)), "0", OK_N, "1", "INVALID", "없는 종류 키", ""),
    ("R18", F(), "0", F(drop=("import-dup",), changed=[A1, A2]), "1", "INVALID", "거부 확인", ""),
    ("R19", F(lost=[L]), "1", F(changed=[A1, A2], lost=[L]), "1", "FAIL", "'lost': 1", "S1: 옛 INVALID → FAIL"),
    ("R20", F(changed=[X]), "1", F(changed=[A1, A2, X]), "1", "FAIL", "'changed': 1", "S1: 옛 INVALID → FAIL"),
    ("R21", F(), "1", OK_N, "1", "FAIL", "exit=1", ""),
    ("R22", '{"error": "ERROR boom"}', "2", OK_N, "1", "INVALID", "check 출력 없음", ""),
    ("R23a", F(lost=3), "1", OK_N, "1", "INVALID", "값 모양 모름", "옛: TypeError traceback(m-b)"),
    ("R23b", F(), "0", F(changed=[A1, A2], lost=3), "1", "INVALID", "값 모양 모름", "옛: TypeError traceback(m-b) -- 허용 없는 쪽"),
    ("R24", '{"findings": []}', "0", OK_N, "1", "INVALID", "check 출력 없음", ""),
    ("R25", "WARNING something\n" + json.dumps(F()), "0", OK_N, "1", "PASS", None, "마지막 줄 JSON"),
    ("R26", F(), "0", F(changed=A1), "1", "INVALID", "모양 모름", ""),
    ("R27", F(), "0", F(changed={"unit": A1}), "1", "INVALID", "모양 모름", ""),
    ("R28", "", "0", OK_N, "1", "INVALID", "check 출력 없음", ""),
    ("R29", F(), "0", F(changed=["gmid_design_pipeline.py::run_gmid_design_pipeline", "run_harness.py::run"]), "1",
     "INVALID", "거부 확인", "A 기준 표기(m-c) -- fail-closed"),
    ("R30a", F(lost=[L], rebind=[RB]), "1", OK_N, "1", "FAIL", "나머지 발견 다른 종류 ['lost', 'rebind']",
     "v4s n-1: det3 모양(허용 있는 쪽에만 lost·rebind) -- 허용 있는 실행이 FAIL 모양 → FAIL"),
    ("R30b", F(lost=[L], rebind=[RB]), "1", F(changed=[A1, A2], lost=[L], rebind=[RB]), "1", "FAIL", "'lost': 1, 'rebind': 1",
     "두 실행 같음 → FAIL"),
    # 작성자 §8.v4 13가지
    ("A01", F(), "0", F(changed=[{"unit": A1}, {"unit": A2}]), "1", "PASS", None, ""),
    ("A02", F(), "0", F(changed=[A1, A2]), "1", "PASS", None, ""),
    ("A03", F(), "0", F(changed=[A2]), "1", "INVALID", "거부 확인", ""),
    ("A04", F(), "0", F(), "0", "INVALID", "거부 확인", ""),
    ("A05", F(), "0", F(changed=[A1, A2]), "0", "INVALID", "거부 확인", ""),
    ("A06", F(), "0", F(changed=[[A1], A2]), "1", "INVALID", "모양 모름", ""),
    ("A07", F(), "0", F(changed=[A1, A2], rebind=[RB]), "1", "INVALID", "거부 확인", ""),
    ("A08", MISSING, "", OK_N, "1", "INVALID", "check 출력 없음", ""),
    ("A09", F(), "0", MISSING, "", "INVALID", "거부 확인", ""),
    ("A10", F(drop=("import-dup",)), "0", OK_N, "1", "INVALID", "없는 종류 키", ""),
    ("A11a", F(lost=[L], rebind=[RB]), "1", OK_N, "1", "FAIL", "거부 확인 불성립", "R30a와 같음(v4s n-1)"),
    ("A11b", F(lost=[L], rebind=[RB]), "1", F(changed=[A1, A2], lost=[L], rebind=[RB]), "1", "FAIL", "'rebind': 1", ""),
    ("A12a", F(import_dup=[{"unit": X}]), "1", OK_N, "1", "FAIL", "거부 확인 불성립", "v4s n-1: 두 실행 어긋남이어도 FAIL 모양 → FAIL"),
    ("A12b", F(import_dup=[{"unit": X}]), "1", F(changed=[A1, A2], import_dup=[{"unit": X}]), "1", "FAIL", "'import-dup': 1", ""),
    ("A13a", F(zzz=[1]), "1", OK_N, "1", "FAIL", "거부 확인 불성립", "v4s n-1: 두 실행 어긋남이어도 FAIL 모양 → FAIL"),
    ("A13b", F(zzz=[1]), "1", F(changed=[A1, A2], zzz=[1]), "1", "FAIL", "'zzz': 1", ""),
    # v4s 검토 v4r n-1: 삭제된 허용 id(D0a 계약 4 180행 -- `changed` 단위가 아니고 두 실행 모두 `lost`)
    ("D01", F(lost=[{"unit": A1}]), "1", F(changed=[A2], lost=[{"unit": A1}]), "1", "FAIL", "허용 id 빠짐 ['" + A1 + "']",
     "검토 v4r V07: 옛 INVALID → FAIL"),
    ("D02", F(lost=[{"unit": A1}, {"unit": A2}]), "1", F(lost=[{"unit": A1}, {"unit": A2}]), "1", "FAIL", "'lost': 2",
     "허용 두 id 모두 삭제: 옛 INVALID → FAIL"),
    ("D03", F(), "0", F(changed=[A2]), "1", "INVALID", "허용 id 빠짐 ['" + A1 + "']",
     "대조: 허용 있는 실행이 PASS 모양이면 여전히 INVALID(공허 PASS 막기)"),
    # v4s 검토 v4r n-3: INVALID 줄이 깨진 조건 이름을 말한다
    ("N01", F(), "0", F(changed=[A1, A2], lost=[L]), "1", "INVALID", "나머지 발견 다른 종류 ['lost']",
     "검토 v4r V02 모양: 옛 줄은 조건을 말하지 않음"),
    ("N02", F(), "0", OK_N, "0", "INVALID", "exit≠1(exit=0)", ""),
    ("N03", F(), "0", F(changed=[A1, A1, A2]), "1", "INVALID", "changed 중복 1", ""),
    ("N04", F(), "0", F(changed=[A1, A2, X]), "1", "INVALID", "changed 차이(허용 두 id 밖) 거부 쪽만 ['" + X + "']", ""),
]


def put(tmp, name, obj):
    p = os.path.join(tmp, name)
    if obj is MISSING:
        return p
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False))
    return p


def run(judge, args, env=None):
    e = dict(os.environ, PYTHONIOENCODING="utf-8")
    if env is not None:
        e = dict(env, PYTHONIOENCODING="utf-8")
    r = subprocess.run([PY, "-B", judge] + args, capture_output=True, text=True, encoding="utf-8", env=e)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    return r.returncode, lines, ("Traceback" in r.stderr)


def first_verdict(lines, eid):
    for ln in lines:
        parts = ln.split(" ", 2)
        if len(parts) >= 2 and parts[0] == eid and parts[1].split("(")[0] in ("PASS", "FAIL", "INVALID", "PENDING"):
            return parts[1].split("(")[0], ln
    return None, None


def main():
    outp = sys.argv[1] if len(sys.argv) > 1 else None
    old = sys.argv[2] if len(sys.argv) > 2 else None
    fails = []

    def log(s):
        print(s)
        if outp:
            with open(outp, "a", encoding="utf-8") as fh:
                fh.write(s + "\n")

    with tempfile.TemporaryDirectory(prefix="e6st_") as tmp:
        for cid, mo, mrc, no, nrc, exp, frag, memo in CASES:
            if mo is None:   # R09: 인자 2개만
                args = ["e6", put(tmp, cid + "_m.json", F()), "0"]
            else:
                args = ["e6", put(tmp, cid + "_m.json", mo), mrc, put(tmp, cid + "_n.json", no), nrc]
            _, lines, tb = run(JUDGE, args)
            got, line = first_verdict(lines, "E6")
            nverd = sum(1 for ln in lines if first_verdict([ln], "E6")[0])
            ok = (got == exp and (frag is None or frag in (line or "")) and not tb and nverd == 1)
            oldv = ""
            if old:
                _, ol, otb = run(old, args)
                ov, _ = first_verdict(ol, "E6")
                oldv = " | 옛 %s%s" % (ov or "판정 줄 없음", " +traceback" if otb else "")
            log("%s %-5s %-7s 기대 %-7s%s | %s%s" % ("OK " if ok else "BAD", cid, got, exp, oldv, line, (" | " + memo) if memo else ""))
            if not ok:
                fails.append(cid)

        # m-b 보강: 명령·인자·환경이 깨져도 판정 줄이 남는가
        cards = put(tmp, "cards.txt", "".join("b c MOD%d s\n" % i for i in range(8)))
        sdir = os.path.join(tmp, "S"); os.makedirs(sdir)
        v3 = {"defs": [], "mutants": 0, "move_rejected": {}, "not_targeted": 0, "targets_by_def": {}, "moved": []}
        for i in range(8):
            put(sdir, "v3_MOD%d.json" % i, v3); put(sdir, "v3_MOD%d.exit" % i, "0"); put(sdir, "chk_MOD%d.exit" % i, "0")
            put(sdir, "chk_MOD%d.json" % i, F(lost=3) if i == 3 else F())
        env_nogc = {k: v for k, v in os.environ.items() if k != "GC"}
        extra = [
            ("M01", [], None, "E?", "INVALID", "명령 모름"),
            ("M02", ["zz"], None, "E?", "INVALID", "명령 모름"),
            ("M03", ["e4"], None, "E4", "INVALID", "판정기 예외"),
            ("M04", ["e2", sdir, cards, "0"], None, "E2", "FAIL", "값 모양 모름"),
            ("M05", ["e01", "x", "0", "y"], env_nogc, "E0", "INVALID", "판정기 예외"),
            ("M05b", ["e01", "x", "0", "y"], env_nogc, "E1", "INVALID", "판정기 예외"),
        ]
        for cid, args, env, eid, exp, frag in extra:
            _, lines, tb = run(JUDGE, args, env)
            got, line = first_verdict(lines, eid)
            ok = got == exp and frag in (line or "") and not tb
            log("%s %-5s %-7s 기대 %-7s | %s" % ("OK " if ok else "BAD", cid, got, exp, line))
            if not ok:
                fails.append(cid)
        ntot = len(CASES) + len(extra)

        # v4s 검토 v4r n-2: e01 `findings`가 목록이 아니면 E1 INVALID(가짜 GC 모듈, N3.10 10행). E0·E1 판정 줄 각 정확히 1개
        gc = os.path.join(tmp, "gc"); os.makedirs(gc)
        put(gc, "import_layering.py", "def mod_table(text):\n    return {'m%d' % i: i for i in range(1, 11)}\n")
        plan = put(tmp, "plan.md", "N3.10\n")
        pres = ["m%d" % i for i in range(1, 11)]
        env_gc = dict(os.environ, GC=gc)
        g_cases = [   # (id, H findings, F2 base findings, 기대 E1, 기대 문구, 메모)
            ("G01", "", [1], "INVALID", "목록이 아니다(str", "검토 v4r: 옛 E1 PASS(len('')=0)"),
            ("G02", {}, [1], "INVALID", "목록이 아니다(dict", "검토 v4r: 옛 E1 PASS"),
            ("G03", 0, [1], "INVALID", "목록이 아니다(int", "검토 v4r W08"),
            ("G04", [], "x", "INVALID", "F2 base `findings`가 목록이 아니다(str", "검토 v4r: 옛 거부 확인 성립(len('x')=1) → PASS"),
            ("G05", [], {"a": 1}, "INVALID", "F2 base `findings`가 목록이 아니다(dict", "옛 PASS(len=1)"),
            ("G06", [], 0, "INVALID", "F2 base `findings`가 목록이 아니다(int", "검토 v4r W10"),
            ("G07", [], [1], "PASS", "거부 확인 F2 base findings=1", "대조: 정상"),
        ]
        for cid, hf, ff, exp, frag, memo in g_cases:
            lay = put(tmp, cid + "_layer.json", {"present": pres, "findings": hf})
            f2 = put(tmp, cid + "_f2.json", {"present": pres, "findings": ff})
            args = ["e01", lay, "0", plan, f2, "1"]
            _, lines, tb = run(JUDGE, args, env_gc)
            got0, _ = first_verdict(lines, "E0")
            got, line = first_verdict(lines, "E1")
            n0 = sum(1 for ln in lines if first_verdict([ln], "E0")[0])
            n1 = sum(1 for ln in lines if first_verdict([ln], "E1")[0])
            ok = got0 == "PASS" and got == exp and frag in (line or "") and not tb and n0 == 1 and n1 == 1
            oldv = ""
            if old:
                _, ol, otb = run(old, args, env_gc)
                ov, _ = first_verdict(ol, "E1")
                oldv = " | 옛 %s%s" % (ov or "판정 줄 없음", " +traceback" if otb else "")
            log("%s %-5s %-7s 기대 %-7s%s | %s | %s" % ("OK " if ok else "BAD", cid, got, exp, oldv, line, memo))
            if not ok:
                fails.append(cid)
        ntot += len(g_cases)

    log("SELFTEST %s %d/%d%s" % ("PASS" if not fails else "FAIL", ntot - len(fails), ntot,
                                 "" if not fails else " 어긋남 " + ",".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
