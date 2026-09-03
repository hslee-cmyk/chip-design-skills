#!/usr/bin/env python3
"""
netclass.py — Stage 1 (net 분류) + Stage 2 (device role 배정)

설계 원칙
---------
LLM 에게 "이 회로가 뭐냐"고 묻지 않는다. 물으면 익숙한 topology 의 형태를
알아보고 교과서 답을 채워 넣는다(회상). 논문의 기여는 대개 canonical 에서
한두 개 비틀린 부분인데, 그게 정확히 회상이 지워버리는 부분이다.

Stage 1 과 2 는 전부 결정론적 그래프 연산이다. 단 하나의 예외:

  ** 잘린 도면에서 INPUT 과 BIAS 는 구조적으로 구별되지 않는다. **
  둘 다 '게이트에만 연결된 외부 넷'이므로 그래프상 동일하다.
  이름 힌트 또는 사용자 선언이 필요하며, 어느 쪽을 썼는지 반드시 출력한다.
"""
import re
from collections import defaultdict


class _CaseInsensitiveNetSet(frozenset):
    """rail net 이름 대소문자와 무관하게 판정한다(2026-08-07 수정 -- 원래는 'VDD'/
    'GND' 같은 대문자 리터럴만 인식해서, 소문자 관례(예: chip-design-skills 프로젝트의
    'vdd'/'gnd')를 쓰는 호출자의 rail이 전부 인식 실패하던 버그가 있었다 -- rail이
    인식 안 되면 이후 net 분류/role 배정/idiom 매칭 전부가 조용히 틀어진다). 특정
    대소문자 조합을 새 리터럴로 추가하는 대신, 비교 자체를 대소문자 무관하게 만들어
    호출자가 어떤 케이스 관례를 쓰든 항상 맞도록 한다."""

    def __contains__(self, item):
        return isinstance(item, str) and frozenset.__contains__(self, item.upper())


RAILS_POS = _CaseInsensitiveNetSet({'VDD', 'AVDD', 'DVDD', 'VCC', 'VDDA'})
RAILS_NEG = _CaseInsensitiveNetSet({'GND', 'VSS', 'AGND', 'DGND', 'VSSA'})
RAILS = _CaseInsensitiveNetSet(set(RAILS_POS) | set(RAILS_NEG))

# 이름 힌트. 구조적으로 판정 불가능한 것만 이걸로 가른다.
# 적용된 힌트는 assumptions 로 전부 보고된다.
HINT_INPUT = re.compile(r'^(v?i[np]?\d*|v?in[pm]?\d*|vi[pm]\d*|inp?|inm?)$', re.I)
HINT_BIAS  = re.compile(r'(bias|vref|vb\d|vcm(?!fb)|vgs)', re.I)
HINT_FB    = re.compile(r'(cmfb|_fb$|^fb|feedback)', re.I)
HINT_CLK   = re.compile(r'(^clk|^ph[12i]|clock|^ck)', re.I)
HINT_OUT   = re.compile(r'^(v?o[up]?\d*|v?out[pm]?\d*|vo[pm]\d*|outp?|outm?)$', re.I)

# net class
SUPPLY, GROUND = 'SUPPLY', 'GROUND'
INPUT, OUTPUT, SIGNAL = 'INPUT', 'OUTPUT', 'SIGNAL'
BIAS, FEEDBACK, CLOCK = 'BIAS', 'FEEDBACK', 'CLOCK'
INTERNAL = 'INTERNAL'

# impedance
HIGH_Z, LOW_Z, RAIL_Z = 'HIGH_Z', 'LOW_Z', 'RAIL'


def terminals(devs):
    """net -> [(device, terminal)] 인덱스"""
    t = defaultdict(list)
    for d in devs:
        for k in 'DGS':
            t[d[k]].append((d['name'], k))
    return t


