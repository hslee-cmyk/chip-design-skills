"""out_check_test 합성 사례 생성기(픽스처).

    python -B cases.py <k1_stick_diagram.py> <출력 디렉터리>

사례마다 <출력>/<이름>/{v.json, out.jsonl}을 쓰고, <출력>/cases.tsv에 '이름<TAB>기대(새)<TAB>설명'을 적는다.
기대값은 card 35(20260930-v3-changed-stmt-scope) 계약 4·5와 review_kits_4a2 §1 m1~m4 문장으로 정한 것이다(피검 heredoc을 불러 만들지 않는다).
"""
import ast
import copy
import hashlib
import json
import os
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
SD = "skills/analog-gmid-design/assets/stick_diagram.py"
src = open(SRC, encoding="utf-8").read()
F = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "find_differential_pair_candidates"][0]
H = hashlib.sha256(ast.dump(F, annotate_fields=True, include_attributes=False, indent=None, show_empty=False).encode("utf-8")).hexdigest()

Q = "stick_diagram:find_differential_pair_candidates:"
MID = Q + "const-:body[1].body[0].iter.args[0].right"
K1, K2 = Q + "const+:body[1].body[0].iter.args[0].right", Q + "cmp:body[1].iter"
E1 = Q + "const+:body[1].body[0].body[0].value.args[0].elts[0]"
N1 = Q + "early_return:body[0]"
N2 = "stick_diagram:other:const+:body[0].value.right"
KD1, KD2 = SD + "::find_differential_pair_candidates", SD + "::other"


def rec(i, r, **kw):
    d = {"id": i, "result": r}
    d.update(kw)
    return d


def base():
    """post-35 정상: 대상 4(killed 2·exempt 1·survived 1), 대상 밖 2(두 def), 섞여 적힘."""
    recs = [rec(N1, "not_targeted"), rec(K1, "killed", exit=1), rec(E1, "exempt", bind_hash=H),
            rec(MID, "survived", tests=["t::a"]), rec(K2, "killed", exit=1), rec(N2, "not_targeted")]
    v = {"tool": "V3", "verdict": "FAIL", "targets": [SD], "mutants": 4, "killed": 2, "survivors": [MID],
         "survivor_bindings": ["%s@%s" % (MID, H)], "exempt_ignored": [], "not_targeted": 2,
         "targets_by_def": {KD1: {"targeted": 4, "not_targeted": 1, "deleted_statements": 0, "def_header_changed": False},
                            KD2: {"targeted": 0, "not_targeted": 1, "deleted_statements": 0, "def_header_changed": False}}}
    return v, recs


def pre35(v):
    v = dict(v)
    v.pop("not_targeted", None)
    v.pop("targets_by_def", None)
    return v


CASES = []


def case(name, exp, desc, v, recs, raw=None):
    CASES.append((name, exp, desc, v, recs, raw))


# ---- 통과해야 하는 것
v, r = base(); case("P01", "PASS", "post-35 정상(nt 2·exempt 1, 두 def)", v, r)
v, r = base(); r = [x for x in r if x["result"] != "not_targeted"]; v["not_targeted"] = 0
v["targets_by_def"][KD1]["not_targeted"] = 0; v["targets_by_def"][KD2]["not_targeted"] = 0
case("P02", "PASS", "post-35 nt 0", v, r)
v, r = base(); r = [x for x in r if x["result"] != "exempt"]; v["mutants"] = 3; v["targets_by_def"][KD1]["targeted"] = 3
case("P03", "PASS", "exempt 없음", v, r)
v, r = base(); case("P04", "PASS", "out에 빈 줄·공백 줄", v, r, raw="\n".join(json.dumps(x, ensure_ascii=False) for x in r[:3]) + "\n\n   \n" + "\n".join(json.dumps(x, ensure_ascii=False) for x in r[3:]) + "\n")
v, r = base()
for d in v["targets_by_def"].values():
    d["deleted_statements"] = None; d["def_header_changed"] = None
case("P05", "PASS", "sim35 모양(deleted_statements·def_header_changed null -- 보지 않음)", v, r)
v, r = base(); r[1]["exit"] = "timeout"; case("P06", "PASS", "killed 레코드 exit='timeout'(도구 실측 -- timeout은 result가 아님)", v, r)
v, r = base(); v["targets_by_def"] = {KD1: {"targeted": 4, "not_targeted": 2, "deleted_statements": 1, "def_header_changed": True}}
case("P07", "PASS", "targets_by_def 한 def에 몰아도 합만 맞으면 통과", v, r)
# 본질적 한계(대조로는 못 막음): 판정 JSON·out·targets_by_def를 함께 자기일관 위조
v, r = base(); r[1] = rec(K1, "not_targeted"); v["mutants"] = 3; v["killed"] = 1; v["not_targeted"] = 3
v["targets_by_def"][KD1]["targeted"] = 3; v["targets_by_def"][KD1]["not_targeted"] = 2
case("L17b", "PASS", "[한계] killed->nt 재분류, JSON·targets_by_def까지 함께 위조(review A17 확장)", v, r)

