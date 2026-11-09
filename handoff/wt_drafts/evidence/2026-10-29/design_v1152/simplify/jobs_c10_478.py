# 2차 단순화 커밋 -- 41 §4.7-8 (9)(4.7-V로 대상 소멸한 커널 A6 판정 tol 변경 항목) → design 이력
D41 = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md"
T = open(D41, encoding="utf-8").read()
a = "(9) **커널 A6 판정 tol을 매 측정 해에서 잼**"
i = T.index(a)
j = T.index("(9′) **지원 밖 원소 정지의 실패 블록 이름**", i)
JOBS = [dict(id="H41-20", file="41", title="§4.7-8 (9) 커널 A6 판정 tol 변경 항목(4.7-V로 대상 소멸)", mode="sub",
             old=T[i:j], new="(9) (대상 소멸 -- 커널 A6 되풀이 삭제, 4.7-V 2행; 옛 항목 = design 이력 H41-20) ")]
