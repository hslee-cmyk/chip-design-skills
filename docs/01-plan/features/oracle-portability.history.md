---
title: oracle-portability -- 계획 이력
plan: oracle-portability.plan.md
date: 2026-10-16
---

# oracle-portability 계획 이력

> 계획서(`oracle-portability.plan.md`)에 넣지 않는 **경위·조사 요지·버전 이력**을 둔다. 현행 규칙·정의·게이트·완료조건은 계획서가 정본이다.

## H1. 결정 경위

### 2026-10-16 착수 결정 T-31·T-33

- 원문: `wt/_drafts/user_decisions.md` '## SPICE 온도 보정 루프 (2026-10-16 ...)' 586-592행.
- T-29~T-32: offset·trim 잔여 합격을 오라클 온도 범위 판정으로 바꾸고 SPICE 온도 보정 루프를 offset-trim 보완으로 진행(TR-7 뒤). 사용자 취지: gm/ID의 장점 = 작은 노력으로 SPICE와 작은 오차로 빠르게 설계, 이번 개발의 가장 큰 이유. 다온도 LUT 엔진 확장 대신 SPICE 최종 판정 단계에서 따진다.
- T-31: 그 선행 card(MC 불일치·온도 의존 확인)는 sky130 한정이 아니라 공정 무관 방법론이어야 한다("다른 fab에서도 사용할 수 있으니까").
- T-33: 지금 오라클도 시뮬레이터 무관이어야 한다. 확인 결과 `tools/spice_oracle` 안 ngspice 언급이 많아 결합도 조사를 했다(H2).
- 범위 조정(코디네이터, 2026-10-16): T-31 절차·PDK 기술자·확인 test·능력 기록 형식은 이 계획이 소유하고 offset-trim 계획(v0.5 N3.9)은 의존만 둔다. offset-trim 쪽 초안은 `wt/_drafts/oracle_capability_handoff_from_offset_trim_v05.md`로 넘어왔다(승인 안 됨).
- S-7: 계획과 다른 부분은 계획부터 고친다. 그래서 상위 계획·design 40·C10 계약의 ngspice 고정 문구는 이 계획 N3.7 개정 목록으로 올렸다.

## H2. 결합도 조사 요지 (2026-10-16, `wt/_scratch_oracle_port/survey.md`)

- 읽기 전용, ngspice·pytest 미실행, base `d783efe`. `ng-bridge`는 `git show`로만 읽었다.
- 오라클 본체 7개 파일 시뮬레이터 결합 약 70곳(6범주), 생성기·어댑터·smoke 약 25곳. 공정 결합은 본체 동작 4곳(offset_mc 이름 규칙·배율, noise 내부 소자 경로, 넷리스트 '모델 = subckt' 가정).
- 구조 결함: 넷리스트 텍스트가 중간 표현(재파싱 7곳), 해석 요청과 결과 읽기가 한 문자열, C10 판정이 nutmeg 스크립트 안, 시뮬레이터 결함 회피와 판정 규칙이 섞임, 허용오차·시간 상한이 ngspice 값, `process.models`가 공정과 방언을 한 칸에, MC 방법이 본체에 박힘, 극성 정규화 층 없음.
- 엔진은 ngspice를 실행하지 않는다. 동작을 규칙으로 옮긴 곳은 bin 경계 하나.
- 조사 권고: 넷리스트·실행·파싱 층 모듈 재작성, 판정 수학 이동, 생성기 소스 정규식 삭제, 두 번째 실제 어댑터는 범위 밖 + stub 어댑터.
- 조사가 확인하지 못한 것(계획에 반영): 실행 동작, 두 번째 시뮬레이터 방언 표현 가능성(X-1), 다른 PDK MC 동작(F-7은 추론), `device_sigma` bin 최대 폭 출처, `ng-bridge` 유효성, C10 계약 원문 대조(이 계획 작성 때 읽어 D-1·N3.7에 반영), design 40 문장 대조(이 계획 작성 때 F-17로 반영).

## H3. 이관 초안 반영 (2026-10-16)

