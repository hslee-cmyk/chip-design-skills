# 세션 인계 2026-10-16 (세션 63c6146a)

다음 세션은 이 파일부터 읽는다. 결정 원문은 `wt/_drafts/user_decisions.md`(이 세션 결정: C-1~C-3, G-1·G-2, L-1~L-3, O-6~O-12, P-1, H-A·H-B, X-22). 백로그는 `wt/_drafts/engine/U17_FOLLOWUPS.md` 끝.

## master
- HEAD `5fea301` (push 안 함). 이 세션 병합: oracle 계획 v0.6.2→v0.6.6, OP-0 design v0.2.6, headroom-chain 계획 v0.6, gain-budget 계획 v6.13·v6.14·v6.15(LT-1 card, HC-D 상위 문언, X-D5 절차), topo/cr-intent(Sooch·Sanchez 원문 보관, current_reuse `_design_intent`, references/circuit-pattern-intents.md P-1), catalog C-3, agents 정의(계산식 전 graph 정본 확인).

## 세션 끝날 때 아직 돌던 agent (결과는 각 worktree·파일에 남음 -- 다음 세션에서 확인)
| 작업 | 위치 | 다음 할 일 |
|---|---|---|
| card B(XRUN-F1 B) test 수정 라운드: 미재작성 96건, B-T1 기대값 오류, 규칙 M-c 강화, README M-d 되돌림(X-22), 전체 suite 자체 확인 | `wt/xrunf1b-test` 브랜치 role/test/xrunf1b (base 083b103) | 끝났으면 `git -C wt/xrunf1b-test log role/test/xrunf1b` 확인 |
| card B code 수정 | `wt/xrunf1b-code` role/code/xrunf1b, 커밋 `0952331`(seal_dc attach_partial, computed_blocks 출력 전용) | 완료 |
| card B data | `wt/xrunf1b-data` role/data/xrunf1b `65549c9` (crto·nmcnr structure.json rule_hash → adc91fc8…, X-22 승인) | 완료 |
| OP-1a 기준선 보관(auditor) | `wt/op1a-audit` role/audit/op1a(base 5fea301), 임시 `wt/_scratch_op1a/` | 판정 기록 id·DV-5 비트 동일 결과 확인 후 master 병합 |
| OP-2 spec·interface card 초안 | `wt/_drafts/oracle/OP2_SPEC_CARD.md`·`OP2_INTERFACE_CARD.md` | 독립 검증 → freeze → test·code 작성자 |
| graph-consumption 계획 v0.1 독립 검증 | 계획 `wt/graph-consumption-plan` plan/graph-consumption `93e1dbc` | 검증 반영 → 사용자 결정 U-G1~U-G8 → 승인 |

## card B 남은 순서
1. test 수정 확인 → 통합 브랜치 다시 만들기: base 083b103에 role/test·role/code·role/data 병합(기존 `wt/xrunf1b-integ`는 옛 것).
2. auditor 재판정(순서 6, 메모리 제약: 하나씩). 지난 판정 FAIL 기록 `wt/xrunf1b-audit` `4e25582`. 재판정 때 M-d 우회는 리뷰 항목(X-22), code 작성자 heredoc 편집 diff 재확인.
3. gap 분석(gap-detector) → master 병합.

## 다음 순서 (원칙: 무거운 실행은 하나씩)
- headroom-chain HC-0(card 0 측정, 13회로) -- card B 병합 뒤. 그다음 HC-D design.
- XRUN-F1 card C (headroom HC-1 병합 전제).
- graph-consumption: 검증 → U-G 결정 → GC-0 측정.
- oracle OP-2 구현 card(OP-1a 뒤), 이후 OP-3~.
- LT-1(옛 엔진·태그·analog-grammar 삭제): 착수 조건 OP-1a 병합, 로컬 tag `legacy-final`(origin push는 별도 승인 전).
- 백로그: structure_rule_fp를 판정 로직(AST)에만 묶기, KCL 구간 결합, DC 저항 방향 표현 공동분석, data_rel 유도식.

