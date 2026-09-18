# -*- coding: utf-8 -*-
"""00-common design §14 DoD 측정: `.ai/verification/_schema.json`이 올바른 기록은 통과시키고
스키마 밖 필드·형식 위반은 **실제로 거부하는지** 잰다(WP-02 -- 통과보다 거부를 먼저 확인).

문서 단계의 측정이다. 로컬에 설치된 jsonschema를 쓴다(프로젝트 의존성 추가 아님, merge gate의
사용 여부는 U-38). date-time 형식 검사는 FormatChecker가 해당 형식 검사기를 가진 경우에만 발동하므로
그 발동 여부를 따로 적는다.

결과는 stdout이 아니라 같은 이름 `.txt`에 append한다(WP-11).
"""
import copy
import io
import json
import os

import jsonschema

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCHEMA = os.path.join(ROOT, ".ai", "verification", "_schema.json")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"

H40 = "a" * 40
H64 = "b" * 64
CHECKS = {f"V{i}": {"verdict": "N/A", "basis": "도입 전(Phase 1)"} for i in range(1, 11)}
BASE = {
    "id": "20260918-sample", "spec_card": "docs/02-design/specs/20260918-sample.spec.md",
    "base_commit": H40, "test_commit": H40, "code_commit": H40, "checks": CHECKS,
    "reproduced_numbers": [{"name": "wall_clock_s", "value": 1.0, "command": "python x.py"}],
    "approvals": [], "auditor_run": {"time": "2026-09-18T10:00:00+09:00", "worktree": "../wt/x",
                                     "commands": ["pytest"]},
}


def rec(**kw):
    d = copy.deepcopy(BASE)
    for k, v in kw.items():
        if v is DEL:
            d.pop(k, None)
        else:
            d[k] = v
    return d


DEL = object()
RG = dict(evidence_type="red-green", red={"test_ids": ["t::a"], "failure_hashes": [H64]})
EQ = dict(evidence_type="equivalence", equivalence={"commands": ["pytest"], "outputs_hash": H64})
TO = dict(evidence_type="test-only", code_commit=None)

VALID = [("red-green", rec(**RG)), ("equivalence", rec(**EQ)), ("test-only", rec(**TO))]


def with_check(d, key, val):
    d = copy.deepcopy(d)
    d["checks"][key] = val
    return d


def drop_check(d, key):
    d = copy.deepcopy(d)
    d["checks"].pop(key)
    return d


