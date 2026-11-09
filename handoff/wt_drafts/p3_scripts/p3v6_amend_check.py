"""p3_doc_amendments.md의 '현재 → 새 문안' 블록을 격리 복제본 사본에 적용해 본다(읽기 전용 측정, 저장소 무변경).

    C:/Python314/python.exe -B p3v6_amend_check.py <복제본> <amendments md> <작업 디렉터리> <출력 json>

확인: (1) '현재' 블록이 해당 파일의 그 줄과 정확히 같다 (2) 교체 뒤 N3.10 표가 파싱되고(mod_table 10행, read_section_table 4열·10행)
(3) '대표 대상' 백틱 식별자 중 두 행 이상에 걸린 이름 0, 이동 대상 세 이름이 기대 행에만 있다 (D-19 두 안 각각)
(4) import_layering --root가 교체된 계획서로 exit 0 (5) 10-test-separation §5.6 표가 여전히 21행.
"""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT, AMD, WORK, OUT = sys.argv[1:5]
sys.path.insert(0, os.path.join(ROOT, "tools", "gates"))
import role_paths as rp  # noqa: E402
import import_layering as il  # noqa: E402

text = open(AMD, encoding="utf-8").read()
blocks = re.findall(r"```\n(.*?)\n```", text, flags=re.S)
blocks = [b for b in blocks if not b.startswith("…")]
PLAN = "docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
C00 = "docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md"
T10 = "docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md"
# 블록 순서(문서 순서): a_cur, a_ga, a_na, b_cur, b_new, c_cur, c_new, d_cur, d_new, s2_cur, s2_new, s3_cur, s3_new,
#                       103_cur, 103_new, 431_cur, 431_new, 250_cur, 250_new, 252_cur, 252_new
assert len(blocks) >= 21, len(blocks)
spec = [  # (파일, 줄, 현재 블록 idx, 새 블록 idx -- 'a'는 변형별)
    (PLAN, 522, 0, "a"), (PLAN, 523, 3, 4), (PLAN, 526, 5, 6), (PLAN, 528, 7, 8), (PLAN, 534, 9, 10), (PLAN, 687, 11, 12),
    (C00, 103, 13, 14), (C00, 431, 15, 16), (T10, 250, 17, 18), (T10, 252, 19, 20),
]
res = {"blocks": len(blocks), "current_match": {}, "variants": {}}
for f, ln, ci, _ in spec:
    lines = open(os.path.join(ROOT, f), encoding="utf-8").read().split("\n")
    res["current_match"]["%s:%d" % (os.path.basename(f), ln)] = (lines[ln - 1] == blocks[ci])

for var, ai in (("D19-ga", 1), ("D19-na", 2)):
    d = os.path.join(WORK, var)
    if os.path.exists(d):
        shutil.rmtree(d)
    for f in (PLAN, C00, T10):
        os.makedirs(os.path.dirname(os.path.join(d, f)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), os.path.join(d, f))
    os.makedirs(os.path.join(d, "skills", "analog-gmid-design"), exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "skills", "analog-gmid-design", "assets"),
                    os.path.join(d, "skills", "analog-gmid-design", "assets"),
                    ignore=shutil.ignore_patterns("tests", "__pycache__"))
    for f, ln, ci, ni in spec:
        p = os.path.join(d, f)
        lines = open(p, encoding="utf-8").read().split("\n")
        assert lines[ln - 1] == blocks[ci], (f, ln)
        lines[ln - 1] = blocks[ai if ni == "a" else ni]
        open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    plan = open(os.path.join(d, PLAN), encoding="utf-8").read()
    mt = il.mod_table(plan)
    hdr, rows = rp.read_section_table(plan, "### N3.10 ")
    rep = hdr.index("대표 대상")
    where = {}
    for r in rows:
        for t in re.findall(r"`([^`]+)`", r[rep]):
            if re.fullmatch(r"[A-Za-z_*][A-Za-z0-9_*]*", t):
                where.setdefault(t, []).append(r[0].strip())
    multi = {k: v for k, v in where.items() if len(v) > 1}
    lay = subprocess.run([sys.executable, "-B", os.path.join(ROOT, "tools", "gates", "import_layering.py"), "--root", d],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    t10 = open(os.path.join(d, T10), encoding="utf-8").read()
    h10, r10 = rp.read_section_table(t10, "### 5.6 ")
    res["variants"][var] = {
        "mod_table_n": len(mt), "n310_cols": len(hdr), "n310_rows": len(rows),
        "multi_row_tokens": multi,
        "load_topology": where.get("load_topology"), "validate_theta_declaration_order": where.get("validate_theta_declaration_order"),
        "optimize_full_circuit_budget": where.get("optimize_full_circuit_budget"), "rail_declaration": where.get("rail_declaration"),
        "import_layering_exit": lay.returncode, "t10_56_header": h10, "t10_56_rows": len(r10),
    }
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
