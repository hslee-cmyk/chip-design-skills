"""의도 영역 `human.intended_region` (gate `intended_region`) -- SPEC_CONTRACT 2절 intended_region_device 행.
영역 어휘(`REGIONS`)는 계약에 값이 적혀 있지 않아 '어휘 밖 영역 -> type' 과 '소자 밖 -> intended_region_device 포함'만 판정한다."""
from __future__ import annotations

import pytest

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}


def test_empty_is_explicit_declaration(sc):
    assert sc.load().intended_region == ()


def test_pending(sc):
    sc.human["intended_region"] = {"pending": "CI-18"}
    assert sc.load().intended_region.decision == "CI-18"


def test_device_outside_topology(sc):
    sc.human["intended_region"] = {"Qzz": {"region": "zz_not_a_region", "source": dict(US)}}
    d = sc.reject()
    assert "intended_region_device" in sc.rules(d)
    assert d["rejected_gates"] == ("intended_region",)


@pytest.mark.parametrize("name", ["Rfb", "Ibs"])
def test_element_is_not_a_device(sc, name):
    sc.human["intended_region"] = {name: {"region": "zz_not_a_region", "source": dict(US)}}
    d = sc.reject()
    assert "intended_region_device" in sc.rules(d)


def test_region_vocab(sc):
    sc.human["intended_region"] = {"Mfx1": {"region": "zz_not_a_region", "source": dict(US)}}
    sc.reject_only("type", "intended_region")


@pytest.mark.parametrize("raw", [[], "saturation", 3])
def test_section_type(sc, raw):
    sc.human["intended_region"] = raw
    d = sc.reject()
    assert "type" in sc.rules(d) and d["rejected_gates"] == ("intended_region",)


# ---------------------------------------------------------------------------------------------------------------
# [EO-1 범위 4·SF-1 로더 조각, interface card 20261104-eo1r4-sf1l §3 표] 영역 `off` 선언 -- 로더 규칙 전 행 (T-L1)
# oracle (식): card §3 표의 입력->결과 행을 행마다 손으로 옮겼다. 항목 형식 {"region","w_m","l_m","judged_by","source"}.
# 해석: 'type' 거부는 SchemaHit rule == "type", gate `intended_region` 하나(기존 어휘 밖 영역 test 와 같은 모양).
# ---------------------------------------------------------------------------------------------------------------

def _off(**kw):
    e = {"region": "off", "w_m": 1e-6, "l_m": 2e-6, "judged_by": ["gain_ss_db"], "source": dict(US)}
    e.update(kw)
    return e


def _drop(e, key):
    e = dict(e)
    e.pop(key)
    return e


def test_region_vocab_constants():
    from gmid_engine.authoring import REGION_OFF, REGIONS
    assert REGION_OFF == "off"
    assert set(REGIONS) == {"triode", "off"}          # 순서는 단언하지 않는다


def test_region_off_accepted_into_tuple_fields(sc):
    sc.human["intended_region"] = {"Mfx1": _off(judged_by=["gain_ss_db", "pm_ss_deg"])}
    (r,) = sc.load().intended_region
    assert (r.device, r.region, r.w_m, r.l_m) == ("Mfx1", "off", 1e-6, 2e-6)
    assert r.judged_by == ("gain_ss_db", "pm_ss_deg")              # tuple 로 받는다(목록 아님)


@pytest.mark.parametrize("judged", ["missing", []])
def test_region_off_empty_judged_by_loads(sc, judged):
    """judged_by 칸 없음·[] 는 로드를 통과한다(정지는 O-h 몫)."""
    sc.human["intended_region"] = {"Mfx1": _drop(_off(), "judged_by") if judged == "missing" else _off(judged_by=judged)}
    (r,) = sc.load().intended_region
    assert r.region == "off" and tuple(r.judged_by) == ()


def test_region_off_and_triode_mix_sorted_by_device(sc):
    sc.human["intended_region"] = {"Mfx5": {"region": "triode", "source": dict(US)}, "Mfx2": _off()}
    regs = sc.load().intended_region
    assert [(r.device, r.region) for r in regs] == [("Mfx2", "off"), ("Mfx5", "triode")]


@pytest.mark.parametrize("entry", [
    _drop(_off(), "w_m"), _drop(_off(), "l_m"),
    _off(w_m=0.0), _off(w_m=-1e-6), _off(l_m=0.0), _off(l_m=-2e-6),
], ids=["no_w", "no_l", "w_zero", "w_neg", "l_zero", "l_neg"])
def test_region_off_needs_positive_w_and_l(sc, entry):
    sc.human["intended_region"] = {"Mfx1": entry}
    sc.reject_only("type", "intended_region")


@pytest.mark.parametrize("extra", [{"w_m": 1e-6}, {"l_m": 2e-6}, {"judged_by": ["gain_ss_db"]}], ids=["w_m", "l_m", "judged_by"])
def test_region_non_off_device_rejects_off_only_fields(sc, extra):
    sc.human["intended_region"] = {"Mfx1": {"region": "triode", "source": dict(US), **extra}}
    sc.reject_only("type", "intended_region")


@pytest.mark.parametrize("judged", ["gain_ss_db", 3, {"a": 1}, [3], [None], ["gain_ss_db", 3]],
                         ids=["str", "int", "dict", "int_item", "none_item", "mixed"])
def test_region_off_judged_by_must_be_list_of_str(sc, judged):
    sc.human["intended_region"] = {"Mfx1": _off(judged_by=judged)}
    sc.reject_only("type", "intended_region")


def test_region_vocab_rejects_linear(sc):
    sc.human["intended_region"] = {"Mfx1": {"region": "linear", "source": dict(US)}}
    sc.reject_only("type", "intended_region")


@pytest.mark.parametrize("name", ["Qzz", "Rfb", "Ibs"])
def test_region_off_on_non_device_rejected(sc, name):
    sc.human["intended_region"] = {name: _off()}
    d = sc.reject()
    assert "intended_region_device" in sc.rules(d)


def test_region_off_w_m_change_changes_operating_fp(sc):
    sc.human["intended_region"] = {"Mfx1": _off(w_m=1e-6)}
    a = dict(sc.load().section_fps)["operating_fp"]
    again = dict(sc.load().section_fps)["operating_fp"]
    sc.human["intended_region"] = {"Mfx1": _off(w_m=2e-6)}
    b = dict(sc.load().section_fps)["operating_fp"]
    assert a == again and a != b
