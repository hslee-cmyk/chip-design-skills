
## hunk  -1434,3 +1434,3   (old 1373 B, new 742 B)
  DEL: 선언식(36.6 MHz)
  ADD: 선언식
  DEL: 응답(30.50
  ADD: 응답
  DEL: MHz)
  ADD: 크로스오버
  DEL: 차이다.
  ADD: 차이다(옛 수치 = design 이력 H40-19).
  DEL: 옛
  ADD: (옛
  DEL: 문언:
  ADD: 문언
  DEL: spec
  ADD: =
  DEL: `search_method`가
  ADD: design
  DEL: 정밀
  ADD: 이력
  DEL: 경로(내층 DP·중층 좌표강하)를 선언하면 탐색 전에 `unsupported_rule_branch`(사유 `precise_path_not_implemented`)로 정지한다. 정밀 경로는 기본 꺼짐이고(DEC-73) 구현이 없는 분기를 타면 정지한다(DEC-76 안전망).
  ADD: H40-20.)
  DEL: 문언:
  ADD: 문언(U-51
  DEL: 사용자
  ADD: 계수
  DEL: 결정
  ADD: 기반
  DEL: 2026-10-12 "U-51은 (나)로": 보상 단 gm/ID는 θ에 포함한다(DEC-04). 폴백은 **계수 기반**이다: 외층 SLSQP가 그 시작점의 반복 상한(as-built `slsqp_outer` 식 maxiter
  ADD: 폴백)
  DEL: Σ_i
  ADD: design
  DEL: max(⌈log2(상자폭_i
  ADD: 이력
  DEL: / FD 스텝_i)⌉, 1), `E/search/slsqp_outer.py:179-181`) 안에 수렴하지 못하면 그 시작점에서만 보상 단 θ를 GB5 규칙값(gm_req = DEC-92 MNA 1-D 근, §3.5)으로 고정해 한 번 다시 푼다. 폴백 사실과 이유(`compensation_fixed_fallback{start, reason: slsqp_maxiter}`)를 기록하고 그 점을 '추정'으로 표시한다. 벽시계·U-47 예산에 의존하지 않는다(결정론). 9회로 실행에서 폴백 빈도를 재서 보고한다. 기록은 결과 JSON front 점의 `fallbacks[]`와 `perf.compensation_fixed_fallback` 계수
  ADD: H40-21

## hunk  -1440 +1440   (old 518 B, new 197 B)
  DEL: 문언: 기본 비활성. spec `optional_stages`(DEC-75)에 bisection 대상 제약 metric 목록을 선언하면 켜진다. 진입점은 `achievable_metric_bound(mode="bisect")`이고 `run_gmid_design_pipeline` 위의 도구가 부른다(MOD10, 패키지 순서상 pipeline 위). 결과는 선언의 `value`와 `_derived{지문, 스텝 이력, 시각}`으로 기록한다. 42 DEC-22 행은 N/A가 아니라 MISS(기본 비활성,
  ADD: 문언(`optional_stages`
  DEL: 경로
  ADD: 키)
  DEL: 설계됨)다.
  ADD: =
  DEL: 키는
  ADD: design
  DEL: `optional_stages.bisection.metrics:
  ADD: 이력
  DEL: [...]`다(DEC-68 명명, §3.10.9 PN4 결정)
  ADD: H40-22.

## hunk  -1808 +1808   (old 91 B, new 87 B)
  DEL: 정본이다.
  ADD: 정본이다(R별
  DEL: 표의
  ADD: 원
  DEL: '상태'
  ADD: 표
  DEL: 열은
  ADD: =
  DEL: 결정
  ADD: design
  DEL: 이전
  ADD: 이력
  DEL: 상태를 남겨 둔 것이다.
  ADD: H40-17).

