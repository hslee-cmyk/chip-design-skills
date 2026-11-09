"""design v1.15.2 단순화(사용자 2026-10-29 '같은 기준으로 과도하게 복잡한 부분 고쳐' -- gm/ID 손계산 우선) 적용 스크립트.
줄 머리(prefix)로 고른 줄(또는 줄 구간)을 새 문장으로 바꾸고, 바뀐 원문을 moved_text.md에 그대로 보존한다(design 문서 쪽은 위치 참조).
한 번만 실행(바뀐 뒤에는 prefix가 없어 실패 -- fail-closed). CRLF 유지."""
import os

D = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing."
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moved_text.md")
EV = "wt/_drafts/evidence/2026-10-29/design_v1152/"
REF = "`" + EV + "simplify/moved_text.md`"

JOBS = [
 # (id, file, start prefix, end prefix (exclusive) or None = one line, new text)
 ("S1", "40-engine.design.md", "**S 셀 집합과 일반형 판정**(v1.15.2", "**보상 수동소자 후보 집합**",
  "**S 셀 집합**(DEC-92 (3) 그대로 -- 손계산 꼴; v1.15.2 단순화): 보상 R과 보상 C가 이어진 경로(R의 한 끝 넷에 R과 보상 C만 닿는 직렬 가지; T 망이면 C마다 경로 하나)마다 그 경로 두 끝에 gate·drain이 걸린 MOS의 합집합이고, 비면 S 미정(fail-closed -- DEC-105 (10) (d)). 출발값 R_S = 1/Σ_{c∈S} gm_c은 교과서·원문의 손계산 꼴(2단 nulling resistor R_z = 1/gm -- 교과서 로컬 PDF 없음·쪽 미확인; nmcnr 원문 Leung 1999 p.2 Structure 4 'R_m = 1/g_m3' -- `assets/library/sources/nmcnr_amplifier__leung_1999/source.pdf`)이다. 다른 구조(결합 경로·T 망 등)에서 영점을 정확히 지우는 R과의 차는 출발점 품질에만 들고, R은 θ로 탐색되며 PM·영점은 봉인 `ss` MNA가 판정한다(DEC-74; 남는 차는 DEC-72 model_error 기록). 'AC로 같은 출력 노드를 구동하는 소자'(class-AB 부유 전류원 출력단)를 S에 넣는 안은 기각한다(그 안의 R은 우반면 영점을 남김 -- 절점식 근거·실측 `" + EV + "class_ab_s/`). 구조 조건(결합 용량 경로)의 처리와 계획 '한계' 문언은 **계획 v6.38.4 대기(P2)**. 9회로 S: two_stage {M6}, current_reuse {M16}·{M26}, nmcnr {M301}, 나머지 6회로 R–C 경로 0(판독 `wt/_drafts/evidence/2026-10-28/s_def_connectivity.txt`). 옛 판의 절점식·162점 훑기·적용표·측정 한계 서술 = " + REF + " S1.\n"),
 ("S2", "40-engine.design.md", "  - (b) **영점 상쇄 보상 저항**(구조 규칙 셀 집합 S가 정의되는 저항", None,
  "  - (b) **영점 상쇄 보상 저항**(S가 정의되는 저항 -- §3.5) -- 물리 결정자: R은 영점 위치를 고르는 설계 변수. 상자 = 출발값 식의 θ 상자 위 구간 [1/max Σ_{c∈S} gm_c, 1/min Σ_{c∈S} gm_c](셀 gm 범위 = LUT gm/ID 정의역 × 그 kind 전류 상자 `current_box` -- 탐색 상자와 같은 LUT·PDK 출처); 계산 = 순수 함수 `zero_cancel_box(lut, S, kinds, current_boxes)` 하나(자리 `E/sizing/theta_schema.py` -- θ 스키마가 부름, 재작성 범위 card SF-1 범위 9). U-134 (가) 성립 실측·상자 폭(상한 = 꺼진 소자 gm의 포락, 실효 상한 = 면적 제약과 MNA 판정)은 계획 U-134 행과 `wt/_drafts/evidence/2026-10-28/u134_measure/`(옛 상세 문장 = " + REF + " S2)."),
 ("S3", "40-engine.design.md", "**측정 부하가 중간 rail에 걸린 회로의 DUT 전력**", None,
  "**측정 부하가 중간 rail에 걸린 회로의 DUT 전력** -- **계획 v6.38.4 대기(P7)**: 정의 선택은 계획이 정한다(후보 = 레일 단자 합(기준 0 V) / DUT 소산(모든 단자); 물리 사실·toy 수치 = `" + EV + "m1_power/README.md`, 옛 상세 = " + REF + " S3). 엔진 `power_dc_w`·oracle OP-11의 자리는 결정 뒤 이 문단에서 정한다. library 발동 = nmcnr 1."),
 ("S4", "40-engine.design.md", "측정 = 엔진 밖 사실 측정(DEC-104 (1′) (b)): integ/it12 `d759838a`", "- 판단(문턱 상수 없음) = 사용자 승인 질문 Q-DC1",
  "측정 = 엔진 밖 사실 측정(DEC-104 (1′) (b), 판정 기록 아님 -- v1.15.2 단순화: 표·측정 서술은 evidence로): FD 단계 노드 풀이 reuse·벽시계·θ 전류 열 비율·유도 손실 표 = `" + EV + "dcblock_measure/`(재현 명령·한계 포함), Rʳ·소자 안 고정점 회차 = `" + EV + "m4_measure/README.md`, 옛 본문 = " + REF + " S4. 판단에 쓰는 요지(손계산 속도 P4 재료일 뿐 정밀 요구가 아님): (i) 합친 블록의 유도 손실 = 실행 벽시계의 0~4 %(6회로, 상계), 야코비안이 도는 current_reuse는 1회당 약 7 s (ii) Rʳ = ∅ 9/9 -- 노드 풀이는 평가마다 1회 (iii) 소자 안 고정점은 측정된 회로에서 대부분 1~2회차이고, 봉인점에서 `slice_cycle`·`finger_below_min`이 생기는 경우의 처리는 **계획 v6.38.4 대기(P5·P8)**. 정밀값은 card WB-1 완료 조건 (5)가 구현 뒤 다시 잰다.\n"),
 ("S5", "40-engine.design.md", "**12. 완료 조건 대응**:", None,
  "**12. 완료 조건 대응**: 계획 card WB-1 완료 조건 (1)~(7)이 정본이다(이 절은 그 toy가 볼 블록 꼴만 정한다). 이 design이 정한 이름 -- `dc_solve`·`dc_finger`·`FingerGeom`·`FingerSlice`·`finger_slice`·`slice_of_finger`·`reachable_slices`·`slice_cycle`·`slice_missing`·`finger_below_min`·`RealizedGeometry.layout_ref`·`dc_scc_log.slice_rounds` -- 은 착수 때 test glob·이름 충돌 grep(42 D-WB 행). toy 자리 = 41 §9. toy 목록 정정 후보는 41 §5.12.7(**계획 v6.38.4 대기(P3)**; 옛 문단 = " + REF + " S5)."),
 ("S6", "41-gain-budget.design.md", "| Q-DC1 |", None,
  "| Q-DC1 | DC 블록 하나(40 §3.7-A)의 손계산 속도 손실을 받아들이나 | 받아들임 -- 계획 DEC-105 (2)가 블록 하나를 고정했다(물리 결정자: W = I·L/IDu라 DC 블록이 전류 열을 READS → θ 전류 FD 열마다 노드 풀이 재계산). 판단 재료 요지 = 40 §3.7-A 9(유도 손실 벽시계 0~4 %, Rʳ = ∅ 9/9라 노드 재풀이 0; 측정 원자료 evidence). 손실이 크다고 판단되면 계획 개정 대상이지 design이 블록을 나누지 않는다 | 판단 재료 충분 -- 사용자 판단 | 계획 개정으로 블록 분할 재검토(R1-b) |"),
 ("S7", "41-gain-budget.design.md", "| Q-PW1 |", None,
  "| Q-PW1 | (계획 승인 질문으로 옮김) DUT 전력 정의 | **계획 v6.38.4 대기(P7)** -- 재료 = 40 §3.1-1 'DUT 전력' 참조 | -- | -- |"),
 ("S8", "41-gain-budget.design.md", "**고지(질문 아님", "**계획 정정 후보 →",
  "**고지(질문 아님)**: (1) W < W_min 점(m = 1에서 격자 반올림 w_f < W_min)은 `finger_below_min` 봉인 실패(40 §3.7-A 5 -- 계획 DEC-105 (2) 'w_f ≥ W_min'): 물리 결정자 = 제조 규칙(difftap.2) 밖 손가락은 PDK·LUT가 정의하지 않음. (2) class-AB S: 'AC 구동 소자 포함' 안 기각, S = 연결 정의(손계산 꼴) -- 40 §3.5; 구조 조건은 **계획 v6.38.4 대기(P2)**.\n\n"
  "**옛 판 질문**: Q-DC2 → 고지 (1), Q-DC4·Q-GL1 → 삭제(O-166·O-170 승인으로 해당 없음). **원래 취지와 다름**(이 판이 새로 만든 것): 없음. v1.15.1 목록·처리 경위 = " + REF + " S8.\n\n"),
]


