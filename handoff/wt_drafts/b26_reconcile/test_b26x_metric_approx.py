"""B26-1 'V3 계획' 4(_metric_kcl_residual 이름 직접 호출) 근사 -- 변이 판정 측정 전용(scratch, 저장소 test 아님).

기대값은 손 계산: n1 = -1.0e-6(M1 nmos drain) + 2.5e-6(M2 pmos drain) = 1.5e-6, n2 = -4.0e-6(M3 nmos drain).
레일 vdd/gnd는 b1의 이름 집합 판정으로 빠진다.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import sizing_recipe as sr  # noqa: E402


def _b26x_topo(tmp_path):
    p = tmp_path / "b26x_kcl.topology.json"
    nl = [{"name": "M1", "kind": "nmos", "source": "gnd", "drain": "n1", "gate": "g1"},
          {"name": "M2", "kind": "pmos", "source": "vdd", "drain": "n1", "gate": "g2"},
          {"name": "M3", "kind": "nmos", "source": "gnd", "drain": "n2", "gate": "g3"}]
    p.write_text(json.dumps({"topology_name": "b26x_kcl", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
                             "netlist": nl, "symmetry": {"matching_pairs": [], "dispositions": []}}), encoding="utf-8")
    return str(p)


def test_b26x_metric_kcl_residual_direct(tmp_path):
    ctx = sr.SizingContext(sized={"M1": {"ID": 1.0e-6}, "M2": {"ID": 2.5e-6}, "M3": {"ID": 4.0e-6}},
                           topology_path=_b26x_topo(tmp_path))
    v_all = sr._metric_kcl_residual({"type": "kcl_residual"}, ctx)
    v_ex = sr._metric_kcl_residual({"type": "kcl_residual", "exclude_nets": ["n2"]}, ctx)
    assert abs(v_all - 4.0e-6) < 1e-12
    assert abs(v_ex - 1.5e-6) < 1e-12