## 이 세션 새 원칙 (memory에도 있음)
- P-1: 규칙은 물리 정합 최우선, 가장 일반적 형태부터, 제한마다 물리 근거.
- analog-grammar 금지, topology 태그는 근거 아님(제거 예정).
- 코드 작성 전 계산식 대상이 graph에 이미 있는지 확인, 있으면 읽기. 엔진 계산은 KVL·KCL 관계를 실제로 풀어야 함.
- 코딩 뒤 보고에 'graph 계산값 소비 확인'(필드 수 / 소비자 0 / 정본 우회 의심) 추가.
- 계획과 다르면 계획부터(S-7), 원래 취지와 다름은 따로 보고.

## 정리 대상(급하지 않음)
- 이 세션에서 끝난 worktree 다수(plan/*, design/*, docs/*, topo/cr-intent 등)는 병합 끝 -- `git worktree remove`로 정리 가능(사용자 확인 후).
- 병합 커밋 baa7883은 트레일러 누락(기록만).

## 추가: graph-consumption 계획 v0.1 독립 검증 결과 (세션 끝 직전 도착)
판정 **수정 필요** -- 차단 5, 중간 9, 낮음 9. 다음 세션에서 계획 작성 agent로 v0.2 개정 → 재검증 → 사용자 결정.
- B1(중요): BD-1·X-G2·U-G2가 사용자 결정 B2(DEC-64 v1 포트 차 고리 = 제약 없음, 쓰기 계획을 계획에 맞게 고침)·K-3(input_tie 폐기, 대칭 포트는 domain.ties) -- user_decisions.md 225·243행, design 41 §6.7-1a -- 과 반대. KVL 정본 정의에서 tie 변 제외, U-G2 철회, K-3 card와 GC-2 순서. **승인된 headroom-chain 계획 v0.6의 Gs⁺(입력 포트–F 변)도 같은 tie 정의를 쓰는지 확인 필요(검증자 지적) -- 충돌이면 S-7로 headroom-chain 계획부터 정정.**
- B2: BD-4 공급 전류 합 판정은 결선 행렬 항등식(독립 아님) -- 삭제/재설계.
- B3: BD-3 결선 대조도 항등. 진짜 독립 경로 = SPICE 오라클 forced(넷별 KCL 잔차)·free(노드전압) + U16 배선, 엔진 보조 = node.terminals 점검, 쓰기 계획 숲 구조 불변량(종속 수 = |E|−|V|+성분 수).
- B4: gvgs_cycles.py 삭제 시 gvgs_self_edge fail-closed 정지(유일 사용처)가 사라짐 -- 정지 이전 단계 필요.
- B5: GC-6·GC-7이 S1V_RULE_FILES 파일을 고쳐 structure.json rule_hash 재기록 필요(X-22 선례, 사용자 승인 항목) -- 백로그의 '지문을 판정 로직에만' 개선과 묶어 검토.
- 중간: 부채 목록은 개수 아닌 항목 집합 부분집합 판정, L-1 죽은 reader·동적 접근 허용 범위, 봉인 8은 재작성 대신 삭제 또는 구조 불변량, MNA 잔차는 공허(조건수), 범위 확장(GC-2~GC-4) 착수 승인 필요, GC-5 충돌 뒤 처리, L-5 AST 한계 명시 등.
- 사용자 결정 필요(새): tie 변 제외·K-3 순서, GC-2~4 범위 승인, 봉인 8 처리, 독립 검증 경로(오라클), rule_hash 재기록, MNA 기록 항목, GC-5 충돌 처리.
- 검증 원문 요약은 이 절, 측정물은 그 agent scratchpad df/rows.json·cls.txt.

## 추가: OP-2 spec·interface card 초안 결과 (세션 끝 직전 도착)
`wt/_drafts/oracle/OP2_SPEC_CARD.md`·`OP2_INTERFACE_CARD.md` 작성됨, 머리에 '멈춤: J 닫히기 전 착수 금지'. 계약 C0~C11, 새 test 16, 측정 14, 완료조건 12, 재측정 사실 F-1~F-21(옛 형식 칸을 읽는 오라클 코드 13곳, --ngspice 진입점 5, conftest 생성기 183줄 + 생성기 밖 직접 수정 19줄·options 2줄·diffusion=False 12곳, 확산 규칙은 sky130_lut_rule_decl.json, tnom kind별, CRLF/blob sha 차이, 규칙 H orphan_test, smoke 재생성 일치 test 12항목, R6 원문 저장소에 없음, design Status 22행 낡음).
**design과 어긋나 멈춘 J-1~J-15** → 다음 세션: design 개정(v0.2.7) → 검증 → 승인, 계획 개정이 필요한 것(J-7, J-1 시점 D-2)은 S-7로 계획부터.
**사용자 결정 필요**: (1) sky130 기술자 값 전부 확인(§10.3: geometry_unit = mismatch_slope_geometry_unit_m, parallel_multiplier = 인스턴스 배수와 mult, lod.spice provenance 커밋 f62031a1 등), (2) J-7 재생성 일치 test 12항목 삭제를 OP-2로 앞당길지(계획 개정 + 기준 약화 승인), (3) J-1 옛 형식 거부를 OP-3으로 미룰지(원래 취지와 다름), (4) J-5 미배선 기간 허용 여부(절대원칙), (5) J-15 sha256 줄 끝 -- .gitattributes 고정(저장소 설정 변경) vs 기계 의존 수용.

## 추가: OP-1a 기준선 보관 완료 (세션 끝 직전 도착, master 병합 안 함)
판정 기록 id `20261016-op1-baseline`, 브랜치 role/audit/op1a (worktree `wt/op1a-audit`), 커밋 8c920f6(보관)·4bea336(판정 기록). V2·V4·V10 PASS, 코드 변경 0.
- 보관: baseline/files 3,512개 18.25 MB 커밋, 원자료 5,133개 sha256 목록, 저장소 밖 185.6 MB는 경로·sha만. sha 재대조 3종 불일치 0.
- DV-5: 재구현 스크립트로 표본별 V_os 201개×2 사례 -- pytest/mc5t0 σ_in·mean_in 기준선과 비트 동일, u6/mc_5t σ_in 비트 동일(mean은 기준선 칸 없음, 기록만). (d) 옛 함수 이름 교체 대조도 비트 동일(시뮬레이터 실행 0).
- **병합 전 확인할 것(원래 취지와 다를 수 있음)**: (a) 기록 폴더에 `.gitattributes`(`* -text`)를 넣음 -- 저장소 설정 변경이고 OP-2 J-15(.gitattributes 고정 여부, 사용자 결정 대기)와 같은 문제라 사용자 확인 후 병합; (b) `.gitignore`에 걸리는 76개를 `git add -f`; (c) .py 사본 5개 이름 끝 `.at_base`; (d) auditor가 worktree를 직접 만듦(브리핑 지시); (e) spec card 파일 없음(로더 규칙 10 미판정).
- 병합 결정 뒤 LT-1 착수 조건(OP-1a 병합) 충족.

## 추가: card B test 수정 라운드 완료 (세션 끝 직전 도착)
role/test/xrunf1b 새 커밋 950df64(B-T1 기대값 0→1, 근거 C1 손 계산)·efce1c9(미재작성 96건 -- 원인은 coupling_hand.py import 별칭 호출 87건 등, 낡은 주석)·2d5ecd8(M-c 강화: import 별칭·이름 대입·getattr 간접 호출 인식, 재대입 허용 -- 판정 단위를 open_run 대입 문장으로, if 가지 안 대입은 위반(fail-closed, design 미정 자리); bad 픽스처 위반 39→44; README 해석 2 design 원문 복귀 X-22 (a)).
- 전체 suite 자체 확인 **미완료**: 임시 복제본(code 68267a0 + data 65549c9 + test HEAD)에서 약 54%까지 F·E 0, 그 뒤 **메모리 부족으로 강제 종료**. rule_hash stale 24건 해소 여부 미확인.
- 다음 세션 card B 순서: (1) 통합 브랜치 새로(base 083b103 + role/test(2d5ecd8) + role/code(0952331) + role/data(65549c9)) → (2) auditor 재판정 -- 메모리 때문에 전체 suite를 디렉터리 단위 순차로 나눠 돌리게 브리핑(한 프로세스에 전부 금지), 시작 전 다른 무거운 작업 0 확인 → (3) gap 분석 → 병합.
- 알림: M-c가 if/else 양쪽 open_run 꼴을 위반으로 보는 것은 design 미정 자리(실제 트리 해당 0) -- 재판정 때 design 40 §2.4.5 원문과 대조.
