"""WB-1 T-2 (interface card 20261104-wb1 §8 표지): 결과 notes 에 {"verdict": "recorded", "rule": "DEC-105 (2)",
"bin_rule_machine_dependent": [...], "midpoint_unverified_slices": [...]} 한 항목이 있다. 판정은 바뀌지 않는다.

oracle (손/식): 합성 LUT 의 모델 파일을 CRLF 바이트로 쓰면 meta 기록 sha X = sha256(CRLF 바이트) 는 선언(LF 값)에 없지만 LF(b) 는 선언에 있다
-> 통과하고 (세트, 상대 경로)가 machine_dependent 에 든다(interface §1 표). 세트 이름 = 슬라이스는 파일 이름, 나머지 "cap". 정렬된 목록.
LUT 는 슬라이스 {100, 200} x nmos·pmos 4장 + cap (모델 파일 kind 마다 하나) -> 기대 쌍 6개.
**미작성(보고)**: `midpoint_unverified_slices` 의 값((nmos, 200) 나열) 단언은 합성 중점 파일 형식(L_source·격자 정합)이 card 에 없어 쓰지 않았다. 키 존재만 단언한다.
"""
import hashlib
from pathlib import Path

from .conftest import circuit_c, theta_r4c
from .wb1_flow import bins_case

KINDS = ("nmos", "pmos")


def note_of(fr):
    hit = [dict(n) for n in fr.notes if dict(n).get("rule") == "DEC-105 (2)"]
    assert len(hit) == 1, [dict(n).get("rule") for n in fr.notes]
    return hit[0]


def pairs(value):
    return [tuple(p) for p in value]


def test_find_front_note_records_bin_rule_without_changing_verdict(tmp_path):
    from gmid_engine.search import find_front
    case = bins_case(tmp_path, circuit_c(), eval_budget=40)
    fr = find_front(case.sctx, [theta_r4c()])
    n = note_of(fr)
    assert n["verdict"] == "recorded"
    assert pairs(n["bin_rule_machine_dependent"]) == []              # LF 모델 파일: X ∈ 선언 -> 기계 의존 0
    assert "midpoint_unverified_slices" in n
    assert len(fr.notes) >= 2                                        # 다른 기록(예산·미측정 항목)은 그대로 있다


def test_find_front_note_lists_machine_dependent_model_files(tmp_path, monkeypatch):
    from gmid_engine.search import find_front
    import sizing.wb1_toy as wb1_toy
    real = wb1_toy.write_toy_bins
    converted = []

    def crlf_write(*a, **k):
        tb = real(*a, **k)
        for kind, rel in tb.rels.items():
            p = Path(tb.pdk_root) / rel
            data = p.read_bytes().replace(b"\n", b"\r\n")
            p.write_bytes(data)
            tb.shas[kind] = hashlib.sha256(data).hexdigest()         # meta 가 닫힌 dict 를 읽으므로 같은 객체를 갱신한다
            converted.append(rel)
        return tb
    monkeypatch.setattr(wb1_toy, "write_toy_bins", crlf_write)
    case = bins_case(tmp_path, circuit_c(), eval_budget=40)
    assert len(converted) == 2                                       # 호출 >= 1 (공허 통과 방지)
    fr = find_front(case.sctx, [theta_r4c()])
    n = note_of(fr)
    rels = {k: "models/toy_%s.spice" % k for k in KINDS}
    want = sorted([(f, rels[k]) for k in KINDS for f in ("r4_%s.npz" % k, "r4_%s_w200.npz" % k)] + [("cap", rels[k]) for k in KINDS])
    assert pairs(n["bin_rule_machine_dependent"]) == want
    assert n["verdict"] == "recorded"
