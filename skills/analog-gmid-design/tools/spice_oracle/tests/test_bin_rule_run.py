"""OP-7 어댑터 조각 진입점 8b -- interface 20261104-op7b §4 T7-10a~e, T7-12. stub 만 쓴다(시뮬레이터 호출 0).

oracle (a)(d): 구성으로 정해진 합성 입력(World toy: 묶음 파일 `m.lib` 하나, 선언 모드 m / 글 "T", 판 stub-1)에서 한 칸만 틀리게 만든
변형이 D §16 의 코드·단계로 거부된다는 규칙 문장, 그리고 거부된 입력은 stub 를 부르지 않는다는 구성. 기대 해시는 hashlib 로 직접 잰다.
해석:
  * H-10 기술자 칸 `bin_rule_decl`(없음 = 선언 참조 없음)은 `op23_support.build_toy(bin_rule=...)`, 선언 파일은 `<폴더>/br.json`.
  * H-11 `fingerprints.compat_sha256` 의 위치는 interface 에 파일 이름이 없어 출력 폴더의 모든 json 에서 키 `fingerprints` 를 찾는다.
  * H-12 거부 기록 `stage`·`detail.ref` 는 reject.json 의 칸(D §11.7).
"""
import json
from pathlib import Path

import pytest

from core.descriptor import load_descriptor
from core.ir import Circuit, Resistor, VSource
from core.requests import Condition, Op, OpOutputs

from op23_support import World, dump, lf_of, make_lut_toy, read_reject, sha, M_LIB, B_LIB, write, bin_rule_doc, build_toy
from stub_adapter import StubAdapter

DEV = {"M1": {"gm": 6e-4, "gds": 1.0 / 60000.0}}


def run_world(w, stub=None):
    stub = stub or StubAdapter(DEV)
    rc, out = w.run(stub)
    return rc, out, stub


def rewrite_decl(w, doc, resync=True):
    """선언 파일 br.json 을 새로 쓰고 기술자 칸 sha 를 파일 LF 값으로 맞춘다."""
    b = dump(doc)
    write(w.toy.br_path, b)
    if resync:
        w.toy.doc["bin_rule_decl"]["sha256"] = lf_of(b)
        w.toy.write_descriptor()
        w.refresh_input_hashes()


def test_positive_control_normal_world_passes(tmp_path):
    w = World(tmp_path)
    rc, out, stub = run_world(w)
    assert rc == 0 and not (out / "cs_toy.reject.json").exists()
    assert len(stub.calls) == 1


def test_t7_10a_no_decl_ref_rejected_at_8b_without_run(tmp_path):
    w = World(tmp_path, bin_rule=False)
    rc, out, stub = run_world(w)
    rec = read_reject(out)
    assert rc == 2 and stub.calls == []
    assert rec["code"] == "bin_rule_undeclared" and rec["stage"] == "8b"
    assert rec["detail"]["why"] == "no_decl_ref"


def test_t7_10b_declared_mode_absent_in_adapter_table(tmp_path):
    w = World(tmp_path)
    stub = StubAdapter(DEV, caps_extra={"compat_modes": {"other": {"spiceinit_text": "T", "log_line": "^MODE other$"}}})
    rc, out, _ = run_world(w, stub)
    rec = read_reject(out)
    assert rc == 2 and stub.calls == []
    assert rec["code"] == "bin_rule_compat_mismatch" and rec["stage"] == "8b"
    assert rec["detail"]["actual"] is None and rec["detail"]["declared"] == sha(b"T")


def test_t7_10b_table_text_differs_from_declared(tmp_path):
    w = World(tmp_path)
    stub = StubAdapter(DEV, caps_extra={"compat_modes": {"m": {"spiceinit_text": "U", "log_line": "^MODE m$"}}})
    rc, out, _ = run_world(w, stub)
    rec = read_reject(out)
    assert rc == 2 and stub.calls == []
    assert rec["code"] == "bin_rule_compat_mismatch" and rec["detail"] == {"declared": sha(b"T"), "actual": sha(b"U")}


