"""[U1b-jrules bcfee60] 단계 A 가 실 spec 파일의 내부 루프 뷰 선언 `{"loop_cut": [넷]}` 를 모아 엔진 루프 뷰 끊는 넷과 대조한다.

조작 없는 spec 파일(monkeypatch 없음)로 확인한다 -- test_stage_a 의 `_internal_loop_decl` 은 loader 가 이 모양을 받기 전에 로드 결과를
바꿔 넣던 우회였다.

근거:
- oracle (a) 손 회로 CMFB_SE(s1v_hand.CMFB 를 출력 role 단일 출력 둘로 바꾼 것, 이름 없는 손 toy): 루프 (cm, cmfb, om)·(cm, cmfb, op)
  의 끊는 점 = (M5, cm)(test_loop_cuts 손 유도: CS gate 엣지 후보 중 두 루프에 다 나오는 것). 출력 포트쌍이 없어 cm_pair 가 아니므로
  내부 루프 뷰이고, 선언이 없으면 `undeclared_loop_constraint`(기록만 -> stopped/2).
- oracle (d) 계약: pipeline CONTRACT 1절(declared_loop_cuts = pm_ 제약의 내부 루프 뷰 선언 끊는 넷, 맞지 않는 선언 넷마다
  `loop_cut_unmatched` review_needed, 뷰 "", subject = 넷), 20~21행(로드 거부 exit 7·`A1_load: `, 기록만 -> stopped/2, review 만 ->
  review_needed/2, 그 밖 ok/0), SPEC_CONTRACT '내부 루프 뷰 선언'(loop_cut 원소 넷이 단자에 없으면 view_net_unknown).
- 이름 전단사 불변(설계 41 1.11): 넷·소자 이름을 정렬 순서가 뒤집히는 새 이름으로 바꾸고 netlist 순서를 섞어도, 선언 넷을 같은
  사상으로 옮기면 상태·코드가 같고 subject·끊는 넷이 사상을 따른다(oracle (a) 구성).
"""
from __future__ import annotations

import json

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.metrics import metric_catalog
from gmid_engine.pipeline import run_stage_a

import jrules_hand as J
import s1v_hand as H

