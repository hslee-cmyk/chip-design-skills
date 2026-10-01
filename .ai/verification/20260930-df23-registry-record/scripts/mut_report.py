"""mut_df23.py 결과 요약 + card 계약 5 (d) 분기 대조표. 사용: python -P mut_report.py <mut.jsonl> <reg_check.py(병합본)> <out.json>
분기 줄 범위는 병합본 4294048의 reg_check.py를 auditor가 읽어 정했다(아래 BRANCHES)."""
import collections, json, sys

mut_path, src_path, out = sys.argv[1:4]
src = open(src_path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
BRANCHES = [
    ("df23-section title (제목 줄 없음 -> 발견 하나만)", 246, 252),
    ("df23-section 목록 줄 없음", 269, 270),
    ("df23-path", 271, 272),
    ("df23-section measured_at 줄 없음", 273, 274),
    ("df23-measured-at", 275, 276),
    ("df23-section 8.1 (소절·표 머리 없음)", 278, 280),
    ("df23-total (§8.1 행 대조)", 282, 296),
    ("df23-section 8.2 (소절·표 머리 없음)", 298, 300),
    ("df23-function (§8.2 행 대조)", 302, 317),
    ("§ 절·소절 경계(_df23_rows_under, 절 끝)", 219, 258),
    ("§8.1·§8.2 기대값 계산(_df23_expected 묶음·DF·Phase)", 186, 216),
    ("ValueError (i) measured_at·items 없음", 172, 173),
    ("ValueError (ii) 항목 필드 없음", 183, 185),
    ("ValueError (iii) function 빈 값", 187, 188),
    ("ValueError (iv) 같은 파일 이름 다른 경로", 206, 208),
    ("ValueError (v) 동작 항목 plan_mapping 형식", 195, 198),
    ("CLI --df23-inventory 루트 밖 -> exit 2", 367, 370),
    ("CLI 목록 읽기·dict 아님 -> exit 2", 371, 375),
    ("CLI 발견 합치기", 376, 376),
    ("CLI 입력 오류 except -> exit 2", 377, 379),
    ("CLI 인자 --df23-inventory", 353, 353),
]
recs = [json.loads(l) for l in open(mut_path, encoding="utf-8")]
head = recs[0]
muts = [r for r in recs if "id" in r]
done = [r for r in recs if r.get("done")]
table = []
for name, a, b in BRANCHES:
    inb = [m for m in muts if not (m["lines"][1] < a or m["lines"][0] > b)]
    table.append({"branch": name, "lines": [a, b], "mutants": len(inb), "killed": sum(1 for m in inb if m["killed"]),
                  "survived": [m["id"] for m in inb if not m["killed"]]})
surv = []
for m in muts:
    if not m["killed"]:
        l0, l1 = m["lines"]
        surv.append({"id": m["id"], "lines": m["lines"], "src": [src[i - 1].strip() for i in range(l0, min(l1, l0 + 4) + 1)]})
res = {"target_defs": head["target_defs"], "mutants_planned": head["mutants"], "mutants_run": len(muts),
       "killed": sum(1 for m in muts if m["killed"]), "survived": len(surv),
       "timeouts": sum(1 for m in muts if m["exit"] == "timeout"),
       "by_op": dict(collections.Counter(m["op"] for m in muts)),
       "done": bool(done), "branches": table, "survivors": surv}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("mutants_planned", "mutants_run", "killed", "survived", "timeouts", "done")}))
for t in table:
    print(t["mutants"], t["killed"], len(t["survived"]), t["lines"], t["branch"].encode("unicode_escape").decode()[:0])