def is_mutual_loop_partner(a, b):
    """두 소자가 서로 다른 두 non-rail 노드 사이를 반대 방향으로 마주보고 잇는
    anti-parallel 2-사이클(`a.S==b.D and a.D==b.S`, kind가 다름, 레일 아님, 게이트도
    서로 다르고 레일 아님)을 이루는지 -- G==D(diode-connected)처럼 특정 idiom의
    이름/분류 결과에 기대지 않는 순수 raw connectivity 사실이다.

    2026-08-24(chip-design-skills, 사용자 지시로 신설) -- Stage 1(`classify_nets()`의
    임피던스 등급, 아래 참고)과 Stage 3(`idioms.py`의 `floating-current-source`)가
    **같은 원시 조건**을 각자 다른 목적으로 재사용한다. G==D를 Stage 1(1e2, BIAS 판정)
    과 Stage 3(`diode-connected` idiom)가 이미 이렇게 공유하는 것과 동일한 패턴 --
    Stage 1이 Stage 3의 *분류 결과*를 소비하는 게 아니라(그러면 순환), 둘 다 netlist
    원시 정보만 보고 독립적으로 같은 조건을 계산할 뿐이므로 순환이 아니다."""
    if a['name'] == b['name'] or a['type'] == b['type']:
        return False
    if a['S'] != b['D'] or a['D'] != b['S']:
        return False
    if a['S'] in RAILS or a['D'] in RAILS:
        return False
    if a['G'] == b['G'] or a['G'] in RAILS or b['G'] in RAILS:
        return False
    return True


def has_mutual_loop_partner(dev, devs):
    """`dev`가 어떤 다른 소자와 `is_mutual_loop_partner()` 관계를 이루는지."""
    return any(is_mutual_loop_partner(dev, o) for o in devs if o['name'] != dev['name'])