REJECT = [
    ("최상위 스키마 밖 필드", rec(**RG, extra_field=1)),
    ("checks.V1 안 스키마 밖 필드", with_check(rec(**RG), "V1", {"verdict": "PASS", "basis": "x", "note": 1})),
    ("checks에 V11", with_check(rec(**RG), "V11", {"verdict": "PASS", "basis": "x"})),
    ("checks V10 누락", drop_check(rec(**RG), "V10")),
    ("verdict 값 SKIP", with_check(rec(**RG), "V3", {"verdict": "SKIP", "basis": "x"})),
    ("basis 빈 문자열", with_check(rec(**RG), "V3", {"verdict": "PASS", "basis": ""})),
    ("red-green인데 red 없음", rec(evidence_type="red-green")),
    ("red-green에 equivalence 동반", rec(**RG, equivalence=EQ["equivalence"])),
    ("red-green인데 code_commit null", rec(**{**RG, "code_commit": None})),
    ("equivalence인데 equivalence 없음", rec(evidence_type="equivalence")),
    ("test-only인데 code_commit 있음", rec(evidence_type="test-only")),
    ("test-only에 red 동반", rec(**TO, red=RG["red"])),
    ("red 안 스키마 밖 필드", rec(evidence_type="red-green",
                             red={"test_ids": ["t"], "failure_hashes": [H64], "x": 1})),
    ("red.test_ids 빈 배열", rec(evidence_type="red-green", red={"test_ids": [], "failure_hashes": [H64]})),
    ("failure_hash 대문자", rec(evidence_type="red-green", red={"test_ids": ["t"], "failure_hashes": ["B" * 64]})),
    ("base_commit 짧은 해시", rec(**{**RG, "base_commit": "a" * 7})),
    ("evidence_type 미지 값", rec(evidence_type="manual")),
    ("id 형식 위반", rec(**{**RG, "id": "sample"})),
    ("spec_card 경로 위반", rec(**{**RG, "spec_card": "specs/20260918-x.md"})),
    ("reproduced_numbers 원소 밖 필드", rec(**{**RG, "reproduced_numbers": [
        {"name": "a", "value": 1, "command": "c", "unit": "s"}]})),
    ("reproduced_numbers value 문자열", rec(**{**RG, "reproduced_numbers": [
        {"name": "a", "value": "1", "command": "c"}]})),
    ("approvals 원소 형식 위반", rec(**{**RG, "approvals": ["ok"]})),
    ("auditor_run 밖 필드", rec(**{**RG, "auditor_run": {**BASE["auditor_run"], "host": "x"}})),
    ("필수 auditor_run 누락", rec(**{**RG, "auditor_run": DEL})),
    # v1.1 추가 -- review21 C-08 독립 케이스(파이썬 re의 $가 끝 개행 앞에서도 맞는 문제 등)
    ("id 끝 개행", rec(**{**RG, "id": "20260918-s\n"})),
    ("base_commit 끝 개행", rec(**{**RG, "base_commit": H40 + "\n"})),
    ("spec_card 끝 개행", rec(**{**RG, "spec_card": BASE["spec_card"] + "\n"})),
    ("basis 공백뿐", with_check(rec(**RG), "V1", {"verdict": "PASS", "basis": "   "})),
    ("approvals 중복", rec(**{**RG, "approvals": ["20260918-a", "20260918-a"]})),
    ("red.test_ids 중복", rec(evidence_type="red-green",
                              red={"test_ids": ["t", "t"], "failure_hashes": [H64, H64]})),
]
# 스키마로는 못 막고 로더 추가 검사(00-common §8.1)가 막는 것 -- 스키마 통과가 설계대로다
LOADER = [
    ("value NaN(로더 3)", rec(**{**RG, "reproduced_numbers": [
        {"name": "a", "value": float("nan"), "command": "c"}]})),
    ("없는 날짜 id(로더 2)", rec(**{**RG, "id": "20261399-s"})),
    ("test_ids·hashes 길이 불일치(로더 4)", rec(evidence_type="red-green",
                                        red={"test_ids": ["t", "u"], "failure_hashes": [H64]})),
]
FORMAT_CASE = ("auditor_run.time 형식 위반", rec(**{**RG, "auditor_run": {**BASE["auditor_run"],
                                                                         "time": "어제"}}))


def main():
    schema = json.load(io.open(SCHEMA, encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    lines = ["=== 00-common §14: _schema.json 통과·거부 측정 ===",
             f"jsonschema {jsonschema.__version__ if hasattr(jsonschema, '__version__') else '?'}"]
    ok_pass = 0
    for name, d in VALID:
        errs = list(v.iter_errors(d))
        ok_pass += not errs
        lines.append(f"  통과 기대  {name:34s} -> {'통과' if not errs else '거부: ' + errs[0].message[:80]}")
    ok_rej = 0
    for name, d in REJECT:
        errs = list(v.iter_errors(d))
        ok_rej += bool(errs)
        lines.append(f"  거부 기대  {name:34s} -> {'거부' if errs else '**통과(결함)**'}")
    for name, d in LOADER:
        errs = list(v.iter_errors(d))
        lines.append(f"  로더 담당  {name:34s} -> {'스키마 통과(설계대로, 로더가 거부)' if not errs else '스키마가 거부'}")
    fname, fd = FORMAT_CASE
    ferrs = list(v.iter_errors(fd))
    lines.append(f"  형식 검사  {fname:34s} -> {'거부' if ferrs else '통과 -- date-time 형식 검사기가 이 환경에 없다. 로더가 따로 검사해야 한다'}")
    lines += [f"결과: 통과 기대 {ok_pass}/{len(VALID)}, 거부 기대 {ok_rej}/{len(REJECT)}, "
              f"date-time 형식 {'강제됨' if ferrs else '미강제'}", ""]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
