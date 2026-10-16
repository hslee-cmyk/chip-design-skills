---
title: oracle-portability -- design 이력
design: oracle-portability.design.md
date: 2026-10-16
---

# oracle-portability design 이력

> design 본문(`oracle-portability.design.md`)에 넣지 않는 경위를 둔다. 현행 규칙은 본문이 정본이다.

## H1. 버전 경위

| 판 | 커밋 | 내용 |
|---|---|---|
| v0.1 | f8b9a69 | card OP-0 초안. 승인된 계획 v0.4.2(O-1·O-2, D-1~D-9) 기준, base `6093d07`. 독립 검증·사용자 승인 전 |
| v0.2 | (이 커밋) | 사용자 결정 O-3(DV-1 (가) 확정, DV-2 별도 card, X-D1·X-D2 수용)을 반영했다. offset-trim design TR-0T의 G-15 닫힘으로 PC-10을 정의했다(입력 `output_reference`). 사용자 결정 T-39로 DC 풀이 허용오차 선언을 강제(`dc_tolerance_undeclared`)하고, 입력 환산 전파값 `dc_resolution_in_V`(§13.4)를 결과에 낸다. X-D3 해소, X-D4 신설 |
| v0.2.1 | (이 커밋) | 사용자 결정 O-4("TR-0T 승인, X-D4 권고대로 해")로 X-D4 수용을 표시했다. 매뉴얼 원문 보관·쪽 번호는 OP-0 card 범위, 영향 측정은 OP-1이다. offset-trim TR-0T가 master에 병합돼(T-40) PC-10·`dc_tolerance_undeclared`의 대조 기준을 master `offset-trim.design.md` §20으로 바꿨다. v0.2 독립 검증 결과는 아직 반영하지 않았다 |
| v0.2.2 | (이 커밋) | v0.2 독립 검증 87점(차단 B-1, 비차단 N-1~N-9)을 반영했다. B-1: X-13 test를 `E/tests/` 아래 읽기 전용 test로 두고(계획 v0.5.1 8a 예외, `oport-plan-r2` `d9f37c4`), 중복 검사도 넣었다. 나머지: N-2 양 종류별 필요 허용오차 키 집합, N-3 매뉴얼 쪽 번호를 OP-2 병합 조건으로, N-4 PC-10 부호 규약 인용 정정(offset-trim 계획 N0.1·design §0 V_in(c))과 단일 출력 기준 셋 모두 `source`, N-5 PC-3 r 출처(`--rel-resolution` 필수)와 기록 지문의 n·r, N-6 오류 표에 `oracle_condition_missing`·`descriptor_source_duplicated`, N-7 §5 조기 종결 문장을 G-13과 맞춤, N-8 `oracle_capability`를 `oracle_run capability` 하위 명령으로, N-9 Summary 판 번호·O-3·O-4·nutmeg 대 `early_window` 독립 기준(b)·T1-4 실행 중 기록 측정, B-2·B-8 '결정(O-3)' 표시. 남은 'trim-design-r1 미병합' 문구 정리 |
| v0.2.3 | (이 커밋) | 재확인 95점(차단 0)의 문구 3건을 고쳤다: §0 값 원칙 '입력 `testbench.options`' → '`simulator.options` 또는 출처 있는 어댑터 보정값', §3.1 CLI 통합 '(기본안)' → '결정(O-3)', §19.1 B-9를 '계획 v0.5.1 8a 예외에 따름'으로 표시 |
| v0.2.3 승인 | (이 커밋) | 사용자 승인(2026-10-16 "모두 권고대로", 결정 기록 O-5). 독립 검증 87 → 95점(차단 0). Status를 '승인됨'으로 바꿨다. 본문 규칙 변경 없음 |
| v0.2.4 | `cbf06d1`(브랜치 `design/oracle-op0-v024`, base `1ba9461`) | 계획 v0.6~v0.6.2(사용자 O-6 D-a·D-b·D-c, 승인 O-7)와 OP-1 측정을 반영한 개정 초안. 독립 검증·사용자 승인 전. 경위는 H3 |
| v0.2.5 | `564245f`(브랜치 `design/oracle-op0-v025`, base `9069e10` + v0.2.4 병합 `9d7ee5f`) | v0.2.4 독립 검증 결함(B-1·B-2, M-1~M-6, 경미)과 계획 v0.6.3~v0.6.4(L-1·L-2·L-3·O-8) 반영 개정 초안. 새 멈춤 DV-4·DV-5. 경위는 H4 |
| v0.2.6 | `5d4a262`(같은 브랜치, master `52945ce` 병합 `dea6549`), 후속 `57c2a0f`·`e6fc0fc`(재검증 조건·경미, 계획 v0.6.6 diff M-1·M-2), `428f87e`(계획 v0.6.6 병합 `b21b4a9` 반영: plan_version 0.6.6·인용 갱신·머리 version 정정), 이 커밋(git 추적 기준 철회 → 계획 v0.6.6 문구 '디스크의 모든 파일 − 제외 목록', X-D6, abspath 표기) | v0.2.5 검증 중간 지적 다섯·경미 일곱, 소비자 미정 칸, 계획 v0.6.5(O-9·O-10)·v0.6.6(어댑터 지문 제외 목록 방식) 반영 개정 초안. DV-4·DV-5 닫힘, 새 멈춤 없음. 독립 검증·사용자 승인 전. 경위는 H5 |

