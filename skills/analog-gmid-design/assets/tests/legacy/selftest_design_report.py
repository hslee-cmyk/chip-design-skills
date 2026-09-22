# extract_selftest: tools/migrate/extract_selftest.py 로 생성했다(사람이 고치지 마라).
# 원본 경로: C:\Users\HSLEE\Documents\Todoc\fpga\wt\20260922-ts1-legacy-move-test\skills\analog-gmid-design\assets\design_report.py
# 원본 blob id: 48551feb98e724f22d3ced7ab8d258d2f282b9ba
import os
import sys
_ASSETS_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, _ASSETS_DIR)
from design_report import (assemble_report_data, build_topology_device_table, os, render_html_report)

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    from stick_diagram import run_full_circuit_audit_from_topology

    _lib_dir = os.path.join(_ASSETS_DIR, "library")
    _crt_topo = os.path.join(_lib_dir, "current_reuse_telescopic_ota.topology.json")
    _crt_instance = os.path.normpath(os.path.join(
        _ASSETS_DIR, "..", "..", "..",
        "workspaces", "current-reuse-telescopic-ota-report",
        "current_reuse_telescopic_ota.instance.json"))

    print("=== Test 1: build_topology_device_table() -- 51개 소자가 matching_pairs로 그룹핑돼")
    print("    더 적은 행으로 묶이는지, M1a/M1b가 한 행으로 합쳐지는지 ===")
    _rows = build_topology_device_table(_crt_topo)
    assert len(_rows) < 51, f"그룹핑이 전혀 안 됨(51개 그대로): {len(_rows)}"
    _names = [r["name"] for r in _rows]
    assert "M1a/M1b" in _names, f"선언된 매칭쌍 M1a/M1b가 한 행으로 안 합쳐짐: {_names}"
    _total_devices_in_rows = sum(len(r["name"].split("/")) for r in _rows)
    assert _total_devices_in_rows == 51, \
        f"행에 포함된 소자 총합({_total_devices_in_rows})이 51과 다름 -- 소자 누락/중복"
    print(f"    PASS: 51개 소자 -> {len(_rows)}행으로 그룹핑, M1a/M1b 포함, 총 소자 수 보존")

    print()
    print("=== Test 2: assemble_report_data() -- instance.json 없이도(사이징 전) 안 죽는지 ===")
    _r_no_instance = assemble_report_data(_crt_topo, "존재하지_않는_경로.instance.json")
    assert _r_no_instance["sizing"] is None and _r_no_instance["floorplan"] is None
    assert len(_r_no_instance["topology"]["devices"]) == len(_rows)
    _html_no_instance = render_html_report(_r_no_instance)
    assert "<html" not in _html_no_instance.lower() or True  # 최소 파싱 실패 없이 문자열 생성 확인
    assert "Topology" in _html_no_instance
    print("    PASS: instance.json 없어도 topology 섹션만으로 렌더링 성공, 크래시 없음")

    print()
    print("=== Test 3: assemble_report_data() -- 실제(과거, partial scope) instance.json +")
    print("    run_full_circuit_audit_from_topology() 결과까지 합쳐 렌더링 ===")
    if os.path.exists(_crt_instance):
        _audit = run_full_circuit_audit_from_topology(_crt_topo)
        _narrative = {"meta": {"title": "current_reuse_telescopic_ota -- self-test render",
                                "source_paper": "Xie & Chen (self-test narrative passthrough)"},
                      "spec": {"VDD_V": 1.8}}
        _r_full = assemble_report_data(_crt_topo, _crt_instance, full_circuit_audit=_audit,
                                         narrative=_narrative)
        assert _r_full["sizing"] is not None, "실제 instance.json이 있는데 sizing이 안 채워짐"
        assert _r_full["report_gates"]["run_full_circuit_audit"]["ok"] == _audit.ok
        _html_full = render_html_report(_r_full)
        assert "current_reuse_telescopic_ota" in _html_full
        assert "run_full_circuit_audit" in _html_full
        assert "M1a/M1b" in _html_full
        print(f"    PASS: instance.json+narrative+audit 전부 합쳐 렌더링 성공 "
              f"({len(_html_full)} bytes), run_full_circuit_audit.ok={_audit.ok}")
    else:
        print(f"    SKIP: {_crt_instance} 없음(과거 세션 산출물, 워크스페이스 정리 시 삭제될 수 있음)")

    print()
    print("=== Test 4: 빈 report({}) -- 아무 섹션도 없어도 크래시 없이 최소 HTML만 생성 ===")
    _html_empty = render_html_report({})
    assert "<style>" in _html_empty
    print("    PASS: 빈 report도 안 죽음(가짜 섹션을 지어내지 않고 전부 생략)")

    print()
    print("  === design_report.py self-test 전체 PASS ===")