def _fingerprints(out: Path):
    found = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("fingerprints"), dict):
                found.append(o["fingerprints"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for p in sorted(out.glob("*.json")):
        walk(json.loads(p.read_text(encoding="utf-8")))
    return found


def test_t7_10c_normal_records_compat_sha_and_passes_text_to_adapter(tmp_path):
    w = World(tmp_path)
    rc, out, stub = run_world(w)
    assert rc == 0
    fps = _fingerprints(out)
    assert fps and all(f.get("compat_sha256") == sha(b"T") for f in fps)      # 손으로 잰 sha256("T")
    assert len(stub.compats) == 1 and stub.compats[0].spiceinit_text == "T"
    assert stub.compats[0].mode == "m" and stub.compats[0].spiceinit_sha256 == sha(b"T")


def test_t7_10d_decl_file_changed_is_descriptor_stale_at_stage_2(tmp_path):
    w = World(tmp_path)
    write(w.toy.br_path, w.toy.br_path.read_bytes() + b" ")       # 한 글자 바꿈, 기술자 칸 sha 는 그대로
    w.refresh_input_hashes()
    rc, out, stub = run_world(w)
    rec = read_reject(out)
    assert rc == 2 and stub.calls == []
    assert rec["code"] == "pdk_descriptor_stale" and rec["stage"] == "2" and rec["detail"]["ref"] == "bin_rule_decl"


def test_t7_10e_model_bundle_mismatch_comes_before_undeclared(tmp_path):
    w = World(tmp_path, bin_rule=False)                             # 기술자 칸 없음
    # 기록 뿌리 교차는 통과(m.lib·b.lib 모두 엔진 선언 sources 이고 기록 sha 가 실제 파일과 같음)하되, b.lib 의 sha 는 묶음(m.lib 만 포함)에
    # 없고 역할 선언도 없어 규칙 (i)에서 걸린다(D §7.2 8단계 순서: 빈 표 -> 기록 뿌리 교차 -> 역할 -> 규칙)
    make_lut_toy(w.lut, model_sha={"m.lib": sha(M_LIB), "b.lib": sha(B_LIB)})
    w.refresh_input_hashes()
    rc, out, stub = run_world(w)
    rec = read_reject(out)
    assert rc == 2 and stub.calls == []
    assert rec["code"] == "model_bundle_mismatch"                   # 8단계가 먼저 (8b 의 bin_rule_undeclared 아님)
    assert rec["stage"] != "8b"


def test_t7_10f_decl_must_cover_recorded_models(tmp_path):
    w = World(tmp_path)
    rewrite_decl(w, bin_rule_doc([sha(b"z\n")]))                    # 선언 묶음이 m.lib 의 LF 를 포함하지 않음
    rc, out, stub = run_world(w)
    rec = read_reject(out)
    assert rc == 2 and stub.calls == []
    assert rec["code"] == "bin_rule_undeclared" and rec["stage"] == "8b" and rec["detail"]["why"] == "model_set"
    assert rec["detail"]["missing"] == [lf_of(M_LIB)]


def test_t7_10f_decl_simulator_version_mismatch(tmp_path):
    w = World(tmp_path)
    rewrite_decl(w, bin_rule_doc([lf_of(M_LIB)], sim_version="2"))   # stub 판 = stub-1
    rc, out, stub = run_world(w)
    rec = read_reject(out)
    assert rc == 2 and stub.calls == []
    assert rec["code"] == "bin_rule_undeclared" and rec["detail"]["why"] == "simulator"
    assert rec["detail"]["declared"] == "stub-2" and rec["detail"]["actual"] == "stub-1"


# ------------------------------------------------------------------ T7-12 compat=None 직접 호출
def test_t7_12_adapter_called_directly_with_compat_none_runs_without_rejection(tmp_path):
    toy = build_toy(tmp_path / "t", kind="nmos", with_model=True, bin_rule=True)
    desc = load_descriptor(toy.d, env={})
    ckt = Circuit(elements=(VSource("V1", "a", "0", 1.0), Resistor("R1", "a", "0", 1000.0)),
                  role={"V1": "testbench", "R1": "circuit"}, meta={})
    cond = Condition(temp_c=27.0, corner="tt")
    req = (Op(id="op", cond=cond, exc=(), outputs=OpOutputs(devices="all", nodes=("a",), currents=())),)
    stub = StubAdapter(DEV)
    res = stub.run(ckt, req, desc, str(tmp_path / "work"), None, None, None)
    assert res.status.error is None and len(stub.calls) == 1 and stub.compats == [None]
    # 손 계산: 1 V 전원이 노드 a 를 직접 구동하므로 V(a) = 1.0 (KVL, 저항은 전압에 무관)
    assert res.by_request["op"].nodes["a"] == pytest.approx(1.0, rel=1e-9)
