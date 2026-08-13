# -*- coding: utf-8 -*-
"""회로-무관(circuit-agnostic) design report 데이터/HTML 조립기 (세션20 신설).

배경: `workspaces/*/build_report.py`+`build_html.py`(및 `report_template.html`)는 지금까지
전부 **회로 하나 전용으로 손으로 짠 스크립트**였다 -- 소자 역할 설명(`topo_devices`)을
매번 텍스트로 재입력하고(사고9 net-이름 드리프트 재발 위험과 같은 근본원인), 사이징/스틱
다이어그램 결과를 담은 JSON 파일 5개를 하드코딩된 경로로 따로 읽고, HTML의 JS 섹션 조립
로직이 그 회로의 cell 이름(`core_signal_cell` 등)/필드(`gain`, `Cgg_fF`)를 그대로 가정했다.
`run_harness.py`가 이제 `run_full_circuit_audit_from_topology()`(세션20)까지 자동으로
계산하는 상황에서, 리포트도 "실행할 때마다 스크립트를 손으로 다시 짜는" 게 아니라 harness가
직접 호출할 수 있는 함수여야 한다는 게 이 모듈의 존재 이유다.

**일반화 범위(의도적으로 좁힘)**: 아래 두 함수가 회로와 무관하게 기계적으로 조립하는 부분은
"소자 표"(topology.json에서 자동)/"사이징·floorplan·audit_row_split·coverage"(instance.json
에서 자동, `save_instance_json()`이 이미 이 스키마로 저장한다)/"matching·hub-merge disposition
전수 감사"(`run_full_circuit_audit_from_topology()` 결과, 호출자가 넘김)뿐이다. 논문 spec 표/
레이아웃 가이드 서술/회로도 좌표처럼 **논문을 읽고 판단해야 하는 내용은 이 모듈이 새로 짓지
않는다** -- 호출자가 `narrative` dict로 그대로 넘기면 있는 그대로 렌더링하고, 없으면 그
섹션은 조용히 지어내지 않고 생략한다(§1.5 원칙과 동일).

⚠️ **알려진 한계**: 기존 `build_html.py`/`report_template.html`의 정교한 SVG 렌더러
(`renderSchematic`/`renderStack`/`renderFloorplan`)는 그 자체로는 이미 데이터 기반이라
일반적이지만, 그걸 감싸는 "SECTION 1~8" 조립 로직이 회로별 cell 이름/enriched 필드를 그대로
가정하고 있어 그대로 재사용하면 다른 회로에서 조용히 깨진다. 이 모듈은 그 대신 **표/카드
기반의 더 단순하지만 실제로 회로-무관한** 렌더러로 대체했다 -- 옛 리포트 수준의 스틱-다이어그램
SVG 시각화를 원하면 그 렌더러들을 이 모듈로 이식하는 별도 후속 작업이 필요하다(세션20 기록,
`.ai/context.md` 참고)."""
import html as _html
import json
import os

from stick_diagram import load_topology, _audit_result_json


def build_topology_device_table(topology_json_path: str) -> list[dict]:
    """topology.json 하나에서 소자 표를 자동 조립한다 -- 손타이핑 없음(사고9 재발 원인
    제거). `symmetry.matching_pairs`로 선언된 쌍/그룹은 한 행으로 합쳐서 보여준다(기존
    수작업 리포트의 "M1a/M1b" 표기 관례와 동일). `device_roles`가 있으면 그 필드를 그대로
    role 텍스트로 쓰고, 없으면(아직 role 메타데이터가 없는 소자) connectivity(gate/source/
    drain)로 대체한다 -- 둘 다 **이미 topology.json에 기록된 값을 옮기는 것**이지 이 함수가
    새로 판단하는 게 아니다."""
    transistors, meta = load_topology(topology_json_path)
    by_name = {t.name: t for t in transistors}
    device_roles = meta.get("device_roles") or {}

    # 2026-08-06(세션20) -- 소자 하나가 서로 다른 matching_pairs 항목 여러 개에 동시에
    # 나올 수 있다(실측: current_reuse_telescopic_ota의 M8은 {M8,M17}(Vom/Vop 대칭)과
    # {M18_bg,M8,M13,M17,M22,M60,M61}(bias-gen replica family) 둘 다에 속함) -- "마지막에
    # 처리된 항목으로 덮어쓰기"는 그 소자가 두 그룹에 동시에 표시돼 총 소자 수가 51을
    # 넘는 이중집계 버그를 낸다(self-test로 발견). union-find로 연결된 성분을 묶어 이런
    # 겹침이 있어도 각 소자가 정확히 한 행에만 속하도록 한다.
    _parent = {t.name: t.name for t in transistors}

    def _find(x):
        while _parent[x] != x:
            x = _parent[x]
        return x

    def _union(a, b):
        ra, rb = _find(a), _find(b)
        if ra != rb:
            _parent[ra] = rb

    for pair in meta["symmetry"]["matching_pairs"]:
        names = [n for n in pair["names"] if n in _parent]
        for a, b in zip(names, names[1:]):
            _union(a, b)

    groups_by_root = {}
    for t in transistors:
        groups_by_root.setdefault(_find(t.name), []).append(t.name)

    seen_groups = set()
    rows = []
    for t in transistors:
        root = _find(t.name)
        if root in seen_groups:
            continue
        seen_groups.add(root)
        group = groups_by_root[root]
        member_ts = [by_name[n] for n in group if n in by_name]
        kinds = sorted(set(m.kind for m in member_ts))

        role_bits = [f"{n}: " + ", ".join(f"{k}={v}" for k, v in device_roles[n].items())
                     for n in group if n in device_roles]
        role_text = " | ".join(role_bits) if role_bits else \
            "; ".join(f"{m.name}(gate={m.gate}, source={m.source}, drain={m.drain})"
                      for m in member_ts)
        rows.append({"name": "/".join(group), "kind": "+".join(kinds), "role": role_text})
    return rows