(v0.2.6 번호 정리: 절을 판 순서대로 H2 작성 → H3 v0.2.4 → H4 v0.2.5 → H5 v0.2.6으로 놓았다. 옛 'H6'(v0.2.5)는 H4다. design 본문 Status의 인용도 같이 고쳤다.)

## H2. 작성 경위 (2026-10-16)

- 지시: 오케스트레이터 'oracle-portability card OP-0(design) 작성'. 범위는 계획 OP-0이다(G 항목 중 OP-0 몫, 형식·스키마·PC 벤치·진단 배선·파일 분할·삭제 목록·test 목록·상위 문서 개정 문안). OP-1 측정이 필요한 칸은 '측정 대기'로 두고, 계획과 다른 결정이 필요하면 멈추고 보고한다(S-7).
- 읽은 것(base `6093d07`):
  - 오라클 8개 파일의 함수·상수 목록
  - `oracle_run.run_one`, `simulate` 결과 칸, `offset_mc_measure` 전체(표본 RNG 순서·V_os 식)
  - 입력 스키마 최상위 칸, `oracle_config.json`
  - smoke 입력 `process` 블록(pmos `lod.spice` include)
  - 엔진 선언 `sources` 목록
  - offset-trim v0.5.5 G-14(닫힘, T-35)·G-15(열림)·N6 오라클 확장 목록
- 실행: 코드 실행·ngspice 실행 없음.
- 멈춤 항목: DV-1(엔진 선언에 없는 include 파일, 계획 N3.4 단일 정본과 D-9의 충돌)과 DV-2(상위 문서 개정 미반영, 구현 card 착수 조건)를 본문 §19.2에 올렸다. DV-1은 임시안만 적고 확정하지 않았다.

## H3. v0.2.4 경위 (2026-10-16)

- 지시: 오케스트레이터 'OP-0 design 개정 v0.2.3 → v0.2.4'. 반영 대상 셋: (1) 계획 v0.6/0.6.1/0.6.2 변경 전부 (2) OP-1 측정 뒤 미뤄 둔 design 항목 (3) v0.2.3 검증자 정리 둘(§20 OP-2·OP-5 겹침, offset-trim N3.9-3 재대조). 계획과 다르게 가야 할 것은 정하지 말고 멈추고 보고(S-7), as-built·범위 결정 금지.
- 읽은 것:
  - 계획 v0.6.2 전문과 history v0.6~v0.6.2 절(`1ba9461`)
  - OP-1 산출물 `wt/_scratch_op1/results/`: `m1_native_mc.jsonl`(18행), `m2_m3_lut_meta.jsonl` 41행, `m7_gain_imag.json`, `m8_errlog.json`·`.console.txt`, `g8_check.json`, `g13_window_cost.json` `aggregate`, `m6_xd4_scan.json`, `m13_mc_replay.jsonl`, `n4_convert.jsonl`. 스크립트 `scripts/g13_window_cost.py`·`m6_xd4_scan.py`·`g8_check.py`, 검증자 초안 `n4_convert_input.py`·`g8_dialect_tokens.draft.json`
  - 다시 잰 코드 위치(base `1ba9461`): `O/oracle_compare.py:38, :228, :379, :708`, `O/oracle_swing.py:306`, `O/smoke/u6_selfchecks.py:136`, `O/legacy_adapter.py:191-192, :261-264`, `O/oracle_netlist.py:145-153`, `O/oracle_offset_mc.py:22-24, :137`, `O/oracle_input.schema.json` `process`, 모델 카드 `…nfet_01v8__tt.pm3.spice:16-30, :67`, `models/all.spice:2`, `E/lut/CONTRACT.md:887, :951`, offset-trim 계획 master v0.5.6 N3.9 466-477행
  - `O/` 코드가 `6093d07`과 같음을 `git diff --stat`으로 확인(README 2줄만 다름)
