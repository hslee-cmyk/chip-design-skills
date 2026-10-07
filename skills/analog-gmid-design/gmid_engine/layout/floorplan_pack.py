"""MOD7 floorplan 패킹 `pack_floorplan_grouped` -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FloorplanBlock:
    """floorplan 배치 대상 1개 — stick diagram의 stack(들)을 하나의 사각형으로 집계한 것.
    `width`/`height`는 절대 물리 치수가 아니라 **비율 프록시**다(finger 개수/행 개수 기반) —
    실제 실리콘 치수를 아는 것처럼 지어내지 않는다는 원칙을 여기서도 지킨다."""
    name: str
    width: float
    height: float


@dataclass
class PlacedBlock:
    name: str
    x: float
    y: float
    width: float
    height: float


@dataclass
class FloorplanResult:
    placements: dict            # name -> PlacedBlock
    bbox_width: float
    bbox_height: float
    aspect_ratio: float          # max(w,h)/min(w,h) -- check_box_shape()과 같은 개념, 스케일만 다름
    packing_density: float       # 전체 block 면적 합 / bbox 면적 -- 1.0에 가까울수록 빈 공간 없음
    symmetry_axis_x: float
    symmetry_max_error: float    # 좌우 대칭쌍의 위치/크기 불일치 최대값(0이면 완전 대칭)
    row_split_candidates: list   # 아래 evaluate_row_split_candidates() 참고


def _block_center(p: "PlacedBlock"):
    return (p.x + p.width / 2, p.y + p.height / 2)


def _total_wire_cost(placements: dict, connections: dict | None, y_targets: dict | None = None) -> float:
    """완성된 배치 하나에 대해, `connections`/`y_targets`가 요구하는 근접성을 실제로 얼마나
    만족했는지 하나의 숫자(가중 맨해튼 거리 합)로 집계한다. `skyline_pack()`이 배치 "도중"
    후보 하나를 고를 때 쓰는 지역적 판단과 달리, 이건 배치가 끝난 뒤 결과 전체를 평가하는
    용도다 — `pack_to_height()`가 "여러 폭 후보 중 어느 게 실제로 배선에 더 유리한가"를
    비교하려면 배치 도중 판단이 아니라 이 완성본 평가가 필요하다."""
    connections = connections or {}
    y_targets = y_targets or {}
    cost = 0.0
    seen = set()
    for name, conns in connections.items():
        if name not in placements:
            continue
        cx1, cy1 = _block_center(placements[name])
        for other, w in conns.items():
            if other not in placements or other == name:
                continue
            key = tuple(sorted((name, other)))
            if key in seen:
                continue
            seen.add(key)
            cx2, cy2 = _block_center(placements[other])
            cost += w * (abs(cx1 - cx2) + abs(cy1 - cy2))
    for name, target_y in y_targets.items():
        if name in placements:
            _, cy = _block_center(placements[name])
            cost += abs(cy - target_y)
    return cost


def skyline_pack(blocks: list, max_width: float, gap: float = 1.0,
                  connections: dict | None = None, y_targets: dict | None = None,
                  height_tolerance: float = 0.0):
    """Bottom-left skyline bin packing (Jylänki 2010) — 폭 `max_width` 안에서 각 블록을
    "지금까지 쌓인 윤곽선(skyline) 중 가장 낮아지는 위치"에 순서대로 배치해 빈 공간을
    최소화한다. 높이가 큰 블록부터 배치하는 것이 이 휴리스틱의 표준 순서(정렬 없이 입력
    순서대로 넣으면 큰 블록이 나중에 들어와 이미 채워진 자리를 못 쓰고 새 공간을 만든다).

    **신호선 근접 배치(2026-07-27 신설)**: 순수 면적 최적화만 하면 실제로 서로 강하게
    연결된 두 블록(예: bias-gen의 vbias1 leg와 그걸 게이트로 읽는 Class-AB 소자)이 아무
    회로적 이유 없이 멀리 떨어지는 사고가 실제로 있었다(§7에 "classab_p2는 biasgen 바로
    옆에 둬야 한다"고 명시했으면서도 §8 floorplan 좌표는 10칸 떨어져 있었다). 면적(높이)
    최소화가 여전히 **1순위**이므로, `height_tolerance` 이내로 높이가 비슷한 후보들 중에서만
    아래 두 가지로 2순위 배점한다(면적을 크게 희생하면서까지 배선 근접을 강제하지 않는다):
    - `connections`: `{name: {other_name: weight}}` — 이 함수 호출 안에서 **같이 packing되는**
      다른 블록과의 연결 가중치. 이미 배치된 연결 상대와의 중심점 거리 합에 가중치를 곱해 비용을
      계산하고, 낮을수록 선호한다.
    - `y_targets`: `{name: target_y}` — **이 호출 밖에서 이미 확정된** 다른 그룹의 y좌표에
      맞추고 싶을 때(예: spine을 먼저 packing해 bias-gen의 y를 알아낸 뒤, 별도로 packing하는
      Class-AB pair 유닛을 그 y에 가깝게 배치) 쓴다. `|y - target_y|`가 비용에 더해진다.

    반환: `(placements: {name: PlacedBlock}, bbox_width, bbox_height)` — 어떤 블록이 `max_width`
    안에 전혀 들어갈 자리가 없으면(폭 자체가 `max_width`보다 크거나, 배치 시도 중 자리를 못
    찾으면) `None`을 반환한다 — 호출자(`skyline_pack_best_width`)가 더 큰 `max_width`로 재시도."""
    connections = connections or {}
    y_targets = y_targets or {}
    ordered = sorted(blocks, key=lambda b: -b.height)
    skyline = [[0.0, max_width, 0.0]]  # [x_start, width, y] 세그먼트 목록
    placements = {}

    def height_at_span(x0, w):
        x1 = x0 + w
        y = 0.0
        for seg_x, seg_w, seg_y in skyline:
            if seg_x < x1 and seg_x + seg_w > x0:
                y = max(y, seg_y)
        return y

    def update_skyline(x0, w, new_y):
        x1 = x0 + w
        new_segs = []
        for seg_x, seg_w, seg_y in skyline:
            seg_x1 = seg_x + seg_w
            if seg_x1 <= x0 or seg_x >= x1:
                new_segs.append([seg_x, seg_w, seg_y]); continue
            if seg_x < x0:
                new_segs.append([seg_x, x0 - seg_x, seg_y])
            if seg_x1 > x1:
                new_segs.append([x1, seg_x1 - x1, seg_y])
        new_segs.append([x0, w, new_y])
        new_segs.sort(key=lambda s: s[0])
        skyline[:] = new_segs

    def wire_cost(name, x, y, w, h):
        cx, cy = x + w / 2, y + h / 2
        cost = 0.0
        for other, weight in connections.get(name, {}).items():
            if other in placements:
                ox, oy = _block_center(placements[other])
                cost += weight * (abs(cx - ox) + abs(cy - oy))
        if name in y_targets:
            cost += abs(cy - y_targets[name])
        return cost

    for b in ordered:
        if b.width > max_width:
            return None
        xs = [s[0] for s in skyline if s[0] + b.width <= max_width + 1e-9]
        if not xs:
            return None
        raw = [(x, height_at_span(x, b.width)) for x in xs]
        min_h = min(y for _, y in raw)
        candidates = [(x, y) for x, y in raw if y <= min_h + height_tolerance]
        if connections.get(b.name) or b.name in y_targets:
            x, y = min(candidates, key=lambda xy: (wire_cost(b.name, xy[0], xy[1], b.width, b.height), xy[1], xy[0]))
        else:
            x, y = min(candidates, key=lambda xy: (xy[1], xy[0]))
        placements[b.name] = PlacedBlock(b.name, x=x, y=y, width=b.width, height=b.height)
        update_skyline(x, b.width + gap, y + b.height + gap)

    bbox_w = max(p.x + p.width for p in placements.values())
    bbox_h = max(p.y + p.height for p in placements.values())
    return placements, bbox_w, bbox_h


def _sweep_widths(blocks: list, gap: float, width_steps: int,
                   connections: dict | None, y_targets: dict | None,
                   height_tolerance: float) -> list:
    """`min_w`(가장 넓은 블록의 폭)~`max_w`(모든 블록을 옆으로 늘어놓은 폭) 구간을
    `width_steps`개로 나눠 각 폭에서 `skyline_pack()`을 한 번씩 돌려본 `(w, placements, bw,
    bh)` 후보 리스트를 낸다 — `skyline_pack_best_width()`/`pack_to_height()`가 이 스윕 루프를
    각자 복붙해서 갖고 있던 걸 공용 코어로 뽑았다(2026-07-28, 순수 리팩터 — 동작 동일).
    스윕 자체는 후보만 생성하고, "어느 폭을 채택할지"(ratio 최근접인지, target_height 이하
    중 최소폭/배선비용인지)는 호출자가 반환값 위에서 직접 판단한다."""
    min_w = max(b.width for b in blocks)
    max_w = sum(b.width for b in blocks) + gap * len(blocks)
    candidates = []
    for i in range(width_steps + 1):
        w = min_w + (max_w - min_w) * i / width_steps
        result = skyline_pack(blocks, w, gap=gap, connections=connections, y_targets=y_targets,
                               height_tolerance=height_tolerance)
        if result is None:
            continue
        placements, bw, bh = result
        candidates.append((w, placements, bw, bh))
    return candidates


def skyline_pack_best_width(blocks: list, gap: float = 1.0, width_steps: int = 60,
                             target_ratio: float = 1.0, connections: dict | None = None,
                             y_targets: dict | None = None, height_tolerance: float = 0.0):
    """`skyline_pack()`은 컨테이너 폭을 입력으로 받는데, 그 폭 자체는 이 알고리즘이 정하지
    않는다(문헌에서도 호출자가 폭을 정하거나 스윕하는 것이 표준 사용법이다). 여기서는 후보 폭을
    여러 개 스윕해 **이 skill의 box-shape 목표(`check_box_shape()`, ratio<=1.5)와 같은 기준**
    으로 가장 정사각형에 가까운(= `target_ratio`에 가장 가까운) 결과를 고른다 — 단순히 면적을
    최소화하면 아주 옆으로 길쭉한 모양이 최소 면적일 수 있어(실제로 이 함수 작성 중 확인됨)
    이 skill이 지금까지 일관되게 써온 "비율" 기준과 다른 목표를 최적화하게 된다.

    **언제 이 함수를 쓰는가**: 대칭쌍이 전혀 없는(모두 spine뿐인, 또는 대칭 요구사항이 없는)
    단일 블록 그룹을 그 자체로 정사각형에 가깝게 packing하고 싶을 때 직접 쓴다. spine과 좌우
    대칭쌍을 함께 다뤄야 하면(이 skill의 일반적인 상황) 이 함수 대신 `pack_floorplan()`이
    내부에서 쓰는 `pack_to_height()`를 쓴다 — 두 조각을 각자 독립적으로 이 함수로 최적화하면
    서로 높이가 안 맞아 결합 결과가 길쭉해지는 문제가 실제로 있었다(`pack_floorplan()`
    docstring 참고)."""
    candidates = _sweep_widths(blocks, gap, width_steps, connections, y_targets, height_tolerance)
    best = None
    for w, placements, bw, bh in candidates:
        ratio = max(bw, bh) / min(bw, bh) if min(bw, bh) > 0 else float("inf")
        density = sum(b.width * b.height for b in blocks) / (bw * bh)
        score = (round(abs(ratio - target_ratio), 3), -density)
        if best is None or score < best[0]:
            best = (score, placements, bw, bh)
    return best[1], best[2], best[3]


def pack_to_height(blocks: list, target_height: float, gap: float = 1.0, width_steps: int = 60,
                    connections: dict | None = None, y_targets: dict | None = None,
                    height_tolerance: float = 0.0, width_tolerance: float = 0.0):
    """`skyline_pack_best_width()`가 "가장 정사각형에 가까운 폭"을 고르는 것과 달리, 이 함수는
    "결과 높이가 `target_height`를 넘지 않는 폭"을 찾는다 — spine과 좌우 pair-stack을
    **같은 목표 높이에 맞춰야** 나란히 배치했을 때 전체가 정사각형에 가까워지기 때문에
    (`pack_floorplan()`의 결합 단계가 이 함수를 쓰는 이유), 각 조각을 독립적으로 최적화하는
    `skyline_pack_best_width()`만으로는 부족하다(실제로 그렇게 짰다가 spine과 pair-stack의
    높이가 서로 안 맞아 전체 bbox가 옆으로 길쭉해지는 걸 이 함수 작성 전 버전에서 확인했다).

    **`width_tolerance`(2026-07-27 신설, `connections`/`y_targets`와 함께 쓸 것)**: 기본값
    0이면 이전과 동일하게(가장 좁은 폭 하나만 선택) 동작한다. 0보다 크면, "가장 좁은 폭"부터
    "가장 좁은 폭 + width_tolerance"까지의 후보들을 전부 계산해 그중 **완성된 배치의 실제
    배선 비용(`_total_wire_cost()`)이 가장 낮은 것**을 고른다.

    **왜 필요한가(실제 사고)**: `connections`/`y_targets`를 `skyline_pack()`에 줘도, 이 함수가
    "가장 좁은 폭 하나"만 시도하면 그 폭에서는 애초에 배치 후보가 1개뿐이라(컨테이너가 꽉
    차서 곁가지로 놓을 자리 자체가 없음) 배선 비용을 반영할 여지가 물리적으로 없다 — 실제로
    이 상태로 "bias-gen과 vbias1로 연결된 classab_p2를 가깝게 배치하라"를 시도했더니 폭을
    조금도 안 늘려서 전혀 안 움직였다. 폭을 살짝 늘려 곁가지로 놓을 자리를 만들어줘야 배선
    비용 비교가 의미를 갖는다 — 이것도 "면적을 무한정 희생하지 않는다"는 원칙과 같은 방식으로
    상한(`width_tolerance`)을 둔다."""
    max_w = sum(b.width for b in blocks) + gap * len(blocks)
    candidates = _sweep_widths(blocks, gap, width_steps, connections, y_targets, height_tolerance)
    valid = [(bw, placements, bh) for w, placements, bw, bh in candidates if bh <= target_height]
    if not valid:  # target_height too tight for any width -- fall back to widest (flattest) packing
        placements, bw, bh = skyline_pack(blocks, max_w, gap=gap, connections=connections,
                                           y_targets=y_targets, height_tolerance=height_tolerance)
        return placements, bw, bh
    min_bw = min(bw for bw, _, _ in valid)
    if width_tolerance <= 0 or not (connections or y_targets):
        bw, placements, bh = min(valid, key=lambda t: t[0])
        return placements, bw, bh
    band = [t for t in valid if t[0] <= min_bw + width_tolerance]
    bw, placements, bh = min(band, key=lambda t: _total_wire_cost(t[1], connections, y_targets))
    return placements, bw, bh


def find_diffusion_safe_split_points(transistor_sequence: list) -> list:
    """`build_stick_diagram()`이 반환한 실제 `transistor_sequence`(finger 순서)에서, 어느
    소자의 finger도 반으로 갈리지 않는 분할 지점을 전부 찾는다. 두 물리 finger가 연속
    diffusion을 공유하면(같은 소자의 병렬 finger들이 항상 그렇다) 그 사이를 끊어 서로 다른
    물리 행에 넣으려면 실제로는 그 소자를 2개로 쪼개 만들고 별도 contact/via를 추가해야 한다
    (이른바 "소자 folding") — 이건 사소한 배치 조정이 아니라 별도 설계 결정이므로, 이 함수는
    그런 지점을 "안전한 분할점"으로 취급하지 않는다.

    분할 지점 i(1<=i<len(seq))가 안전하려면 `seq[:i]`와 `seq[i:]`에 **공통으로 등장하는 소자
    이름이 하나도 없어야** 한다 — 즉 각 소자가 어느 한쪽에만 통째로 들어있어야 한다.

    반환: 안전한 분할 지점 인덱스 리스트(오름차순, 없으면 빈 리스트 — 예: 이 세션의 실제
    S1_TAILP 시퀀스 `[M6,M6,M6,M6,M7,M6,M7,M6,M7,M6]`은 M6/M7이 전체 구간에 걸쳐 완전히
    인터리브돼 있어 안전한 분할 지점이 하나도 없다 — `find_diffusion_safe_split_points()`로
    실제 확인됨)."""
    n = len(transistor_sequence)
    valid = []
    for i in range(1, n):
        left, right = set(transistor_sequence[:i]), set(transistor_sequence[i:])
        if not (left & right):
            valid.append(i)
    return valid


def evaluate_row_split_candidates(blocks: list, bbox_width: float, bbox_height: float,
                                   dominance_ratio: float = 0.6,
                                   transistor_sequences: dict | None = None) -> list:
    """packing이 끝난 뒤, 특정 블록 하나의 폭(또는 높이)이 전체 bbox의 지배적인 부분을 차지해
    box-shape를 깨뜨리고 있는지 진단한다 — §8.5(row-split 비용 계산)와 같은 목적을 floorplan
    레벨로 옮긴 것. **이 함수는 스스로 finger 수를 바꾸지 않는다** — 후보만 알려준다.

    `transistor_sequences`(선택, `{block_name: transistor_sequence}` — `build_stick_diagram()`
    이 실제로 반환한 값 그대로): 주어지면 각 후보에 대해 `find_diffusion_safe_split_points()`로
    **실제로 안전하게 쪼갤 수 있는 지점이 있는지까지 확인**한다(사용자 지적: "packing할 때
    MOS의 diffusion 영역이 고려돼서 엉뚱하게 split되는 문제가 없도록 해야 한다" — 폭/높이가
    지배적이라는 사실만으로 분할을 추천하면 특정 소자의 finger를 반으로 가르는 물리적으로
    무의미한 분할을 제안할 위험이 있다. 실제로 이 회로의 S1_TAILP(M6:M7 인터리브 tail)가 정확히
    이런 사례 — 폭이 가장 넓은 spine 행이지만 안전한 분할 지점이 하나도 없다). `splittable`이
    `False`면 **분할을 제안하지 말고** 대신 §8.5의 "행 분할 없이 수용" 논리를 적용할 것.
    `transistor_sequences`를 안 주면 `diffusion_check: "not_verified"`로 정직하게 표시한다 —
    확인 안 했으면서 안전하다고 가정하지 않는다.

    실제로 쪼개기로 결정하면(그리고 `splittable`이 True면) 그 블록의 원래 stick diagram
    (`build_stick_diagram()`/`check_box_shape()`)부터 그 안전한 지점 기준으로 다시 계산하고,
    그 결과로 바뀐 gm/ID·W가 있으면 §5(sizing Definition of Done)와 SPICE 재검증까지
    되먹여야 한다(design-report-spec.md §1.7 참고) — 이 함수 하나로 끝나는 최적화가 아니다."""
    candidates = []
    for b in blocks:
        dominant = b.width >= dominance_ratio * bbox_width
        dominant_h = b.height >= dominance_ratio * bbox_height
        if not dominant and not dominant_h:
            continue
        dim = "width" if dominant else "height"
        value = b.width if dominant else b.height
        bbox_dim = bbox_width if dominant else bbox_height
        entry = {
            "name": b.name, "dimension": dim, "value": value, "bbox": bbox_dim,
            "reason": f"{dim} {value} covers >= {dominance_ratio*100:.0f}% of bbox {dim} {bbox_dim}",
        }
        if transistor_sequences is not None and b.name in transistor_sequences:
            splits = find_diffusion_safe_split_points(transistor_sequences[b.name])
            entry["diffusion_check"] = "verified"
            entry["splittable"] = len(splits) > 0
            entry["safe_split_points"] = splits
            if not splits:
                entry["reason"] += (" -- but NO diffusion-safe split point exists (every device's "
                                     "fingers are interleaved across the whole row) -- do not split, "
                                     "accept per sec8.5 reasoning instead")
        else:
            entry["diffusion_check"] = "not_verified"
            entry["splittable"] = None
        candidates.append(entry)
    return candidates


def pack_floorplan(spine: list, mirror_pairs: list, gap: float = 1.0, height_steps: int = 40,
                    transistor_sequences: dict | None = None,
                    net_weights: dict | None = None, height_tolerance: float = 1.0,
                    width_tolerance: float = 2.0) -> FloorplanResult:
    """공유(비대칭) 블록(spine)과 좌우 대칭 블록 쌍(mirror_pairs)을 함께 packing한다.

    좌우 대칭 쌍은 **각 쌍을 (max(오른쪽폭,왼쪽폭) x max(오른쪽높이,왼쪽높이)) 크기의 단일
    유닛으로 취급해 그 유닛들끼리 packing**한 뒤, 유닛이 배치된 자리를 좌우로 거울반사해서
    실제 두 블록을 채운다 — 대칭은 유닛을 반으로 나눠 채우는 방식 자체가 구조적으로 보장한다
    (ASF-B*-tree의 symmetry-island와 같은 원리: 대칭 그룹을 따로 다뤄 사후 검증하는 게 아니라
    애초에 깨질 수 없게 만든다).

    spine과 pair-unit들은 **같은 목표 높이 H에 맞춰(`pack_to_height()`) 나란히 배치**한다 —
    spine과 pair-stack을 각자 독립적으로 "제일 정사각형에 가까운 모양"으로 최적화하면(첫
    재작성 버전이 이렇게 했다) 둘의 높이가 서로 안 맞아서 나란히 붙였을 때 전체가 옆으로
    길쭉해지는 문제가 실제로 나왔다 — "spine 폭 + pair-stack 폭 x 2"가 전체 폭이고 "두 높이의
    max"가 전체 높이이므로, 두 조각의 높이를 미리 맞춰야 결합 결과도 정사각형에 가까워진다.
    여러 후보 H를 스윕해서 결합 결과의 aspect ratio가 가장 낮아지는 H를 채택한다.

    이 결합 방식에도 한계가 있다 — spine과 pair-stack을 여전히 "따로 packing한 뒤 옆으로
    붙이는" 2단계 구조라, 완전한 non-slicing floorplan(모든 블록을 한 번에 최적화)만큼
    빈틈이 없지는 않다. 잔여 비대칭/저밀도는 `packing_density`/`row_split_candidates`로
    그대로 보고한다 — FAIL이면 §8.5/§1.7 절차로 재검토할 것(이 함수가 자동으로 재귀
    최적화하지 않는다 — 그렇게 하려면 전체를 simulated annealing급 B*-tree로 다시 짜야 하고,
    이 skill의 범위를 넘는다).

    `transistor_sequences`(선택, `{block_name: transistor_sequence}` — `build_stick_diagram()`
    의 실제 반환값): 주면 `row_split_candidates`가 각 후보에 대해 실제로 diffusion을 깨지 않고
    쪼갤 수 있는 지점이 있는지까지 확인한다(`evaluate_row_split_candidates()` 참고) — packing
    단계가 어떤 소자의 finger를 반으로 가르는 분할을 조용히 추천하는 일을 막는다. 안 주면 그
    확인 자체를 안 했다고 `diffusion_check: "not_verified"`로 정직하게 표시한다.

    **신호선 근접 배치(2026-07-27 신설)**: `net_weights`(선택, `{name: {other_name: weight}}`,
    양방향 대칭 아니어도 됨 — 한쪽만 적어도 조회됨) — 실제 회로 net 공유(예: bias-gen의 vbias1
    leg와 그걸 게이트로 읽는 Class-AB 소자)를 반영해 강하게 연결된 block/pair를 서로 가깝게
    배치한다. **면적(box-shape)이 여전히 1순위** — `height_tolerance`(기본 1.0)만큼 높이가
    늘어나는 것까지만 허용하고, 그 안에서만 배선 비용을 줄이는 위치를 고른다(면적을 무한정
    희생하면서 배선 근접을 강제하지 않는다). spine 블록/그룹 간 연결은 spine packing에 직접
    반영되고, `mirror_pairs`(spine과 별도로 packing되는 대칭 유닛)는 이미 배치가 끝난 spine
    블록들과의 연결 가중치를 바탕으로 `y_target`(연결된 spine 블록들의 y좌표 가중평균)을 계산해
    반영한다 — **실제 사고**: 이 파라미터가 없던 버전은 "classab_p2는 bias-gen 바로 옆에 둬야
    한다"(§7에 이미 명시돼 있었음)는 회로 지식을 floorplan 좌표에 전혀 반영하지 못해 둘이
    10칸이나 떨어져 있었다(사용자가 직접 지적: "배치는 신호선과 근접한 곳에 위치시키면
    routing delay가 없어진다")."""
    sym_errors = []
    pair_units, unit_of_pair = [], {}
    for right, left in mirror_pairs:
        uw, uh = max(right.width, left.width), max(right.height, left.height)
        unit_name = f"__unit__{right.name}__{left.name}"
        pair_units.append(FloorplanBlock(unit_name, uw, uh))
        unit_of_pair[unit_name] = (right, left)
        sym_errors.append(abs(right.width - left.width) + abs(right.height - left.height))

    net_weights = net_weights or {}
    total_area = sum(b.width * b.height for b in spine) + 2 * sum(u.width * u.height for u in pair_units)
    h0 = total_area ** 0.5 if total_area > 0 else 1.0

    best = None
    for i in range(height_steps + 1):
        H = h0 * 0.3 + (h0 * 2.2) * i / height_steps
        sp, sw, sh = pack_to_height(spine, H, gap=gap, connections=net_weights,
                                     height_tolerance=height_tolerance,
                                     width_tolerance=width_tolerance) if spine else ({}, 0.0, 0.0)
        # pair-unit y_target = weighted-average y-center of already-placed spine blocks it connects to
        pair_y_targets = {}
        for unit_name, (right, left) in unit_of_pair.items():
            weighted, total_w_ = 0.0, 0.0
            for other, w_ in net_weights.get(right.name, {}).items():
                if other in sp:
                    cy = sp[other].y + sp[other].height / 2
                    weighted += w_ * cy
                    total_w_ += w_
            if total_w_ > 0:
                pair_y_targets[unit_name] = weighted / total_w_
        pp, pw, ph = pack_to_height(pair_units, H, gap=gap, y_targets=pair_y_targets,
                                     height_tolerance=height_tolerance,
                                     width_tolerance=width_tolerance) if pair_units else ({}, 0.0, 0.0)
        total_w = sw + (2 * (gap + pw) if pair_units else 0.0)
        total_h = max(sh, ph)
        ratio = max(total_w, total_h) / min(total_w, total_h) if min(total_w, total_h) > 0 else float("inf")
        if best is None or ratio < best[0]:
            best = (ratio, sp, sw, sh, pp, pw, ph, total_w, total_h)

    _, spine_placements, spine_w, spine_h, pair_placements, pair_stack_w, pair_stack_h, bbox_width, bbox_height = best

    placements = {}
    for name, p in spine_placements.items():
        placements[name] = PlacedBlock(name, x=p.x - spine_w / 2, y=p.y, width=p.width, height=p.height)

    right_anchor = spine_w / 2 + gap
    for unit_name, p in pair_placements.items():
        right, left = unit_of_pair[unit_name]
        placements[right.name] = PlacedBlock(right.name, x=right_anchor + p.x, y=p.y,
                                              width=right.width, height=right.height)
        placements[left.name] = PlacedBlock(left.name, x=-(right_anchor + p.x + left.width), y=p.y,
                                             width=left.width, height=left.height)

    physical_area = sum(b.width * b.height for b in spine) + sum(
        r.width * r.height + l.width * l.height for r, l in mirror_pairs)
    bbox_area = bbox_width * bbox_height
    all_blocks = list(spine) + [b for pair in mirror_pairs for b in pair]
    return FloorplanResult(
        placements=placements, bbox_width=bbox_width, bbox_height=bbox_height,
        aspect_ratio=(max(bbox_width, bbox_height) / min(bbox_width, bbox_height)
                      if min(bbox_width, bbox_height) > 0 else float("inf")),
        packing_density=(physical_area / bbox_area if bbox_area > 0 else 0.0),
        symmetry_axis_x=0.0, symmetry_max_error=max(sym_errors) if sym_errors else 0.0,
        row_split_candidates=evaluate_row_split_candidates(
            all_blocks, bbox_width, bbox_height, transistor_sequences=transistor_sequences),
    )


def _pack_by_subkind(blocks: list, sub_kind: dict, gap: float = 1.0, height_steps: int = 40):
    """`blocks`를 `sub_kind`(예: `{"cmfb_p1": "pmos", "cmfb_n1": "nmos", ...}` — 같은 물리
    diffusion/폴러리티에 속하는 row를 묶는 키)로 나눠, 각 하위그룹을 **공통 목표 높이에
    맞춰서(`pack_to_height()`) 따로 packing한 뒤 옆으로 나란히 붙인다** — `pack_floorplan()`이
    spine과 mirror-pair-stack을 결합하는 것과 정확히 같은 원리를 그룹 내부에도 한 단계 더
    적용한 것. 2개 미만의 하위그룹이면(전부 같은 kind면) 나눌 의미가 없어 `None`을 반환한다.

    반환: `(FloorplanBlock, internal_placements)` — `pack_group_as_unit()`과 같은 형식."""
    by_kind: dict = {}
    for b in blocks:
        by_kind.setdefault(sub_kind.get(b.name, "_default"), []).append(b)
    if len(by_kind) < 2:
        return None

    total_area = sum(b.width * b.height for b in blocks)
    h0 = total_area ** 0.5 if total_area > 0 else 1.0
    best = None
    for i in range(height_steps + 1):
        H = h0 * 0.3 + (h0 * 2.2) * i / height_steps
        packed = []
        for kind, blks in by_kind.items():
            pl, bw, bh = pack_to_height(blks, H, gap=gap)
            packed.append((pl, bw, bh))
        total_w = sum(bw for _, bw, _ in packed) + gap * (len(packed) - 1)
        total_h = max(bh for _, _, bh in packed)
        ratio = max(total_w, total_h) / min(total_w, total_h) if min(total_w, total_h) > 0 else float("inf")
        if best is None or ratio < best[0]:
            best = (ratio, packed, total_w, total_h)
    _, packed, gw, gh = best

    internal = {}
    x_off = 0.0
    for pl, bw, bh in packed:
        for bname, p in pl.items():
            internal[bname] = PlacedBlock(bname, x=p.x + x_off, y=p.y, width=p.width, height=p.height)
        x_off += bw + gap
    return FloorplanBlock("_", gw, gh), internal


def pack_group_as_unit(name: str, blocks: list, gap: float = 1.0, target_ratio: float = 1.0,
                        net_weights: dict | None = None, height_tolerance: float = 1.0,
                        sub_kind: dict | None = None):
    """기능적으로 묶여야 하는 block 그룹(예: CMFB의 5개 stack 전부)을 그 그룹 내부에서만
    `skyline_pack_best_width()`로 촘촘히 packing한 뒤, 그 결과를 **하나의 FloorplanBlock으로
    캡슐화**한다 — 상위 packer(`pack_floorplan()`)는 이 그룹을 더는 쪼갤 수 없는 블록 하나로만
    본다.

    **왜 필요한가(실제 사고)**: `pack_floorplan()`에 spine 전체(Stage-1/bias-gen/CMFB 등 서로
    무관한 기능 블록의 모든 물리 행)를 평평한 리스트로 넘기면, skyline packer는 "빈 공간 최소화"
    만 최적화하지 "같은 회로 블록끼리 뭉쳐 있어야 한다"는 건 전혀 모른다 — 실제로 이 회로에서
    `cmfb_n1`(높이 2)이 CMFB의 나머지 4개 행(cmfb_p1/p2/n2, 전부 높이 1)과 떨어져 Stage-1의
    높이-2 블록들 사이에 끼어 들어가는 결과가 나왔다(사용자가 직접 지적: "cmfb_n1은 왜
    어중간하게 중간에 배치돼 있지?"). 이 함수는 좌우 대칭쌍을 하나의 유닛으로 다루는
    `pack_floorplan()`의 원리(§6.7 상단 설명)를 spine 내부의 **기능적 그룹**에도 그대로
    적용한 것 — 대칭 유닛이 "절대 갈라지면 안 되는 쌍"이듯, 기능 그룹도 "절대 갈라지면 안 되는
    묶음"으로 다룬다.

    **`sub_kind`(선택, 2026-07-27 신설)**: `{block_name: kind}` — 같은 물리 diffusion/폴러리티
    에 속하는 row를 표시한다(예: CMFB의 P측 legs vs N측 legs). 주어지면 이 함수는 **두 가지
    packing을 실제로 계산해서 비교한다**: (1) 이 그룹 전체를 하나로 보고 packing(기존 방식),
    (2) `_pack_by_subkind()`로 kind별로 나눠 각각 공통 높이에 맞춰 packing한 뒤 옆으로 붙이는
    방식(사용자 제안: "P영역/N영역을 구분해서 배치하면 더 compact해지지 않을까 — 확인해보라") —
    **둘 중 aspect ratio가 `target_ratio`(정사각형)에 더 가까운 쪽을 채택**한다(어느 쪽이
    더 나은지 가정하지 않고 매번 실측 비교). `sub_kind`를 안 주면 (1)만 계산한다(기존 동작과
    동일).

    **왜 밀도가 아니라 ratio로 고르는가(실제로 발견된 함정)**: 처음엔 "이 그룹만의
    `packing_density`가 더 높은 쪽"을 채택했는데, Stage-1에 실제로 적용해보니 그룹 자체의
    밀도는 같은데도(둘 다 밀도가 그대로거나 오히려 개선됐는데도) 모양이 10x9(거의 정사각형)
    에서 19x4(아주 옆으로 길쭉)로 바뀌었고, 이 길쭉한 그룹 블록이 상위 `pack_floorplan()`에서
    bias-gen/CMFB/Class-AB pair-stack과 결합되자 **전체 회로의 aspect ratio가 1.36→3.10으로
    악화**됐다 — "이 그룹만 보면 더 나은 선택"이 "전체로 보면 더 나쁜 선택"이었다. 그래서
    그룹 하나의 밀도가 아니라, 그 그룹이 **다른 조각과 잘 결합될 모양(정사각형에 가까움)**을
    기준으로 바꿨다.

    반환: `(group_block: FloorplanBlock, internal_placements: {name: PlacedBlock})` —
    `internal_placements`의 좌표는 그룹 내부 상대좌표(그룹의 좌상단이 원점)다. 상위 packing이
    이 그룹 블록의 최종 위치를 정하면, 그 위치를 이 상대좌표에 더해 각 구성 block의 절대좌표를
    복원한다(`pack_floorplan_grouped()`가 이 과정을 자동으로 한다)."""
    if len(blocks) == 1:
        b = blocks[0]
        return (FloorplanBlock(name, b.width, b.height),
                {b.name: PlacedBlock(b.name, 0.0, 0.0, b.width, b.height)})

    flat_placements, flat_w, flat_h = skyline_pack_best_width(
        blocks, gap=gap, target_ratio=target_ratio, connections=net_weights,
        height_tolerance=height_tolerance)
    flat_ratio = max(flat_w, flat_h) / min(flat_w, flat_h) if min(flat_w, flat_h) > 0 else float("inf")

    if sub_kind:
        by_kind_result = _pack_by_subkind(blocks, sub_kind, gap=gap)
        if by_kind_result is not None:
            _, kind_placements = by_kind_result
            kind_w = max(p.x + p.width for p in kind_placements.values())
            kind_h = max(p.y + p.height for p in kind_placements.values())
            kind_ratio = max(kind_w, kind_h) / min(kind_w, kind_h) if min(kind_w, kind_h) > 0 else float("inf")
            # 선택 기준은 "이 그룹만의 밀도"가 아니라 **aspect ratio(정사각형에 얼마나 가까운가)**다
            # -- 실제로 확인된 함정: Stage-1을 P/N으로 나누면 그 그룹 자체의 밀도는 그대로면서도
            # 모양이 10x9(정사각형)에서 19x4(옆으로 아주 길쭉)로 바뀌었다 -- 이 그룹 블록이 다른
            # 그룹/pair-stack과 결합되는 상위 packing에서는 "이 조각 자체가 얼마나 정사각형인가"가
            # "이 조각 내부에 빈틈이 없는가"보다 전체 결과에 더 크게 영향을 준다(실측: 이 기준으로
            # 안 걸렀을 때 전체 회로 aspect ratio가 1.36→3.10으로 악화됐었다). 그래서 밀도가 아니라
            # ratio로 고른다 — "이 그룹만 보면 더 나은 선택"이 "전체로 보면 더 나쁜 선택"일 수 있다는
            # 걸 발견한 뒤 반영한 기준이다.
            if abs(kind_ratio - target_ratio) < abs(flat_ratio - target_ratio):
                return FloorplanBlock(name, kind_w, kind_h), kind_placements

    return FloorplanBlock(name, flat_w, flat_h), flat_placements


def pack_floorplan_grouped(spine_groups: dict, mirror_pairs: list, gap: float = 1.0,
                           height_steps: int = 40, transistor_sequences: dict | None = None,
                           net_weights: dict | None = None, height_tolerance: float = 1.0,
                           width_tolerance: float = 2.0, sub_kinds: dict | None = None) -> FloorplanResult:
    """`pack_floorplan()`과 같은 일을 하지만, spine을 평평한 리스트가 아니라
    **`{group_name: [FloorplanBlock, ...]}`로 미리 기능별로 묶어서** 받는다 — 각 그룹은
    `pack_group_as_unit()`으로 먼저 내부 packing된 뒤 하나의 블록으로 상위 packing에 들어가므로,
    같은 그룹의 block들이 서로 갈라져 무관한 다른 블록 사이에 끼어 들어가는 일이 구조적으로
    불가능하다. 대칭쌍(`mirror_pairs`) 처리는 `pack_floorplan()`과 동일 — 그룹화는 spine에만
    적용된다(mirror_pairs는 이미 그 자체로 "갈라지면 안 되는 쌍" 처리가 돼 있다).

    반환된 `FloorplanResult.placements`는 그룹 이름이 아니라 **원래의 개별 block 이름**으로
    키가 채워진다(그룹은 packing 중간 단계의 내부 표현일 뿐, 최종 결과에는 노출되지 않는다).

    **트레이드오프**: 그룹 단위로 묶었으므로 `pack_floorplan()`이 평평한 리스트로 할 수 있었던
    "그룹 경계를 넘나드는 미세한 빈틈 채우기"는 못 한다 — packing_density가 약간 낮아질 수
    있다. 이건 의도된 것이다: 회로 구조(어떤 block들이 기능적으로 묶여야 하는지)를 지키는 것이
    빈 공간을 1~2칸 더 줄이는 것보다 우선이다.

    `net_weights`(선택, `{group_or_pair_name: {other_name: weight}}`): `pack_floorplan()`과
    같은 개념이지만 키는 **그룹 이름**(spine_groups의 key, 예: "biasgen") 또는 **mirror_pairs의
    오른쪽 소자 이름**(예: "classab_p2") 기준이다 — 개별 물리 행 이름이 아니다(그룹으로
    묶였으므로 그룹 단위로만 위치를 조정할 수 있다).

    `sub_kinds`(선택, `{group_name: {block_name: kind}}`, 2026-07-27 신설): 특정 그룹 안의
    row를 같은 물리 diffusion/폴러리티 기준으로 나눠(예: CMFB의 P측 legs vs N측 legs), 그
    구분을 지킨 배치와 안 지킨 배치 중 실제로 더 촘촘한 쪽을 채택한다 — `pack_group_as_unit()`
    의 `sub_kind` 파라미터 참고. 이 그룹화는 spine_groups의 기능 그룹화(반드시 지켜야 하는
    제약)와 다르다 — polarity 구분은 **더 나은 결과를 낼 때만 채택되는 후보**다."""
    group_blocks, group_internal = [], {}
    for gname, blocks in spine_groups.items():
        gblock, internal = pack_group_as_unit(gname, blocks, gap=gap,
                                               sub_kind=(sub_kinds or {}).get(gname))
        group_blocks.append(gblock)
        group_internal[gname] = internal

    result = pack_floorplan(group_blocks, mirror_pairs, gap=gap, height_steps=height_steps,
                             transistor_sequences=transistor_sequences,
                             net_weights=net_weights, height_tolerance=height_tolerance,
                             width_tolerance=width_tolerance)

    final_placements = {}
    for name, p in result.placements.items():
        if name in group_internal:
            for bname, bp in group_internal[name].items():
                final_placements[bname] = PlacedBlock(bname, x=p.x + bp.x, y=p.y + bp.y,
                                                        width=bp.width, height=bp.height)
        else:
            final_placements[name] = p
    result.placements = final_placements
    return result