def classify_nets(devs, inputs=(), outputs=(), biases=(), feedbacks=(), clocks=()):
    """
    Stage 1. 반환: (netclass dict, impedance dict, assumptions list)
    """
    term = terminals(devs)
    assume = []
    cls = {}

    # --- 1a. 전원 레일 -----------------------------------------------------
    for n in term:
        if n in RAILS_POS: cls[n] = SUPPLY
        elif n in RAILS_NEG: cls[n] = GROUND

    # --- 1b. 사용자 선언이 최우선 ------------------------------------------
    for grp, k in ((inputs, INPUT), (outputs, OUTPUT), (biases, BIAS),
                   (feedbacks, FEEDBACK), (clocks, CLOCK)):
        for n in grp:
            if n in term:
                cls[n] = k
                assume.append(f"[declared] {n} = {k}")

    # --- 1c. 게이트 전용 외부 넷: 여기가 유일한 판정 불가 지점 -------------
    for n, ts in term.items():
        if n in cls: continue
        kinds = {k for _, k in ts}
        if kinds == {'G'}:                       # D/S 로는 한 번도 안 나타남
            if   HINT_CLK.search(n):   cls[n], why = CLOCK,    'name hint (clock)'
            elif HINT_FB.search(n):    cls[n], why = FEEDBACK, 'name hint (feedback)'
            elif HINT_BIAS.search(n):  cls[n], why = BIAS,     'name hint (bias)'
            elif HINT_INPUT.match(n):  cls[n], why = INPUT,    'name hint (input)'
            else:                      cls[n], why = BIAS,     'default: gate-only external -> BIAS'
            assume.append(f"[inferred] {n} = {cls[n]}  ({why})  "
                          f"<= 구조만으로는 INPUT/BIAS 구별 불가")

    # --- 1d. 신호 전파 (INPUT 에서 정방향) ---------------------------------
    sig = {n for n, c in cls.items() if c in (INPUT, FEEDBACK)}
    changed = True
    while changed:
        changed = False
        for d in devs:
            g, dr, s = d['G'], d['D'], d['S']
            # transconductance: 게이트가 신호면 드레인이 신호 (반전)
            if g in sig and dr not in RAILS and dr not in sig:
                sig.add(dr); changed = True
            # source follower: 드레인이 레일이면 소스가 신호
            if g in sig and dr in RAILS and s not in RAILS and s not in sig:
                sig.add(s); changed = True
            # cascode / current buffer: 소스가 신호이고 게이트가 고정이면 드레인도 신호
            if s in sig and cls.get(g) in (BIAS, None) and dr not in RAILS and dr not in sig:
                sig.add(dr); changed = True
    for n in sig:
        cls.setdefault(n, SIGNAL)
        if cls[n] not in (INPUT, OUTPUT, FEEDBACK): cls[n] = SIGNAL

    # --- 1e. 출력 추정 -----------------------------------------------------
    for n, c in list(cls.items()):
        if c == SIGNAL and HINT_OUT.match(n):
            cls[n] = OUTPUT
            assume.append(f"[inferred] {n} = OUTPUT  (name hint)")

    # --- 1e2. 남은 '게이트를 구동하는 내부 넷' 분류 ------------------------
    # 이 규칙이 없으면 level-shift 스택(class-AB floating battery)의 출력처럼
    # 내부에서 만들어져 게이트로 가는 넷이 미분류로 남고, Stage 2 에서
    # UNRESOLVED 가 연쇄한다.
    #
    # ⚠️ 2026-08-07 수정 -- "diode로만 구동되면 BIAS, 능동 드레인이면 SIGNAL"이라는
    # 원래 규칙은 그 능동 드레인을 만드는 소자 자신의 게이트가 이미 BIAS인 경우를
    # 놓친다. current mirror(정의상 G != D)로 만들어지는 bias net이 정확히 이 경우다
    # -- 예: Vbias1(순수 diode 기준)을 게이트로 받는 미러 소자가 Vbias4를 드레인으로
    # 만들면, Vbias4는 diode가 아니라는 이유만으로 SIGNAL이 되고, 이걸 다시 게이트로
    # 받는 다음 미러 소자가 Vbias2를 만들면 그것도 SIGNAL이 된다 -- 실제로는 셋 다
    # AC 성분이 없는 순수 DC bias 트리인데도(current_reuse_telescopic_ota의
    # Vbias1->M60->Vbias4->M68->Vbias2 사슬로 실측 발견, chip-design-skills 프로젝트
    # .ai/context.md 세션23 참고), "diode인가"만 보고 "그 소자의 게이트가 이미
    # 안정된 BIAS인가"는 재귀적으로 확인하지 않아서 생기는 오분류다.
    #
    # 그래서 이 net을 드라이브하는(G != D) 소자들의 게이트 클래스를 본다 -- 전부
    # BIAS로 이미 확정돼 있으면(고정 게이트로 일정 전류를 흘리는 미러/전류원이라는
    # 뜻) 이 net도 BIAS로 전파한다. 아직 미확정인 게이트가 섞여 있으면 그 게이트가
    # 풀릴 때까지 다음 라운드로 미룬다(1d의 신호 전파와 동일한 고정점 반복 패턴) --
    # net 이름 처리 순서에 의존하지 않고, Vbias1->Vbias4->Vbias2처럼 몇 단이든
    # 사슬 깊이만큼 자연히 수렴한다.
    live_drivers = defaultdict(list)
    for d in devs:
        if d['G'] != d['D']:
            live_drivers[d['D']].append(d)

    changed = True
    while changed:
        changed = False
        for n, ts in term.items():
            if cls.get(n) not in (None, INTERNAL): continue
            if not any(k == 'G' for _, k in ts): continue
            drivers = live_drivers.get(n, [])
            if not drivers:
                cls[n] = BIAS
                assume.append(f"[derived] {n} = BIAS  (diode 구동 DC 노드)")
                changed = True
                continue
            driver_gate_classes = {cls.get(dr['G']) for dr in drivers}
            if driver_gate_classes == {BIAS}:
                cls[n] = BIAS
                assume.append(f"[derived] {n} = BIAS  "
                              f"(구동 소자 전부 게이트가 BIAS -- 미러/전류원 재귀 전파)")
                changed = True
            elif None not in driver_gate_classes:
                cls[n] = SIGNAL
                assume.append(f"[derived] {n} = SIGNAL  "
                              f"(능동 드레인 구동, 구동 소자 게이트가 BIAS 아님)")
                changed = True
            # else: 구동 소자 게이트가 아직 미확정 -- 다음 라운드에 재시도

    # 순환 의존 등으로 끝까지 안 풀린 net은 안전하게 SIGNAL로 폴백(조용히 BIAS로
    # 단정하지 않음 -- 판정 불가 상태를 숨기지 않는다는 원칙).
    for n, ts in term.items():
        if cls.get(n) not in (None, INTERNAL): continue
        if not any(k == 'G' for _, k in ts): continue
        cls[n] = SIGNAL
        assume.append(f"[derived] {n} = SIGNAL  (구동 소자 게이트 판정이 끝까지 안 풀림 -- 안전 폴백)")

    for n in term:
        cls.setdefault(n, INTERNAL)

    # --- 1f. 임피던스 등급 -------------------------------------------------
    # 2026-08-24(chip-design-skills, 사용자 지시로 수정) -- source 단자가 하나라도
    # 있으면 무조건 LOW_Z였는데, `is_mutual_loop_partner()`(anti-parallel floating
    # loop, 위 참고)의 절반인 소자의 source는 예외다: 이 노드가 실제로 저임피던스라서
    # source가 붙은 게 아니라, floating loop 구조상 부수적으로 생기는 것뿐이다(실측:
    # `current_reuse_telescopic_ota`의 Vom1 -- 진짜 상보형 cascode 이득 노드인데
    # floating-current-source 절반(M18b)의 source가 물려 있어 LOW_Z로 오분류되던
    # 회귀). 이 예외를 빼면 나머지 source 판정 원칙(소스가 붙으면 저임피던스)은 그대로.
    dev_by_name = {d['name']: d for d in devs}
    imp = {}
    for n, ts in term.items():
        if n in RAILS: imp[n] = RAIL_Z; continue
        kinds = [k for dname, k in ts
                 if not (k == 'S' and has_mutual_loop_partner(dev_by_name[dname], devs))]
        if all(k == 'D' for k in kinds) or set(kinds) <= {'D', 'G'}:
            imp[n] = HIGH_Z          # 드레인만 모인 노드 = 이득 노드
        else:
            imp[n] = LOW_Z           # 소스가 붙으면 저임피던스
    return cls, imp, assume