- 실행: 코드 실행·시뮬레이터 실행 없음(OP-1 산출물 읽기와 grep만).
- 판단 근거 몇 가지:
  - `1e-3`: v0.2.3 §14의 `data_rel` 대체안(B-7)은 계획 D-c가 뒤집었다(측정 170건 뒤집힘). 기본안 B-7을 철회로 표시하고 NFR-P2 예외로 옮겼다.
  - 진단 `value_rule`의 `z·1e-6/√m`: 기하 단위·병렬 배수를 소자 줄에서 전달하면(D-b) 이 배율이 두 번 들어간다. 계획 N3.6 삭제 목록(배율 삭제)대로 기술자 식에도 옮기지 않게 고쳤다.
  - 분포 값 sha256 불일치는 이미 있는 `pdk_descriptor_stale`로 낸다(같은 사실에 코드 둘을 만들지 않음).
  - `lut_reference_width_m`·`provenance`: 오라클 본체 grep 0이라 새 형식에서 지운다. `legacy_adapter`의 기준 폭 대체값이 함께 없어지므로 dump 값만 쓰고 없으면 막힘(조용한 대체 금지).
  - 상위 문서 개정 card `gb-oracle-rev`가 `b105b65`로 병합돼 있어 §1.3·§20 OP-2·§19.2 DV-2에 충족을 적었다.
- 멈춘 항목: DV-3(계획 N3.5 (ii)·N4 MC 수학 '끝까지 비트 동일'과 D-b 넷리스트 변화의 충돌). 권고 (가)는 적었지만 정하지 않았다.
- 알림(다른 문서 소유): 계획 N3.5.1 기준 커밋 문구, offset-trim N3.9 '순서 의존'의 '초안' 문구, `b105b65` 병합본 대 §17 문안 미대조.

## H4. v0.2.5 경위 (2026-10-16)

- 지시: 오케스트레이터 'OP-0 design 개정 v0.2.4 → v0.2.5'. v0.2.4(`cbf06d1`)가 master에 없어 worktree `wt/oracle-op0-v025`에서 `design/oracle-op0-v024`를 `--no-ff`로 병합(`9d7ee5f`, 충돌 없음)한 뒤 개정. 기준 계획 v0.6.4(승인). 계획과 다르게 가야 할 것은 정하지 말고 멈추고 목록으로(S-7), as-built 결정 금지.
- 반영 (A) v0.2.4 독립 검증(오케스트레이터 전달):
  - B-1 모델 묶음 비교 → 계획 X-22 역할 구분(§12.5 다시 씀: 역할 선언 출처, 옆 선언 형식 `lut_file_roles/1`, 근거 두 측정, 규칙 (i)~(iii), `lut_aux_input_mismatch`, 기술자 `lut_record_root`·`lut_file_roles`, OP-3 병합 (c))
  - B-2 §18.1 완료 조건 4에 PC-10 깨진 변형 셋과 `reference_undeclared` 거부
  - M-1 결과 칸 개명: 생산자 10곳·소비자를 다시 재고(S-23) §11.5 경로별 대응·`None` 처리 표, `method` 값(S-24)
  - M-2 실행 전 검사 순서 §7.2와 OP-3 (a) 양성 대조
  - M-3 '차이가 선언에서만' 판정 절차(§10.6: 기준선에 선언 변환 → 정규화 → 남은 차이 0)
  - M-4 삭제 모듈 소비자 §15.4(smoke 넷, conftest 장치, 엔진 test 하나 → DV-4)
  - M-5 §7.1 회복된 경고(S-30 로그 근거), pz 요청 단위 오류, 주입 로그 test
  - M-6 계획 X-20대로 기술자 `requires` 삭제, 코어 고정 요구(§10.4)
  - 경미: `geometry_unit_unsupported` 삭제(기존 코드로 합침), `mc_distribution_inline` 닫힌 키 집합, `descriptor_schema_invalid`, `pdk_descriptor_stale` detail, 4a 인스턴스 기하 = 보고 원값 대 test 계산 기대값(`instance_geometry_reported`), T1-0 D11 연기를 계획 X-23 단계 규칙으로, abstol 출처(S-28), 인용 정정(m1 12행 §12.3·§19.3, S-22, Status의 'H1 v0.2.4' → H3)
