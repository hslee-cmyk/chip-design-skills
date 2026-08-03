"""
topology.json의 모든 connectivity를 사람이 검토하기 쉬운 표(topology.md)로 렌더링한다.

배경(2026-08-03, current_reuse_telescopic_ota 논문 재검증 세션): AI가 논문 이미지/PDF에서
회로도를 읽고 "확인했다"고 판단한 뒤 topology.json에 반영한 연결이 실제로는 여러 곳 틀려
있었다(예: M2a/M3a가 직렬 캐스코드가 아니라 drain끼리 만나는 구조인데 직렬로 오독, M8이
독립 전류원인데 M11a 위에 직렬로 쌓인 것으로 오독) -- 이미지 인식만으로는 dense한 회로도의
connectivity를 신뢰성 있게 재현할 수 없다는 게 실측으로 확인됐다. `topology-extraction-
checklist.md`가 이미 이 문제를 §5(Stage 2 자동 이상탐지 게이트)/§6(Stage 3 선택적 인간 확인)
에서 방법론으로 제안해뒀지만 실제 구현이 없었다 -- 이 스크립트가 그 구현이다.

용도: topology.json을 새로 만들거나 connectivity를 수정할 때마다 반드시 이 스크립트를 실행해
(1) `<topology_name>.topology.md` 파일로 저장하고 (2) 같은 내용을 stdout에도 출력해(세션
창에서 바로 검토 가능하게) 사람이 표 형태로 전체 connectivity를 한눈에 재확인하게 한다.
텍스트로 51개 소자의 source/drain/gate를 하나씩 되짚는 것보다, "이 net에 정확히 어떤 단자들이
물려있는지"를 net 기준으로 뒤집어서 보여주는 쪽이 실제로 오류를 더 잘 잡아낸다(이 세션에서
발견된 오류 전부가 "내가 두 개의 다른 노드를 같은 이름으로 착각"하는 유형이었다 -- net 기준
표는 이런 착각을 구조적으로 드러낸다).

사용법: `python topology_to_markdown.py <topology.json 경로> [출력 .md 경로]`
        출력 경로 생략 시 입력과 같은 디렉터리에 `<topology_name>.topology.md`로 저장.
"""
import sys
import os
import json
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stick_diagram import load_topology  # noqa: E402


def _flag_dangling_nets(transistors, elements):
    """단자 1개짜리 net(=이 회로 안에서 딱 한 소자/수동소자/ideal source만 이 net을
    전류단자로 씀)을 찾는다. gate-only 참조(전류 안 흘림)는 셈에서 뺀다 -- gate만 참조하는
    게 정상인 net(예: 외부 입력 핀)도 많아서, source/drain(+`elements`의 terminals) 관점에서
    진짜 고아인 net만 "구조적으로 의심스러움"으로 flag. `elements`는 `passive_elements`+
    `ideal_sources`를 합친 것 -- 둘 다 세어야 R1/R2나 Iref처럼 netlist(트랜지스터)엔 안
    잡히지만 실제로는 연결된 net을 오탐하지 않는다."""
    sd_count = defaultdict(int)
    for t in transistors:
        sd_count[t.source] += 1
        sd_count[t.drain] += 1
    for p in elements:
        for net in p.get("terminals", []):
            sd_count[net] += 1
    return {net for net, n in sd_count.items() if n == 1}


def _flag_gate_only_nets(transistors, elements):
    """어느 소자의 source/drain(+`elements`의 terminal)으로도 안 쓰이고 gate로만 등장하는
    net -- 이 net을 실제로 구동하는 소자가 topology.json 안에 없다는 뜻(외부 입력 핀이면
    정상, 내부 노드인데 이러면 감지망 등이 누락됐을 가능성 -- 이번 세션 CMFB의 'Voc' dangling
    gate가 실제 사례, passive_elements 신설 전까지는 오탐이었음)."""
    sd_nets = set()
    gate_nets = set()
    for t in transistors:
        sd_nets.add(t.source)
        sd_nets.add(t.drain)
        gate_nets.add(t.gate)
    for p in elements:
        sd_nets.update(p.get("terminals", []))
    return gate_nets - sd_nets


def _net_table(transistors, elements):
    """net 이름 -> [(device_name, terminal), ...] (terminal in {source, drain, gate}
    또는 수동소자/ideal source의 terminal 순번 "t0"/"t1"/...)."""
    by_net = defaultdict(list)
    for t in transistors:
        by_net[t.source].append((t.name, "source"))
        by_net[t.drain].append((t.name, "drain"))
        by_net[t.gate].append((t.name, "gate"))
    for p in elements:
        for i, net in enumerate(p.get("terminals", [])):
            by_net[net].append((p["name"], f"t{i}"))
    return by_net