## hunk  -1818,35 +1818,37   (old 5963 B, new 3569 B)
  DEL: 출처
  ADD: 처리(결정
  DEL: |
  ADD: 뒤
  DEL: 계획 근거 | 상태 |
  ADD: --
  ADD: 열)
  DEL: |---|---|---|---|---|---|
  ADD: |---|---|---|
  DEL: R §4 D18, R §0.2, `search/CONTRACT.md:26-31` | FR-4, DEC-03·71·73·77 | **사용자가 철회(2026-10-08)** |
  DEL: | R §0.2 행 32, D18 | GB3, DEC-71 (7) | 미결
  DEL: | R §0.2 행 33, K6. 계획 N6.1 단위 7('GB4 축소')에도 반영됨 | FR-8, GB4, IC6 | **복원**(Q1, 41 §4.5)
  DEL: P N7.2 U-49 | FR-4와 긴장 | 미결(계획서 안의 대기 결정) |
  DEL: `metrics/CONTRACT.md:13-14`, 초안 M15:191, L7a:261 | FR-2, DEC-05·66, N3.8 | 미결 |
  DEL: 초안 U25:196·201·133, R N5~N7 미착수 | FR-1, GB2, DEC-43·57·59·63·65·81 | 미결 |
  DEL: graph CONTRACT | DEC-59 | 미결 |
  DEL: | `find_front.py:45-48` | DEC-92 (1)(2) | 미결
  DEL: `metrics/CONTRACT.md:14` | DEC-58·65·96·104, N3.8 | 미결 |
  DEL: | `SPEC_CONTRACT.md:226-228`, R D5('N3.15 축소') | GB0, DEC-03, DEC-58 | 미결
  DEL: `search/CONTRACT.md:535-537,591` | DEC-77, U-13, N3.5 | 미결 |
  DEL: | `layout/CONTRACT.md` 4.14, `search` S-14 | DEC-79 (b), DEC-84, LY3·LY7, 사용자 12번 (나) | 계획은 범위 안
  DEL: | `graph/CONTRACT.md:220` | DEC-17, LR1 | 미결
  DEL: `sizing/CONTRACT.md:276,741,766` | DEC-70, DEC-95, N3.6 | 미결 |
  DEL: `graph/CONTRACT.md:491,538`, JU4:131 | SP1-1 (4), DEC-93 (1) | 미결 |
  DEL: | `search/CONTRACT.md` 3.23 (4) | 사용자 2026-10-08 대칭 결정 | 미결
  DEL: | core 조사 | DEC-96 (2), N3.16 | 선행 조건
  DEL: `[ng-oracle-early]` 계약 L42-54 | 사용자 결정 2026-10-08 4번 | 사용자 결정과 모순 |
  DEL: | `[ng-cmfb-pm]` README, `tools/spice_oracle/README.md:516` | 사용자 결정 A(엔진 탐색 규칙), P N3.6 오라클 합격 정의 | 미결
  DEL: `E/layout/floorplan.py:83` | DEC-79, DEC-95 (2) | 미결 |
  DEL: | `layout/CONTRACT.md:217,306-311` | LY5 마지막 문장 | 미결
  DEL: `E/layout/_ly_fields.py` | DEC-89 (5), DEC-91 (2), DEC-79 | 미결 |
  DEL: | `metrics/CONTRACT.md:246,424` | DEC-72, DEC-90 (3), N3.8 | 미결
  DEL: | `E/search/objectives.py:9`, `metrics/CONTRACT.md:544,627` | DEC-78, U-10 | 정의 차이
  DEL: | `lut/CONTRACT.md` 1.4, 4.0.1, 4.2 | DEC-87, DEC-88, LR3 | 미결
  DEL: `E/tests/` | N3.11, N6.2 T9, IC1~IC11 | 미결 |
  DEL: | 초안 SF:209, M15:43 | DEC-90 (2), DEC-96 (3) | 슬루 '기록만'(Q5 (ii))은 대체 -- 슬루 = oracle `.tran` 판정(합격 T5 안, 전 폭 계단 출력의 20 %~80 % 구간 기울기; P DEC-90 (2)·T5, O-121 B-2·O-122 -- **원래 취지와 다름(승인 O-122)**; FAIL 뒤 처리 = U-112 닫힘 -- front 제외·기록, 되먹임 없음, O-143 (4)·O-144; 추종 검사 O-144). 정착 '기록만'은 v1.15.0에서 대체 -- 정착은 oracle `.tran` 판정 spec이다(`settle_s`·static settling error, 계획 N3.8 '정착 측정 정의', 사용자 결정 O-132·O-133·O-145; current_reuse는 AP-1까지 판정 대기). **잡음은 사용자 결정 2026-10-08로 범위 안이 됨**("노이즈 spec을 추가해서 코드를 만들어야지.")
  DEL: 초안 M6:299 | DEC-73·75 | **계획 승인됨**(기본 비활성) |
  DEL: | 41 §5.3 | DEC-71 (3), LR5 | 사용자 확인 필요
  DEL: 41 §6.5, §3.5 | U-12, U-50, DEC-85 | U-12 미확정 |
  DEL: | 41 §1.8 | U-24, 사용자 2026-10-08 CM 결정 | 사용자 확인 필요
  DEL: 41 §5.1 | DEC-71 (3), DEC-85 | 사용자 결정 |
  DEL: §4-2·3 | 사용자 결정 4번 | 사용자 결정이 근거 |
  ADD: (출처·계획 근거·결정 전 상태 열 = design 이력 H40-17.)

## hunk  -1862 +1862   (old 209 B, new 114 B)
  DEL: 근거(2026-10-08
  ADD: 근거(r1
  DEL: r1
  ADD: 실측
  DEL: 실측):
  ADD: --
  DEL: L
  ADD: 피드스루 조건만 쓰면 긴 L·약반전 칸에서 B를 크게 낮게 읽음)
  DEL: 20
  ADD: design
  DEL: µm·약반전(gm/ID
  ADD: 이력
  DEL: 25)에서 입력 환산 잡음이 피드스루 식의 예측보다 훨씬 낮은 주파수에서 1차 저역 통과로 떨어진다. (1)만 쓰면 B를 86 % 낮게 읽고, (2)를 더하면 6 % 낮게 읽는다(1e5 Hz 점).
  ADD: H41-19.
  DEL: 규칙이다(설계와 구현 일치).
  ADD: 규칙이다.