CMFB_SE = H.topo("cmfbse", tuple((e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in H.CMFB["netlist"]),
                 {"inp": H.DIFF_P, "inn": H.DIFF_N, "op": H.SE_OUT, "om": H.SE_OUT},
                 passives=tuple((e["name"], e["kind"], tuple(e["terminals"])) for e in H.CMFB["passive_elements"]),
                 bias=("vb", "vref"))


def _pair(tmp_path, doc, loop_cut, stem=None):
    """(topology 경로, spec 경로). spec 은 jrules_hand.spec_doc(pm_ss_deg 하나, feedback 없음)에 view {"loop_cut": ...} 를 단 실 파일.
    loop_cut None 이면 pm 제약 없음(대조군 -- loop_cut 없는 pm 은 출력 포트 2개라 유도 뷰가 없다)."""
    tp, sp = J.write_pair(tmp_path, doc, stem=stem, pm=loop_cut is not None)
    if loop_cut is not None:
        spec = json.loads(sp.read_text(encoding="utf-8"))
        (c,) = spec["human"]["constraints"]
        assert c["metric"] == "pm_ss_deg"
        c["view"] = {"loop_cut": list(loop_cut)}
        sp.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    return tp, sp


def _split(lines):
    return [x.split("|")[:4] for x in lines]


def _codes(lines):
    return {x.split("|")[1] for x in lines}


def _go(tmp_path, real_lut, doc, loop_cut, out="o", stem=None):
    tp, sp = _pair(tmp_path, doc, loop_cut, stem=stem)
    return run_stage_a(tp, sp, real_lut, output_dir=tmp_path / out, supplies_v=H.SUPPLIES)


# ------------------------------------------------------------------ 해제·불일치·거부
def test_without_declaration_stops_on_undeclared_loop(tmp_path, real_lut):
    # 대조군(oracle (a)): 선언 없음 -> 내부 루프 뷰 cm 이 미선언 -> 기록만 -> stopped/2
    r = _go(tmp_path, real_lut, CMFB_SE, None)
    assert (r.exit_code, r.status) == (2, "stopped")
    assert "undeclared_loop_constraint" in _codes(r.report["stop_reasons"])


def test_matching_loop_cut_lifts_undeclared_record(tmp_path, real_lut):
    # 선언 넷 cm = 손 유도 끊는 gate 넷 -> 미선언 기록 해제, 불일치 없음 -> ok/0(계약 36행: ok 면 두 목록이 비어 있다)
    r = _go(tmp_path, real_lut, CMFB_SE, ["cm"])
    assert (r.exit_code, r.status) == (0, "ok"), r.report["stop_reasons"] + r.report["review_needed"]
    assert r.report["stop_reasons"] == [] and r.report["review_needed"] == []


def test_non_matching_loop_cut_is_review_and_record_stays(tmp_path, real_lut):
    # cmfb 는 루프 위 넷이지만 끊는 점이 아니다 -> loop_cut_unmatched(review, 뷰 "", subject cmfb). cm 은 여전히 미선언 -> stopped/2
    r = _go(tmp_path, real_lut, CMFB_SE, ["cmfb"])
    assert (r.exit_code, r.status) == (2, "stopped")
    assert "undeclared_loop_constraint" in _codes(r.report["stop_reasons"])
    hits = [h for h in _split(r.report["review_needed"]) if h[1] == "loop_cut_unmatched"]
    assert hits == [["review_needed", "loop_cut_unmatched", "", "cmfb"]]


def test_partly_matching_loop_cut_reports_only_the_extra_net(tmp_path, real_lut):
    # cm 은 맞고(해제) cmfb 만 불일치 -> review 만 -> review_needed/2
    r = _go(tmp_path, real_lut, CMFB_SE, ["cmfb", "cm"])
    assert (r.exit_code, r.status) == (2, "review_needed")
    assert r.report["stop_reasons"] == []
    assert [h for h in _split(r.report["review_needed"]) if h[1] == "loop_cut_unmatched"] == [
        ["review_needed", "loop_cut_unmatched", "", "cmfb"]]


def test_unknown_loop_cut_net_is_load_rejection(tmp_path, real_lut):
    # 계약: loop_cut 원소가 단자에 없음 -> view_net_unknown -> 단계 A1 로드 거부 exit 7, s1v None
    r = _go(tmp_path, real_lut, CMFB_SE, ["nowhere"])
    assert r.exit_code == 7 and r.s1v is None
    assert len(r.report["stop_reasons"]) == 1 and r.report["stop_reasons"][0].startswith("A1_load: ")
    assert "view_net_unknown" in r.report["stop_reasons"][0]


# ------------------------------------------------------------------ 이름 전단사 불변
def _maps():
    nets, devs = H.json_nets(CMFB_SE), H.json_mos(CMFB_SE) | {e["name"] for e in CMFB_SE["passive_elements"]}
    # 레일(vdd·gnd)은 사용자 supplies_v 키라 그대로 둔다(SUPPLIES 를 같은 사상으로 옮기는 대신 -- 레일은 끊는 넷 후보가 아니다)
    nets, devs = sorted(set(nets) - set(CMFB_SE["supply_nets"])), sorted(devs)
    # 정렬 순서를 뒤집는 새 이름(이름 tie-break 가 결과를 바꾸면 드러난다), 넷·소자 이름 공간 분리
    return ({n: "w%02d" % (len(nets) - i) for i, n in enumerate(nets)},
            {n: "E%02d" % (len(devs) - i) for i, n in enumerate(devs)})


def test_loop_cut_view_maps_under_renaming(tmp_path):
    # 로드 결과 ViewDecl.cuts: 원본 (("", cm), ("", cmfb)) -> 새 이름은 순서가 뒤집혀 (("", f(cmfb)), ("", f(cm))) (넷순, oracle (d))
    nmap, dmap = _maps()
    assert nmap["cmfb"] < nmap["cm"]                                       # 전제: 사상이 두 넷 순서를 뒤집는다
    out = {}
    for tag, doc, cut in (("a", CMFB_SE, ["cmfb", "cm"]), ("b", H.rename(CMFB_SE, nmap, dmap, 7), [nmap["cm"], nmap["cmfb"]])):
        (tmp_path / tag).mkdir()
        tp, sp = _pair(tmp_path / tag, doc, cut, stem="cmfbse")
        spec = load_sizing_spec(str(sp), load_topology(str(tp)), metric_catalog())
        (c,) = [c for c in spec.constraints if c.metric == "pm_ss_deg"]
        out[tag] = tuple(c.view.cuts)
    assert out["a"] == (("", "cm"), ("", "cmfb"))
    assert out["b"] == (("", nmap["cmfb"]), ("", nmap["cm"]))


def test_stage_a_result_maps_under_renaming(tmp_path, real_lut):
    nmap, dmap = _maps()
    ren = H.rename(CMFB_SE, nmap, dmap, 11)
    ren["topology_name"] = "ren"                                            # 파일 stem = meta.circuit(spec_meta 규칙)
    for cut, want_status in ((["cm"], (0, "ok")), (["cmfb"], (2, "stopped")), (["cmfb", "cm"], (2, "review_needed"))):
        a = _go(tmp_path, real_lut, CMFB_SE, cut, out="a" + "_".join(cut))
        b = _go(tmp_path, real_lut, ren, [nmap[n] for n in cut], out="b" + "_".join(cut))
        assert (a.exit_code, a.status) == (b.exit_code, b.status) == want_status
        assert _codes(a.report["stop_reasons"]) == _codes(b.report["stop_reasons"])
        ua = sorted(h[3] for h in _split(a.report["review_needed"]) if h[1] == "loop_cut_unmatched")
        ub = sorted(h[3] for h in _split(b.report["review_needed"]) if h[1] == "loop_cut_unmatched")
        assert sorted(nmap[n] for n in ua) == ub
        # 엔진 루프 뷰의 끊는 gate 넷(보고서 views[].cuts[*][1])도 사상을 따른다 -- 손 유도 cm
        ca = sorted(c[1] for v in a.report["views"] for c in v["cuts"])
        cb = sorted(c[1] for v in b.report["views"] for c in v["cuts"])
        # 전달 뷰·루프 뷰 모두 끊는 점이 (M5, cm) 이다(test_loop_cuts: transfer:0 의 cuts 도 ((M5, cm),)) -> 넷 집합 {cm}
        assert set(ca) == {"cm"} and cb == sorted(nmap[n] for n in ca)
