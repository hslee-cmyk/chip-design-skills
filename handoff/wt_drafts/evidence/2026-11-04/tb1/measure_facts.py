"""TB-1 spec card 사실 문장 재측정(엔진 실행 없음, git 읽기 전용). 결과 = 같은 폴더 facts.txt.
엔진 인용 용도 = 재작성 범위만(원칙 8). 대상 = master, integ/it12.
"""
import os
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


for ref in ("master", "integ/it12"):
    emit("#", ref, git("rev-parse", ref).strip())
    emit("\n## 옛 이름 소비자", ref)
    for name in ("OrderHints", "NO_ORDER_HINTS", "order_hints", "TIE_ROOT", "w4_root", "TIE_KRUSKAL", "writer_edge", "dc_tie_breaks"):
        emit("###", name)
        for line in git("grep", "-n", "-w", name, ref, "--", E).splitlines():
            emit("  ", line.replace(ref + ":" + E + "/", "")[:150])
    emit("\n## 새 이름 충돌", ref)
    for name in ("theta_class", "ThetaClass", "THETA_CLASS_WRITER", "dependent_member", "dc_colour_not_unique", "test_theta_class",
                 "BRANCH_COLOUR_NOT_UNIQUE", "structure_fact_mismatch", "structure_fact_orphan"):
        lines = git("grep", "-n", "-w", name, ref, "--", E, ":!*.md").splitlines()
        emit("  ", name, len(lines), "|", " ; ".join(x.replace(ref + ":" + E + "/", "")[:80] for x in lines[:4]))
    emit("\n## concept 상수", ref)
    for line in git("grep", "-n", "-E", r"CONCEPT_[A-Z_]+ *=", ref, "--", E + "/graph", ":!*.md").splitlines():
        emit("  ", line.replace(ref + ":" + E + "/", "")[:130])
    emit("\n## dc_writer_plan 호출자", ref)
    for line in git("grep", "-n", r"dc_writer_plan(", ref, "--", E).splitlines():
        emit("  ", line.replace(ref + ":" + E + "/", "")[:130])
    emit("\n## test 파일별 order_hints·OrderHints·w4_root·input_tie 계수", ref)
    for line in git("grep", "-c", "-E", r"OrderHints|ORDER_HINTS|order_hints|w4_root|TIE_ROOT", ref, "--", E + "/tests").splitlines():
        emit("  ", line.replace(ref + ":" + E + "/", ""))

emit("\n## integ/it12 겹침")
for f in ("sizing/writer_plan.py", "sizing/s2_values.py", "sizing/kernel_context.py", "sizing/__init__.py", "sizing/CONTRACT.md", "_module_map.py",
          "tests/sizing/test_writer_plan.py", "tests/sizing/conftest.py", "tests/sizing/test_kernel_run.py", "tests/sizing/test_s2_values.py", "tests/sizing/test_size_and_seal.py"):
    s = git("diff", "--numstat", "master...integ/it12", "--", E + "/" + f).strip()
    emit("  ", f, s.split("\t")[:2] if s else "겹침 0")

emit("\n## _module_map sizing 층 (integ/it12)")
txt = git("show", "integ/it12:" + E + "/_module_map.py").split("\n")
on = False
for line in txt:
    if line.strip() == '"sizing",':
        on = True
    if on:
        emit(line[:170])
        if line.startswith("    ),"):
            break

emit("\n## structure.json 사실 파일(library)")
for line in git("ls-tree", "--name-only", "master", "skills/analog-gmid-design/assets/library/").splitlines():
    if line.endswith(".structure.json"):
        emit("  ", line.rsplit("/", 1)[-1])

emit("\n## S1v 필드·stage·roles")
for pat in (r"class Block\b", r"roles", r"\bstage\b"):
    for line in git("grep", "-n", "-E", pat, "integ/it12", "--", E + "/graph/s1v_values.py").splitlines()[:8]:
        emit("  ", line.replace("integ/it12:" + E + "/", "")[:150])
emit("\n## 구조 색·정준 위치")
for line in git("grep", "-n", "-E", "canonical_position|canonical_pos|정준 위치", "integ/it12", "--", E + "/graph", E + "/sizing", ":!*.md").splitlines()[:14]:
    emit("  ", line.replace("integ/it12:" + E + "/", "")[:170])
emit("\n## build_s1v vs build_kernel_context 순서(S1v가 lift 전에 있는지)")
for line in git("grep", "-n", "-E", r"build_s1v|lift_s1|s1v|views", "integ/it12", "--", E + "/sizing/s2_lift.py", E + "/sizing/kernel_context.py", E + "/sizing/s2_values.py").splitlines()[:16]:
    emit("  ", line.replace("integ/it12:" + E + "/", "")[:170])
emit("\n## KernelContext 호출자의 S1 인자")
for line in git("grep", "-n", r"build_kernel_context(", "integ/it12", "--", E, ":!*/tests/*", ":!*.md").splitlines():
    emit("  ", line.replace("integ/it12:" + E + "/", "")[:170])
emit("\n## tests build_kernel_context 호출 계수(master)")
rows = git("grep", "-c", r"build_kernel_context(", "master", "--", E + "/tests").splitlines()
emit("파일", len(rows), "합", sum(int(x.rsplit(":", 1)[1]) for x in rows))
