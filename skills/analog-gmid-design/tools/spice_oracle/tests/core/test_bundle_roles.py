"""OP-3 모델 묶음 비교 규칙 (i)(ii)(iii) + 역할 옆 선언 -- interface §6 '묶음' T3-6a~j, '옆 선언', design §12.5.

oracle (a): 서로 다른 64자 해시와 구성으로 정해진 묶음(규칙 문장 (i) 부분집합, (ii) 정의 파일 sha 포함, (iii) 보조 입력 sha 일치를
그대로 대입). 파일 바이트가 필요한 (iii)은 test 가 쓴 바이트의 hashlib 값을 기록으로 쓴다. 피검 함수로 기대값을 만들지 않는다.
해석: `lut_records = {상대 경로: 기록 sha}`(없음 = None), `roles = {상대 경로: {"sha256", "role"}}`,
`read_aux(상대 경로) -> bytes | None`, 반환 = 기계 의존 항목 목록 `[{"ref", "matched", ...}]`.
"""
import hashlib
import json

import pytest

from core.bundle import check_bundle
from core.descriptor import load_descriptor
from core.results import OracleError

from op23_support import build_toy, dump, lf_of, write

S1, S2, S3 = "1" * 64, "2" * 64, "3" * 64
AUX = b"aux\r\ncontent\n"
S4 = hashlib.sha256(AUX.replace(b"\r\n", b"\n")).hexdigest()       # 보조 입력 기록 = 파일 LF 값(손으로 정한 바이트의 해시)
KIND = "nk"


def base():
    return dict(
        lut_records={"m": S1, "x": S2},
        roles={},
        bundle={"/p/m": {"lf": S1, "raw": S1}, "/p/x": {"lf": S2, "raw": S2}},
        texts={"/p/m": ".subckt mod a b"},
        model_name="mod",
        read_aux=lambda rel: None,
    )


def call(**over):
    a = base()
    a.update(over)
    return check_bundle(KIND, a["lut_records"], a["roles"], a["bundle"], a["texts"], a["model_name"], a["read_aux"])


def rej(**over):
    with pytest.raises(OracleError) as ei:
        call(**over)
    return ei.value


def blob(e):
    return json.dumps(e.detail, ensure_ascii=False, default=str)


def test_t3_6a_positive_control():
    assert call() == []


def test_t3_6b_rule_i_missing_sha():
    e = rej(lut_records={"m": S1, "x": S2, "y": S3})
    assert e.code == "model_bundle_mismatch" and e.detail["rule"] == "i"
    assert S3 in blob(e) and '"y"' in blob(e)                         # 빠진 sha 와 역할 미선언 기록 경로


def test_t3_6c_rule_ii_defining_file_absent():
    e = rej(texts={"/p/m": ""})
    assert e.code == "model_bundle_mismatch" and e.detail["rule"] == "ii"


def test_t3_6d_rule_ii_defining_sha_not_in_records():
    e = rej(lut_records={"x": S2})
    assert e.code == "model_bundle_mismatch" and e.detail["rule"] == "ii"


def test_t3_6e_empty_records():
    e = rej(lut_records={})
    assert e.code == "lut_model_provenance_missing" and e.detail["why"] == "empty"


def test_t3_6f_meta_absent():
    e = rej(lut_records=None)
    assert e.code == "lut_model_provenance_missing" and e.detail["why"] == "meta_absent"


def aux_args(read):
    r = base()["lut_records"]
    r["b"] = S4
    return dict(lut_records=r, roles={"b": {"sha256": S4, "role": "generation_aux_input"}}, read_aux=read)


def test_t3_6g_aux_input_matching_file_is_not_in_rule_i():
    assert call(**aux_args(lambda rel: AUX if rel == "b" else None)) == []     # S4 는 묶음에 없는데도 통과


def test_t3_6h_aux_input_changed_or_missing():
    e = rej(**aux_args(lambda rel: b"different\n"))
    assert e.code == "lut_aux_input_mismatch"
    act = e.detail["actual_sha256"]
    assert set(act) == {"lf", "raw"} and act["lf"] != S4 and act["raw"] != S4
    e2 = rej(**aux_args(lambda rel: None))
    assert e2.code == "lut_aux_input_mismatch" and e2.detail["actual_sha256"] == "missing"


