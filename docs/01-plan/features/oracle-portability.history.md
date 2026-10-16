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

- offset-trim 이관 초안 §2(기술자 항목) → 계획 N3.4 표. 위치 안(엔진 PDK 선언에 오라클 절, 단일 정본)을 그대로 채택.
- §3 확인 C1~C6 → PC-1·PC-3·PC-4·PC-5·PC-6·PC-7로 다시 번호(오라클 README C1~C27과 충돌 피함). C3의 '배수 = 소비 요구의 k'는 기록에 배수를 박지 않고 소비자가 사용할 때 판정하도록 바꿨다(새 상수 방지). PC-2(극성), PC-8(LUT와 다른 온도 입력 -- offset-trim N3.9-3 다섯째 요구), PC-9(bin 경계, D-4)를 더했다(계획 X-9).
- §4 능력 기록·fail-closed → N3.5. §5 공정 무관 증거(손 모델 기술자, 실제 두 번째 PDK 불요 권고) → N3.5·D-8.
- 코디네이터 추가 지시(2026-10-16): offset-trim v0.5(`trim-plan-r1` `9faccca`) N3.9-3의 확인 항목 다섯과 대조표 → 계획 N3.5.1(다섯 모두 담김).

## H4. 측정 근거

- 계획 N3.0 함수 위치는 2026-10-16 base `d783efe`에서 grep으로 다시 확인했다(`O/oracle_netlist.py:53, :124, :145, :561, :727, :730, :1105`, `O/oracle_simulate.py:86, :104, :402, :540, :607, :633, :826`, `O/oracle_noise.py:48, :65, :74, :82`, `O/oracle_offset_mc.py:52, :69`, `O/oracle_swing.py:69`, `O/oracle_compare.py:226`, `O/legacy_adapter.py:157`). 오라클 `*.py` 합계 5114줄.
- `ng-bridge` 마지막 커밋 `d529ea5`(2026-10-08), master에 병합 안 됨(`git merge-base --is-ancestor` 확인).
- 코드 변경·ngspice 실행 없음.

## Version History

| 버전 | 날짜 | 변경 |
|---|---|---|
| 0.1 | 2026-10-16 | 초안: 계획서·history 신설. 3층 구조, 능력 확인 PC-1~PC-9, offset-trim N3.9-3 대조표, 재작성·삭제 목록, 상위 문서 개정 목록, card OP-0~OP-9, D-1~D-8, X-1~X-9. 사용자 승인 전 |
