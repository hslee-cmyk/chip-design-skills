# 세션 컨텍스트 (최종 갱신: 2026-08-03)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 지금 당장 이어서 할 일 (다음 세션 최우선)

배치 7-5(`analog-topology-json-library` 기능의 마지막 게이트)는 **"계산은 완주,
최적점 탐색은 미완"** 상태다.

1. **`workspaces/current-reuse-telescopic-ota-report/run_harness_smoke.py`를 먼저
   실행**해서 현재 상태를 재확인할 것(theta를 중간값 하나로 고정, 몇 초~수십 초 내
   끝남). 이게 51개 소자 전체 사이징+지표 계산이 여전히 예외 없이 도는지 확인하는
   가장 빠른 방법이다.
2. **진짜 최적점(theta*) 탐색**: `run_harness.py`가 9개 실제 theta(2^9=512 조합)
   full grid search를 수행하는데, 이 환경에서 백그라운드 프로세스가 9~40분 사이에
   반복적으로 강제 종료(killed)돼 완주 못 함(원인 미확인 — 이 세션/환경의 실행시간
   제한으로 추정). 다음 세션에서 시도할 것:
   - 그리드를 더 줄이거나(`spec["VDS_candidates"]`/`spec["gm_id_grid"]` 이미 3×6으로
     축소됨 — 더 줄이거나 `grid_points_per_theta` 자체를 줄일 방법 검토)
   - 이 대화 세션이 아닌 별도 터미널/nohup 등으로 환경 제약을 우회
   - 또는 CMRR 미달 원인(`L_cascode`의 `metric_stage_budget` feed가 쓰는 고정
     `gm_id=15.0` 기본값)을 먼저 topology.json에서 명시적으로 지정해 탐색 공간을
     좁히는 것도 시도해볼 만함(`feeds.gm_id` 필드 추가)
3. **theta*를 찾으면**: `save_instance_json()`으로
   `current_reuse_telescopic_ota.instance.json` 저장 → 기존
   `workspaces/current-reuse-telescopic-ota-report/sizing_results.json`(2026-07-28~29
   손 계산본)과 비교.
4. **레이아웃 단계 확인**: `assign_finger_geometry()`→`run_topology_pipeline()`→
   `repair_matching_safety()`까지 완화된 constraints로 시도했을 때
   `common_centroid_layout()`의 `"count=1가 소자 수 n=2보다 작다"` 에러가 났다 —
   극단적으로 작은 W를 가진 소자 쌍 때문으로 보이나 실제 feasible theta*에서도
   재현되는지는 미확인. 재현되면 원인(어느 소자 쌍인지) 조사 필요.
5. 전부 통과하면 `docs/03-analysis/analog-topology-json-library.gap-findings.md`
   §26과 `do.md` 배치 7-5 섹션에 "완전 완료"로 갱신.

## 배경 — analog-topology-json-library 기능이란

- **WHY**: topology netlist가 Python 코드 하드코딩이라 재현 불가능, agent마다 해석이
  달라짐.
- **핵심 산출물**: `topology.json` 스키마(netlist/symmetry/compensation 고정 3섹션 +
  sizing_roles/device_roles) + 오케스트레이션 레이어(`load_topology`,
  `run_topology_pipeline`, `save_instance_json`, `optimize_full_circuit_budget` 등,
  전부 `skills/analog-gmid-design/assets/{stick_diagram,sizing_recipe}.py`).
- **관련 문서**:
  - `docs/01-plan/features/analog-topology-json-library.plan.md`
  - `docs/02-design/features/analog-topology-json-library.design.md`
  - `docs/03-analysis/analog-topology-json-library.gap-findings.md` (§26이 최신)
  - `docs/04-report/analog-topology-json-library.do.md` (2324줄+, 배치 1~7-6 구현
    경위 전부 기록 — 배치 7-5 섹션 끝의 2026-08-03 업데이트가 최신 상태)
  - `skills/analog-gmid-design/references/consistency-map.md` (2026-07-27 이후
    갱신 안 됨 — 배치 7 작업 전체가 미반영된 상태로 남아있음, 알려진 기록 지연)

## 이번 세션 진행 이력 (요약)

### 1단계 — do.md 스펙 대비 구현 현황 체크
문서의 "완료" 표시를 그대로 믿지 않고 실제 코드로 대조 검증(general-purpose agent
위임). 결과: 배치 1~6, 배치 7-1~7-4b/7-6 전부 실제 구현·self-test 통과 확인. **배치
7-5(harness-only 51소자 완주 "최종 증거")만 미실행 상태**였음 — 함수는 다 있지만
실제로 51개 소자 전체를 돌려본 적이 없었음.

### 2단계 — 커밋 (`e329283`)
배치 1~7(7-5 제외) 구현 전체를 커밋. 이후 사용자가 "배치 7-5 실행"을 다음 작업으로
선택.

