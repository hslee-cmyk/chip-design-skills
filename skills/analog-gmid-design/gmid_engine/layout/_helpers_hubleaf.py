"""MOD7 hub-leaf 공용 helper(두 패턴 파일 공용) -- 옛 stick_diagram.py 본문 복사(L10).

정의 이름은 복사 원본 그대로 `_` 로 시작한다(본문·호출부 AST 해시 보존). 다른 파일은
아래 끝의 공개 별칭(앞 `_` 를 뗀 이름)으로 import 하고 `as _원래이름` 으로 다시 묶는다
(구조 규칙 B: 다른 파일의 `_` 이름 import 금지).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .transistor import Transistor
from .euler_graph import build_graph
from .euler_condition import check_euler_condition
from .euler_trail import hierholzer
from .crossover import find_min_crossover_layout


def _hubleaf_sequence_node_path(trs: list, hub_net, leaf_of: dict):
    """주어진 finger 순서(trs)가 hub-leaf 그래프(공유 hub_net + 소자별 leaf_of[name])에서
    실제로 인접 finger가 공유 net을 갖는 유효한 오일러 경로/회로인지 **가정하지 않고 직접
    검증**한다 — 가능한 시작 노드(hub 또는 각 leaf)로 순회를 시도해 끝까지 막힘없이
    이어지면 그 node_sequence를 반환하고, 어느 시작점으로도 안 되면 None을 반환한다.
    `common_centroid_layout()`의 그래프 기반(rotation_exact) 경로가
    `build_graph()`+`hierholzer()`로 아예 유효한 순서를 계산해내는 것과 달리, 이 함수는
    **이미 정해진(패턴표에서 온) 순서 하나가 유효한지만**
    검사한다 — 표의 pattern_key마다 실제로 1개 metal layer로 실현 가능한지가 다르기
    때문에(§2.7.2: `ABBA`/`AAB`는 가능, `ABA`는 불가능, 실측으로 확인됨) 반드시 필요한
    검증 단계다."""
    candidate_starts = {hub_net} | {leaf_of[name] for name in trs}
    for n0 in candidate_starts:
        n = n0
        path = [n0]
        ok = True
        for name in trs:
            edge = {hub_net, leaf_of[name]}
            if n not in edge:
                ok = False
                break
            n = next(iter(edge - {n})) if len(edge) == 2 else n
            path.append(n)
        if ok:
            return path
    return None


def _row_feasible(share, leaf_of: dict, hub_net) -> bool:
    """`share`(`{name: count}`)가 한 행(1개 metal layer, hub-leaf 오일러 walk)으로 실현
    가능한지 확인한다(실제 소자가 1개 이하면 자명하게 가능)."""
    trs = [Transistor(nm, "nmos", source=hub_net, drain=leaf_of[nm], n_fingers=c)
           for nm, c in share.items() if c > 0]
    if len(trs) <= 1:
        return True
    return check_euler_condition(build_graph(trs)).kind != "impossible"


def _repair_row_parity(shares: list, leaf_of: dict, hub_net, max_iters: int = 50):
    """`_slice_into_rows()`가 만든 소자별 개수 배분 중 오일러 조건이 깨진 행이 있으면
    (홀수차수 leaf 3개 이상), 그 행의 홀수-개수 소자 하나를 골라 인접 행과 1개씩
    주고받아본다 — 양쪽 다 실현 가능해지는 조합을 찾으면 채택(실측 확인: A=6/B=4/C=2를
    4행으로 나눌 때 슬라이싱만으로는 모든 phase가 실패했지만 이 보정으로 해결됨). 못
    고치면 `None`(그 phase는 이 target_rows로 포기)."""
    shares = [Counter(s) for s in shares]
    for _ in range(max_iters):
        bad = [i for i, s in enumerate(shares) if not _row_feasible(s, leaf_of, hub_net)]
        if not bad:
            return shares
        i = bad[0]
        fixed = False
        odd_names = [nm for nm, c in shares[i].items() if c % 2 == 1]
        for nm in odd_names:
            for j in (i - 1, i + 1):
                if j < 0 or j >= len(shares) or j == i:
                    continue
                trial_i, trial_j = dict(shares[i]), dict(shares[j])
                trial_i[nm] -= 1
                trial_j[nm] = trial_j.get(nm, 0) + 1
                if trial_i[nm] == 0:
                    del trial_i[nm]
                if _row_feasible(trial_i, leaf_of, hub_net) and _row_feasible(trial_j, leaf_of, hub_net):
                    shares[i], shares[j] = Counter(trial_i), Counter(trial_j)
                    fixed = True
                    break
            if fixed:
                break
        if not fixed:
            return None
    return None


def _build_rows_from_shares(shares: list, leaf_of: dict, hub_net):
    """각 행의 소자별 개수 배분(`shares`)을 실제 `build_graph()`+`hierholzer()`로 finger
    순서까지 계산한다 — **0-crossover 전용**, 실현 불가능한 행이 남아있으면 `None`(호출자가
    `_build_rows_from_shares_with_crossover()`로 폴백할지 판단). `"segments"`는 항상 행
    전체 1개짜리, `"crossover_after"`는 항상 빈 리스트(회전 경로와 스키마를 맞추기 위함)."""
    rows = []
    for share in shares:
        trs = [Transistor(nm, "nmos", source=hub_net, drain=leaf_of[nm], n_fingers=c)
               for nm, c in share.items() if c > 0]
        if not trs:
            rows.append({"transistor_sequence": [], "node_sequence": [], "segments": [], "crossover_after": []})
            continue
        g = build_graph(trs)
        v = check_euler_condition(g)
        if v.kind == "impossible":
            return None
        nodes, seq = hierholzer(g, v.start)
        rows.append({
            "transistor_sequence": seq, "node_sequence": nodes,
            "segments": [{"transistor_sequence": seq, "node_sequence": nodes}],
            "crossover_after": [],
        })
    return rows


def _build_rows_from_shares_with_crossover(shares: list, leaf_of: dict, hub_net):
    """`_build_rows_from_shares()`의 crossover-허용판(2026-07-28 4차 신설 — 탐색 경로에도
    회전 경로와 같은 crossover 폴백을 추가해달라는 요청) — **절대 실패하지 않는다**(각 행이
    0-crossover로 안 되면 `find_min_crossover_layout()`으로 최소 crossover 배치를 대신
    쓴다, `find_min_crossover_layout()` 자체가 그래프 이론상 항상 성공하므로). 반환:
    `(rows, total_crossover_count)` — `total_crossover_count`는 이 후보의 모든 행에 걸친
    crossover 총합(탐색 경로의 사전식 정렬 1순위 기준으로 쓰임, `_common_centroid_nway_
    search()` 참고)."""
    rows = []
    total_crossover = 0
    for share in shares:
        trs = [Transistor(nm, "nmos", source=hub_net, drain=leaf_of[nm], n_fingers=c)
               for nm, c in share.items() if c > 0]
        if not trs:
            rows.append({"transistor_sequence": [], "node_sequence": [], "segments": [], "crossover_after": []})
            continue
        g = build_graph(trs)
        v = check_euler_condition(g)
        if v.kind != "impossible":
            nodes, seq = hierholzer(g, v.start)
            rows.append({
                "transistor_sequence": seq, "node_sequence": nodes,
                "segments": [{"transistor_sequence": seq, "node_sequence": nodes}],
                "crossover_after": [],
            })
            continue
        mc = find_min_crossover_layout(trs)
        flat_names = [nm for seg in mc["segments"] for nm in seg["transistor_sequence"]]
        flat_nodes = [nd for seg in mc["segments"] for nd in seg["node_sequence"]]
        crossover_after = []
        cursor = -1
        for seg in mc["segments"][:-1]:
            cursor += len(seg["transistor_sequence"])
            crossover_after.append(cursor)
        rows.append({
            "transistor_sequence": flat_names, "node_sequence": flat_nodes,
            "segments": mc["segments"], "crossover_after": crossover_after,
        })
        total_crossover += mc["crossover_count"]
    return rows, total_crossover


def _common_centroid_residual(rows: list) -> float:
    """각 소자의 "행 내 상대 위치"(0~1, 그 행 길이로 정규화 — 행 길이가 달라도 비교
    가능하도록)를 전부 모아 평균 낸 뒤, 소자 간 평균 차이(최대-최소)를 잔차로 삼는다.
    0이면 완전한 common-centroid(모든 소자 평균 위치 일치).

    ⚠️ 2026-07-28 실측으로 발견/수정된 결함: 길이 1인 행을 그냥 건너뛰면(이전 버전),
    어떤 소자가 길이 1인 행에만 등장하고 길이 2 이상인 행에는 전혀 없을 때 그 소자가
    `positions`에 아예 안 잡혀 — 즉 존재하지 않는 것처럼 완전히 빠진 채로 잔차가
    계산됐다(실측: A만 있는 길이2 행 + B만 있는 길이1 행 2개로 구성하면 잔차=0.0이
    나왔다 — B가 통째로 빠졌는데 "완벽"으로 잘못 보고된 것). 길이 1인 행은 대신
    **중립값 0.5**(어느 쪽으로도 치우치지 않은 위치)를 부여해 그 소자가 반드시
    `positions`에 기록되도록 한다 — 0이나 1(양 끝) 대신 0.5를 쓰는 이유는 왼쪽/오른쪽
    치우침을 인위적으로 만들지 않기 위해서다. 길이 0인 행(소자 없음)만 실제로 건너뛴다."""
    positions = defaultdict(list)
    for row in rows:
        seq = row["transistor_sequence"]
        length = len(seq)
        if length == 0:
            continue
        if length == 1:
            positions[seq[0]].append(0.5)
            continue
        for i, nm in enumerate(seq):
            positions[nm].append(i / (length - 1))
    if not positions:
        return 0.0
    avgs = [sum(p) / len(p) for p in positions.values()]
    return max(avgs) - min(avgs)


def _count_isolated_pairs(rows: list, names: list) -> int:
    """`names`의 모든 소자 쌍 중, 단 하나의 행에서도 함께 등장한 적이 없는(=한 번도
    같은 행에 같이 배치되지 않은) 쌍의 개수를 센다. 2026-07-28 실측으로 발견된 잔차
    지표의 개념적 한계에 대응하기 위한 보조 지표: 소자 하나가 통째로 자기 행에만
    격리되면(예: A는 항상 자기 혼자만 있는 행, B도 항상 자기 혼자만 있는 행) 각자
    행 내부에서는 대칭적으로 보여 `_common_centroid_residual()`이 0에 가깝게 나올 수
    있지만, 실제로는 서로 전혀 섞이지 않은 것이라 진짜 common-centroid가 아니다. 0이면
    모든 쌍이 적어도 한 행에서 공존했다는 뜻(잔차가 낮다고 주장하기 전에 최소한의
    타당성 조건)."""
    cooccurred = set()
    for row in rows:
        present = set(row["transistor_sequence"])
        for i, a in enumerate(names):
            if a not in present:
                continue
            for b in names[i + 1:]:
                if b in present:
                    cooccurred.add((a, b))
    total_pairs = len(names) * (len(names) - 1) // 2
    return total_pairs - len(cooccurred)


# 공개 별칭 -- 다른 layout 파일이 쓰는 helper(정의 이름은 복사 원본 그대로).
build_rows_from_shares = _build_rows_from_shares
build_rows_from_shares_with_crossover = _build_rows_from_shares_with_crossover
common_centroid_residual = _common_centroid_residual
count_isolated_pairs = _count_isolated_pairs
hubleaf_sequence_node_path = _hubleaf_sequence_node_path
repair_row_parity = _repair_row_parity
