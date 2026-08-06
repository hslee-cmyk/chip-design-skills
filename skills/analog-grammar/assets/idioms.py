#!/usr/bin/env python3
"""
idioms.py — Stage 3 (L1 idiom 매칭) + Stage 4 (계층 축약)

아날로그 회로에는 실재하는 조합 문법이 있다. 이 문제는 본질적으로
digital synthesis 의 technology mapping 과 같다: cell library 를 놓고
subgraph isomorphism 으로 매칭하는 것.

  L0 primitive : MOS, R, C, L, diode
  L1 idiom     : 여기서 다루는 것. 30~50개면 실무 회로의 대부분을 덮는다.
  L2 block     : OTA, bandgap, LDO, integrator, VCO, PFD/CP, DAC unit cell
  L3 system    : ADC, PLL, PMIC

새 idiom 추가 방법
------------------
@idiom('name', level=1, priority=N) 로 데코레이트한 함수를 하나 쓴다.
함수는 (devs, cls, imp, role) 를 받아 Match 리스트를 반환한다.
priority 가 높을수록 겹침 해소에서 우선한다 (더 특수한 패턴일수록 높게).

주의: 패턴을 YAML DSL 로 만들지 않았다. 아날로그 idiom 은 'role 조건 +
넷 클래스 조건 + 그래프 형태'의 조합이라 선언형으로 짜면 금세 표현력이
부족해지고, 반쪽짜리 DSL 은 파이썬보다 읽기 어렵다.
"""
from collections import defaultdict
from netclass import (RAILS, RAILS_POS, RAILS_NEG, HIGH_Z, LOW_Z,
                      DIODE, CURR_SRC, CTRL_SRC, CASCODE, AMP, FOLLOWER,
                      SWITCH, ACTIVE_LOAD, BIAS, SIGNAL, INPUT, OUTPUT, FEEDBACK)

REGISTRY = []


class Match:
    def __init__(self, kind, devices, ports=None, note='', priority=0):
        self.kind, self.devices = kind, tuple(sorted(devices))
        self.ports, self.note, self.priority = ports or {}, note, priority
    def __repr__(self):
        return f"{self.kind}({'+'.join(self.devices)})"


def idiom(name, priority=0):
    def deco(fn):
        REGISTRY.append((name, priority, fn)); return fn
    return deco


def _by_name(devs): return {d['name']: d for d in devs}


# ── 단일 소자 ───────────────────────────────────────────────────────────
@idiom('diode-connected', priority=1)
def m_diode(devs, cls, imp, role):
    return [Match('diode-connected', [d['name']], {'node': d['D']}, priority=1)
            for d in devs if role[d['name']] == DIODE]


@idiom('source-follower', priority=3)
def m_follower(devs, cls, imp, role):
    return [Match('source-follower', [d['name']],
                  {'in': d['G'], 'out': d['S']}, priority=3)
            for d in devs if role[d['name']] == FOLLOWER]


# ── 2소자 이상 ──────────────────────────────────────────────────────────
@idiom('tail-current-source', priority=2)
def m_tail(devs, cls, imp, role):
    """차동쌍의 tail 노드를 구동하는 전류원. 단일 소자지만 기능적으로 유의미."""
    tails = set()
    for m in m_diffpair(devs, cls, imp, role):
        tails.add(m.ports['tail'])
    out = []
    for d in devs:
        if role[d['name']] in (CURR_SRC, CTRL_SRC) and d['D'] in tails:
            out.append(Match('tail-current-source', [d['name']],
                             {'tail': d['D'], 'gate': d['G']},
                             note='CMFB 제어' if role[d['name']] == CTRL_SRC else 'DC 바이어스',
                             priority=2))
    return out


@idiom('active-load', priority=2)
def m_active_load(devs, cls, imp, role):
    return [Match('active-load', [d['name']], {'node': d['D'], 'gate': d['G']}, priority=2)
            for d in devs if role[d['name']] == ACTIVE_LOAD]


@idiom('current-mirror', priority=4)
def m_mirror(devs, cls, imp, role):
    out, grp = [], defaultdict(list)
    for d in devs:
        grp[(d['G'], d['S'], d['type'])].append(d)
    for (g, s, t), ms in grp.items():
        if len(ms) < 2: continue
        ref = [m['name'] for m in ms if role[m['name']] == DIODE]
        if not ref: continue
        out.append(Match('current-mirror', [m['name'] for m in ms],
                         {'ref': ref[0], 'bias': g, 'rail': s},
                         note=f"{t}, ratio branches={len(ms)}", priority=4))
    return out


@idiom('differential-pair', priority=5)
def m_diffpair(devs, cls, imp, role):
    out, grp = [], defaultdict(list)
    for d in devs:
        if d['S'] in RAILS: continue
        grp[(d['S'], d['type'])].append(d)
    for (tail, t), ms in grp.items():
        if len(ms) != 2: continue
        a, b = ms
        if a['G'] == b['G']: continue
        if not all(role[m['name']] == AMP for m in ms): continue
        out.append(Match('differential-pair', [a['name'], b['name']],
                         {'tail': tail, 'inp': a['G'], 'inm': b['G'],
                          'outp': a['D'], 'outm': b['D']},
                         note=t, priority=5))
    return out


@idiom('cascode-stack', priority=4)
def m_cascode(devs, cls, imp, role):
    out, by_d = [], defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    for up in devs:
        if role[up['name']] != CASCODE: continue
        for lo in by_d[up['S']]:
            if lo['name'] == up['name'] or lo['type'] != up['type']: continue
            out.append(Match('cascode-stack', [lo['name'], up['name']],
                             {'mid': up['S'], 'out': up['D'],
                              'lower_role': role[lo['name']]},
                             note=up['type'], priority=4))
    return out


