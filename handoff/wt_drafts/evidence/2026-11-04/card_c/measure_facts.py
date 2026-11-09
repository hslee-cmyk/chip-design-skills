"""XRUN-F1 card C spec card 사실 문장 재측정(엔진 실행 없음, git 읽기 전용, 저장소 쓰기 0).

실행: PYTHONIOENCODING=utf-8 C:/Python314/python.exe measure_facts.py
결과: 같은 폴더 facts.txt(줄마다 바로 씀). 대상: master, integ/it12, fix/o181-tests, design/eo1(있으면).
엔진 인용 용도 = 재작성 범위만(원칙 8).
"""
import os
import re
import subprocess

R = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
E = "skills/analog-gmid-design/gmid_engine"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facts.txt")
out = open(OUT, "w", encoding="utf-8")


def git(*args):
    return subprocess.run(["git", "-C", R, *args], capture_output=True).stdout.decode("utf-8", "replace")


def emit(*parts):
    out.write(" ".join(str(p) for p in parts) + "\n")
    out.flush()


emit("# master", git("rev-parse", "master").strip())
emit("# integ/it12", git("rev-parse", "integ/it12").strip(), "behind master by", git("rev-list", "--count", "integ/it12..master").strip())
emit("# E/search 변경 c8ecc4e7..master:", git("diff", "--stat", "c8ecc4e7", "master", "--", E + "/search").strip().splitlines()[-1:] or "0")
emit("# 엔진 전체 변경 c8ecc4e7..master:", git("diff", "--stat", "c8ecc4e7", "master", "--", E).strip().splitlines()[-1:] or "0")

emit("\n## 1. 예산 자리 전수 (master, tests·md 제외)")
for name, pat in {
    "eval_budget": r"\beval_budget\b", "_budget_stop": r"\b_budget_stop\b", "_e_total": r"\b_e_total\b",
    "EvalBudget": r"\bEvalBudget\b", "evaluate(": r"\bevaluate\(", "fd_jacobian(": r"\bfd_jacobian\(",
    "open_run(": r"\bopen_run\(", "scipy_minimize": r"\bscipy_minimize\b", "layer0_start|sweep_front": r"\b(layer0_start|sweep_front)\(",
}.items():
    emit("###", name)
    txt = git("grep", "-n", "-E", pat, "master", "--", E + "/search", E + "/convergence", E + "/pipeline", ":!*/tests/*", ":!*.md")
    for line in txt.splitlines():
        emit("  ", line.replace("master:" + E + "/", "")[:170])

emit("\n## 2. 같은 자리 (integ/it12 -- 줄 어긋남 확인)")
for name, pat in {"_budget_stop": r"\b_budget_stop\b", "fd_jacobian(": r"\bfd_jacobian\(", "evaluate(": r"\bevaluate\("}.items():
    emit("###", name)
    txt = git("grep", "-n", "-E", pat, "integ/it12", "--", E + "/search", ":!*/tests/*", ":!*.md")
    for line in txt.splitlines():
        emit("  ", line.replace("integ/it12:" + E + "/", "")[:170])
emit("### integ/it12 겹침(card C 파일)")
for f in ("search/fd_jacobian.py", "search/kernel.py", "search/CONTRACT.md", "_module_map.py", "search/find_front.py", "search/layer0_center.py",
          "search/slsqp_outer.py", "search/l_bin_search.py", "search/eps_sweep.py", "search/residual_probe.py", "search/start_points.py",
          "search/gate_run.py", "search/s3_index.py", "search/open_run.py", "search/search_values.py", "search/search_context.py",
          "tests/search/test_fd_jacobian.py", "tests/integration/test_g10_no_recompute_9circuits.py"):
    s = git("diff", "--numstat", "master...integ/it12", "--", E + "/" + f).strip()
    emit("  ", f, s.split("\t")[:2] if s else "겹침 0")

emit("\n## 3. test 호출 계수 (master)")
for pat, label in ((r"\bfd_jacobian(", "fd_jacobian 직접 호출"), (r"open_run(", "open_run 호출"), (r"eval_budget", "eval_budget"), (r"\bE_B\b", "E_B")):
    txt = git("grep", "-c", "-E" if pat == r"\bE_B\b" else "-e", pat, "master", "--", E + "/tests")
    rows = txt.splitlines()
    emit(label, "파일", len(rows), "합", sum(int(x.rsplit(":", 1)[1]) for x in rows))
    if len(rows) <= 4:
        for x in rows:
            emit("  ", x.replace("master:" + E + "/", ""))

