# 세션 컨텍스트 (최종 갱신: 2026-08-04, 세션 5 끝)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 지금 상태 (다음 세션이 읽어야 할 것 1순위)

- **커밋 안 됨 — working tree에 변경사항 있음.** HEAD는 아직 `82e3556`(세션 4 핸드오프
  커밋)에 머물러 있고, 세션 5의 모든 작업은 uncommitted 상태다. `git status --short`로
  확인: `current_reuse_telescopic_ota.topology.json`/`.topology.md`,
  `sizing_recipe.py`, `pending_topology_corrections.md` 4개 파일 수정됨. **다음 세션은
  커밋할지 먼저 사용자에게 물어볼 것**(이 세션에서 커밋 지시가 없었음).
- **`optimize_full_circuit_budget()`을 회로 전체(51개 소자)에 처음 실제로 돌려보는 시도
  중** — 세션 4 핸드오프가 "다음에 하면 좋은 것 1번"으로 남긴 과제. 그 과정에서 진짜
  netlist 오류 2건을 발견해 수정했고, 지금은 **탐색공간 크기 문제로 아직 완주 못 함**
  (아래 "미완료 작업" 참고).

## 세션 5에서 발견·수정한 것 (중요도 순)

### 1. topology.json connectivity 정정 2건 (`_correction_log_8` 참고)
- **`M14a`/`M14b`가 `Vop1`과 무관**: `M14a.source`/`M14b.drain,gate`를 `Vop1`에서 신설
  사설net `N14a_14b`로 분리. `vdd–M13(diode)–N14a14b–M14a(diode)–N14a_14b–M14b(diode)–gnd`,
  완전히 독립된 3단 직렬 체인.
- **`M23a`/`M24b`가 `Vom1`과 무관**: 재구성 → `vdd–M22(diode)–N24b23a–M23a(diode)–
  N23a24b(신설)–M24b(diode)–gnd`, 역시 독립 체인.
- **왜 틀렸었나(중요, 반복 방지)**: 세션 4의 `_correction_log_6`이 "M14a/M14b는 Vop1과
  연결, M23a/M24b는 Vom1 유지"로 기록했던 게 둘 다 옛 `Vg16`/`Vg26` **블랭킷 병합**의
  잔재였다 — 사용자는 각각 `M10.drain=M9b.source=Vop1`, `M19.drain=Vom1=M18b.source`
  딱 한 문장만 확인해줬는데, 그 문장을 "옛 net 전체를 그대로 새 net에 병합"으로 확대
  해석하면서 M14a/M14b·M23a/M24b까지 같이 끌려갔다. **artifact가 이 연결을 "확정"으로
  문서화했던 것도 독립 재검증이 아니라 그 블랭킷 병합을 그대로 기록한 것뿐이었다** —
  이번 세션에 "artifact로 확인했던 것과 다른데?"라는 사용자 질문에 처음엔 artifact를
  근거로 방어했다가, 재검토 후 틀렸음을 인정하고 정정했다. **교훈**: artifact/문서가
  "확정"이라고 적어놨다고 해서 독립 재검증된 게 아니다 — 그 문서 자체가 어떻게
  생성됐는지(사용자 원문장 vs Claude의 확대해석) 추적해야 한다.
- **판단 근거**: 사용자가 "Vop와 Vom쪽 회로는 완전 대칭이어야 해(M6.gate/M7.gate 제외)"
  원칙을 제시 — 이 원칙으로 표를 대조하며 정정 방향을 찾았다(`M22-M23a-M24b`가
  `M11a-M11b-M12`와 같은 "무관 독립 체인" 유형, `M13-M14a-M14b`도 마찬가지 — 애초에
  "한쪽만 출력버스에 물리는 의도된 비대칭"은 이 회로에 없었다).

### 2. `sizing_recipe.py` 엔진 버그 수정
`derive_stack_groups()`가 `matching_pairs`의 **모든** kind(`branch_symmetric` 포함)를
KCL stack_id 병합에 재사용하고 있었다 — `branch_symmetric`은 "레이아웃 매칭 필요"라는
뜻이지 "같은 전류"라는 뜻이 아닌데(정의상 공유 노드가 없는 쌍을 위한 카테고리), 이걸
그대로 A엔진에 넘기면서 서로 다른 free theta로 사이징되는 소자들이 강제로 같은 전류로
묶여 KCL ValueError가 났다. **수정**: `optimize_full_circuit_budget()`에서 `stack_groups_kcl`
계산 시 `branch_symmetric` 쌍은 제외(`current_mirror`/`diff_pair`는 포함 유지),
`stack_groups_geometry`(floorplan용)는 기존대로 전체 포함. `sizing_recipe.py` 1802행
부근 주석 참고.