@idiom('push-pull-output', priority=6)
def m_pushpull(devs, cls, imp, role):
    """Class-AB / CMOS inverter 형 출력단: 상보 쌍이 출력 노드를 공유."""
    out, by_d = [], defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    for node, ms in by_d.items():
        if node in RAILS or len(ms) != 2: continue
        p = [m for m in ms if m['type'] == 'PMOS' and m['S'] in RAILS_POS]
        n = [m for m in ms if m['type'] == 'NMOS' and m['S'] in RAILS_NEG]
        if not (p and n): continue
        if not all(role[m['name']] in (AMP, ACTIVE_LOAD, CURR_SRC) for m in ms): continue
        sep = p[0]['G'] != n[0]['G']
        out.append(Match('push-pull-output', [p[0]['name'], n[0]['name']],
                         {'out': node, 'gp': p[0]['G'], 'gn': n[0]['G']},
                         note='class-AB (게이트 분리)' if sep else 'class-A/inverter (게이트 공통)',
                         priority=6))
    return out


@idiom('floating-battery', priority=5)
def m_battery(devs, cls, imp, role):
    """
    Class-AB 바이어스용 'magic battery': diode-connected 소자 2개가 직렬로
    쌓여 두 출력 게이트 사이의 DC 레벨차를 만든다.
    """
    out, by_d = [], defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    for up in devs:
        if role[up['name']] != DIODE: continue
        for lo in by_d[up['S']]:
            if lo['name'] == up['name'] or role[lo['name']] != DIODE: continue
            out.append(Match('floating-battery', [lo['name'], up['name']],
                             {'top': up['D'], 'mid': up['S'], 'bottom': lo['S']},
                             note='level shift between two gate drives', priority=5))
    return out


@idiom('current-reuse-pair', priority=9)
def m_current_reuse(devs, cls, imp, role):
    """
    ★ 이 라이브러리의 존재 이유를 보여주는 패턴 ★
    상보형 차동쌍 두 개가 같은 입력 넷을 게이트로 받고, 동일한 DC 전류경로
    안에 직렬로 놓인다. gm_eff = gmn + gmp 가 되어 같은 전류로 두 배 gm.
    canonical telescopic 과 겉모습이 비슷해서, '아는 회로'로 회상하면
    바로 이 차이가 지워진다. 구조 매칭은 지워지지 않는다.
    """
    pairs = m_diffpair(devs, cls, imp, role)
    out = []
    for i, a in enumerate(pairs):
        for b in pairs[i + 1:]:
            if a.note == b.note: continue                       # 같은 타입이면 아님
            if {a.ports['inp'], a.ports['inm']} != {b.ports['inp'], b.ports['inm']}:
                continue                                        # 같은 입력쌍이어야 함
            out.append(Match('current-reuse-pair', list(a.devices) + list(b.devices),
                             {'inp': a.ports['inp'], 'inm': a.ports['inm'],
                              'tail_hi': a.ports['tail'], 'tail_lo': b.ports['tail']},
                             note='gm_eff = gmn + gmp (동일 전류 재사용)', priority=9))
    return out


@idiom('telescopic-cascode-node', priority=8)
def m_telescopic(devs, cls, imp, role):
    """
    이득 노드에 상보형 cascode 두 개의 드레인이 마주 물린 구조.
    folded cascode 와의 구별점: telescopic 은 두 cascode 가 같은 전류
    경로 위에 있고, folded 는 별도 전류 가지를 통해 접힌다.
    여기서는 이득 노드 형태만 판정하고 fold 여부는 SFG 단계로 넘긴다.
    """
    out, by_d = [], defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    for node, ms in by_d.items():
        if node in RAILS or imp.get(node) != HIGH_Z or len(ms) != 2: continue
        if not all(role[m['name']] == CASCODE for m in ms): continue
        if ms[0]['type'] == ms[1]['type']: continue
        out.append(Match('cascoded-gain-node', [m['name'] for m in ms],
                         {'node': node}, note='상보형 cascode 대향', priority=8))
    return out


# ── 매칭 실행 및 겹침 해소 ──────────────────────────────────────────────
def match_all(devs, cls, imp, role):
    ms = []
    for name, prio, fn in REGISTRY:
        ms.extend(fn(devs, cls, imp, role))
    return ms


def resolve_overlaps(matches):
    """
    maximum-coverage 근사: priority 내림차순, 그다음 소자 수 내림차순으로
    탐욕 선택하되 이미 쓰인 소자를 다시 쓰지 않는다.
    단 단일 소자 idiom(diode-connected 등)은 주석 성격이라 항상 남긴다.
    """
    keep, used = [], set()
    for m in sorted(matches, key=lambda m: (-m.priority, -len(m.devices))):
        if len(m.devices) == 1:
            keep.append(m); continue
        if used & set(m.devices): continue
        keep.append(m); used |= set(m.devices)
    return keep, used


def contract(devs, kept):
    """
    Stage 4. 선택된 idiom 을 supernode 로 축약한다.
    반환: [(supernode_name, kind, member_devices, ports)]
    """
    sup, i = [], 0
    for m in kept:
        if len(m.devices) == 1: continue
        i += 1
        sup.append(dict(id=f"U{i}", kind=m.kind, members=list(m.devices),
                        ports=m.ports, note=m.note))
    # coverage 는 supernode 뿐 아니라 단일 소자 idiom 주석까지 포함해서 센다.
    # 그렇지 않으면 tail 전류원처럼 정상적으로 해석된 소자가 '미해석'으로 보인다.
    covered = {d for s in sup for d in s['members']}
    covered |= {d for m in kept if len(m.devices) == 1 for d in m.devices}
    leftover = [d['name'] for d in devs if d['name'] not in covered]
    return sup, leftover