# ── Stage 2: device role ────────────────────────────────────────────────
DIODE       = 'DIODE_CONNECTED'
CURR_SRC    = 'CURRENT_SOURCE'
CTRL_SRC    = 'CONTROLLED_CURRENT_SOURCE'
CASCODE     = 'CASCODE'
FLOAT_SRC   = 'FLOATING_CURRENT_SOURCE'
DIODE_CASC  = 'DIODE_REFERENCED_CASCODE'
AMP         = 'AMPLIFYING'
FOLLOWER    = 'SOURCE_FOLLOWER'
SWITCH      = 'SWITCH'
ACTIVE_LOAD = 'ACTIVE_LOAD'


def _floating_source_legs(devs):
    """Monticelli class-AB floating current source의 다리를 구한다: 서로 다른
    kind(PMOS/NMOS)가 비-레일 노드 두 개 사이를 `a.S==b.D`이고 `a.D==b.S`인
    anti-parallel loop로 마주보고(게이트는 서로 다른 독립 다이오드스택에서 옴,
    레일 아님) 잇는 소자쌍 -- `idioms.py`의 `m_float_source()`와 정확히 같은 판정
    기준(2026-08-08 신설, 그쪽 docstring에 실측 근거 상세 기록).

    2026-08-08 추가(사용자 지적) -- `assign_roles()`가 이 다리들을 전부 `CASCODE`로
    뭉뚱그리고 있었다(`current_reuse_telescopic_ota`의 `M9a`/`M9b`/`M18a`/`M18b`
    실측 사례). `M9a`가 `M8`을 캐스코드하는 게 아니라 floating current source의
    절반이라는 게 `idioms.m_cascode()`(2026-08-08 수정)에서 이미 드러났는데, 그보다
    더 아래 계층인 이 함수가 여전히 `CASCODE`를 부여하면 `idioms.py`를 거치지 않는
    모든 소비자(예: `analyze.py` Stage 2 role 표시)가 이 오분류를 그대로 물려받는다.
    role 배정은 소자 하나만 보고는 못 하는 판단(파트너 소자와의 관계가 필요)이라
    `assign_roles()` 본문 루프 전에 미리 전역으로 한 번 계산해 둔다."""
    legs = set()
    for a in devs:
        for b in devs:
            if a['name'] >= b['name'] or a['type'] == b['type']: continue
            if a['S'] != b['D'] or a['D'] != b['S']: continue
            if a['S'] in RAILS or a['D'] in RAILS: continue
            if a['G'] == b['G'] or a['G'] in RAILS or b['G'] in RAILS: continue
            legs.add(a['name']); legs.add(b['name'])
    return legs


