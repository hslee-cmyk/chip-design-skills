# R7 실측 -- 봉인 6(벌크 역바이어스, 위반 크기 > tol_V 이면 거부) 대안 (가) '경계 0 고정, 엔진 값 위반 = 크기 무관 E-0'의 동작 변화 표본.
# 입력 = o200_q5/q5_engine_rows.jsonl(library 6회로 엔진 평가 소자점, terminal_voltages 꼴 vgs·vds·vsb -- 선언 방향 양수 규약).
# source–bulk 순방향 = vsb < 0, drain–bulk 순방향 = vds + vsb < 0. 띠 (0, tol_V] 안 위반 점 수 = (가)로 바뀌는 점 수. 결과 = r7_bulk_band.txt(덮어씀).
import json, pathlib, collections
HERE = pathlib.Path(__file__).parent
R = [json.loads(l) for l in pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-31/o200_q5/q5_engine_rows.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
sb = [r for r in R if r["vsb"] < 0]
db = [r for r in R if r["vds"] + r["vsb"] < 0]
band = [r for r in sb + db if max(-r["vsb"], -(r["vds"] + r["vsb"])) <= r["tol"]]
out = [f"# R7 벌크 순방향 표본 (q5_engine_rows, {len(R)} 소자점, 회로 {sorted(set(r['circuit'] for r in R))})",
       f"source–bulk 순방향(vsb < 0) {len(sb)}점, drain–bulk 순방향(vds + vsb < 0) {len(db)}점, 그중 띠 (0, tol_V] 안 {len(band)}점",
       f"vsb 최솟값 {min(r['vsb'] for r in R)!r} (출력 '-0.000'은 음의 0 표기), 회로별 {dict(collections.Counter(r['circuit'] for r in sb + db))}",
       "한계: 봉인 표본 회로 6/13(나머지 7 = 단계 A stopped·review_needed 또는 봉인 평가 0, q5_engine_circuits.jsonl). bulk가 선언 레일이 아닌 회로(erfc M19·M20·M21, O-174)는 단계 A stopped라 표본 0."]
(HERE / "r7_bulk_band.txt").write_bytes(("\n".join(out) + "\n").encode("utf-8"))
print("\n".join(out))