- offset-trim 이관 초안 §2(기술자 항목) → 계획 N3.4 표. 위치 안(엔진 PDK 선언에 오라클 절, 단일 정본)을 v0.1에서 채택했다가 v0.2에서 별도 오라클 기술자 파일(엔진 선언 sha256 참조)로 바꿨다(검증 B-2, 계획 D-9·X-11).
- §3 확인 C1~C6 → PC-1·PC-3·PC-4·PC-5·PC-6·PC-7로 다시 번호(오라클 README C1~C27과 충돌 피함). C3의 '배수 = 소비 요구의 k'는 기록에 배수를 박지 않고 소비자가 사용할 때 판정하도록 바꿨다(새 상수 방지). PC-2(극성), PC-8(LUT와 다른 온도 입력 -- offset-trim N3.9-3 다섯째 요구), PC-9(bin 경계, D-4)를 더했다(계획 X-9).
- §4 능력 기록·fail-closed → N3.5. §5 공정 무관 증거(손 모델 기술자, 실제 두 번째 PDK 불요 권고) → N3.5·D-8.
- 코디네이터 추가 지시(2026-10-16): offset-trim v0.5(`trim-plan-r1` `9faccca`) N3.9-3의 확인 항목 다섯과 대조표 → 계획 N3.5.1(다섯 모두 담김).

## H4. 측정 근거

- 계획 N3.0 함수 위치는 2026-10-16 base `d783efe`에서 grep으로 다시 확인했다(`O/oracle_netlist.py:53, :124, :145, :561, :727, :730, :1105`, `O/oracle_simulate.py:86, :104, :402, :540, :607, :633, :826`, `O/oracle_noise.py:48, :65, :74, :82`, `O/oracle_offset_mc.py:52, :69`, `O/oracle_swing.py:69`, `O/oracle_compare.py:226`, `O/legacy_adapter.py:157`). 오라클 `*.py` 합계 5114줄.
- `ng-bridge` 마지막 커밋 `d529ea5`(2026-10-08), master에 병합 안 됨(`git merge-base --is-ancestor` 확인).
- 코드 변경·ngspice 실행 없음.
- v0.2 추가 확인(2026-10-16, 읽기만): `E/core/pdk_decl.py:190-196` 모르는 키 거부(`pdk_decl_keys`), `decl_sha256` 흐름(`E/metrics/junction_source.py:25, :36`, `E/metrics/aux_types.py:35`, `E/tests/integration/test_s0_layer_9circuits.py:336, :369`), `E/lut/CONTRACT.md:528`(VDSAT = ngspice `@m[vdsat]`), `E/metrics/junction_cap.py:8`, `O/oracle_offset_mc.py:127, :137, :202`, `O/oracle_netlist.py:124-126`, `O/oracle_simulate.py:65`(`_model_files`). 상위 문서 ngspice 줄 전수: 상위 계획 22줄, design 40 17줄(`grep -n -i ngspice`, base `d783efe`). `trim-plan-r1` HEAD `3879c7e`(v0.5.1) N3.9 438-456행.

## H5. 검증 반영 기록

### 2026-10-16 v0.1 독립 검증(72점, 차단 6, 비차단 15) 반영 → v0.2