### 3. 새로 드러난 사이징 gap 3건 (전부 topology.json에 theta로 추가 완료)
버그 수정 후 실행해보니, 원래 `branch_symmetric` 병합 버그가 **우연히** 전류를 흘려주고
있던 소자들이 진짜로는 시드가 없었다는 게 드러났다:
- `M10`/`M19`(출력버스 독립 sink) → `r_sink_vop1vom1` 신설(root=[M10,M19] 동시 시드,
  대칭 원칙 그대로 반영).
- `M58`/`M57`(Vbias2 bias-gen 서브체인, `_correction_log_7`의 옛 "M61->M58->M57" 서술은
  이후 정정으로 이미 stale했었음) → `r_bg_vbias2` 신설.
- 전부 `r_biasgen`/`r_diode_M11a`와 같은 "신호경로 대비 작은 하우스키핑 비율"
  [0.02,0.15] 카테고리로 근사(논문에 이 전류들을 정하는 식 자체가 없음 — 정직한 한계).

### 4. theta 병합으로 탐색공간 축소 + 대칭성 강제
사용자 질문("theta가 많아지면 탐색공간이 늘어나는데, branch 몇 개를 같은 전류로 묶는
방법도 있지 않냐")을 계기로 감사한 결과, `r_diode_M11a`(Vom측)와 `r_diode_M20a`(Vop측)가
**분리된 독립 theta**로 남아있던 걸 발견 — `r_classab_src`/`r_sink_vop1vom1`은 이미
양쪽을 한 theta로 묶어놨는데 이것만 누락돼 있었다. 완전 대칭 원칙상 두 체인은 항상 같은
비율이어야 하므로, 하나로 병합(`r_diode_M11a`의 root에 M20a/M20b/M21 추가, `r_diode_M20a`
삭제) — 자유 theta 14개→13개, 동시에 "그리드서치가 대칭을 깰 수 있는" 잠재적 버그도 제거.

### 5. `symmetry.dispositions` 재생성
위 connectivity 정정 후 `rerun_symmetry.py` 재실행 → stale 3건 발견(M14b→M16,
M23a→M26 죽은 관계 2건 삭제, `N24b23a`/`Vom1`/`Vop1` 멤버 갱신 1건대씩) → 전부 실측
결과로 갱신 완료(`Voc_des` 무관 stale 1건만 남음, 원래도 의도된 것).

## 미완료 작업 (다음 세션 최우선)

**`run_harness.py`가 아직 완주 못 함** — KCL 에러는 다 해소됐지만(위 1~3번), **탐색공간이
너무 커서** 실행이 안 끝난다. 자유 theta 13개 × `grid_points_per_theta=2` = 2^13=8192
조합, 각각 전체 회로 사이징을 도는 구조라 시간이 오래 걸린다(3분 타임아웃 2회 경험,
사용자가 둘 다 "멈춰봐"로 중단시킴 — 아직 결과를 못 봤다).

**다음 세션에서 시도할 것**:
1. 먼저 `run_harness.py`를 **background로 충분히 길게**(10분+) 돌려서 실제로 완주하는지,
   아니면 `sizing_recipe.py`가 이미 알고 있는 "동점 처리로 인한 순환"(limit cycle) 버그에
   걸리는지 확인. `run_in_background: true` 필수(세션 4 이전부터 있던 원칙).
2. 여전히 안 끝나면: (a) 더 병합 가능한 theta 쌍이 있는지 재검토(이번 세션 패턴,
   "완전 대칭인데 분리된 theta 없나" 감사), (b) `grid_points_per_theta`를 일부 theta에만
   낮게 적용하는 방법이 있는지(현재는 전역 파라미터), (c) 정말 필요하면 random/coarse
   search로 1차 근사 후 promising 영역만 fine search 하는 새 메커니즘 검토(현재
   `optimize_full_circuit_budget()`엔 없음, 새 기능이라 신중히).
3. 완주하면 `result["audit_ok"]`/`result["metrics"]` 확인하고, 세션 4 핸드오프의 원래
   "다음 단계"(Cc/Rz/Iref 값 채우기, PSRR 폐형식 재유도)로 이어가면 됨.

## 배경 — analog-topology-json-library 기능이란

- **WHY**: topology netlist가 Python 코드 하드코딩이면 재현 불가능, agent마다 해석이
  달라짐 — 그래서 `topology.json` 하나를 유일한 소스로 둔다.
- **핵심 산출물**: `topology.json` 스키마(`netlist`/`symmetry`/`compensation`/
  `passive_elements`/`ideal_sources`/`ports`/`sizing_roles`/`device_roles`) +
  오케스트레이션 레이어(`load_topology`, `run_topology_pipeline`, `save_instance_json`,
  `optimize_full_circuit_budget` 등, 전부 `skills/analog-gmid-design/assets/
  {stick_diagram,sizing_recipe}.py`) + `topology_to_markdown.py`(connectivity 검토용
  표 생성기).
- **권한 경계(중요, 항상 지킬 것)**: `netlist`/`passive_elements`/`ideal_sources`의
  connectivity(`source`/`drain`/`gate`/`terminals`)는 **사용자만 고친다** — Claude는
  절대 임의로 안 바꾸고, 사용자가 논문을 보며 불러주는 정정만 반영한다(대기열에 쌓았다가
  "한꺼번에 반영해"할 때 일괄 처리). 반면 `device_roles`/`symmetry.matching_pairs`/
  `symmetry.dispositions`/`sizing_roles`(theta 포함) 같은 **역할·메타데이터는 Claude가
  connectivity로부터 분석해서 업데이트해도 된다**. **세션5 추가 원칙**: 논문에 없는
  값(component value)은 "논문에 있다"고 인용만 하고 끝내지 말 것 — 사용자가 직접
  지정하지 않으면 실제 설계 방법론(closed-form 유도, gm/ID 탐색)으로 Claude가 합리적
  값을 도출해야 한다([[feedback_no_paper_values_derive_rationally]] 메모리).
- **관련 문서**:
  - `docs/04-report/analog-topology-json-library.do.md` — 배치 7-5~7-5d 섹션이 최신
    (세션5 작업은 아직 여기 반영 안 됨 — 필요시 정리).
  - `skills/analog-gmid-design/references/topology-extraction-checklist.md` §5 —
    `topology_to_markdown.py` 필수 사용 절차.
  - `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.md`
    — 이 회로의 connectivity 표(net별/소자별, 세션5 재생성 완료: 51소자, 37net,
    자동 플래그 0건).

## current_reuse_telescopic_ota 회로 — 지금까지 검증된 핵심 구조

- **1단(입력)**: PMOS 입력쌍(M1a/M1b, tail=Vx=M6∥M7) + NMOS 입력쌍(M4a/M4b, tail=Vy=M5)이
  같은 입력(Vip/Vim)을 공유하며 각자 캐스코드(M2a/M2b pmos, M3a/M3b nmos)를 거쳐
  출력노드(Vom1/Vop1)에서 드레인끼리 합류한다(current-reuse의 핵심).
- **2단(Class-AB 출력) 교차결합**: Vom측 2단 내부노드=`Vop1`, Vop측 2단 내부노드=`Vom1`
  (1단 차동출력이 반대쪽 2단 바이어스로 넘어감) — **단, `M14a`/`M14b`(Vom측)와
  `M23a`/`M24b`(Vop측)는 이번 세션 정정으로 이 교차결합에서 제외됨**(위 "세션5" 1번
  참고, `N14a_14b`/`N23a24b` 사설net으로 완전히 독립).
- **CMFB(Fig.5)**: M37a(gate=Voc)/M37b(gate=Voc_des)가 M38 tail을 공유하는 차동쌍, 양쪽
  부하 M36a/M36b는 미러가 아니라 독립 diode 2개. Voc_des는 M39/M40(PMOS diode 2개
  분압기)가 만드는 저임피던스 노드(소신호 v=0). Voc는 트랜지스터가 아니라 R1/R2(최종출력
  Vom/Vop 평균)가 구동.
- **bias-gen**: `M18_bg`(diode, drain=gate=Vbias1)를 `Iref`(ideal, 1.2µA, Vbias1→gnd,
  사용자가 논문에서 직접 확인한 값)가 구동, 나머지가 Vbias1을 gate로 공유하는 미러.
  `M58`/`M57`(Vbias2 서브체인)은 세션5에 새 theta(`r_bg_vbias2`) 추가로 사이징 gap 해소.
- **CMRR**: open-loop는 물리적으로 수 dB를 못 넘음 — 논문의 94.4dB를 설명하는 건 CMFB
  루프(`telescopic_class_ab_cmfb`, 앵커 148.1dB/166.2dB).
- **Cc=500fF**: ⚠️ 이 값의 출처는 "논문 Section III.C 인용"일 뿐, 이 프로젝트가 실제
  sky130 LUT 기준으로 독립 재도출한 값이 아니다(세션5 초반에 확인, 아직 미해결) —
  `[[feedback_no_paper_values_derive_rationally]]` 원칙대로 다시 봐야 할 후보.

## 작업 파일 위치

- `skills/analog-gmid-design/assets/topology_to_markdown.py` — connectivity 표 생성기.
  topology.json 손댈 때마다 실행할 것.
- `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.md` —
  위 스크립트 산출물(세션5 재생성 완료).
- `workspaces/current-reuse-telescopic-ota-report/rerun_symmetry.py` — symmetry 재생성
  재현 스크립트(branch_symmetric은 이 스크립트가 검증 못 하는 카테고리임에 주의 —
  current_mirror/diff_pair/hub_merge만 자동 탐지).
- `workspaces/current-reuse-telescopic-ota-report/run_harness.py` — 전체 회로 사이징
  실행 스크립트, `optimize_full_circuit_budget()` 단일 호출. **다음 세션 시작점.**
- `workspaces/current-reuse-telescopic-ota-report/pending_topology_corrections.md` —
  정정 대기열 로그(세션5 항목 전부 APPLIED로 종료). 새 정정 생기면 이 패턴 재사용.
- `workspaces/current-reuse-telescopic-ota-report/paper_pages/` — 논문 PDF 렌더링/크롭
  이미지, git 미포함(로컬 전용, 지우지 말 것).
- 논문 원본 PDF: `G:\내 드라이브\work\Todoc\논문모음\A 126uW Current-Reuse Telescopic
  OTA with Class-AB Output Stage.pdf` (18페이지, 텍스트 추출 가능한 건 1-8페이지뿐,
  나머지는 스키매틱 이미지).
- Artifact: `current_reuse_telescopic_ota — connectivity review`
  (https://claude.ai/code/artifact/a00dad7b-e1db-4b28-8c60-748ea76cca45) — **주의**:
  이 artifact는 세션4 시점 topology.json의 스냅샷일 뿐 세션5 정정이 반영 안 됨, "확정"
  문구를 독립 재검증으로 오인하지 말 것(위 세션5 1번 교훈 참고). 다음 세션에서 갱신
  검토 필요.

## 참고 — 사용자 협업 메모리 (자동 메모리 시스템에 저장됨, 요약만)

- 최종 보고는 항상 한글로.
- 상상으로 채우지 말고 근거·실제 확인 후 진행 — **artifact/문서의 "확정" 표기도
  맹신 금지, 그게 어떻게 만들어졌는지(사용자 원문 vs Claude 확대해석) 추적할 것**
  (세션5 신규 교훈).
- topology.json이 유일한 토폴로지 소스 — connectivity는 사용자 전용, role/matching/theta
  같은 메타데이터는 Claude가 분석해서 업데이트 가능.
- 장시간 실행은 `run_in_background: true`.
- 회로도 이미지/PDF 판독은 신뢰 못 함 — `topology_to_markdown.py`로 net 기준 표를 뽑아
  세션에 출력하고 사람이 재확인할 것.
- topology 정정은 대기열에 쌓았다가 "한꺼번에 반영해" 지시가 와야 일괄 반영.
- 논문에 없는 컴포넌트 값은 "논문 인용"만으로 확정 짓지 말 것 — 사용자가 직접 지정하지
  않으면 실제 방법론으로 합리적 값을 도출(세션5 신규, `Cc=500fF` 등 재검토 후보 있음).
- 복잡한 analog 회로 폐형식 재유도는 opus 에이전트(가능하면 git worktree 격리)에 위임이
  효과적.
- git commit 시 heredoc-in-`$()`이 bkit 훅에 막힘 — 파일로 메시지 작성 후 `git commit -F`.