def _diode_cascode_legs(devs):
    """diode-connected 소자(`up`, `up.G==up.D`) 바로 아래(직렬, `lo.D==up.S`)에 얹혀
    그 diode의 노드를 그대로 게이트로 받는(`lo.G==up.D`) 소자를 구한다 -- `idioms.py`
    의 `m_diode_cascode()`와 동일 판정 기준(2026-08-08 신설, 사용자 지적: `M63`이
    `M64`(diode) 바로 아래서 같은 노드를 게이트로 받는 걸 idiom 층에서 잡았는데,
    `assign_roles()`는 여전히 그냥 `CASCODE`로 뭉뚱그리고 있었다 -- `FLOAT_SRC`와
    같은 이유로 role 계층에서도 분리해야 `idioms.py`를 안 거치는 소비자까지 정확해진다).
    diode 여부(`up.G==up.D`) 자체는 role을 몰라도 판정 가능해서(자기참조 연결성 사실)
    role 배정 이전에 안전하게 미리 계산할 수 있다."""
    by_d = defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    legs = set()
    for up in devs:
        if up['G'] != up['D']: continue
        for lo in by_d[up['S']]:
            if lo['name'] == up['name']: continue
            if lo['G'] != up['D']: continue
            legs.add(lo['name'])
    return legs


def assign_roles(devs, cls, imp):
    """
    Stage 2. net class 가 주어지면 완전히 결정론적이다.
    판정 순서가 중요하다 — 위쪽 규칙이 더 특수하다.
    """
    role = {}
    float_legs = _floating_source_legs(devs)
    diode_casc_legs = _diode_cascode_legs(devs)
    for d in devs:
        n, g, dr, s = d['name'], d['G'], d['D'], d['S']
        gc, sc = cls.get(g), cls.get(s)

        if g == dr:
            role[n] = DIODE
        elif gc == CLOCK:
            role[n] = SWITCH
        elif gc in (SIGNAL, INPUT, OUTPUT):
            # 게이트가 신호를 받는 소자
            if dr in RAILS and s not in RAILS:
                role[n] = FOLLOWER          # 드레인 접지 = 소스 팔로워
            else:
                role[n] = AMP
        elif gc == FEEDBACK:
            role[n] = CTRL_SRC
        elif gc == BIAS:
            if s in RAILS:
                # 레일에 소스가 붙은 고정 바이어스 소자.
                # 드레인이 이득 노드면 능동부하, 아니면 전류원.
                role[n] = ACTIVE_LOAD if imp.get(dr) == HIGH_Z else CURR_SRC
            elif n in float_legs:
                role[n] = FLOAT_SRC         # 비-레일 anti-parallel 상보쌍 = floating 전류원
            elif n in diode_casc_legs:
                role[n] = DIODE_CASC        # 바로 위 diode의 노드를 게이트로 직접 받음
            else:
                role[n] = CASCODE           # 소스가 내부 노드 = 직렬 적층
        else:
            role[n] = 'UNRESOLVED'
    return role


def stack_edges(devs):
    """직렬 적층 관계: X.S == Y.D 이면 Y 위에 X 가 얹혀 있다."""
    out = []
    by_d = defaultdict(list)
    for d in devs: by_d[d['D']].append(d)
    for d in devs:
        if d['S'] in RAILS: continue
        for lower in by_d[d['S']]:
            if lower['name'] != d['name']:
                out.append((lower['name'], d['name'], d['S']))
    return out
