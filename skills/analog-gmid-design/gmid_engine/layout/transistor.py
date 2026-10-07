"""MOD7 레이아웃 입력 소자 레코드 `Transistor` -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Transistor:
    """stick diagram 계산에 필요한 최소 정보만 담는다 — bulk net, VT, 공정 파라미터는 이 모듈의
    관심사가 아니다(source/drain 연결성과 finger 수만 Euler 그래프에 영향을 준다). `gate`는
    Euler 분석 자체에는 쓰이지 않지만 §2.6 `find_matching_candidates()`가 matching 그룹
    (전류거울=gate 공유, 차동쌍=source 공유+gate 상이)을 구조적으로 찾아내는 데 필요하다."""

    name: str
    kind: str                      # 'nmos' | 'pmos' — 극성이 다르면 같은 diffusion을 공유 못 함
    source: str                    # source net 이름
    drain: str                     # drain net 이름
    n_fingers: int = 1              # finger 개수(짝/홀이 §2 stick 규칙의 핵심 변수)
    finger_w: float | None = None   # finger 1개당 W(같은 stack인지 판정 + §3.5 divisibility 검사에 사용)
    w: float | None = None          # 소자 전체 W(gm/ID sizing 결과값). finger_w와 함께 주면
                                     # §3.5 check_finger_width_compatibility()가 W/finger_w의
                                     # 정수 여부를 검사한다 — n_fingers 자체는 여전히 호출자가
                                     # 직접 정해서 넣는다(이 필드는 검증용이지 자동 계산용이 아니다).
    l: float | None = None          # channel length(m, gm/ID sizing 결과값 -- sizing_recipe.py의
                                     # sizing[name]["L"]에서 옴). finger_w/w와 동일한 선택적 필드
                                     # 패턴: 있으면 compute_row_geometry()가 실제 물리 폭 계산에
                                     # 쓰고, 없으면 그 소자는 근사 계산에서 빠진다(approx 플래그로
                                     # 명시, 조용히 대체하지 않음). 이 필드는 gm/ID 지식을 요구하지
                                     # 않는 순수 치수값이라 이 모듈의 "gm/ID를 모르는 순수 그래프
                                     # 모듈" 경계(위 모듈 docstring 20-24행)를 깨지 않는다.
    gate: str | None = None          # gate net 이름(선택) — §2.6 matching 그룹 자동 탐지에만 사용
    stack_id: str | None = None     # 명시적 stack 배정(지정 시 극성/폭 자동 그룹핑보다 우선)

    def __post_init__(self):
        if self.n_fingers < 1:
            raise ValueError(f"{self.name}: n_fingers는 1 이상이어야 한다")
        if self.kind not in ("nmos", "pmos"):
            raise ValueError(f"{self.name}: kind는 'nmos' 또는 'pmos'만 허용")
