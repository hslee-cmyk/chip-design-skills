#!/usr/bin/env python3
"""(dec, 2026-10-07) b26_1_carry.sh check 단계 V5 heredoc 사례 -- [B26-1 V5] 두 경로(B34 test + P9 test) 수용, 그 밖 거부(fail-closed).

    python v5_cases.py <v5_t1_c247a76.json> <출력 디렉터리>

입력 = 실제 1차 T1 c247a76에 base 판(6df4bd7) weakening_diff.py를 모래상자 복제본에서 돌린 출력(2026-10-07, /c/g437 -- 측정 뒤 삭제).
기대값은 사용자 승인 범위([B26-1 V5] 질문 문안: 대상 경로 = P9 test + B34 test, U5: P9 두 시그니처 test)와 carry 계약(base_check.json diff_hash 하나,
재실행 = diff-hash)으로 정한다 -- 피검을 불러 만들지 않는다. 사례마다 <이름>/bc.json·rr.json·dh.txt, cases.tsv(이름, 기대, 이유 문구, 설명).
"""
import copy, json, os, sys

src, out = sys.argv[1:3]
R = json.load(open(src, encoding="utf-8"))
A = "skills/analog-gmid-design/assets/tests/contracts/"
B34, P9, OTHER = A + "test_b34_grammar_explicit.py", A + "test_dup_kcl_edges.py", A + "test_b26pre_existing_paths.py"
assert R["diff_paths"] == [B34, P9] and R["verdict"] == "FAIL" and R["approved"] is False, R["diff_paths"]
os.makedirs(out)
rows = []


def case(name, exp, why, desc, rr, bc=None, dh=None):
    d = os.path.join(out, name); os.makedirs(d)
    json.dump(rr, open(os.path.join(d, "rr.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"V5": rr if bc is None else bc}, open(os.path.join(d, "bc.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(d, "dh.txt"), "w").write((dh or rr["diff_hash"]) + "\n")
    rows.append((name, exp, why, desc))


def mut(f):
    r = copy.deepcopy(R); f(r); return r


H2 = "0" * 64
case("v5_two_paths", "PASS", "", "실제 T1 출력: diff_paths [B34, P9], P9 두 시그니처 단위 + B34 <module> 리터럴", R)
case("v5_third_path", "STOP", "base_check.json diff_paths", "세 번째 경로(b26pre test) 발견 추가",
     mut(lambda r: (r["findings"].append({"path": OTHER, "unit": "test_x", "pattern": "비교 완화", "detail": ""}), r.__setitem__("diff_paths", sorted([B34, P9, OTHER])))))
case("v5_p9_only", "STOP", "base_check.json diff_paths", "P9 한 경로뿐(B34 발견 없음 -- 두 경로 기록의 해시와 다름)",
     mut(lambda r: (r.__setitem__("findings", [f for f in r["findings"] if f["path"] == P9]), r.__setitem__("diff_paths", [P9]))))
case("v5_order", "STOP", "", "rr diff_paths 순서 뒤집힘(bc는 정상)", mut(lambda r: r.__setitem__("diff_paths", [P9, B34])), bc=R)
case("v5_b34_unit", "STOP", "B34 발견이 <module> 리터럴 변경만이 아니다", "B34 발견 단위가 test 함수",
     mut(lambda r: [f.__setitem__("unit", "test_b34_c8_restored_values_equal_fresh_process") for f in r["findings"] if f["path"] == B34]))
case("v5_b34_extra", "STOP", "B34 발견이 <module> 리터럴 변경만이 아니다", "B34에 비교 완화 발견 하나 더",
     mut(lambda r: r["findings"].append({"path": B34, "unit": "<module>", "pattern": "비교 완화", "detail": ""})))
case("v5_p9_units", "STOP", "P9 발견 단위가 두 시그니처 test가 아니다", "P9 시그니처 단위 하나 빠짐",
     mut(lambda r: r.__setitem__("findings", [f for f in r["findings"] if f["unit"] != "test_kcl_and_matching_edges_signature_unchanged"])))
case("v5_hash", "STOP", "diff_hash 불일치", "diff-hash(dh) 값이 다름", R, dh=H2)
with open(os.path.join(out, "cases.tsv"), "w", encoding="utf-8", newline="\n") as fh:
    for r in rows:
        fh.write("\t".join(x or "-" for x in r) + "\n")   # 빈 칸은 '-'(bash read IFS 탭은 연속 탭을 하나로 접는다)
print("V5 사례 %d" % len(rows))
