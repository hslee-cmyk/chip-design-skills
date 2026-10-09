"""레이아웃 후보 비교 점수 -- 커널 슬라이스 키 선택에 쓴다 (계획 N3.17 LY5·LY7, 설계 40 §3.9 U14).

진입점: `layout_score(layout, unplaced) -> tuple`.

작을수록 좋은 사전식 점수 (평가 커널 호출 0):
1. 놓지 못한 소자 수(`unplaced`),
2. 배치되지 못한 common-centroid 요구 그룹 수(`CC_REQUIRED_ROLES`, 패턴 없음, W_request 응답 대기도 아님),
3. W_request 응답 대기 그룹 수(W 를 바꿔야 서는 그룹 -- 재평가가 더 든다),
4. 판정 축 외곽 면적(m², 수동소자 블록 포함).
이름·회로 무관, 새 상수 없음.
"""
from gmid_engine.layout import CC_REQUIRED_ROLES


def layout_score(layout, unplaced):
    groups = layout.groups
    return (len(unplaced), sum(1 for g in groups if g.role in CC_REQUIRED_ROLES and g.pattern is None and not g.pending),
            sum(1 for g in groups if g.pending), layout.floorplan.outline_area_m2)