def run():
    moved = ["# design v1.15.2 단순화로 옮긴 원문(2026-10-29)\n\n원문 그대로 보존 -- design 쪽은 각 자리에 이 파일의 ID로 참조. 근거: 사용자 2026-10-29 '같은 기준으로 과도하게 복잡한 부분 고쳐'(gm/ID 손계산 우선, 오차는 DEC-72 기록, 최종 확정은 SPICE), 분류표 `classification.md`.\n"]
    cache = {}
    for jid, f, start, end, new in JOBS:
        p = D + f
        if p not in cache:
            raw = open(p, "rb").read().decode("utf-8")
            cache[p] = raw.split("\r\n")
        lines = cache[p]
        si = [i for i, l in enumerate(lines) if l.startswith(start)]
        assert len(si) == 1, (jid, len(si))
        si = si[0]
        if end is None:
            ei = si + 1
        else:
            ei = next(i for i in range(si + 1, len(lines)) if lines[i].startswith(end))
        old = lines[si:ei]
        moved.append("\n## %s -- %s 줄 %d~%d(앞 작업 적용 뒤 줄 번호, 원 판 = design/v115 HEAD 285ec820)\n\n" % (jid, f, si + 1, ei) + "\n".join(old) + "\n")
        newlines = new.rstrip("\n").split("\n")
        if new.endswith("\n"):
            newlines.append("")
        lines[si:ei] = newlines
    for p, lines in cache.items():
        open(p, "wb").write("\r\n".join(lines).encode("utf-8"))
    open(OUT, "w", encoding="utf-8", newline="\n").write("".join(moved))
    print("done", len(JOBS))


run()