### 3단계 — 배치 7-5 실제 실행 (이번 세션 핵심 작업)
`optimize_full_circuit_budget(current_reuse_telescopic_ota.topology.json, spec)`을
처음으로 51개 소자 전체에 실행 → 실제 에러를 하나씩 고쳐나가며 반복 실행(약 20회
이상 iterate). **최종 확인된 것: 51개 소자 전체의 사이징(W/L/gm/ID/gm_id) + 지표
계산(gain/mismatch/CMRR/PSRR/power/area)이 예외 없이 완주.**

실행 중 실제 traceback으로 재현·확인한 gap 15건을 전부 고침(상세는
`gap-findings.md` §26):
- **topology.json 선언 11건**: theta feed 필드 누락(K_replica/N_cmfb_bw/r_biasgen),
  `L_cascode`/`L_stage2out` bounds 단위 버그(L=1미터가 나옴), M25/M26 사이징 경로
  누락, **M63의 실제 넷리스트 연결 오류**(source가 "gnd"로 잘못 적혀 M64.drain이
  끊긴 노드였음), Vbias1 계열 8개 소자 전류 시드 누락, M5/M38/M11a/M20a/M9b/M18b
  다중-branch KCL 합류 미해결, M18a 사이징 경로 누락, CMRR/PSRR metric spec 키
  불일치.
- **sizing_recipe.py 코드 4건**: A엔진 실행 순서 버그(theta 루프 전 1차 패스 추가),
  **`shared_gm_id_groups` 신설**(물리적으로 같은 직렬 전류인 gmp/gmn 스테이지가
  독립 최적화되며 다른 gm_id를 골라 KCL 위반을 일으키던 실제 버그를 sky130 실LUT로
  처음 발견 — toy LUT self-test는 우연히 안 걸렸음), `_feed_root_ratio()`의 `root`
  리스트化 + `ctx.seed_currents` fallback(theta 차원 폭발 방지), `_feed_diode_
  stack_target()` 완전 replica화(W만이 아니라 ID/gm/gds/gm_id/L 전부).
- **성능 버그 1건**: `bounds[0]==bounds[1]`(고정값 theta, KCL 합산용 8개)도
  `grid_points_per_theta`만큼 반복 평가하던 문제로 조합 수가 2^17(13만+)까지
  폭발 — 고정값이면 1개 점만 평가하도록 수정, 9개 실제 theta만 남아 2^9=512로 축소.

**모든 수정 후 `stick_diagram.py`/`sizing_recipe.py` self-test 재확인 — 회귀 없음
(exit 0, FAIL/Traceback 없음).**

### 미해결로 남긴 것 (위 "지금 당장 이어서 할 일" 참고)
- 진짜 feasible theta* 탐색(전체 512-combo grid search)은 환경 제약(백그라운드
  프로세스 killed, 9~40분 사이)으로 못 끝냄 — **계산 자원/실행 방식 문제이지
  알고리즘/코드 문제가 아님**.
- 레이아웃 단계(`common_centroid_layout`) 새 에러 1건, 재현 조건 미확인.
- 부수적으로 발견했으나 손대지 않은 것: metric 이름 단위 접미사(`_uA`)가 실제
  반환값(SI 기본단위 A) 오해 소지, `_metric_flicker_plus_thermal_sum()`이 kind별
  LUT를 안 가려 씀(정밀도 저하, 이 회로에서 실제로 해당).

## 작업 파일 위치
- `workspaces/current-reuse-telescopic-ota-report/run_harness.py` — 본 실행
  스크립트(512-combo 전체 grid search, spec 정의 포함).
- `workspaces/current-reuse-telescopic-ota-report/run_harness_smoke.py` — theta를
  중간값 하나로 고정한 빠른 진단용(초 단위로 끝남). **다음 세션에서 상태 재확인은
  이걸로 먼저 할 것.**
- `workspaces/current-reuse-telescopic-ota-report/*.log` — 이번 세션의 여러 반복
  실행 로그(git에는 안 잡힘, 로컬 디버깅 이력만 남아있음).

## 참고 — 사용자 협업 메모리 (관련)
- 최종 보고는 항상 한글로(추론은 영어 가능).
- 상상으로 채우지 말고 근거·실제 확인 후 진행 — 이번 세션에서 topology.json의
  모든 gap을 실제 traceback으로 재현 확인 후에만 고쳤고, 확신 없는 값(예:
  bias-gen 전류 배분 비율)은 이유를 명시한 근사/theta 탐색 대상으로 남겼다.
- topology.json이 유일한 토폴로지 소스 — connectivity/device 정보는 항상
  `load_topology()`로 JSON을 읽어 쓸 것, 손타이핑 금지.
- 배경 프로세스는 `run_in_background: true`로 시작하고 완료 알림을 기다릴 것 —
  직접 만든 `&`/`nohup` 백그라운딩은 이 세션에서 추적이 끊기는 문제가 있었다.
