"""셀 분류 (설계 41 §1.4, 계획 N3.2-3 '셀 우선순위').

진입점: `classify_cells(model, ground, reach, sense, view_id) -> CellsResult`.

뷰마다 모든 MOS 에 셀 하나를 붙인다(`signal_reach` 의 신호 넷 S·순방향 F 위에서):
1. gate == drain -> `diode_load`(셀이 아니라 그 노드의 부하 1/gm. 도달성·엣지·거리에는 소자 단위로 그대로 센다).
2. gate ∈ S(신호를 받는 gate):
   * drain 이 교류접지면 CD(출력 = source), source 가 교류접지면 CS(출력 = drain).
   * 둘 다 아니면 source 가 **순방향 위 다른 신호 셀의 입력(그 셀의 gate)이나 출력 포트(감지 넷)** 에 닿는지 본다. 닿으면 CD·CS
     이중 출력이라 `cell_ambiguous`(기록만, DEC-59 정지), 닿는 상대 셀도 모호하면 그 쌍을 함께 올린다. 닿지 않으면 CS(degeneration).
3. gate ∉ S(신호 경로 밖):
   * source 와 drain 이 모두 신호 넷이고 같은 두 노드 사이에 반대 방향으로 놓인 소자가 정확히 둘이면 둘이 pass 묶음 하나.
     같은 두 노드에 셋 이상이면서 방향이 섞인 묶음은 `pass_group_unsupported`(기록만).
   * 아니고 source ∈ S 이면 CG(출력 = drain). 그 밖은 `off`.
CG·pass 의 구분은 도달 거리나 우회 가능성이 아니라 위 구조 조건만 쓴다(plan 규칙 3). 순방향 제한: 대조표 셀 수는 출력 단자가 F 에
드는 셀(`CellInfo.forward`)만 센다.
"""
import dataclasses

from gmid_engine.core import sorted_items

from .s1v_values import (
    PAIR,
    CELL_CD,
    CELL_CG,
    CELL_CS,
    CELL_DIODE_LOAD,
    CELL_OFF,
    CELL_PASS,
    F_CELL_AMBIGUOUS,
    F_PASS_GROUP,
    SEVERITY_UNSUPPORTED,
    CellInfo,
    Finding,
    PassBundle,
)


@dataclasses.dataclass(frozen=True)
class CellsResult:
    """`cells` = CellInfo 이름순, `bundles` = pass 묶음, `findings` = 기록."""

    cells: tuple
    bundles: tuple
    findings: tuple


def _signal_cells(model, ground, signal):
    """gate ∈ S 인 소자의 (소자 -> 'CD' | 'CS' | None(모호))."""
    kinds = {}
    for m in model.mos:
        if m.g == m.d or m.g not in signal:
            continue
        if m.d in ground:
            kinds[m.name] = CELL_CD
        elif m.s in ground:
            kinds[m.name] = CELL_CS
        else:
            kinds[m.name] = None
    return kinds


def _ambiguity(model, reach, sense, kinds, view_id):
    """모호한 소자의 이름 집합과 기록. 상대 셀 = 모호 소자의 source 를 gate 로 읽는 다른 신호 셀(출력이 순방향 위이거나 그 셀도 모호)."""
    flagged = set()
    findings = []
    for m in model.mos:
        if m.name not in kinds or kinds[m.name] is not None:
            continue
        touching = []
        for other in model.by_gate.get(m.s, ()):
            if other.name == m.name or other.name not in kinds:
                continue
            out = {CELL_CD: other.s, CELL_CS: other.d}.get(kinds[other.name])
            if out is None or out in reach.forward:
                touching.append(other.name)
        if m.s in sense or touching:
            flagged.add(m.name)
            findings.append(Finding(F_CELL_AMBIGUOUS, SEVERITY_UNSUPPORTED, view_id, tuple(sorted({m.name, *touching})),
                                    "source 가 순방향 위 신호 셀 입력 또는 출력 포트에 닿아 CD·CS 이중 출력이다",
                                    ("N3.2-3", "DEC-59")))
    return flagged, findings


def _pass_groups(model, signal, ground, view_id):
    candidates = [m for m in model.mos
                  if m.g not in signal and m.g != m.d and m.d in signal and m.s in signal and m.d not in ground]
    groups = {}
    for m in candidates:
        groups.setdefault(frozenset((m.d, m.s)), []).append(m)
    bundles = []
    findings = []
    in_bundle = {}
    for nodes, members in sorted_items(groups, key=sorted):
        directions = {(m.d, m.s) for m in members}
        if len(members) == len(PAIR) and len(directions) == len(PAIR):
            names = tuple(sorted(m.name for m in members))
            bundles.append(PassBundle(names, tuple(sorted(nodes))))
            in_bundle.update({name: names for name in names})
        elif len(directions) > 1:
            names = tuple(sorted(m.name for m in members))
            findings.append(Finding(F_PASS_GROUP, SEVERITY_UNSUPPORTED, view_id, names,
                                    "같은 두 노드 사이에 소자 " + str(len(members)) + "개가 방향이 섞여 놓였다", ("N3.2-3", "DEC-76")))
            in_bundle.update({name: () for name in names})
    return tuple(bundles), tuple(findings), in_bundle


def classify_cells(model, ground, reach, sense, view_id):
    signal = reach.signal
    kinds = _signal_cells(model, ground, signal)
    flagged, findings = _ambiguity(model, reach, sense, kinds, view_id)
    bundles, pass_findings, in_bundle = _pass_groups(model, signal, ground, view_id)
    out = []
    for m in model.mos:
        degeneration = False
        if m.g == m.d:
            kind, net = CELL_DIODE_LOAD, ""
        elif m.name in kinds:
            kind = CELL_CS if kinds[m.name] is None else kinds[m.name]
            degeneration = kinds[m.name] is None and m.name not in flagged
            net = m.s if kind == CELL_CD else m.d
        elif m.name in in_bundle:
            kind, net = (CELL_PASS, "") if in_bundle[m.name] else (CELL_OFF, "")
        elif m.s in signal:
            kind, net = CELL_CG, m.d
        else:
            kind, net = CELL_OFF, ""
        if kind == CELL_PASS:
            forward = all(node in reach.forward for node in next(b.nodes for b in bundles if m.name in b.members))
        else:
            forward = bool(net) and net in reach.forward
        out.append(CellInfo(m.name, kind, net, forward, degeneration))
    return CellsResult(tuple(out), bundles, tuple(findings) + pass_findings)