emit("\n## 4. 새 이름 충돌 (master·integ/it12 엔진·test, md 제외)")
for name in ("search_ceiling", "search_stop", "FdBudgetShortfall", "_helpers_ceiling", "gate_reserve", "e_total", "open_bound", "close_bound",
             "index_bound", "time_budget_below_search_reserve", "test_search_ceiling", "test_search_stop", "test__helpers_ceiling"):
    for ref in ("master", "integ/it12"):
        txt = git("grep", "-n", "-w", name, ref, "--", E, ":!*.md")
        lines = txt.splitlines()
        emit("  ", name, ref, len(lines), "|", " ; ".join(x.replace(ref + ":" + E + "/", "")[:70] for x in lines[:3]))
emit("### 기존 test 파일 존재(master)")
for f in ("test_search_ceiling.py", "test_search_stop.py", "test__helpers_ceiling.py", "test_s3_index.py", "test_find_front.py", "test_gate_run.py",
          "test_start_points.py", "test_l_bin_search.py", "test_eps_sweep.py", "test_residual_probe.py", "test_slsqp_outer.py", "test_layer0_center.py", "test_kernel.py"):
    emit("  ", f, "있음" if git("ls-tree", "master", E + "/tests/search/" + f).strip() else "없음")
emit("  test_g10:", git("ls-tree", "master", E + "/tests/integration/test_g10_no_recompute_9circuits.py").strip()[:30] or "없음")
emit("### test glob 충돌: search_ 머리 test 이름 / conftest 수집 규칙")
emit(git("grep", "-n", "-E", "NOT_SEARCHED|LIBRARY|circuits *=|CIRCUITS", "master", "--", E + "/tests/integration/test_g10_no_recompute_9circuits.py").replace("master:" + E + "/", "")[:900])
emit("--- fix/o181-tests")
emit(git("grep", "-n", "-E", "NOT_SEARCHED|LIBRARY|circuits *=|CIRCUITS", "fix/o181-tests", "--", E + "/tests/integration/test_g10_no_recompute_9circuits.py").replace("fix/o181-tests:" + E + "/", "")[:900])

emit("\n## 5. 선행 card 상태 (판정 기록·브랜치)")
for vid in ("gl1", "it12", "it1", "eo1", "xrunf1b", "20261103-xrunf1c"):
    emit("  .ai/verification/" + vid + ".json", "있음" if git("ls-tree", "master", ".ai/verification/" + vid + ".json").strip() else "없음")
emit("  G-8 structure_checks master:", len(git("grep", "-n", "scan_shared_calls", "master", "--", E).splitlines()))
emit("  branches:", " ".join(x.strip(" +*") for x in git("branch", "--list", "*eo1*", "*gl1*", "*gl-1*", "*it12*", "*o181*").splitlines()))
emit("  fix/o181-tests ancestor of master:", subprocess.run(["git", "-C", R, "merge-base", "--is-ancestor", "fix/o181-tests", "master"]).returncode == 0)
emit("  EO-1 범위 4 새 파일 off_judged master:", bool(git("ls-tree", "master", E + "/search/off_judged.py").strip()))

emit("\n## 6. 계획·design 줄 (master)")
P = git("show", "master:docs/01-plan/features/gain-budget-gmid-sizing.plan.md").split("\n")
for key in ("| E-26 |", "XRUN-F1 card C(평가 예산 상한", "| XRUN-F1 card C | design 40", "**XRUN-F1 card C와**", "| HC-S | headroom-chain"):
    for i, line in enumerate(P, 1):
        if key in line:
            emit("P:%d" % i, line[:320])
D = git("show", "master:docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md").split("\n")
for key in ("open_bound", "DF-1", "DF-2", "DF-3", "DF-4", "DF-5", "DF-6"):
    hits = [i for i, line in enumerate(D, 1) if key in line]
    emit("D40", key, hits[:12])
H = git("show", "master:docs/02-design/features/headroom-chain.design.md").split("\n")
emit("HC card C 인용:", [i for i, line in enumerate(H, 1) if "card C" in line][:12])
G = git("show", "master:docs/02-design/features/gain-budget-gmid-sizing.42-gap-checklist.design.md").split("\n")
for i, line in enumerate(G, 1):
    if re.match(r"\| D-XR", line):
        emit("42:%d" % i, line[:260])