- 반영 (B) 계획 v0.6.3/v0.6.4: 생산자 0(§3.1·§11.4·§15.1·§18.2·§19.1 B-13 철회·§19.3·§20 OP-2), OP-1a(§13.2·§18.1·§20), DV-3 = O-8 (가-1)(가-2)(§13.2·§10.5·§19.2), OQ-4(§13.2), X-23(§18.1 T1-0)
- 다시 잰 것(base `9069e10`): `git grep` `ngspice_rc|ngspice_runs`, `O/oracle_simulate.py:401-402, :777-812, :1025-1067, :1105-1118, :1170-1202, :1230-1252, :1270-1320`, `O/oracle_noise.py:114-151, :294`, `O/oracle_offset_mc.py:109-196`, `O/oracle_swing.py:105, :306`, `O/smoke/*.py` import, `O/tests/conftest.py:36-51`, `E/tests/metrics/test_verified_by.py:1-65`, `A/sky130_lut_sweep.py:231-232, :680-695, :885-895`, `A/sky130_pdk_decl.json` `pdk_root`·`sources`, `E/lut/provenance.py:1-20`, `R/m1_native_mc.jsonl` 18행, `R/m13_mc_replay.jsonl`, `scripts/m13_mc_replay.py`, `R/m8_errlog.json`, 기준선 로그 `cmfb0/out/tcm_cmfb.free.cmloop.pz.log`·`mc5t0/o/t5ota.free.mc.log`, `R/m2_m3_lut_meta.jsonl`(38 슬라이스 중 32 `.bins.csv`), offset-trim 계획 N3.9 459-477행. `1ba9461..HEAD`의 `O/` 차이 0.
- 실행: 코드·시뮬레이터 실행 없음(읽기·grep·작은 JSON 집계만).
- 멈춘 항목: DV-4(엔진 test가 최상위 `oracle_*.py`를 glob, 완료 조건 8a와 충돌), DV-5(기준선에 표본별 V_os 칸 없음, (가-1)(가-2) 표본별 비교의 기준값 미정).

## H5. v0.2.6 경위 (2026-10-16)

- 지시: 오케스트레이터 'OP-0 design v0.2.5 → v0.2.6'. 같은 worktree에서 master `52945ce`(계획 v0.6.5, 사용자 O-9·O-10)를 `--no-ff`로 병합(`dea6549`, 충돌 없음)한 뒤 개정. 계획과 다르게 가야 할 것은 멈추고 목록으로.
- 반영 (A) v0.2.5 검증 중간 지적 다섯:
  1. §11.5 실행 전 반환 경로(S-31)의 사유 대응표 규칙, 옛 상태 칸 `log`·`log_errors`·`op_ok`·`skipped`·`cache`·`stability_cache`와 `RunStatus` 대응·소비자(S-32), 시뮬레이터 이름이 든 사유 문장(S-33)
  2. B-18 `lut_record_root` → 기존 정본 `A/lut_v2_location.json` `pdk_root` 참조(S-35, 엔진 무변경)
  3. 어댑터 지문 = 제외 목록 방식(§0, §8.3), 측정 도구 폴더 `calibration_tools/`(B-25), §3.2 import 방향
  4. `u6_selfchecks.py`의 conftest 소비와 conftest 옛 형식 입력 생성기·`make_lut`(S-34)를 §15.4·§18.2·§20에, u6 삭제 = O-10 승인, 삭제 card를 OP-3으로 고침
  5. §7.2 `lut_record_root` 교차 검사 = 8단계 `lut_record_root_mismatch`(값 불일치), `pdk_descriptor_stale`를 2단계 하나로