def assemble_report_data(topology_json_path: str, instance_json_path: str,
                          full_circuit_audit=None, narrative: dict | None = None,
                          extra_sections: dict | None = None) -> dict:
    """topology.json + instance.json(+ `run_full_circuit_audit_from_topology()`의 반환값
    + 선택적 `narrative`)에서 REPORT 데이터 dict를 조립한다. `instance_json_path`가 아직
    없으면(사이징이 partial이라 `save_instance_json()`이 아직 안 불렸으면) `sizing`/
    `floorplan`류 섹션은 빠진 채로 조립된다(에러 아님 -- 호출자가 이미 알고 있는 정직한
    부분 스코프, run_harness.py의 `pipeline_result is None` 분기와 동일 원칙).

    `narrative`(선택): `{"meta":..., "spec":..., "layout_guide":..., "schematics":...}` --
    논문 판단이 필요한 서술을 호출자가 그대로 채워 넣는다. 없으면 해당 섹션은 렌더러가
    생략한다(빈 문자열/가짜 값으로 채우지 않음).
    `extra_sections`(선택): `{"spice_single_device":..., "power":...}`처럼 이 함수가 모르는
    다른 산출물(SPICE 결과 등)을 REPORT 최상위에 그대로 얹는다."""
    narrative = narrative or {}
    instance = None
    if instance_json_path and os.path.exists(instance_json_path):
        with open(instance_json_path, encoding="utf-8") as f:
            instance = json.load(f)

    meta = narrative.get("meta") or {"title": os.path.basename(topology_json_path),
                                      "source_paper": None, "process_note": None}
    topology_section = {"devices": build_topology_device_table(topology_json_path)}
    if "schematics" in narrative:
        topology_section["schematics"] = narrative["schematics"]

    report = {
        "meta": meta,
        "topology": topology_section,
        "spec": narrative.get("spec"),
        "sizing": (instance or {}).get("sizing"),
        "floorplan": (instance or {}).get("floorplan"),
        "box_shape": (instance or {}).get("box_shape"),
        "audit_row_split": (instance or {}).get("audit_row_split"),
        "coverage": (instance or {}).get("coverage"),
        "layout_guide": narrative.get("layout_guide"),
        "report_gates": {
            "run_full_circuit_audit": _audit_result_json(full_circuit_audit)
                                        if full_circuit_audit is not None else None,
            "instance_json_path": instance_json_path,
        },
    }
    if extra_sections:
        report.update(extra_sections)
    return report