def render_markdown(topology_json_path: str) -> str:
    transistors, meta = load_topology(topology_json_path)
    with open(topology_json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    known_dangling = raw.get("_known_dangling_nets", {})  # {net_name: 근거 설명}
    passives = raw.get("passive_elements", [])
    ideal_sources = raw.get("ideal_sources", [])
    all_elements = passives + ideal_sources
    name = meta.get("topology_name", os.path.basename(topology_json_path))
    dangling = _flag_dangling_nets(transistors, all_elements) - set(known_dangling)
    gate_only = _flag_gate_only_nets(transistors, all_elements) - set(known_dangling)
    net_table = _net_table(transistors, all_elements)

    lines = []
    lines.append(f"# {name} -- topology connectivity table")
    lines.append("")
    lines.append(f"소스: `{topology_json_path}`. 이 파일은 `topology_to_markdown.py`가 "
                 "topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 "
                 "고친 뒤 다시 생성할 것.")
    lines.append("")

    if dangling or gate_only:
        lines.append("## ⚠️ 자동 플래그 (사람 재확인 필요)")
        lines.append("")
        if dangling:
            lines.append(f"- **고아 net(단자 1개, source/drain 기준)**: "
                          f"{', '.join(sorted(dangling))}")
            lines.append("  이 회로 안에서 이 net을 source/drain으로 쓰는 소자가 하나뿐입니다 "
                          "-- 외부 포트(정상)이거나, 실제로는 다른 소자와 연결돼야 하는데 "
                          "이름이 잘못 붙었을 가능성이 있습니다.")
        if gate_only:
            lines.append(f"- **구동 소자 없는 net(gate로만 참조됨)**: "
                          f"{', '.join(sorted(gate_only))}")
            lines.append("  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 "
                          "-- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 "
                          "그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.")
        lines.append("")
    else:
        lines.append("## ⚠️ 자동 플래그: 없음 (구조적으로는 이상 없음 -- §8 정직한 한계 참고)")
        lines.append("")

    if known_dangling:
        lines.append("## ℹ️ 해소된 플래그 (근거 있음 -- `_known_dangling_nets` 참고)")
        lines.append("")
        for net, reason in sorted(known_dangling.items()):
            lines.append(f"- **`{net}`**: {reason}")
        lines.append("")

    lines.append("## Net별 연결 표 (이 net에 물린 모든 단자)")
    lines.append("")
    lines.append("| Net | 연결된 단자 (device.terminal) | 단자 수 |")
    lines.append("|---|---|---|")
    for net in sorted(net_table.keys()):
        terms = sorted(net_table[net])
        term_str = ", ".join(f"{d}.{t}" for d, t in terms)
        if net in known_dangling:
            flag = " ℹ️"
        elif net in dangling or net in gate_only:
            flag = " ⚠️"
        else:
            flag = ""
        lines.append(f"| `{net}`{flag} | {term_str} | {len(terms)} |")
    lines.append("")

    lines.append("## 소자별 연결 표 (name/kind/source/drain/gate)")
    lines.append("")
    lines.append("| Name | Kind | Source | Drain | Gate |")
    lines.append("|---|---|---|---|---|")
    for t in sorted(transistors, key=lambda t: t.name):
        lines.append(f"| {t.name} | {t.kind} | `{t.source}` | `{t.drain}` | `{t.gate}` |")
    lines.append("")

    if passives:
        lines.append("## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)")
        lines.append("")
        lines.append("| Name | Kind | Terminals |")
        lines.append("|---|---|---|")
        for p in sorted(passives, key=lambda p: p["name"]):
            terms = ", ".join(f"`{n}`" for n in p.get("terminals", []))
            lines.append(f"| {p['name']} | {p.get('kind', '?')} | {terms} |")
        lines.append("")

    if ideal_sources:
        lines.append("## ⚡ Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`, "
                      "**구현 불가 소자**)")
        lines.append("")
        lines.append("| Name | Kind | Terminals | Value | Implementable |")
        lines.append("|---|---|---|---|---|")
        for s in sorted(ideal_sources, key=lambda s: s["name"]):
            terms = ", ".join(f"`{n}`" for n in s.get("terminals", []))
            value = s.get("value_amp", s.get("value_volt"))
            value_str = str(value) if value is not None else "미상"
            impl = s.get("implementable", False)
            lines.append(f"| {s['name']} | {s.get('kind', '?')} | {terms} | {value_str} "
                          f"| {'⚠️ False' if not impl else 'True'} |")
        lines.append("")
        lines.append("⚠️ 위 소자는 실제 회로에 없는 **이상적 모델링 소자**다(예: 논문의 외부 "
                      "레퍼런스 전류원/전압원) -- `implementable: false`. sizing/layout "
                      "파이프라인(`sizing_recipe.py`/`stick_diagram.py`)이 이 배열을 참조할 "
                      "일이 생기면 반드시 걸러내고 실제 트랜지스터로 구현하지 말 것.")
        lines.append("")

    lines.append(f"총 {len(transistors)}개 소자 + {len(passives)}개 수동소자 + "
                  f"{len(ideal_sources)}개 ideal source, {len(net_table)}개 net.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    try:  # Windows 콘솔 기본 코드페이지(cp949/cp1252)가 한글을 못 찍는 문제 방지
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) < 2:
        print("사용법: python topology_to_markdown.py <topology.json 경로> [출력 .md 경로]")
        sys.exit(1)
    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        topo_name = json.load(f).get("topology_name", os.path.splitext(os.path.basename(json_path))[0])
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(json_path)), f"{topo_name}.topology.md")
    md = render_markdown(json_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(md)
    print(f"\n[저장됨] {out_path}", file=sys.stderr)