# ---- m3: 35 전 도구 출력은 이제 거부(설계상)
v, r = base(); r = [x for x in r if x["result"] != "not_targeted"]; case("A01", "FAIL", "[m3 설계상] pre-35 정상(nt·targets_by_def 키 없음)", pre35(v), r)
v, r = base(); del v["not_targeted"]; case("A03", "FAIL", "not_targeted 키 없음(targets_by_def 있음)", v, r)
v, r = base(); del v["targets_by_def"]; case("A03b", "FAIL", "[m3] targets_by_def 키 없음(not_targeted 있음)", v, r)
v, r = base(); r = [x for x in r if x["result"] != "not_targeted"]; v = pre35(v); v["not_targeted"] = 0
case("A31", "FAIL", "[m3] pre-35 + not_targeted 0만 있음(targets_by_def 없음)", v, r)
v, r = base(); case("A30", "FAIL", "pre-35 JSON + post-35 out", pre35(v), r)
# ---- 수 불일치
v, r = base(); v["not_targeted"] = 1; case("A04", "FAIL", "nt 값 1", v, r)
v, r = base(); v["not_targeted"] = 3; case("A05", "FAIL", "nt 값 3", v, r)
v, r = base(); v["not_targeted"] = "2"; case("A06", "FAIL", "nt \"2\"", v, r)
v, r = base(); v["not_targeted"] = None; case("A07", "FAIL", "nt null", v, r)
v, r = base(); v["mutants"] = 6; v["targets_by_def"][KD2]["targeted"] = 2; case("A08", "FAIL", "mutants = 전체 레코드 수(옛 의미)", v, r)
v, r = base(); del v["mutants"]; case("A09", "FAIL", "mutants 없음", v, r)
v, r = base(); v["mutants"] = "4"; case("A10", "FAIL", "mutants \"4\"", v, r)
# ---- id 중복·키 없음
v, r = base(); r[0]["id"] = K1; case("A11", "FAIL", "id 중복 nt<->대상", v, r)
v, r = base(); r[0]["id"] = MID; case("A12", "FAIL", "id 중복 nt<->생존", v, r)
v, r = base(); r[4]["id"] = K1; case("A13", "FAIL", "id 중복 대상<->대상", v, r)
v, r = base(); del r[1]["id"]; case("A14", "FAIL", "id 키 없음", v, r)
v, r = base(); del r[1]["result"]; case("A15", "FAIL", "result 키 없음", v, r)
# ---- 생존 숨김·위조
v, r = base(); r[3] = rec(MID, "not_targeted"); v["mutants"] = 3; v["not_targeted"] = 3
v["targets_by_def"][KD1]["targeted"] = 3; v["targets_by_def"][KD1]["not_targeted"] = 2
case("A16", "FAIL", "생존을 not_targeted로 숨김(수·targets_by_def 맞춤)", v, r)
v, r = base(); r[1] = rec(K1, "not_targeted"); v["mutants"] = 3; v["killed"] = 1; v["not_targeted"] = 3
case("A17a", "FAIL", "[m4] killed->nt 재분류, JSON 수만 맞추고 targets_by_def는 그대로", v, r)
v, r = base(); r[1] = rec(K1, "survived", tests=["t::a"]); v["killed"] = 1; case("A18", "FAIL", "생존 2(out)", v, r)
v, r = base(); r[2] = rec(E1, "survived", tests=["t::a"]); case("A25", "FAIL", "exempt->survived", v, r)
v, r = base(); v["killed"] = 3; case("A26", "FAIL", "killed 수 불일치", v, r)
v, r = base(); v["survivors"] = [MID, K1]; case("A33", "FAIL", "survivors 2", v, r)
# ---- m1: result 닫힌 집합
v, r = base(); r.insert(2, rec(Q + "x:body[0]", "foo")); v["mutants"] = 5; v["targets_by_def"][KD1]["targeted"] = 5
case("A19", "FAIL", "[m1] 미지 result \"foo\"(mutants·targets_by_def 맞춤)", v, r)
v, r = base(); r.insert(2, rec(Q + "x:body[0]", "timeout")); v["mutants"] = 5; v["targets_by_def"][KD1]["targeted"] = 5
case("A19b", "FAIL", "[m1] result \"timeout\"(도구는 result로 쓰지 않음)", v, r)
v, r = base(); r.insert(2, rec(Q + "x:body[0]", "baseline")); v["mutants"] = 5; v["targets_by_def"][KD1]["targeted"] = 5
case("A19c", "FAIL", "[m1] result \"baseline\"", v, r)
v, r = base(); r.insert(2, rec(Q + "x:body[0]", None)); v["mutants"] = 5; v["targets_by_def"][KD1]["targeted"] = 5
case("A19d", "FAIL", "[m1] result null", v, r)
v, r = base(); r[0]["result"] = "NOT_TARGETED"; case("A20", "FAIL", "\"NOT_TARGETED\"(대소문자)", v, r)
# ---- m2: 엄격 int
v, r = base(); r = [x for x in r if x["id"] != N2]; v["not_targeted"] = True; v["targets_by_def"][KD2]["not_targeted"] = 0
case("A21", "FAIL", "[m2] nt=True(레코드 1)", v, r)
v, r = base(); r = [x for x in r if x["id"] != N2]; v["not_targeted"] = 1.0; v["targets_by_def"][KD2]["not_targeted"] = 0
case("A22", "FAIL", "[m2] nt=1.0(레코드 1)", v, r)
v, r = base(); v["mutants"] = 4.0; case("A22b", "FAIL", "[m2] mutants=4.0", v, r)
v, r = base(); v["killed"] = 2.0; case("A22c", "FAIL", "[m2] killed=2.0", v, r)
v, r = base(); r = [x for x in r if x["id"] != K2]; v["killed"] = True; v["mutants"] = 3; v["targets_by_def"][KD1]["targeted"] = 3
case("A22d", "FAIL", "[m2] killed=True(killed 레코드 1)", v, r)
# ---- m4: not_targeted 레코드 모양
v, r = base(); r[0]["reason"] = "x"; case("A23", "FAIL", "[m4] nt 레코드에 여분 키", v, r)
v, r = base(); r[0] = {"result": "not_targeted", "id": N1}; case("A23b", "FAIL", "[m4] nt 레코드 키 순서 result,id(계약 5 순서 아님)", v, r)
v, r = base(); r[0]["id"] = 7; case("A23c", "FAIL", "[m4] nt 레코드 id가 문자열 아님", v, r)
# ---- m4: targets_by_def 교차 대조
v, r = base(); v["targets_by_def"][KD1]["targeted"] = 3; case("A34", "FAIL", "[m4] Σtargeted != mutants", v, r)
v, r = base(); v["targets_by_def"][KD2]["not_targeted"] = 0; case("A34b", "FAIL", "[m4] Σnot_targeted != not_targeted", v, r)
v, r = base(); v["targets_by_def"][KD1]["targeted"] = 5; v["targets_by_def"][KD2]["targeted"] = -1
case("A34c", "FAIL", "[m4] 음수로 합 맞춤", v, r)
v, r = base(); v["targets_by_def"] = []; case("A36", "FAIL", "[m4] targets_by_def가 dict 아님(list)", v, r)
v, r = base(); v["targets_by_def"] = None; case("A36b", "FAIL", "[m4] targets_by_def null", v, r)
v, r = base(); v["targets_by_def"] = {}; case("A36c", "FAIL", "[m4] targets_by_def {}(대상 4인데 합 0)", v, r)
v, r = base(); v["targets_by_def"][KD1]["targeted"] = 4.0; case("A37", "FAIL", "[m4] targeted float", v, r)
v, r = base(); v["targets_by_def"][KD2]["not_targeted"] = True; case("A37b", "FAIL", "[m4] not_targeted bool", v, r)
v, r = base(); del v["targets_by_def"][KD1]["targeted"]; case("A37c", "FAIL", "[m4] targeted 키 없음", v, r)
v, r = base(); v["targets_by_def"]["skills/x.py::other"] = v["targets_by_def"].pop(KD2); case("A39", "FAIL", "[m4] 키 경로가 targets 밖", v, r)
v, r = base(); v["targets_by_def"]["other"] = v["targets_by_def"].pop(KD2); case("A40", "FAIL", "[m4] 키에 '::' 없음", v, r)
v, r = base(); v["targets_by_def"][KD2] = [0, 1]; case("A41", "FAIL", "[m4] 항목이 dict 아님", v, r)
# ---- out 파일 결함
v, r = base(); case("A27", "PASS", "빈 줄 끝(P04와 같은 계열)", v, r, raw="\n".join(json.dumps(x, ensure_ascii=False) for x in r) + "\n\n\n")
v, r = base(); case("A28", "FAIL", "잘린 줄", v, r, raw="\n".join(json.dumps(x, ensure_ascii=False) for x in r) + "\n{\"id\": \"x\", \"res\n")
v, r = base(); case("A29", "FAIL", "빈 out", v, r, raw="")
v, r = base(); case("A35", "FAIL", "비객체 줄", v, r, raw="\n".join(json.dumps(x, ensure_ascii=False) for x in r) + "\n[1, 2]\n")
# ---- 기존 단정 회귀(변경 밖)
v, r = base(); v["verdict"] = "PASS"; case("A43", "FAIL", "verdict PASS(기존 단정)", v, r)
v, r = base(); v["survivor_bindings"] = ["%s@%s" % (MID, "0" * 64)]; case("A44", "FAIL", "묶기 해시 불일치(기존 단정)", v, r)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "cases.tsv"), "w", encoding="utf-8", newline="\n") as tsv:
    for name, exp, desc, v, recs, raw in CASES:
        d = os.path.join(OUT, name)
        os.makedirs(d)
        with open(os.path.join(d, "v.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(v, fh, ensure_ascii=False)
        with open(os.path.join(d, "out.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(raw if raw is not None else "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recs))
        tsv.write("%s\t%s\t%s\n" % (name, exp, desc))
print("cases", len(CASES), "hash", H[:16])