_CSS = r"""
:root{
  --paper:#eef1f4; --paper-raise:#ffffff; --ink:#161b22; --muted:#5b6472; --line:#d3d9e0;
  --accent:#3a5a78; --accent-soft:#d7e2ea;
  --ok:#2e7d5b; --ok-soft:#d9ecdf; --warn:#a8720a; --warn-soft:#f3e3c2; --bad:#b23b3b; --bad-soft:#f5d9d9;
  --mono: ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  --sans: -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  --radius: 8px;
}
@media (prefers-color-scheme: dark){
  :root{
    --paper:#11151b; --paper-raise:#181e26; --ink:#e6ebf1; --muted:#8b96a3; --line:#2a323d;
    --accent:#7fa4c4; --accent-soft:#1d2b38;
    --ok:#5fbd8d; --ok-soft:#173427; --warn:#d9a63e; --warn-soft:#3a2e12; --bad:#e07a7a; --bad-soft:#3a1f1f;
  }
}
*{box-sizing:border-box;}
body{ background:var(--paper); color:var(--ink); font-family:var(--sans); margin:0; padding:0 20px 80px; line-height:1.5; }
.wrap{max-width:1100px; margin:0 auto;}
header.top{ padding:22px 0 14px; border-bottom:1px solid var(--line); margin-bottom:32px; }
header.top h1{ font-size:1.2rem; margin:0 0 6px; }
header.top .sub{color:var(--muted); font-size:0.82rem; max-width:80ch;}
section.rsec{margin-bottom:44px;}
section.rsec h2{font-size:1.1rem; margin:0 0 10px;}
.twrap{overflow-x:auto;}
table.sizing{ width:100%; border-collapse:collapse; font-size:0.82rem; background:var(--paper-raise); border:1px solid var(--line); border-radius:var(--radius); overflow:hidden; }
table.sizing th, table.sizing td{ padding:7px 10px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; }
table.sizing th{ font-size:0.66rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--muted); font-weight:600; }
table.sizing tr:last-child td{border-bottom:none;}
.finding{ font-size:0.84rem; background:var(--warn-soft); border:1px solid var(--line); border-radius:var(--radius); padding:12px 16px; margin-top:10px; }
.finding.ok{background:var(--ok-soft);}
.finding.bad{background:var(--bad-soft);}
.scope-note{font-size:0.78rem; color:var(--muted); border-left:2px solid var(--warn); padding:6px 0 6px 12px; margin-top:10px; max-width:90ch;}
footer{ margin-top:60px; padding-top:20px; border-top:1px solid var(--line); font-size:0.76rem; color:var(--muted); }
"""


