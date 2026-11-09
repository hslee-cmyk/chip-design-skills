# 검증 43 (7): v3 전수 grep(o200_v3/grep_conduction.py)이 놓칠 수 있는 동의어로 보충 grep.
# 패턴: 차단 | 누설 | cut-off/cutoff | 약반전 | subthreshold | 소수 가지 | I0 | 꺼진 쪽 | leak
# 각 적중 줄이 v3 hits 의 (파일:행) 집합에 없으면 '새 줄'로 기록한다. 출력 = v43_grep_supp.txt (Python append)
import re, pathlib
ROOTS = [pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386/docs/01-plan/features"),
         pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features")]
UD = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md")
V3 = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-31/o200_v3/grep_conduction_hits.txt")
seen = set(re.findall(r"^\[([^\]]+)\]", V3.read_text(encoding="utf-8"), re.M))
RX = re.compile(r"차단|누설|cut-?off|약반전|subthreshold|소수 가지|꺼진 쪽|leak", re.I)
NUM = re.compile(r"tol_V(?!Dsat)|tol_I|분해능|허용오차|dc_tol_v|ε|I_off|floor|바닥|abstol|reltol")
files = [f for r in ROOTS for f in sorted(r.glob("*.md")) if "history" not in f.name and "verilog" not in f.name] + [UD]
out = open(pathlib.Path(__file__).with_suffix(".txt"), "a", encoding="utf-8")
n_all = n_new = n_new_num = 0
for f in files:
    for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        m = RX.search(line)
        if not m:
            continue
        n_all += 1
        key = f"{f.name}:{i}"
        if key in seen:
            continue
        n_new += 1
        num = bool(NUM.search(line))
        n_new_num += num
        if num:
            s = max(0, m.start() - 200); e = min(len(line), m.end() + 200)
            out.write(f"[{key}] NEW+NUM ...{line[s:e]}...\n")
out.write(f"# 합계: 적중 줄 {n_all}, v3 hits 밖 {n_new}, 그중 수치 양 같은 줄 {n_new_num}\n")
out.close()
print(n_all, n_new, n_new_num)