| 지적 | v0.1 | v0.2 반영 |
|---|---|---|
| B-1 완료 조건 1 측정 주체 | 방언 토큰을 어댑터 문법표에서 뽑음(작성자가 기준 소유), 코어 어휘와 겹침, 코어 파일 집합 미정 | N0.1 코어 모듈 집합 = `O/core/`, 토큰 목록은 검증자 소유·문법 형태(점 지시문, 내부 벡터 틀, 스크립트 명령 형태), import 금지 = 어댑터 패키지 + `subprocess`(N3.1-1, FR-P1, 완료 조건 1, G-8, OP-1) |
| B-2 OP-2가 엔진 변경 | 엔진 선언에 오라클 절 | D-9 신설: 별도 오라클 기술자 파일이 엔진 선언을 sha256으로 참조(권고 (가)), 엔진 선언·로더 무변경, 완료 조건 8a, F-13 보강, N3.4·N5.2 정정. D-2에 옛 생성기 sha 결속 주의와 X-10 |
| B-3 offset-trim 대조 최신화 | `9faccca` 요구 다섯 | `3879c7e` v0.5.1 요구 일곱, PC-10(V_sys(T))·PC-11(결정적 벡터, G-14 조건부) 신설, '확정 시 재대조'를 OP-0 착수 조건으로 |
| B-4 상위 문서 개정 전수표 | 9행 요약 | 상위 계획 22줄·design 40 17줄 줄별 '고침/둠' 분류표 + 그 밖 4행(N3.7) |
| B-5 PC-4 합격 규칙 부재 | 기록만, 판정은 소비자 k | PC-3·PC-4를 결정적 섭동·결정적 σ로 바꾸고 합격 규칙(해 정확도 분해능 전파 폭, 면적 지수) 명시, 규칙 소유 = 이 계획, 판정 실행 = 검증자. 표본 σ̂ 일치는 기록만(X-12). 완료 조건 4와 일치 |
| B-6 D-7 공칭 차단 | 공칭 판정에도 능력 기록 | 능력 기록은 MC·온도 계층만, 공칭은 실행마다 모델 묶음 sha256 자동 대조(`model_bundle_mismatch`) + 극성은 어댑터 test(D-7, N3.5 표, X-8 재작성, N9) |
| N-1 | F-15 '14개' | test 13개 + helper 1개 |
| N-2 | F-3 방언 틀이 코드에 있다고 읽힘 | 틀은 입력 `op_probe`, 결합은 입력·생산자 |
| N-3 | 근거 586-592행 | 584-592행 |
| N-4 | F-12 bin 규칙만 | LUT VDSAT 정의(DEC-88)·접합 용량 주석 추가, PC-7에 vdsat 대응 |
| N-5 | OP-7·OP-8·완료 조건 8 무조건 | 'D-4·D-2 승인 시' 표시, OP-9 선행 조정 |
| N-6 | PC-9 미확인이어도 선언값 사용 가능 | LUT에 묶은 선언 + PC-9 기록 id, 미확인이면 경계 L 거부(`bin_tie_unverified`), G-14 |
| N-7 | 능력 없는 어댑터 = 전체 창만 | 창별 재실행 대안 검토(N3.3, G-13, X-2) |
| N-8 | X-4 지연 크기 없음 | card 7개·대략 1~3주 추정, 레인 P 병렬이면 지연 0 가능(N5.2, X-4) |
| N-9 | 온도 게이트 미배선 | 온도 요청 경로에 OP-6에서 배선(N3.5 '배선', OP-6) |
| N-10 | stub 한계 미정 | G-10 해석별 'stub 실행/능력 없음 거부 test' 목록, G-3에 `tran_plan` LTE 결합 |
| N-11 | PC-3 신뢰 구간 = 새 상수 | 결정적 섭동으로 바꿈, G-11에 유도 출처 강제 |
| N-12 | PC-1 '결과에서 모델 sha 읽기' | 어댑터가 include 묶음 재귀 해시(`_model_files`), 한계 명시 |
| N-13 | 삭제 목록 누락 | `oracle_offset_mc.py:127, :137, :202` 추가, 나머지 같은 종류는 OP-0 전수 grep |
| N-14 | import 검사 대상 불명 | 금지 목록 = 어댑터 패키지 + `subprocess`(B-1과 함께) |
| N-15 | 옛 입력 대 새 입력 변환 주체 | 검증자 소유 기계적 변환 스크립트, OP-0 필드 대응표(N4-2a) |

## Version History

| 버전 | 날짜 | 변경 |
|---|---|---|
| 0.1 | 2026-10-16 | 초안: 계획서·history 신설. 3층 구조, 능력 확인 PC-1~PC-9, offset-trim N3.9-3 대조표, 재작성·삭제 목록, 상위 문서 개정 목록, card OP-0~OP-9, D-1~D-8, X-1~X-9. 사용자 승인 전 |
| 0.2 | 2026-10-16 | 독립 검증 72점 차단 B-1~B-6·비차단 N-1~N-15 반영(H5). D-9·G-13·G-14·PC-10·PC-11·X-10~X-12 추가, D-2·D-4·D-7 권고 갱신. 사용자 승인 전 |
