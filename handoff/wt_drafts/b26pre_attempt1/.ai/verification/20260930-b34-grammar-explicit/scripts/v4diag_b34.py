"""V4 (1)/(2) 가시성 진단(브리프 3.1 계약 8 모양, 재현 b34_kit/proto_066/v4diag.py와 같은 내부 함수):
T의 새 test 파일 모든 test 함수의 판정 문장마다 피검 호출 수(왼쪽·오른쪽, 공유)를 base 판 test_lint 내부로 잰다.
또 계약 5·6의 `== []` 원형(분할 전) 변형을 같은 도구 (2)에 넣어 결과를 비교한다(B60 확인).
사용: PYTHONPATH=<캐시> python -P v4diag_b34.py <복제본>"""
import ast, json, sys
import test_lint as tl

root = sys.argv[1]
iface = open(root + "/docs/02-design/specs/20260930-b34-grammar-explicit.interface.md", encoding="utf-8").read()
subjects = {s for _, s in tl.read_card_symbols(iface)}
src = open(root + "/skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py", encoding="utf-8").read()
sd = open(root + "/skills/analog-gmid-design/assets/stick_diagram.py", encoding="utf-8").read()
print("subjects:", len(subjects))
for n, fn in tl.find_test_functions(ast.parse(src)):
    for line, a, b, hooked in tl._assert_pairs(fn.body, subjects):
        if a is None:
            continue
        ka, kb = tl._call_keys(a, subjects), tl._call_keys(b, subjects)
        if ka or kb:
            print("%s line %d: left=%d %s right=%d shared=%d -> (1) %s" % (
                n, line, len(ka), sorted({k[0] for k in ka}), len(kb), len(ka & kb), "FAIL" if ka & kb else "no hit"))


def lint(s, name):
    f = next(x for nm, x in tl.find_test_functions(ast.parse(s)) if nm == name)
    return [(r["rule"], r["line"], r["output"]) for r in tl.lint_function(s, f, {sd: subjects}, subjects)]


print("T c5:", lint(src, "test_b34_c5_no_gate_devices_unchanged"))
print("T c6:", lint(src, "test_b34_c6_theta_without_findings"))
# 분할 전 원형(`== []` 한 문장) 변형: 같은 파일에서 해당 두 줄 쌍만 바꾼다.
orig = src.replace("    found = stick_diagram.audit_theta_root_direction(fx, None)\n    assert isinstance(found, list)\n    assert len(found) == 0\n",
                   "    assert stick_diagram.audit_theta_root_direction(fx, None) == []\n")
orig = orig.replace("    assert isinstance(found_a, list)\n    assert len(found_a) == 0\n", "    assert found_a == []\n")
orig = orig.replace("    assert isinstance(found_signed, list)\n    assert len(found_signed) == 0\n", "    assert found_signed == []\n")
assert orig.count("== []\n") >= 3, "variant not built"
print("== [] variant c5:", lint(orig, "test_b34_c5_no_gate_devices_unchanged"))
print("== [] variant c6:", lint(orig, "test_b34_c6_theta_without_findings"))
