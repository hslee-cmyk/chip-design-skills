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

⚠️⚠️ **`@idiom` REGISTRY에 없는 재사용 가능한 유틸리티 함수들 (신규 코드 작성 전 필독)**
------------------------------------------------------------------------------
2026-08-18(chip-design-skills 세션) -- 이 파일 안의 REGISTRY 밖 함수(아래)를 몰라서
Transistor connectivity 위에 새 그래프 탐색/BFS 코드를 손으로 다시 짜다가 방향을
두 번 틀린 사고가 실제로 있었다(`audit_theta_root_direction()`, 3차 재작성 끝에
이 함수들 재사용으로 정착). **캐스코드 체인/root-follower 방향/diode 레퍼런스 전파
같은 걸 다루려 한다면, 새 코드를 짜기 전에 먼저 이 목록부터 확인할 것**:

- `m_cascode(devs, cls, imp, role)` -- 캐스코드로 기능하는 소자쌍을 찾는다(같은 kind
  직렬 `up.S==lo.D` + 2026-08-18 신설 PMOS/NMOS 경계 `up.D==lo.D` cross-kind 둘 다).
  `Match.kind=='cascode-stack'`, `ports`에 `lo`/`up`이 항상 명시됨.
- `_cascode_lo_up_pairs(devs, matches)` -- `cascode-stack` Match들을 `[(lo_name,
  up_name), ...]`로 정리(순서 모호성 없이).
- `propagate_reference_role_through_cascode(matches, seed_names, devs)` -- **seed로
  준 소자 집합("이 성질을 가졌다고 판정한 소자들")을 캐스코드 체인 위로 전파**한다
  (다단 캐스코드까지 고정점 반복). "A가 B보다 전류를 먼저 정하는 쪽인가?"(root/
  reference 방향, lo/up 방향) 판단이 필요하면 이 함수를 먼저 쓸 것 -- 직접 BFS를
  짜지 않는다.
- `find_cascoded_active_load_legs(devs, matches, imp, cls=None)` -- current-mirror
  다리 위에 캐스코드가 쌓여 진짜 이득노드(HIGH_Z)가 그 위로 옮겨간 경우까지
  active-load 판정을 확장(`m_mirror()`의 `active_load_legs`가 놓치는 부분).
- `netclass.stack_edges(devs)` -- role/net분류 불필요, 순수 connectivity로
  "X.source==Y.drain이면 Y가 X 위에 얹혀있다"는 관계 전부를 낸다(레이어별 대칭쌍
  전파, `find_stacked_matching_candidates()` 참고).

