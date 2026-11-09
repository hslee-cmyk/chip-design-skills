# 2차 단순화 커밋 3 -- 머리 판 이력(40 줄 12~77, 41 줄 17~43) → design 이력
H = "design 이력 "
JOBS = [
 dict(id="H40-01", file="40", title="머리 Status와 판 이력 v1.15.2~v1.4(원문 줄 12~77)", mode="lines",
      start="> **Date**: 2026-10-29 · **Status**", end="> **Planning Doc**",
      new="> **Date**: 2026-10-29 · **Status**: **design v1.15.2 -- 계획 v6.38.3(승인 O-170·O-172) 맞춤, 검증 대기**(브랜치 design/v115, base master `07181524`; 40·41·42 같은 판). 계획 v6.38.4 P1~P8 자리는 '계획 v6.38.4 대기' 표지만 둔다; 승인 질문 = 41 §5.12.7. 판 이력(v1.15.2~v1.4 커밋별 경위·승인 기록) = " + H + "H40-01(`gain-budget-gmid-sizing.design.history.md` -- 이 문서들에서 옮긴 경위·옛 문언 전부의 자리).\n>"),
 dict(id="H41-16", file="41", title="머리 Status와 판 이력 v1.15.2~v1.4(원문 줄 17~43)", mode="lines",
      start="> **Date**: 2026-10-29 · **Status**", end="> 색인과 표기는",
      new="> **Date**: 2026-10-29 · **Status**: **design v1.15.2 -- 계획 v6.38.3(승인 O-170·O-172) 맞춤, 검증 대기**(40·42와 같은 판 -- 40 Status). 승인 질문 = §5.12.7. 판 이력(v1.15.2~v1.4) = " + H + "H41-16(`gain-budget-gmid-sizing.design.history.md`).\n>"),
 dict(id="H41-17", file="41", title="as-built 요약의 삭제된 '최소형 층 0' 행", mode="lines",
      start="- ~~최소형 층 0: `E/search/layer0_center.py`", end=None, new=""),
]