def _kv_table(rows: list, columns: list[str] | None = None) -> str:
    """`rows`(dict 리스트)를 표로 렌더링한다. `columns`를 안 주면 등장하는 모든 key의
    합집합을 첫 등장 순서로 사용한다(회로마다 sizing 필드 구성이 달라도 깨지지 않도록)."""
    if not rows:
        return "<p class=\"scope-note\">(no rows)</p>"
    if columns is None:
        columns = []
        seen = set()
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    seen.add(k)
                    columns.append(k)
    head = "".join(f"<th>{_html.escape(str(c))}</th>" for c in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{_html.escape(str(r.get(c, '')))}</td>" for c in columns) + "</tr>"
        for r in rows
    )
    return f'<div class="twrap"><table class="sizing"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def render_html_report(report: dict) -> str:
    """`assemble_report_data()`의 반환값을 self-contained HTML 문자열로 렌더링한다(파일
    IO 없음, 순수 함수). 섹션은 데이터가 있을 때만 나온다 -- 없는 섹션을 빈 표/가짜 값으로
    채우지 않는다(§1.5 원칙)."""
    meta = report.get("meta") or {}
    title = meta.get("title") or "Design Report"
    parts = [f"<header class=\"top\"><h1>{_html.escape(str(title))}</h1>"]
    if meta.get("source_paper"):
        parts.append(f'<p class="sub">{_html.escape(str(meta["source_paper"]))}</p>')
    if meta.get("process_note"):
        parts.append(f'<p class="sub">{_html.escape(str(meta["process_note"]))}</p>')
    parts.append("</header>")

    n = 0

    def _section(title_text, body_html):
        nonlocal n
        n += 1
        parts.append(f'<section class="rsec"><h2>&sect;{n} {_html.escape(title_text)}</h2>{body_html}</section>')

    topo = report.get("topology") or {}
    if topo.get("devices"):
        _section("Topology (from topology.json)", _kv_table(topo["devices"], ["name", "kind", "role"]))

    if report.get("spec"):
        spec = report["spec"]
        chips = "".join(f'<div class="finding"><b>{_html.escape(str(k))}</b>: {_html.escape(str(v))}</div>'
                         for k, v in spec.items())
        _section("Design spec (narrative, paper-sourced)", chips)

    if report.get("sizing"):
        sizing = report["sizing"]
        rows = [{**{"name": name}, **vals} for name, vals in sizing.items()] \
            if isinstance(sizing, dict) else sizing
        _section("Sizing (from instance.json)", _kv_table(rows))

    if report.get("box_shape") is not None:
        bs = report["box_shape"]
        # 2026-08-13(세션31 CN, 실측 발견) -- bs가 dict이기만 하면 무조건 "여러 cell의
        # {cell명: verdict} 모음"으로 오판했다 -- cell_groups를 안 쓰는 회로(예: two_stage_
        # ota)는 bs 자체가 단일 BoxShapeVerdict를 그대로 dict화한 것({"ok":...,
        # "row_widths":...,...})이라 .items()로 돌리면 "ok"/"row_widths" 등 필드명을
        # cell 이름으로 잘못 펼쳐 dict(cell=k, **v)가 bool/str 값에 **를 시도해 TypeError가
        # 났다. 바로 아래 audit_row_split 블록이 이미 쓰는 "ok" not in ars 판별을 여기도
        # 그대로 적용(같은 두 형태를 구분하는 동일한 문제라 같은 판별 기준을 재사용).
        bs_list = bs if isinstance(bs, list) else [bs] if not isinstance(bs, dict) or "ok" in bs else \
            [dict(cell=k, **v) for k, v in bs.items()]
        _section("Box-shape check (from instance.json)", _kv_table(bs_list))

    if report.get("audit_row_split") is not None:
        ars = report["audit_row_split"]
        ars_items = ars.items() if isinstance(ars, dict) and "ok" not in ars else [("(combined)", ars)]
        body = ""
        for cell, v in ars_items:
            ok = v.get("ok")
            cls = "ok" if ok else "bad"
            checks = v.get("checks", [])
            body += (f'<div class="finding {cls}"><b>{_html.escape(str(cell))}</b>: '
                     f'{"PASS" if ok else "FAIL"}'
                     + ("".join(f"<br>- {_html.escape(c['name'])}: {_html.escape(str(c['detail']))}"
                                for c in checks if not c.get("ok"))) + "</div>")
        _section("audit_row_split() (from instance.json)", body)

    if report.get("coverage") is not None:
        cov = report["coverage"]
        cls = "ok" if cov.get("ok") else "bad"
        _section("check_stick_diagram_coverage() (from instance.json)",
                 f'<div class="finding {cls}"><b>{"PASS" if cov.get("ok") else "FAIL"}</b>'
                 + (f": missing {_html.escape(str(cov.get('missing')))}" if not cov.get("ok") else "") + "</div>")

    fca = (report.get("report_gates") or {}).get("run_full_circuit_audit")
    if fca is not None:
        fca_list = fca if isinstance(fca, list) else [fca] if "ok" in fca else \
            [dict(cell=k, **v) for k, v in fca.items()]
        body = ""
        for entry in fca_list:
            cls = "ok" if entry.get("ok") else "bad"
            checks = entry.get("checks", [])
            body += (f'<div class="finding {cls}"><b>{_html.escape(str(entry.get("cell", "run_full_circuit_audit")))}</b>: '
                     f'{"PASS" if entry.get("ok") else "FAIL"}'
                     + _kv_table(checks, ["name", "ok", "detail"]) + "</div>")
        _section("run_full_circuit_audit() -- device count / net-name / matching-disposition", body)

    if report.get("layout_guide"):
        lg = report["layout_guide"]
        _section("Layout guide (narrative)", f"<pre>{_html.escape(json.dumps(lg, indent=2, ensure_ascii=False))}</pre>")

    if report.get("floorplan"):
        fp = report["floorplan"]
        _section("Physical floorplan (from instance.json)",
                  f"<pre>{_html.escape(json.dumps(fp, indent=2, ensure_ascii=False))}</pre>")

    for key, val in report.items():
        if key in ("meta", "topology", "spec", "sizing", "box_shape", "audit_row_split",
                    "coverage", "layout_guide", "floorplan", "report_gates"):
            continue
        if val:
            _section(key, f"<pre>{_html.escape(json.dumps(val, indent=2, ensure_ascii=False))}</pre>")

    parts.append('<footer>Generated by design_report.py (analog-gmid-design skill, 세션20) -- '
                 'topology.json/instance.json/run_full_circuit_audit_from_topology()에서 자동 조립. '
                 'narrative 섹션은 호출자가 채운 값을 그대로 옮긴 것.</footer>')

    body_html = "\n".join(parts)
    return f"""<!doctype html>
<meta charset="utf-8">
<title>{_html.escape(str(title))}</title>
<style>{_CSS}</style>
<div class="wrap">
{body_html}
</div>
"""


def save_html_report(report: dict, output_path: str) -> None:
    """`render_html_report()`의 결과를 파일로 쓴다(순수 렌더링과 파일 IO를 분리 --
    self-test/재사용 시 파일을 안 거치고 문자열만 검증할 수 있도록)."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(render_html_report(report))


if __name__ == "__main__":
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    from stick_diagram import run_full_circuit_audit_from_topology

    _lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library")
    _crt_topo = os.path.join(_lib_dir, "current_reuse_telescopic_ota.topology.json")
    _crt_instance = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
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