`references/analog-grammar-integration.md`(analog-gmid-design skill)에 더 상세한
연동 설계/self-test 계획이 있다 -- 그 문서도 이 유틸리티들이 신설되기 전(§6까지만)
버전이라 함께 갱신 대상이다.
"""
from collections import defaultdict, deque
from netclass import (RAILS, RAILS_POS, RAILS_NEG, HIGH_Z, LOW_Z,
                      DIODE, CURR_SRC, CTRL_SRC, CASCODE, AMP, FOLLOWER,
                      SWITCH, ACTIVE_LOAD, BIAS, SIGNAL, INPUT, OUTPUT, FEEDBACK,
                      is_mutual_loop_partner)

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


def _reaches_output(node, devs, cls, maxhop=6):
    """`node`가 어떤 소자의 gate로 쓰이고, 그 소자의 drain/source를 타고 가다 보면
    `cls`상 `OUTPUT`으로 분류된 net에 도달하는지 BFS로 확인한다 -- 도달하면 hop 수,
    못 하면 `None`. `sfg.build_sfg()`의 gm-edge(신호 클래스가 이미 SIGNAL/INPUT/
    OUTPUT/FEEDBACK인 게이트만 인정)보다 **더 관대하게** 아무 게이트나 따라간다 --
    2026-08-08 실측(사용자 지적, `current_reuse_telescopic_ota`)으로 `Vg15`(`netclass`가
    구조 규칙상 `BIAS`로 분류)가 실은 `M15.gate`로 `Vom`(선언된 출력)까지 1-hop인
    사례가 나왔다 -- **BIAS로 분류된 노드도 실제로는 출력단 게이트를 구동할 수 있고,
    그건 connectivity를 게이트까지 따라가야만 보인다.** `outputs=`를 선언하지 않은
    호출(`cls`에 `OUTPUT`이 아예 없음)에서는 이 함수가 항상 `None`만 반환해 부작용이
    없다."""
    by_gate = defaultdict(list)
    for d in devs: by_gate[d['G']].append(d)
    seen, q = {node}, deque([(node, 0)])
    while q:
        n, h = q.popleft()
        if cls.get(n) == OUTPUT: return h
        if h >= maxhop: continue
        for d in by_gate.get(n, []):
            for nxt in (d['D'], d['S']):
                if nxt not in seen:
                    seen.add(nxt); q.append((nxt, h + 1))
    return None


# ── 단일 소자 ───────────────────────────────────────────────────────────
@idiom('diode-connected', priority=1)
def m_diode(devs, cls, imp, role):
    return [Match('diode-connected', [d['name']], {'node': d['D']}, priority=1)
            for d in devs if role[d['name']] == DIODE]


@idiom('diode-cascode', priority=4)
def m_diode_cascode(devs, cls, imp, role):
    """diode-connected 소자(`up`, `up.G==up.D`) 바로 아래(직렬, `lo.D==up.S`)에 얹힌
    같은 kind 소자 `lo`가 **자기 게이트를 그 diode의 노드로 그대로 받는**(`lo.G==up.D`)
    패턴 -- `floating-battery`(둘 다 diode)와 달리 `lo`는 diode가 아니어도 된다.

    2026-08-08 신설(사용자 지적) -- `M63`(role=`CASCODE`, gate=`Vbias3`)이 `M64`
    (diode-connected, gate=drain=`Vbias3`) 바로 아래 얹혀 같은 노드를 게이트로 받고,
    `M58`(role=`CASCODE`, gate=`Vbias2`)도 `M57`(diode, gate=drain=`Vbias2`)에 대해
    정확히 같은 관계다 -- 이런 "diode-connected 위에 얹힌 캐스코드가 그 diode 노드로
    자기 게이트를 직접 받는" 구조는 지금까지 `diode-connected`(단일 소자, `up`만 봄)와
    `m_cascode()`(직렬 판정만, 게이트 출처는 안 봄) 어느 쪽도 명시적으로 못 잡고 있었다
    -- 정밀한 다이오드 기준전압을 만드는 흔한 회로 패턴(예: 캐스코드된 diode reference)
    인데 idiom 어휘에 이름이 없었다.

    ⚠️ `ports['lo']`/`ports['diode']`로 소자 이름을 명시(2026-08-08 추가) -- `Match.
    devices`는 `sorted()`라 이름 알파벳순대로 `(lo,diode)` 또는 `(diode,lo)`가 뒤섞여
    나온다(예: `M63`/`M64`는 `lo`가 먼저(`M63<M64`), `M57`/`M58`은 `diode`가 먼저
    (`M57<M58`)) -- `devices[0]`을 그냥 `lo`로 가정하면 소자 이름에 따라 조용히
    틀린다(실측으로 직접 걸림, headroom_role 재평가 스크립트에서 처음 발견)."""
    out, by_d = [], defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    for up in devs:
        if role[up['name']] != DIODE: continue
        for lo in by_d[up['S']]:
            if lo['name'] == up['name'] or lo['type'] != up['type']: continue
            if lo['G'] != up['D']: continue
            out.append(Match('diode-cascode', [lo['name'], up['name']],
                             {'lo': lo['name'], 'diode': up['name'],
                              'diode_node': up['D'], 'lo_role': role[lo['name']]},
                             note='diode 노드를 그대로 게이트로 받는 하위 캐스코드', priority=4))
    return out


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
    """⚠️ 2026-08-14(chip-design-skills 세션34, 사용자 지적) -- 미러의 non-ref leg가
    `role`상 `AMPLIFYING`으로 나올 수 있다(gate net이 SIGNAL로 분류되면 `assign_roles()`의
    role 우선순위상 `ACTIVE_LOAD` 판정보다 `AMP`가 항상 먼저 걸림, 예: 5T/2단 OTA의
    `M4` -- diode 레퍼런스 `M3`을 미러하면서 동시에 자기 게이트가 반대쪽 diffpair branch
    net이라 SIGNAL로 분류됨). 이건 "active-load가 아니다"라는 뜻이 아니라 role의 단일
    라벨 설계가 "게이트가 신호를 받는다"와 "드레인이 HIGH_Z 이득노드다"라는 **동시에 참일
    수 있는 두 사실** 중 하나만 표현할 수 있어서 생기는 그림자일 뿐이다 -- `role`을 덮어쓰지
    않고(다른 소비자가 이미 `role`의 단일 라벨 계약에 기대고 있음), 이 idiom이 이미 받고
    있는(그러나 지금까지 안 쓰던) `imp` 파라미터로 non-ref leg 각각의 실제 임피던스 등급을
    직접 확인해 `active_load_legs` 포트로 노출한다 -- role 라벨과 무관하게 "이 미러의 어느
    leg가 실제로 HIGH_Z 이득노드에 앉아있는가"를 소비자가 직접 물을 수 있게 한다.

    ⚠️ **2026-08-14 세션34 후속(사용자 지적, `nmcnr_amplifier`의 `M203`/`M204` 계기) --
    `ref_is_signal` 포트 추가**: diode-connected 레퍼런스(`ref`) 자신의 노드(`g`, 곧
    `ref`의 gate==drain)가 고정 `BIAS`가 아니라 `SIGNAL`이면(예: `M203`이 `M201`의 신호
    스윙을 그대로 받는 이득단 능동부하 자신이면서 동시에 diode-connected인 경우), 그
    레퍼런스를 미러하는 다리들의 목적은 전류비가 아니라 신호-종속 전압/전류 관계를
    그대로 "복사"하는 것이다(diffpair/구조 대칭이 전혀 없어도 성립하는 원칙, `M3`/`M4`류
    diffpair branch-load와는 별개의 독립 신호). `g`는 이미 계산돼 있고 `cls`도 이미
    파라미터로 받고 있어 재계산 없이 그대로 노출한다.

    ⚠️ **2026-08-15(chip-design-skills 세션35 후속, 사용자 지적 -- "신호경로인지는
    analog-grammar를 쓰면 알 수 있잖아") -- `active_load_legs`에 `cls` 필터 추가**:
    `imp.get(D)==HIGH_Z`만으로는 "드레인만 모인 노드"(§1f, `netclass.classify_nets()`)
    라는 **위상적** 사실만 확인할 뿐, 그 노드가 진짜 증폭 신호 경로인지 아니면 다른
    바이어스 생성 회로가 읽어가는 순수 DC 기준 노드인지는 구분 못 한다(실측 발견:
    `current_reuse_telescopic_ota`의 `M60`/`M61`/`M68` -- 드레인이 `Vbias3`/`Vbias4`/
    `Vbias2`로 전부 `cls==BIAS`, 다른 바이어스 생성기가 읽어가는 노드일 뿐인데 위상만
    보면 "active load"로 오탐됨). `classify_nets()`가 이미 계산해주는 `cls`(그 노드가
    실제로 무엇으로 쓰이는지 -- `BIAS`/`SIGNAL`/`OUTPUT`/`INTERNAL` 등)로 `BIAS`인
    경우만 걸러낸다(`SIGNAL`/`OUTPUT`/`INTERNAL`은 전부 통과 -- `folded_cascode`의
    `out`=`INTERNAL`, `nmcnr_amplifier`의 `NodeS2`=`SIGNAL`/`Vout`=`OUTPUT` 전부 실측
    확인, 진짜 이득 노드는 `BIAS`로 분류되는 일이 없다)."""
    out, grp = [], defaultdict(list)
    for d in devs:
        grp[(d['G'], d['S'], d['type'])].append(d)
    for (g, s, t), ms in grp.items():
        if len(ms) < 2: continue
        ref = [m['name'] for m in ms if role[m['name']] == DIODE]
        if not ref: continue
        active_load_legs = [m['name'] for m in ms
                             if m['name'] != ref[0] and imp.get(m['D']) == HIGH_Z
                             and cls.get(m['D']) != BIAS]
        out.append(Match('current-mirror', [m['name'] for m in ms],
                         {'ref': ref[0], 'bias': g, 'rail': s,
                          'active_load_legs': active_load_legs,
                          'ref_is_signal': cls.get(g) == SIGNAL},
                         note=f"{t}, ratio branches={len(ms)}", priority=4))
    return out


@idiom('differential-pair', priority=5)
def m_diffpair(devs, cls, imp, role):
    """같은 non-rail source를 공유하는 소자 쌍을 differential pair 후보로 매칭한다.

    ⚠️ 2026-08-07 수정(chip-design-skills 세션24) -- 원래는 source를 공유하는 소자가
    "정확히 2개"일 때만 인정했는데, 셋째 소자가 같은 source에 우연히 얹혀 있으면(예:
    bias 인출용 소자가 같은 tail net에 물림) 이 조건이 깨져 **진짜 differential pair를
    통째로 놓쳤다**(실측: `current_reuse_telescopic_ota`의 `M1a`/`M1b`가 `M58`이 같은
    `Vx`를 source로 쓴다는 이유만으로, `M4a`/`M4b`가 `M63`이 같은 `Vy`를 쓴다는 이유만
    으로 전부 안 잡혔다 -- `stick_diagram.py`의 `find_differential_pair_candidates()`가
    이미 같은 문제를 같은 방식으로 고쳤음). 이제 같은 source를 공유하는 그룹 안에서
    가능한 모든 쌍을 개별적으로 판정한다 -- 셋째(넷째, ...) 소자가 섞여 있어도 진짜
    쌍은 그대로 잡히고, 무관한 조합은 여전히 (같은 gate 또는 role!=AMP 조건으로) 걸러진다.

    ⚠️ 이 수정이 그 자리에서 새 오탐을 하나 만들었다(실측으로 발견, 바로 다음 조건으로
    막음) -- `role[up] in (..., AMPLIFYING, ...)`로 `m_cascode()`를 넓히는 것과 맞물려,
    `M58`(bias 인출용, `M1a`/`M1b`와 같은 `Vx`를 source로 씀)의 role이 CMFB 승격 후
    `AMPLIFYING`으로 바뀌면 `M1a`/`M58`, `M1b`/`M58`까지 "쌍 단위로 다 비교"하는 이
    함수의 새 로직에 그대로 걸려 differential-pair로 오탐됐다. `M1a`(`gate=Vip`,
    class=`INPUT`)과 `M58`(`gate=Vbias2`, class=`SIGNAL`)은 게이트 net **class**가
    다르다는 게 실측으로 확인된 구별점 -- 진짜 differential pair는 두 입력이 의미상
    대칭인 같은 종류의 net(둘 다 `INPUT`, 또는 승격된 2차 입력이면 둘 다 그 class)이어야
    한다는 원칙을 `cls.get(a['G']) == cls.get(b['G'])` 조건으로 코드화했다.

    ⚠️ 2026-08-18 확장(chip-design-skills 세션, `m_cascode()` cross-kind 확장 검증 중
    실측 발견) -- `role==AMP`만 인정하던 게 **CMFB 비교기 차동쌍**(게이트가 `FEEDBACK`으로
    분류돼 `role=CONTROLLED_CURRENT_SOURCE`가 되는 경우, 예: `current_reuse_telescopic_
    ota`의 `M37a`(gate=`Voc`)/`M37b`(gate=`Voc_des`))을 놓쳤다 -- 그 결과 `m_cascode()`의
    `diffpair_legs` 제외가 안 먹혀 `M38`(tail) 위에 얹힌 평범한 캐스코드로 오분류됐다.
    이 파일의 `m_tail()`(위, CMFB 제어/DC 바이어스 tail을 `(CURR_SRC, CTRL_SRC)` 둘 다
    인정)과 원래 비일관됐던 부분 -- `AMP`뿐 아니라 `CTRL_SRC`도 "진짜 신호를 증폭/비교하는
    소자"로 인정한다(둘 다 게이트가 실제 신호 클래스를 받는다는 점은 같고, `FEEDBACK`이냐
    `SIGNAL/INPUT/OUTPUT`이냐만 다르다 -- `assign_roles()`의 role 우선순위상 `FEEDBACK`이
    먼저 걸려 `CTRL_SRC`가 되는 것뿐, 기능은 differential 비교와 동일)."""
    out, grp = [], defaultdict(list)
    for d in devs:
        if d['S'] in RAILS: continue
        grp[(d['S'], d['type'])].append(d)
    for (tail, t), ms in grp.items():
        if len(ms) < 2: continue
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                a, b = ms[i], ms[j]
                if a['G'] == b['G']: continue
                if role[a['name']] not in (AMP, CTRL_SRC) or role[b['name']] not in (AMP, CTRL_SRC): continue
                if cls.get(a['G']) != cls.get(b['G']): continue
                out.append(Match('differential-pair', [a['name'], b['name']],
                                 {'tail': tail, 'inp': a['G'], 'inm': b['G'],
                                  'outp': a['D'], 'outm': b['D']},
                                 note=t, priority=5))
    return out


@idiom('cascode-stack', priority=4)
def m_cascode(devs, cls, imp, role):
    """물리적으로 직렬(`up.S == lo.D`)인 같은 kind 소자쌍을 캐스코드로 매칭한다.

    ⚠️ 2026-08-07 수정(사용자 지적, chip-design-skills 세션24) -- 원래는
    `role[up]=='CASCODE'`(게이트가 고정 `BIAS`로 분류될 때만 나오는 role)만 인정해서,
    캐스코드 게이트가 CMFB 등으로 능동 구동돼 `SIGNAL`/`FEEDBACK`로 재분류되면
    (role이 `AMPLIFYING`/`CONTROLLED_CURRENT_SOURCE`로 바뀜) 물리적으로는 여전히
    캐스코드로 동작하는데도 매칭이 통째로 빠졌다(regulated/gain-boosted cascode류 --
    실측: `current_reuse_telescopic_ota`의 `M2a`가 CMFB 경로로 `Vbias2`가 `SIGNAL`이
    되면서 이 문제로 빠짐, `Vcmfb`를 `feedbacks=`로 선언하면 같은 이유로
    `CONTROLLED_CURRENT_SOURCE`가 되는 경우도 실측 확인).

    role 허용 범위를 `(CASCODE, AMPLIFYING, CONTROLLED_CURRENT_SOURCE)`로 넓히되,
    `up`이 (위) `m_diffpair()`가 찾은 differential-pair의 다리면 제외한다 -- 안 그러면
    "차동쌍 입력소자가 자기 tail 전류원 위에 있는 것"(예: `M1a` on `M6`)까지 캐스코드로
    오탐된다(role만으로는 이 둘을 구별 못 함 -- 둘 다 `AMPLIFYING`이 될 수 있다는 게
    실측으로 확인됨, `m_diffpair()`가 정확해야 이 제외도 정확해진다). diode-connected는
    role이 항상 `DIODE`라 이 허용 목록에 없어 자동으로 계속 제외된다(2-diode 레벨시프트
    체인이 캐스코드로 오탐되는 것 방지, 실측 확인됨). ⚠️ 여전히 일반적인 캐스코드 탐지는
    아니다 -- role이 이 세 값이 아닌 다른 조합(예: `FOLLOWER`, `UNRESOLVED`)으로 분류되는
    경우는 여전히 못 잡는다.

    ⚠️ 2026-08-08 추가 제외(사용자 지적) -- "물리적으로 직렬"이라는 조건만으로는
    `up`이 정말 캐스코드로 **기능**하는지 보장 못 한다는 게 실측으로 드러났다: `M8`
    (`CURRENT_SOURCE`)+`M9a`(`CASCODE`)가 이 조건을 전부 만족해 캐스코드로 매칭됐지만,
    `M9a`의 실제 기능은 `M8`의 출력 임피던스를 부스트하는 게 아니라 Monticelli
    class-AB floating current source(`M9a`(PMOS)/`M9b`(NMOS)가 비-레일 노드 2개
    사이를 상보 anti-parallel로 마주보는 구조, 아래 `floating-current-source` 참고)
    의 절반이었다 -- `m_diffpair()`와 정확히 같은 이유(role만으로는 두 기능을 구별
    못 함)로 같은 방식(leg 집합 제외)으로 막는다. **analog-grammar는 physical
    layout 도구가 아니라 functional 이해 도구다** -- "같은 well에 물리적으로 쌓을 수
    있다"는 사실이 있어도 그게 캐스코드로 "기능"한다는 뜻은 아니므로, 그 physical
    adjacency 자체가 필요한 소비자(예: `stick_diagram.py`의 layout 스택 제안)는
    `netclass.stack_edges()`처럼 role/idiom 해석이 섞이지 않은 순수 구조 함수를 따로
    써야 한다(2026-08-08 세션, 아래 `m_float_source()`가 실측 근거).

    ⚠️ 2026-08-08 추가 제외 #2(사용자 지적) -- `float_legs` 제외는 `M9a`류처럼 이미
    이름 붙은 다른 idiom(floating-current-source)이 있을 때만 통한다. 그런 idiom이
    없는 새 회로에서도 같은 오탐을 막으려면 더 근본적인 판정이 필요하다: 캐스코드가
    캐스코드로 "기능"하려면 부스트된 임피던스가 **drain 쪽(high-Z)**에 나타나야 한다
    -- source 쪽 임피던스는 어떤 회로든 항상 `1/gm` 근방(low-Z)이라 예외가 없다.
    그러니 `up.source`가 `up.drain`보다 선언된 `OUTPUT`에 (더 가깝게 또는 동률로)
    도달하면, 그 소자는 "출력이 low-Z 쪽에 있는 캐스코드"라는 모순된 상태다 -- 라벨을
    `mid`/`out`으로 바꿔 부른다고 해결되는 게 아니라(source가 low-Z라는 물리적 사실은
    안 바뀜), 애초에 캐스코드로 기능하고 있지 않다는 뜻이라 매칭 자체를 제외한다
    (`_reaches_output()`, `outputs=` 미선언 시엔 `cls`에 `OUTPUT`이 없어 이 조건이
    항상 거짓 -- 부작용 없음).

    ⚠️ 2026-08-18 확장(chip-design-skills 세션, 사용자 지적 -- "PMOS/NMOS 경계는 항상
    drain-drain이야", "m_cascode() 자체를 확장(근본 해결)") -- 위 `up.S==lo.D`(같은 kind만
    인정) 판정 하나로는 **PMOS/NMOS 경계 캐스코드**(다이오드로 전류를 생성하는 소자와
    반대 kind의 캐스코드가 drain-drain으로 만나는 구조, 예: `nmcnr_amplifier`의 `M108`
    (pmos 다이오드)/`M106`(nmos 캐스코드) — `M106.source`가 아니라 `M106.drain`이
    `M108.drain`과 같은 노드다)를 아예 못 잡는다는 게 실측으로 드러났다 -- `by_d[up['S']]`
    루프만으로는 `M104`(같은 kind, source=drain 체인)만 잡히고 `M108`은 통째로 빠졌다.
    같은 `up` 필터(role/diffpair·float 제외/`_reaches_output` 기능성 검사)를 그대로 쓰되,
    `lo` 탐색을 `by_d[up['D']]`(같은 drain을 쓰는 **다른** kind)로 한 번 더 돈다 --
    같은 kind 탐색과 겹치지 않도록 `lo['type'] == up['type']`인 건 여기서 제외한다.

    ⚠️ **`ports['lo']`/`ports['up']`을 명시**(2026-08-08 `m_diode_cascode()`가 이미 쓰던
    패턴과 동일 이유) -- 이 cross-kind 케이스는 `up`의 drain과 `lo`의 drain이 **똑같은
    노드**라 기존 `_cascode_lo_up_pairs()`의 `ports['mid']` 기반 추론(`da.get('D')==mid`)이
    양쪽 다 참이 되어 어느 쪽이 lo인지 못 가른다 -- 처음부터 명시해서 이 모호성 자체를
    없앤다(같은 kind 케이스에도 일관되게 명시 -- `_cascode_lo_up_pairs()`가 이제 명시된
    키를 최우선으로 본다)."""
    out, by_d = [], defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    diffpair_legs = {n for m in m_diffpair(devs, cls, imp, role) for n in m.devices}
    float_legs = {n for m in m_float_source(devs, cls, imp, role) for n in m.devices}
    for up in devs:
        if role[up['name']] not in (CASCODE, AMP, CTRL_SRC): continue
        if up['name'] in diffpair_legs or up['name'] in float_legs: continue
        out_hops = _reaches_output(up['D'], devs, cls)
        mid_hops = _reaches_output(up['S'], devs, cls)
        if mid_hops is not None and (out_hops is None or mid_hops <= out_hops): continue
        for lo in by_d[up['S']]:
            if lo['name'] == up['name'] or lo['type'] != up['type']: continue
            out.append(Match('cascode-stack', [lo['name'], up['name']],
                             {'lo': lo['name'], 'up': up['name'],
                              'mid': up['S'], 'out': up['D'],
                              'lower_role': role[lo['name']]},
                             note=up['type'], priority=4))
        # 2026-08-18 -- `up`이 진짜 "무언가 위에 쌓인" 소자이려면 `up.source`가 레일이면
        # 안 된다(레일=그 컬럼의 맨 밑/맨 위, 더 이상 아래에 쌓일 게 없다는 뜻). 이 조건이
        # 없으면 `current_reuse_telescopic_ota`의 `M15`(pmos,source=vdd)/`M16`
        # (nmos,source=gnd)처럼 **같은 출력 노드(Vom)를 서로 다른 레일에서 각자 독립적으로
        # 구동하는 complementary push-pull 출력단**까지 "캐스코드"로 오탐한다(실측 발견 --
        # 겉보기엔 D-D 접합이라 구조가 똑같아 보이지만, 기능적으로는 캐스코드(하나가 나머지
        # 위에 얹혀 전류를 그냥 통과시킴)가 전혀 아니라 서로 독립적으로 전류를 생성하는
        # 두 소자가 우연히 한 노드에서 만나는 것뿐이다). `up.source`가 non-rail(내부 노드,
        # 즉 진짜 다른 컬럼 위에 앉아 있음)일 때만 캐스코드 관계로 인정한다.
        if up['S'] in RAILS: continue
        for lo in by_d[up['D']]:
            if lo['name'] == up['name'] or lo['type'] == up['type']: continue
            # D-D 접합은 대칭이라(둘 다 drain이 같은 노드) lo/up 둘 다 `up` 필터(role in
            # CASCODE/AMP/CTRL_SRC)를 통과하면 방향이 반대인 Match 2개가 동시에 나오는
            # 모순이 실측으로 드러났다(nmcnr_amplifier의 M107(CASCODE)/M109(AMPLIFYING) --
            # 둘 다 이 loop에서 up 후보라 (lo=M107,up=M109)와 (lo=M109,up=M107)이 둘 다
            # 생성됨). CASCODE는 정의상 전류를 생성하지 않으므로(이 확장 자체의 전제) lo가
            # CASCODE면 그 방향은 무조건 배제한다 -- 남는 진짜 생성원 쪽(M109, AMPLIFYING)만
            # lo로 채택된다.
            if role[lo['name']] == CASCODE: continue
            out.append(Match('cascode-stack', [lo['name'], up['name']],
                             {'lo': lo['name'], 'up': up['name'],
                              'mid': up['D'], 'out': up['D'],
                              'lower_role': role[lo['name']], 'cross_kind_boundary': True},
                             note=up['type'], priority=4))
    return out


def _cascode_lo_up_pairs(devs, matches):
    """`cascode-stack` Match마다 실제 (lo, up) 소자 이름을 물리적 근거(`ports['mid']`가
    `lo`의 drain이자 `up`의 source인 net)로 다시 식별해 `[(lo_name, up_name), ...]`로
    반환한다(2026-08-15, chip-design-skills 세션35 -- `propagate_reference_role_through_
    cascode()`/`find_cascoded_active_load_legs()` 공유 헬퍼).

    ⚠️ **버그 수정**: `Match.__init__`이 `devices`를 항상 `tuple(sorted(...))`로 정렬해
    저장하므로(`Match` 클래스 정의 참고), `m.devices`를 `lo_name, up_name = m.devices`처럼
    "선언 순서"로 그냥 언패킹하면 **소자 이름의 알파벳/자릿수 순서가 우연히 물리적
    lo/up 순서와 다를 때 뒤바뀐다**(실측 발견: `folded_cascode`는 우연히 대부분 일치했지만
    일반적으로 보장되지 않음 -- 예를 들어 두 자리 숫자 이름은 문자열 비교가 물리적
    순서와 어긋나기 쉽다). `devs`(원본 소자 리스트, 각 `D`/`S` 필드 보유)로 어느 쪽이
    진짜 lo(`D==mid`)이고 어느 쪽이 up(`S==mid`)인지 다시 확인해 이 gap을 없앤다.

    ⚠️ 2026-08-18 확장 -- `ports['lo']`/`ports['up']`이 명시돼 있으면(2026-08-18부터
    `m_cascode()`가 항상 명시함) 그 값을 최우선으로 쓴다. PMOS/NMOS 경계 캐스코드
    (`cross_kind_boundary`, `up.D==lo.D`)는 `up`/`lo` 둘 다 `D==mid`를 만족해 아래
    `mid` 기반 추론이 어느 쪽인지 못 가르기 때문에 명시가 필수다 -- `ports['lo']`가
    없는(과거 방식으로 만들어진, 또는 이 함수 밖에서 합성한) Match만 기존 `mid` 기반
    추론으로 하위호환 처리한다."""
    by_name = _by_name(devs)
    pairs = []
    for m in matches:
        if m.kind != 'cascode-stack':
            continue
        explicit_lo, explicit_up = m.ports.get('lo'), m.ports.get('up')
        if explicit_lo is not None and explicit_up is not None:
            pairs.append((explicit_lo, explicit_up))
            continue
        mid = m.ports.get('mid')
        a, b = m.devices
        da, db = by_name.get(a), by_name.get(b)
        if da is not None and da.get('D') == mid:
            pairs.append((a, b))
        elif db is not None and db.get('D') == mid:
            pairs.append((b, a))
        # 둘 다 안 맞으면(방어적) 이 pair는 건너뛴다 -- 지어내지 않는다.
    return pairs


def propagate_reference_role_through_cascode(matches, seed_names, devs):
    """`m_cascode()`가 이미 찾은 `cascode-stack` 관계(`up.source==lo.drain`)를 따라,
    호출부가 "이 성질을 가진 소자"로 판정한 `seed_names`를 위쪽(캐스코드로 쌓인 소자)으로
    전파한다 -- `lo`가 이미 그 성질을 가지면(seed_names에 있거나 이전 반복에서 전파돼
    들어왔으면) `up`도 "같은 전류경로가 그 성질을 가진 소자에서 온다"는 사실을 물려받는다.
    고정점까지 반복(다단 캐스코드 지원 -- 세션34 실측은 1단이면 충분했지만 일반화).

    ⚠️ **무엇을 seed로 볼지는 이 함수가 정하지 않는다** -- `analog-gmid-design/
    chip-design-skills` 세션34(2026-08-14, `.ai/context.md` 참고) 신설 계기: `folded_
    cascode`의 `M8`(`role='AMPLIFYING'`, 게이트가 폴딩 노드와 겹쳐 신호로 분류됨)이
    `M10`(`role='CURRENT_SOURCE'`, 정적 레퍼런스) 위에 물리적으로 쌓여 있는데도 "정적
    레퍼런스"로 분류돼야 하는 케이스가 계기였다 -- 그런데 "무엇이 정적 레퍼런스인가"
    (`DIODE_CONNECTED`/`CURRENT_SOURCE`/`ACTIVE_LOAD`/`CASCODE`였다)는 그 소비자의
    판단이지 이 함수(또는 idiom 레이어)가 하드코딩할 성질이 아니다 -- 다른 소비자는
    다른 seed 기준을 쓸 수 있다. 그래서 `seed_names`를 그대로 받는다(`role` 자체를
    재분류하거나 덮어쓰지 않음 -- `netclass.assign_roles()`의 단일-라벨 계약에 기대는
    다른 소비자를 깨지 않기 위함, `m_mirror()`의 `active_load_legs`와 같은 원칙).

    `matches`: `idioms.match_all()`(또는 그 부분집합)의 반환값 그대로 -- `kind==
    'cascode-stack'`이 아닌 Match는 내부에서 걸러진다. `devs`(2026-08-15 세션35 신설
    필수 인자): lo/up을 물리적으로 다시 식별하는 데 쓴다(`_cascode_lo_up_pairs()`
    참고 -- `Match.devices` 정렬 때문에 순서를 그대로 못 믿는다).

    반환: `seed_names`를 포함해 전파로 확장된 **새** set(`seed_names` 원본은 변경
    안 함)."""
    pairs = _cascode_lo_up_pairs(devs, matches)
    out = set(seed_names)
    for _ in range(len(pairs) + 1):
        grew = False
        for lo_name, up_name in pairs:
            if lo_name in out and up_name not in out:
                out.add(up_name)
                grew = True
        if not grew:
            break
    return out


def find_cascoded_active_load_legs(devs, matches, imp, cls=None):
    """current-mirror(`m_mirror()`) 다리의 드레인이 자기 자신이 아니라 그 위에 캐스코드로
    쌓인 소자의 드레인에서 `HIGH_Z` 이득노드를 만드는 경우까지 "active load" 판정을
    확장한다(2026-08-15, chip-design-skills 세션35 신설 -- 사용자 통찰: "stacked current
    mirror의 output impedance가 active load 값이 되는 거다, 전형적인 stacked current
    mirror 형태다"). `cls`(선택, `netclass.classify_nets()`의 net 분류 결과)를 주면
    `m_mirror()`의 `active_load_legs`와 동일한 `BIAS` 노드 제외 필터를 적용한다(순수
    바이어스 생성 노드는 실제 신호 경로가 아니므로 gain 후보에서 뺀다 -- `m_mirror()`
    docstring의 "2026-08-15 후속" 항목 참고). `cls=None`이면 이 필터를 건너뛴다(하위호환).

    `m_mirror()`의 `active_load_legs`는 "이 다리 **자신의** 드레인이 HIGH_Z인가"만
    본다 -- 그런데 그 다리 위에 캐스코드가 한 단 이상 쌓여 있으면(예: `folded_cascode`의
    `M10`(미러 다리) 위에 `M8`(캐스코드)이 쌓임) "자기 드레인"이 아니라 캐스코드 스택의
    **꼭대기** 드레인이 진짜 이득노드다 -- 자기 드레인(`Vg10`)은 그 위 캐스코드의
    소스라 `netclass.classify_nets()` §1f 정의상 `LOW_Z`로 분류되는 게 **정상**이다
    (버그 아님 -- 소스가 붙은 net은 항상 LOW_Z). 이 함수는 그 "정상적으로 LOW_Z인 자기
    드레인" 때문에 `m_mirror()`가 놓치는 진짜 active-load 다리를, 캐스코드 스택을
    끝까지 걸어 올라가 다시 찾아준다.

    ⚠️ 2026-08-15 리팩터(사용자 지적 -- "seed name을 주는 helper를 이미 만들어뒀는데
    그걸 재사용하지 않았다") -- 자체 스택 워킹 루프 대신 `propagate_reference_role_
    through_cascode()`(세션34 신설 범용 helper, "호출부가 정한 seed 성질을 캐스코드
    위로 전파")를 그대로 재사용한다: 미러 다리 전체를 seed로 주고 전파시킨 뒤, "새로
    편입된"(원래 seed가 아니었던) 이름만 골라낸다 -- `leg==top`(캐스코드가 아예 없는
    경우, 이미 `m_mirror()`의 기존 판정이 제외조건까지 정확히 처리하는 대상)은 seed
    집합에 그대로 남아 전파 결과에서 "새로 편입"으로 안 잡히므로, 소비자가 별도로
    `leg != top` 필터를 만들 필요가 없어진다(이전 버전에서 이 필터를 깜빡해 current_
    reuse_telescopic_ota/nmcnr_amplifier에 실제 회귀를 낸 적이 있음 -- 이 재사용이
    그 사고 클래스 자체를 구조적으로 없앤다).

    반환: 캐스코드 스택을 타고 새로 "active load" 성질을 물려받은 소자 이름의 `set`
    (예: `{"M8"}` -- `M10`(미러 다리) 자신은 포함 안 됨, 그 위 캐스코드 `M8`만).
    각 이름의 자기 드레인이 `imp`상 `HIGH_Z`로 확인된 경우만 포함한다. `matches`는
    `idioms.match_all()`(또는 부분집합) 그대로 -- `'current-mirror'`/`'cascode-stack'`
    둘 다 필요."""
    by_name = _by_name(devs)
    legs = {leg for m in matches if m.kind == 'current-mirror'
            for leg in m.devices if leg != m.ports.get('ref')}
    propagated = propagate_reference_role_through_cascode(matches, legs, devs)
    out = set()
    for top in propagated - legs:
        top_dev = by_name.get(top)
        if top_dev is None or imp.get(top_dev.get('D')) != HIGH_Z:
            continue
        if cls is not None and cls.get(top_dev.get('D')) == BIAS:
            continue
        out.add(top)
    return out


def _walk_single_fanout_top(node, arrived_via, by_source):
    """`m_diffpair_branch_load()` 전용 헬퍼 -- `node`에서 시작해 **단일 fanout**(그 net을
    source로 쓰는 소자가 정확히 1개)인 동안만 위로 걷는다(레일 도달 또는 fanout≠1이면
    멈춤, 추측하지 않음). `kind` 제한이 없다 -- `m_cascode()`(같은 kind만 인정, 물리적
    diffusion 적층 판정)와 달리 이건 **전기적 신호 경로**(예: PMOS diffpair 다리 ->
    폴딩 노드 -> NMOS 캐스코드처럼 kind가 바뀌는 폴디드 캐스코드도 포함)라 별개 헬퍼다.

    반환: `(final_node, last_hop_device_name_or_arrived_via)`."""
    seen = {node}
    while node not in RAILS:
        candidates = by_source.get(node, [])
        if len(candidates) != 1:
            break
        nxt = candidates[0]
        if nxt['D'] in seen:
            break
        arrived_via = nxt['name']
        node = nxt['D']
        seen.add(node)
    return node, arrived_via


@idiom('diffpair-branch-load', priority=4)
def m_diffpair_branch_load(devs, cls, imp, role):
    """`.ai/context.md`(chip-design-skills) 세션34(2026-08-14) 후속 -- `m_diffpair()`가
    찾은 diffpair의 **두 branch 꼭대기에 각각 앉은 부하**를 매칭한다(예: 5T/2단 OTA의
    diode+mirror 비대칭 부하 `M3`/`M4`, 또는 폴디드 캐스코드를 한 단 거쳐야 나오는
    `nmcnr_amplifier`의 `M108`/`M109`).

    ⚠️ **왜 `m_mirror()`/`m_cascode()`만으론 못 찾는가**: `M3`(diode-connected)/`M4`(그
    미러)는 `gate==drain` 여부가 달라 그래프 자기동형이 아니고, `m_mirror()`가 찾는
    "같은 gate 공유 그룹"에도 안 걸린다(서로 다른 gate: `M3.gate=D3`, `M4.gate=D3`는
    같지만 -- 실제로는 같은 gate라 `m_mirror()`가 찾긴 하지만, 그건 우연이고 `nmcnr_
    amplifier`의 `M108`/`M109`처럼 gate가 다른 경우(`M108.gate=NodeM1`, `M109.gate=
    NodeM1`도 같지만 폴디드 캐스코드 뒤라 diffpair와 직접 안 이어짐)는 그 신호 하나로
    "이게 diffpair의 부하다"라는 문맥 자체를 못 얻는다). 이 idiom은 diffpair(문맥) +
    branch 꼭대기 부하(위치)를 명시적으로 연결한다.

    각 diffpair leg의 drain에서 `_walk_single_fanout_top()`으로 전기적 신호 경로를
    (kind 무관, 단일 fanout인 동안만) 꼭대기까지 걷는다 -- `two_stage_ota`의 M3/M4처럼
    캐스코드가 아예 없으면 첫 걸음에서 fanout≠1이라 즉시 멈춰(diffpair leg 자기 drain이
    곧 꼭대기) 원래 1-hop 판정과 동일해진다. 두 꼭대기 노드가 다르고, 그 노드를 drain으로
    쓰는 소자가 (걸어 올라오며 마지막으로 거친 소자를 뺴고) **각각 정확히 1개씩**이며
    같은 kind면 매칭한다. **애매하면(부하가 0개거나 2개 이상, kind가 다르면) 아무것도
    매칭하지 않는다** -- 근거 없는 기본값을 채우지 않는다는 프로젝트 전역 원칙.

    반환: `[Match('diffpair-branch-load', [load_a, load_b], {'diffpair': (a, b),
    'top_a', 'top_b'}), ...]`."""
    by_name = _by_name(devs)
    by_drain, by_source = defaultdict(list), defaultdict(list)
    for d in devs:
        by_drain[d['D']].append(d)
        if d['S'] not in RAILS:
            by_source[d['S']].append(d)

    out = []
    for dp in m_diffpair(devs, cls, imp, role):
        a, b = dp.devices
        top_a, via_a = _walk_single_fanout_top(by_name[a]['D'], a, by_source)
        top_b, via_b = _walk_single_fanout_top(by_name[b]['D'], b, by_source)
        if top_a == top_b:
            continue
        loads_a = [d['name'] for d in by_drain.get(top_a, []) if d['name'] != via_a]
        loads_b = [d['name'] for d in by_drain.get(top_b, []) if d['name'] != via_b]
        if len(loads_a) == 1 and len(loads_b) == 1:
            la, lb = loads_a[0], loads_b[0]
            if la != lb and by_name[la]['type'] == by_name[lb]['type']:
                out.append(Match('diffpair-branch-load', [la, lb],
                                 {'diffpair': (a, b), 'top_a': top_a, 'top_b': top_b},
                                 note=f"diffpair={a}/{b}", priority=4))
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


@idiom('floating-current-source', priority=7)
def m_float_source(devs, cls, imp, role):
    """Monticelli class-AB floating current source: 서로 다른 kind(PMOS/NMOS) 소자
    두 개가 레일이 아닌 노드 두 개 사이를 **서로 반대 방향으로 마주보고** 잇는다
    (`a.S==b.D` 이고 동시에 `a.D==b.S` -- 완전한 anti-parallel 2-노드 loop). 두 노드는
    전형적으로 2단 push-pull 출력쌍(`push-pull-output` 참고)의 게이트 두 개다. 게이트는
    서로 다른 독립 다이오드스택(각각 `floating-battery`)에서 와서 quiescent 전류를
    고정한다 -- `floating-battery`와 구별점은 diode-connected 직렬 단일경로가 아니라
    **비-diode 소자 두 개가 두 노드 사이를 순환(loop)한다**는 것.

    2026-08-08 신설(chip-design-skills, 사용자 지적) -- `current_reuse_telescopic_ota`의
    `M9a`(PMOS)/`M9b`(NMOS)가 실측 사례: `Vg15`(=M15.gate)<->`Vop1`(=M16.gate) 사이를
    마주보고 잇는다(`examples/fig3_classab.json`의 고립 fixture로 재확인, 논문 원본
    구조). `m_cascode()`가 `M8`+`M9a`(같은 PMOS, 직렬)와 `M10`+`M9b`(같은 NMOS, 직렬)를
    각각 물리적 스택으로 잡는 것 자체는 **layout 관점(같은 well/diffusion column에
    쌓을 수 있다는 사실)에서 여전히 유효** -- 이 idiom은 그 매칭을 대체하지 않고
    나란히 추가된다(`M9a`/`M9b`가 두 매칭 모두에 나타남, `resolve_overlaps()`에서만
    priority=7이 cascode-stack의 4를 이겨 `M9a`/`M9b`를 이쪽으로 배정하고 `M8`/`M10`은
    미축약 leftover로 남는다 -- Stage 4/6 표시용, `stick_diagram.py`의 레이아웃 판단에는
    영향 없음). ⚠️ `M8`/`M10`을 'M9a/M9b를 캐스코드하는 전류미러'로 부르는 것은 틀렸다
    -- 실제로는 이 floating loop에 위/아래에서 바이어스 전류를 대주는 별개의 고정
    전류원/싱크일 뿐이다."""
    out, seen = [], set()
    for a in devs:
        for b in devs:
            if a['name'] >= b['name']: continue
            if not is_mutual_loop_partner(a, b): continue
            key = frozenset((a['name'], b['name']))
            if key in seen: continue
            seen.add(key)
            p, n = (a, b) if a['type'] == 'PMOS' else (b, a)
            out.append(Match('floating-current-source', [p['name'], n['name']],
                             {'node_a': p['S'], 'node_b': p['D'],
                              'gate_p': p['G'], 'gate_n': n['G']},
                             note='Monticelli class-AB 상보 anti-parallel loop', priority=7))
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

    2026-08-24(chip-design-skills, 사용자 지적으로 발견) -- 원래는 `len(ms) != 2`로
    이 노드에 드레인을 대는 소자 수를 그대로 셌다. 고립된 fixture(순수 1단만)에서는
    이득 노드에 진짜 cascode 2개뿐이라 문제가 없었지만, 실제 완성된 회로에서는 같은
    이득 노드에 floating-current-source(Monticelli class-AB battery)나 단순
    current-mirror sink가 **추가로** 드레인을 댈 수 있다(`current_reuse_telescopic_ota`
    의 Vom1 실측: M2a/M3a(진짜 cascode) 외에 M18a(floating battery)/M19(mirror sink)도
    drain=Vom1이라 len(ms)==4가 되어 이 idiom이 통째로 스킵됐다 -- 그 결과 M18a가
    엉뚱하게 M3a의 cascode-stack 후보로 오매칭되는 회귀로 이어짐). role==CASCODE로
    먼저 걸러낸 뒤 그 개수가 2인지 보면, 몇 개의 소자가 이 노드에 더 물려 있든
    "진짜 상보형 cascode 쌍"만 정확히 골라낸다(role 배정 자체가 이미 floating-
    current-source/current-source를 CASCODE와 구분해주므로 새 판정 로직 불필요).
    """
    out, by_d = [], defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    for node, ms in by_d.items():
        if node in RAILS or imp.get(node) != HIGH_Z: continue
        cascodes = [m for m in ms if role[m['name']] == CASCODE]
        if len(cascodes) != 2: continue
        if cascodes[0]['type'] == cascodes[1]['type']: continue
        out.append(Match('cascoded-gain-node', [m['name'] for m in cascodes],
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
