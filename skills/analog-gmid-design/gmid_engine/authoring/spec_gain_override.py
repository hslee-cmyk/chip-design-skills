"""블록 gain 고정 선언 `human.gain_budget_db_override` (설계 40 §3.1 '이 설계가 추가하는 spec 필드', 41 §5.7, 41 §1.7-3).

진입점: `gain_override_declaration(raw, topology) -> (tuple[GainOverrideDecl], tuple[SchemaHit])`.

모양: `[{"block": [<출력노드 넷 이름>, ...], "value_db": 수, "source": {...}}, ...]`. 키가 없으면(None) 빈 tuple.
* `block` -- **정렬된** 출력노드 넷 이름 배열이 블록 키다(41 §1.7-3): 비어 있지 않은 문자열 list, 사전순 엄격 증가
  (`block_not_sorted` -- 순서가 다르거나 같은 넷이 두 번이면). 한 블록에 표기 하나(키가 문서 표기에 따라 달라지지 않는다).
  `topology` 가 있으면 각 넷이 어느 단자에 있어야 한다(`block_net_unknown`). 같은 블록 키가 두 항목이면 `block_duplicate`.
* `value_db` -- 유한 수(`type`). `source` -- 필수, kind `user_spec` 만(`source_declaration_checks`).
* 받는 키 = block·value_db·source(`_` 주석 제외, 그 밖은 `key_hits` 가 옛 이름/회로 전용/미지 키로 거부한다).
이 블록 키가 S1v 의 실제 블록과 맞는지(`override_block_unknown`)는 구조 유도가 끝난 뒤 GB5 가 판정한다(여기서는 구조를 모른다).
결과는 블록 키 순서 tuple(문서 순서와 무관 -- 지문이 같다).
"""
from ._spec_fields import at, finite_number, key_hits
from ._terminal_nets import mos_terminal_nets, two_terminal_nets
from .spec_model import GainOverrideDecl
from .spec_sources import source_declaration_checks
from .topology_model import SchemaHit

WHERE = "human.gain_budget_db_override"
SECTION = "gain_budget_db_override"
ITEM_KEYS = ("block", "value_db", "source")


def _block(raw, where, nets, hits):
    """블록 키 -> 정렬 tuple 또는 None(위반은 hits 에 더한다)."""
    place = at(where, "block")
    if not isinstance(raw, list) or not raw or not all(isinstance(n, str) and n for n in raw):
        hits.append(SchemaHit("type", place, "block 은 비어 있지 않은 넷 이름(문자열) list 여야 한다: " + repr(raw)))
        return None
    if any(a >= b for a, b in zip(raw, raw[1:])):
        hits.append(SchemaHit("block_not_sorted", place, "블록 키는 출력노드 이름을 사전순으로 정렬한 배열이어야 한다(중복 불가, "
                              "41 §1.7-3): " + repr(raw), tuple(raw)))
        return None
    if nets is not None:
        unknown = [n for n in raw if n not in nets]
        for net in unknown:
            hits.append(SchemaHit("block_net_unknown", place, "블록 넷 " + repr(net) + " 이 어느 단자에도 없다", (net,)))
        if unknown:
            return None
    return tuple(raw)


def gain_override_declaration(raw, topology):
    if raw is None:
        return (), ()
    if not isinstance(raw, list):
        return (), (SchemaHit("type", WHERE, "gain_budget_db_override 는 list 여야 한다: " + type(raw).__name__),)
    nets = None
    if topology is not None:
        nets = mos_terminal_nets(topology.devices) | two_terminal_nets(topology.passives + topology.sources)
    hits = []
    out = []
    for index, item in enumerate(raw):
        where = at(WHERE, index)
        if not isinstance(item, dict):
            hits.append(SchemaHit("type", where, "항목은 {block, value_db, source} 객체여야 한다"))
            continue
        before = len(hits)
        hits.extend(key_hits(item, ITEM_KEYS, where))
        block = _block(item.get("block"), where, nets, hits)
        value = item.get("value_db")
        if not finite_number(value):
            hits.append(SchemaHit("type", at(where, "value_db"), "value_db 는 유한 수여야 한다: " + repr(value)))
        source, source_hits = source_declaration_checks(item.get("source"), where, SECTION)
        hits.extend(source_hits)
        if len(hits) == before:
            out.append(GainOverrideDecl(block, float(value), source))
    seen = set()
    for index, decl in enumerate(out):
        if decl.block in seen:
            hits.append(SchemaHit("block_duplicate", at(WHERE, index), "같은 블록 키가 두 번: " + repr(decl.block), decl.block))
        seen.add(decl.block)
    if hits:
        return (), tuple(hits)
    return tuple(sorted(out, key=lambda d: d.block)), ()
