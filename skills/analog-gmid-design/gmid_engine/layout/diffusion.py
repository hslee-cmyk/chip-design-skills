"""MOD7 확산 기하 `ly.diffusion` -- Euler 행의 공유 확산 통계 (계획 LY8, DEC-89 (5)·DEC-91 (2), U12 D-LY3).

진입점: `diffusion_geometry(rows, devices, pdk) -> tuple[DeviceDiffusion]`(소자 이름순).

`rows` = 최종 `RowLayout` 들(접기·재구성 뒤), `devices` = {이름: `source`·`drain` 속성 객체}, `pdk` = `LayoutPdk`.
행의 diffusion 섬(`segments`, 없으면 행 전체가 한 섬)마다 finger k 개와 확산 영역 k+1 개가 있다(영역 j = node_sequence[j],
finger i 는 영역 i 와 i+1 사이). 영역 길이 D = `pdk.finger_pitch_overhead_m`(행 폭 식 sum nf x (L + D) 가 finger 마다 접촉 확산 하나를
세는 바로 그 PDK 양 -- 새 상수 없음), 폭 = finger_w.
* 공유 영역(양쪽이 finger): finger 마다 절반. 면적 W·D/2, 둘레 D(위·아래 STI 변 2D 의 절반) + 자기 게이트 쪽 변 W.
* 섬 끝 영역(한쪽만 finger): 그 finger 가 전부. 면적 W·D, 둘레 2D(STI) + 자기 게이트 변 W + 반대쪽 끝 변 W.
  끝 변은 행 끝 dummy(floorplan 이 양끝에 넣는다)·섬 사이 break 의 게이트 변이다. dummy 는 넷리스트에 없으므로 그 변의 접합은
  끝 영역과 함께 finger 에 합산한다(면적을 전부 주는 것과 같은 집계).
* BSIM4 perMod=1 둘레 규약: PD·PS 는 게이트 쪽 변을 포함한 둘레다(접합 용량이 `PD − Weffcj` 를 STI 측벽으로 쓴다,
  `metrics.junction_cap`).
finger 의 어느 쪽이 drain 인지는 그 finger 의 소자 (source, drain) 와 node_sequence 로 정한다(영역 i 의 넷 == source 이면 영역 i 가 source 쪽,
소자 source == drain 이면 왼쪽을 source 로 센다). 소자 값 = 모든 행·finger 합 / n_fingers(finger 평균 -- `DiffusionGeometry` 와 오라클
`devices[].diffusion` 이 finger 하나 기준이고 `m` = n_fingers).
"""
from .contract_output import DeviceDiffusion


class _Sum:
    """소자 하나의 finger 합(finger_w, finger 수, 영역 면적·둘레 합)."""

    def __init__(self, width):
        self.width = width
        self.fingers = 0
        self.area = {"drain": 0.0, "source": 0.0}
        self.perimeter = {"drain": 0.0, "source": 0.0}


def _island_sides(sequence, nodes, devices):
    """섬 하나의 (finger 이름, source 쪽 영역 인덱스, drain 쪽 영역 인덱스) 열."""
    out = []
    for i, name in enumerate(sequence):
        source = devices[name].source
        left_is_source = nodes[i] == source or nodes[i + 1] != source
        out.append((name, i if left_is_source else i + 1, i + 1 if left_is_source else i))
    return out


def _region_terms(width, length, shared):
    """영역 하나에서 finger 하나가 받는 (면적, 둘레). 영역에 닿는 finger 수로 나눈다(공유 = 둘, 섬 끝 = 하나)."""
    share = 1 / (1 + int(shared))
    sti_edges = (length, length)
    far_edge = 0.0 if shared else width
    return width * length * share, width + sum(sti_edges) * share + far_edge


def diffusion_geometry(rows, devices, pdk):
    length = pdk.finger_pitch_overhead_m
    totals = {}
    for row in sorted(rows, key=lambda r: r.row_id):
        islands = row.segments if row.segments else ((row.transistor_sequence, row.node_sequence),)
        for sequence, nodes in islands:
            last = len(sequence)
            for name, source_region, drain_region in _island_sides(sequence, nodes, devices):
                acc = totals.setdefault(name, _Sum(row.finger_w_m))
                acc.fingers += 1
                for side, region in (("source", source_region), ("drain", drain_region)):
                    area, perimeter = _region_terms(row.finger_w_m, length, 0 < region < last)
                    acc.area[side] += area
                    acc.perimeter[side] += perimeter
    return tuple(DeviceDiffusion(name, a.width, a.fingers, a.area["drain"] / a.fingers, a.area["source"] / a.fingers,
                                 a.perimeter["drain"] / a.fingers, a.perimeter["source"] / a.fingers)
                 for name, a in sorted(totals.items()))