def test_t3_6i_no_silent_exemption_without_role():
    r = base()["lut_records"]
    r["b"] = S4
    e = rej(lut_records=r, roles={})
    assert e.code == "model_bundle_mismatch"                           # 역할 미선언 = 모델 파일로 본다


def test_t3_6j_raw_only_match_is_machine_dependent():
    out = call(bundle={"/p/m": {"lf": S3, "raw": S1}, "/p/x": {"lf": S2, "raw": S2}})
    assert len(out) == 1
    assert out[0]["ref"] == f"lut_model_file:{KIND}:m" and out[0]["matched"] == "raw"


def test_roles_pair_must_match_exactly_else_undeclared():
    # 선언된 (경로, sha) 쌍이 기록과 다르면 역할 미선언 = 모델 파일 취급 (interface '옆 선언' 끝 문장, T3-6i 와 같은 결과)
    r = base()["lut_records"]
    r["b"] = S4
    e = rej(lut_records=r, roles={"b": {"sha256": S3, "role": "generation_aux_input"}}, read_aux=lambda rel: AUX)
    assert e.code == "model_bundle_mismatch"


# ------------------------------------------------------------------ 옆 선언 파일 형식 (lut_file_roles_invalid)
# 옆 선언은 기술자 `lut_file_roles` 가 가리키고 load_descriptor 가 2단계에서 형식을 본다(D §7.2, §12.5).
def roles_doc():
    g = "f" * 64
    return {"schema": "lut_file_roles/1", "generator_sha256": g,
            "roles": {"b": {"sha256": S4, "role": "generation_aux_input"}},
            "evidence": {"generator": {"commit": "c0ffee", "path": "gen.py", "file_sha256": g, "matched": "lf",
                                       "aux_append_lines": [1]},
                         "include_graph": {"start": ["m"], "files": ["m"]},
                         "measured_by": "verifier", "date": "2026-11-04"}}


def with_roles(tmp_path, doc):
    toy = build_toy(tmp_path)
    b = dump(doc)
    write(tmp_path / "roles.json", b)
    toy.doc["lut_file_roles"] = [{"path": "roles.json", "sha256": lf_of(b)}]
    toy.write_descriptor()
    return toy


def test_roles_declaration_positive_control(tmp_path):
    toy = with_roles(tmp_path, roles_doc())
    load_descriptor(toy.d, env={})


def _extra_key(d):
    d["extra"] = 1


def _bad_role(d):
    d["roles"]["b"]["role"] = "silent_pass"


def _no_evidence(d):
    del d["evidence"]


def _generator_sha_differs(d):
    d["evidence"]["generator"]["file_sha256"] = "e" * 64


def _no_commit_no_data_path(d):
    d["evidence"]["generator"].pop("commit")


@pytest.mark.parametrize("mut", [_extra_key, _bad_role, _no_evidence, _generator_sha_differs, _no_commit_no_data_path],
                         ids=["closed_keys", "role_value", "no_evidence", "generator_sha_ne", "commit_or_data_path"])
def test_roles_declaration_invalid(tmp_path, mut):
    # interface '옆 선언': 키 닫힘 / 역할 값 밖 / evidence 없음 / generator.file_sha256 != generator_sha256 /
    # commit·data_path 둘 다 없음 [D-3] = lut_file_roles_invalid
    d = roles_doc()
    mut(d)
    toy = with_roles(tmp_path, d)
    with pytest.raises(OracleError) as ei:
        load_descriptor(toy.d, env={})
    assert ei.value.code == "lut_file_roles_invalid" and ei.value.stage == "2"


def test_roles_declaration_data_path_instead_of_commit_is_accepted(tmp_path):
    d = roles_doc()
    d["evidence"]["generator"]["commit"] = None
    d["evidence"]["generator"]["data_path"] = "verification/slices_vdsat/gen.py"      # [D-3] commit 대신 data_path
    toy = with_roles(tmp_path, d)
    load_descriptor(toy.d, env={})
