#!/usr/bin/env python3
"""
sfg.py — Stage 5 (signal flow graph) + Stage 6 (기능 가설)

Stage 5 는 그래프 연산이라 결정론적이다.
Stage 6 은 '구조 시그니처'까지만 결정론적으로 만들고, 그것을 사람이 읽는
기능 서술로 옮기는 마지막 한 걸음만 LLM 에게 남긴다. 이 분리가 중요하다 —
시그니처가 근거이고 서술은 표현일 뿐이므로, 서술이 틀려도 시그니처로
되짚을 수 있다.
"""
from collections import defaultdict
from netclass import (RAILS, HIGH_Z, LOW_Z, BIAS, SIGNAL, INPUT, OUTPUT,
                      FEEDBACK, CLOCK, SUPPLY, GROUND,
                      AMP, CASCODE, FLOAT_SRC, FOLLOWER, DIODE, CTRL_SRC,
                      ACTIVE_LOAD, CURR_SRC)


def build_sfg(devs, cls, imp, role):
    """
    방향성 신호 흐름 그래프.
      gate -> drain   : 반전 transconductance
      gate -> source  : 비반전 (source follower)
      source -> drain : current buffer (cascode)
    """
    E = []
    for d in devs:
        n, g, dr, s = d['name'], d['G'], d['D'], d['S']
        if cls.get(g) in (SIGNAL, INPUT, OUTPUT, FEEDBACK):
            if dr not in RAILS:
                E.append((g, dr, '-', n, 'gm'))
            if s not in RAILS and role[n] == FOLLOWER:
                E.append((g, s, '+', n, 'follower'))
        if role[n] in (CASCODE, FLOAT_SRC) and s not in RAILS and dr not in RAILS:
            E.append((s, dr, '+', n, 'cascode'))
    return E


def forward_paths(E, srcs, dsts, limit=40):
    adj = defaultdict(list)
    for a, b, sgn, dev, kind in E: adj[a].append((b, sgn, dev))
    out = []
    def walk(n, path, sign, seen):
        if len(out) >= limit: return
        if n in dsts and len(path) > 1:
            out.append((list(path), sign)); return
        for nx, sgn, dev in adj[n]:
            if nx in seen: continue
            walk(nx, path + [nx], sign * (-1 if sgn == '-' else 1), seen | {nx})
    for s in srcs: walk(s, [s], 1, {s})
    return out


def find_loops(E, limit=20):
    adj = defaultdict(list)
    for a, b, sgn, dev, kind in E: adj[a].append((b, sgn, dev))
    loops, seen = [], set()
    def walk(start, n, path, sign):
        if len(loops) >= limit: return
        for nx, sgn, dev in adj[n]:
            s2 = sign * (-1 if sgn == '-' else 1)
            if nx == start and len(path) >= 2:
                keyv = tuple(sorted(path))
                if keyv not in seen:
                    seen.add(keyv); loops.append((list(path), s2))
            elif nx not in path and len(path) < 8:
                walk(start, nx, path + [nx], s2)
    for n in list(adj): walk(n, n, [n], 1)
    return loops


def structural_signature(devs, cls, imp, role, kept, sup, E):
    """
    Stage 6a — 결정론적 구조 시그니처. 여기까지가 코드의 책임 범위다.
    """
    kinds = [m.kind for m in kept]
    gain_nodes = sorted(n for n, z in imp.items()
                        if z == HIGH_Z and cls.get(n) in (SIGNAL, OUTPUT))
    ins  = sorted(n for n, c in cls.items() if c == INPUT)
    outs = sorted(n for n, c in cls.items() if c == OUTPUT) or gain_nodes
    fbs  = sorted(n for n, c in cls.items() if c == FEEDBACK)

    paths = forward_paths(E, ins, set(outs))
    loops = find_loops(E)

    # 차동 여부: 입력 2개 + 대칭 diff-pair 존재
    # current-reuse-pair 는 differential-pair 를 흡수하므로 함께 봐야 한다
    diff = len(ins) == 2 and any(
        k in ('differential-pair', 'current-reuse-pair') for k in kinds)
    # 이득단 수: 정방향 경로가 지나는 서로 다른 이득 노드 수의 최댓값
    stages = 0
    for p, _ in paths:
        stages = max(stages, sum(1 for n in p if n in gain_nodes))
    stages = stages or (1 if gain_nodes else 0)

    sig = dict(
        n_devices=len(devs),
        differential=diff,
        inputs=ins, outputs=outs, feedback_nets=fbs,
        gain_nodes=gain_nodes,
        gain_stages=stages,
        output_impedance='HIGH_Z (transconductance)' if outs and imp.get(outs[0]) == HIGH_Z
                         else 'LOW_Z (voltage output)',
        idioms=sorted(set(kinds)),
        supernodes=[f"{s['id']}:{s['kind']}({'+'.join(s['members'])})" for s in sup],
        forward_paths=[('->'.join(p), '반전' if sgn < 0 else '비반전') for p, sgn in paths[:8]],
        loops=[('->'.join(p), '음귀환' if sgn < 0 else '양귀환') for p, sgn in loops[:8]],
        roles={d['name']: role[d['name']] for d in devs},
    )
    return sig


def hypothesise(sig):
    """
    Stage 6b — 시그니처에서 규칙으로 도출 가능한 기능 서술.
    규칙으로 안 되는 부분(문헌상의 정확한 명칭, 신규 구조 명명)은
    LLM 에게 넘길 근거로 남긴다.
    """
    H, evid = [], []
    ids = set(sig['idioms'])

    if sig['differential']:
        H.append('fully differential' if len(sig['outputs']) >= 2 else 'differential input')
        evid.append('differential-pair + 입력 넷 2개')
    if 'current-reuse-pair' in ids:
        H.append('current-reuse 입력단 (gm_eff = gmn + gmp)')
        evid.append('상보형 차동쌍 2조가 동일 입력 게이트를 공유')
    if 'cascoded-gain-node' in ids:
        H.append('cascode 이득 노드 (telescopic 또는 folded)')
        evid.append('이득 노드에 상보형 cascode 드레인 대향')
    if 'push-pull-output' in ids:
        H.append('push-pull 출력단')
        evid.append('상보 쌍이 출력 노드 공유')
    if 'floating-battery' in ids:
        H.append('class-AB 바이어스 (floating battery)')
        evid.append('diode-connected 직렬쌍이 게이트 구동 레벨차 생성')
    if 'floating-current-source' in ids:
        H.append('Monticelli floating current source (class-AB 출력단 quiescent 전류 고정)')
        evid.append('상보형(PMOS/NMOS) 소자 쌍이 비-레일 노드 2개 사이를 anti-parallel loop로 순환')
    if 'current-mirror' in ids:
        H.append('current mirror 바이어싱')
    if sig['feedback_nets']:
        H.append(f"CM 또는 전역 귀환 존재 ({', '.join(sig['feedback_nets'])})")
        evid.append('FEEDBACK 클래스 넷이 게이트를 구동')
    if sig['gain_stages'] >= 2:
        H.append(f"{sig['gain_stages']}단 증폭")
    elif sig['gain_stages'] == 1:
        H.append('단일 이득단 (이 도면 범위에서)')
    if sig['output_impedance'].startswith('HIGH_Z'):
        H.append('transconductance 출력 (OTA 계열)')

    neg = [p for p, k in sig['loops'] if k == '음귀환']
    if neg: evid.append(f"음귀환 루프 {len(neg)}개 검출")
    return H, evid
