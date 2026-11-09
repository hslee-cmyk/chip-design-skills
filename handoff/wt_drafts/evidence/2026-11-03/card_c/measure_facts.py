"""XRUN-F1 card C spec card 초안의 사실 문장 재측정(엔진 실행 없음, git 읽기 전용).

실행: PYTHONIOENCODING=utf-8 C:/Python314/python.exe measure_facts.py
결과: 같은 폴더 facts.txt(줄마다 바로 씀 -- 중간에 죽어도 남는다).
대상: master(계획 v6.38.7, c8ecc4e7), integ/it12, design/v115.
"""
import json
import os
import re
import subprocess

R = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
E = "skills/analog-gmid-design/gmid_engine"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facts.txt")


def git(*args):
    return subprocess.run(["git", "-C", R, *args], capture_output=True).stdout.decode("utf-8", "replace")


out = open(OUT, "w", encoding="utf-8")


def emit(*parts):
    line = " ".join(str(p) for p in parts)
    print(line)
    out.write(line + "\n")
    out.flush()


emit("# master", git("rev-parse", "master").strip())
emit("# design/v115", git("rev-parse", "design/v115").strip(), "commits ahead", git("rev-list", "--count", "master..design/v115").strip())
emit("# plan/v6388 commits ahead", git("rev-list", "--count", "master..plan/v6388").strip())
emit("# integ/it12", git("rev-parse", "integ/it12").strip(), "merge-base", git("merge-base", "master", "integ/it12").strip())

emit("\n## 1. 예산 자리 전수 (master, E/search, tests·md 제외)")
PAT = {
    "eval_budget": r"\beval_budget\b",
    "_budget_stop": r"\b_budget_stop\b",
    "_exhausted": r"\b_exhausted\b",
    "_e_total": r"\b_e_total\b",
    "_halton_probe": r"\b_halton_probe\b",
    "evaluate(": r"\bevaluate\(",
    "fd_jacobian(": r"\bfd_jacobian\(",
    "residual_probe(": r"\bresidual_probe\(",
}
for name, pat in PAT.items():
    emit("###", name)
    txt = git("grep", "-n", "-E", pat.replace(r"\b", r"\b"), "master", "--", E + "/search", E + "/convergence", E + "/pipeline", ":!*/tests/*", ":!*.md")
    for line in txt.splitlines():
        emit("  ", line.replace("master:" + E + "/", "")[:150])

emit("\n## 2. open_run 호출(엔진·test)")
emit("engine def/call:", len([l for l in git("grep", "-n", r"\bopen_run()", "master", "--", E, ":!*/tests/*", ":!*.md").splitlines() if "=" in l and '"""' not in l]))
tests = git("grep", "-c", r"open_run(", "master", "--", E + "/tests")
emit("test files:", len(tests.splitlines()), "test occurrences:", sum(int(l.rsplit(":", 1)[1]) for l in tests.splitlines()))

emit("\n## 3. fd_jacobian 직접 호출 test")
txt = git("grep", "-c", r"\bfd_jacobian(", "master", "--", E + "/tests")
for line in txt.splitlines():
    emit("  ", line.replace("master:" + E + "/", ""))

emit("\n## 4. 이름 충돌 (새 이름이 master 엔진·test에 있는가)")
for name in ("search_ceiling", "search_stop", "FdBudgetShortfall", "_helpers_ceiling", "bind_total", "index_bound", "time_budget_below_search_reserve"):
    emit("  ", name, len(git("grep", "-l", "-w", name, "master", "--", E).splitlines()))

emit("\n## 5. integ/it12 와 겹침(card C 파일)")
base = git("merge-base", "master", "integ/it12").strip()
names = git("diff", "--name-only", base, "integ/it12").splitlines()
emit("integ/it12 변경 파일 수:", len(names))
CARD_C = [E + "/search/" + f for f in ("fd_jacobian.py", "kernel.py", "layer0_center.py", "slsqp_outer.py", "l_bin_search.py", "eps_sweep.py", "residual_probe.py",
                                       "gate_run.py", "find_front.py", "start_points.py", "search_context.py", "s3_index.py", "open_run.py", "CONTRACT.md")]
CARD_C += [E + "/_module_map.py", E + "/tests/search/test_fd_jacobian.py", E + "/tests/integration/test_g10_no_recompute_9circuits.py"]
for f in CARD_C:
    if f in names:
        stat = git("diff", "--numstat", base, "integ/it12", "--", f).strip().split("\t")
        emit("  겹침", f.replace(E + "/", ""), "+" + stat[0], "-" + stat[1])

emit("\n## 6. 회로별 n_θ (기록, 엔진 실행 안 함)")
fact = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1a_pg/m1_current_facts.jsonl"
n_theta = {}
with open(fact, encoding="utf-8") as f:
    for l in f:
        o = json.loads(l)
        if "circuit" in o and "n_theta" in o:
            n_theta[o["circuit"]] = o["n_theta"]
summary = json.load(open(R + "/.ai/verification/xrunf1b/b_summary.json", encoding="utf-8"))
emit("회로 n_θ  2n_θ  R=2n_θ E_total(E_B=40) 첫묶음(시작 평가 뒤 남은 39 >= 2n_θ?)  as-built커널수(card B 판정)")
for c, n in sorted(n_theta.items()):
    k = (summary.get(c, {}).get("head") or {}).get("kernel_calls")
    emit("  ", c, n, 2 * n, 2 * n, 40 + 2 * n, "시작" if 39 >= 2 * n else "시작 안 함", k)
lib = [p.rsplit("/", 1)[1].replace(".topology.json", "") for p in git("ls-files", "skills/analog-gmid-design/assets/library").splitlines() if p.endswith(".topology.json") and "/_" not in p]
emit("library:", len(lib), "n_θ 기록 없음:", [c for c in lib if c not in n_theta])

emit("\n## 7. 표 대조: 계획 줄")
P = git("show", "master:docs/01-plan/features/gain-budget-gmid-sizing.plan.md").splitlines()
for i, l in enumerate(P, 1):
    if l.startswith("| E-26 ") or l.startswith("| E-25 "):
        emit("P:%d" % i, l[:260])
for n in (1563, 1623):
    m = re.search(r"XRUN-F1 card C.{0,160}", P[n - 1])
    emit("P:%d" % n, m.group(0) if m else P[n - 1][:200])

emit("\n## 8. GL-1 상태")
emit("판정 기록:", [p for p in git("ls-files", ".ai/verification").splitlines() if re.search(r"gl-?1", p, re.I)])
emit("structure_checks G-8 흔적:", len(git("grep", "-n", "G-8", "master", "--", E + "/tests/structure/structure_checks.py").splitlines()))
emit("scan_shared_calls 저장소 안:", [p for p in git("ls-files", "tools").splitlines() if "scan_shared" in p])

emit("\n## 9. design/v115 card C 표지와 LA-1a 순서")
D = git("show", "design/v115:docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md").splitlines()
for i, l in enumerate(D, 1):
    if l.startswith("| **C** 예산 결함"):
        for m in re.finditer(r".{50}대상 소멸.{40}", l):
            emit("D40(v115):%d" % i, m.group(0))
    if "생성자 필수 인자로 더하고" in l:
        m = re.search(r".{30}생성자 필수 인자로 더하고.{60}", l)
        emit("D40(v115):%d" % i, m.group(0))
HC = git("show", "master:docs/01-plan/features/headroom-chain.plan.md").splitlines()
for n in (367, 531, 551):
    emit("HC:%d" % n, HC[n - 1][:200])
out.close()