- 경미 일곱: §10.6 지시 줄 값·문법 출처와 `name_map` 의존 기록, §13.2 재구현 스크립트 표기, offset_mc 옛 rc 비교 제외(P-1) + `n_failed`, §7.1 주입 증거 단계 = B-24, B-20 '승인됨', history 번호 정리(H2를 앞으로, 옛 H6 → H4, 이 절 H5)·§19.3 머리, 엔진 쪽 낡은 인용 알림(S-36)
- 소비자 미정 칸: §6.1 신설(칸마다 소비자 또는 출력 전용). `RunStatus.cache_hit: bool`을 `cache_state` 넷 값으로 바꿈(옛 `'off(…)'` 상태, `O/oracle_simulate.py:105-110`), `mc_identity_lost` 새 코드, 시드 적용 = 5단계 능력 확인
- 반영 (B) 계획 v0.6.5: DV-4·DV-5 닫힘(§19.2), 8a 예외 둘째 행(§18.1), 기준선 표본별 V_os(§13.2), (d) 선택 대조 = `run_ngspice` 이름 교체 경로, conftest 손 넷리스트 기준 경로 `O/tests/adapters/ngspice/`
- 다시 잰 것(base `52945ce`, `9069e10..HEAD` `skills/` 차이 0): `O/oracle_noise.py:114-130`, `O/oracle_offset_mc.py:109-196`, `O/oracle_simulate.py:86-125, :1025-1060, :1084-1170, :1270-1320, :1369-1375`, `O/oracle_compare.py:374-390`, `O/oracle_run.py:40-60`, `O/tests/conftest.py`, 캐시 단언 test 넷, `A/lut_v2_location.json`, `E/lut/data_location.py:32-41, :58-83`, `git grep spice_oracle -- '*.py'`(엔진 쪽 인용)
- 실행: 코드·시뮬레이터 실행 없음.
- 멈춘 항목: 새 멈춤은 없다. 단 **계획 v0.6.6 개정 대기**(어댑터 지문 제외 목록 방식, 브랜치 `plan/oracle-v066` `c62f3bf`·`16af2cf` 미병합) -- §19.2 '개정 대기'. 같은 판 후속 커밋 `57c2a0f`(재검증 '승인 가능' 조건 1 + 경미 4, 계획 v0.6.6 diff 확인 M-1·M-2): 대기 표시, `lut_record_root` 규칙 출처 = `E/lut/CONTRACT.md` 1.8(256-261행, `os.path.abspath`)·의도된 엄격·X-D5, `n_failed` = 옛 정의(결과 없는 표본 수, rc는 `sample_status`만), §15.1·§11.5 u6 소비자 서술과 OP-3~OP-5 점검 공백, `lut_location_decl_invalid` 분리, 지문 파일 집합(git 추적·상대 POSIX 경로 정렬)·정규 JSON 규칙·`adapter_fingerprint_unavailable`(B-28).
- 개정 대기 해소: 계획 v0.6.6이 master `7edd723`으로 병합됨(사용자 X-22 승인) → worktree 병합 `b21b4a9` 뒤 `plan_version` 0.6.6, §0·§8.3·§12.4 인용 v0.6.6, §19.2 대기 줄 '해소'. 같은 커밋에서 머리 front matter가 `version: 0.2.5`·`plan_version: 0.6.4`로 남아 있던 것(v0.2.6 개정 때 Edit 실패, 미확인)을 `0.2.6`·`0.6.6`으로 고쳤다. X-D5는 사용자 확인 항목으로 그대로 둔다.
- diff 확인 '수정 필요'(중간 1, 경미 3) 반영: 오케스트레이터 결정(계획 문구 복귀)으로 B-28의 git 추적 파일 기준과 '추적 판정 불가 시 거부'를 철회하고 지문 파일 집합을 계획 v0.6.6 문구 '어댑터 패키지 아래 디스크의 모든 파일 − 닫힌 제외 목록'(순수 파일 열거)으로, 재현성 메모 §19.4 X-D6(잔여 파일 → 기록 무효·재생성, 의도된 엄격), §18.1 '기록 뿌리 해석' abspath를 env 값·default 둘 다에, H1 v0.2.6 행에 후속 커밋.
