# 세션 컨텍스트 (최종 갱신: 2026-08-03, 세션 4 끝)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 지금 상태 (다음 세션이 읽어야 할 것 1순위)

- **전부 커밋됨, 클린 상태.** 현재 HEAD: `3e1bcac`(세션 4 커밋, `b63e394` 다음).
- `python skills/analog-gmid-design/assets/sizing_recipe.py` self-test **전체 통과
  (exit 0)** — 세션 3이 남긴 FAIL은 세션 4에서 해소됨.
- `current_reuse_telescopic_ota.topology.json`의 connectivity는 사용자가 논문 원본 PDF를
  직접 재확인해 완전히 검증됨(세션 3~4에 걸쳐). **급한 미해결 TODO 없음** — 아래는
  "하면 좋은 것"이지 "막혀서 못 넘어가는 것"이 아니다.

## 다음 세션에서 하면 좋은 것 (우선순위 순, 급한 건 아님)

1. **전체 회로 사이징 시도**: bias-gen 블록까지 포함해 51개 소자 전부 사용자와 재검증
   완료됐으니, `optimize_full_circuit_budget()`을 이 회로 전체에 실제로 돌려볼 만하다 —
   세션 3까지는 51개 중 일부(6/51)만 하네스가 커버했었다.
2. **Cc/Rz/Iref 값 채우기**: `passive_elements`의 `Rz1`/`Rz2`(nulling resistor)와
   `ideal_sources`의 일부 소자는 값이 미상(`value_ohm`/`value_farad`: null) — 테이프아웃
   전 SPICE로 채워야 한다. `Cc`=500fF, `Iref`=1.2µA는 이미 확정됨.
3. **`symmetry.dispositions` 재확인 습관화**: connectivity가 또 바뀌면 다시 stale해질 수
   있다 — 그때마다 `workspaces/current-reuse-telescopic-ota-report/rerun_symmetry.py`
   패턴(`find_matching_candidates()`/`find_hub_merge_candidates()`/
   `check_symmetry_dispositions()` 재실행)으로 재생성할 것. 손으로 고치지 말 것.
4. **PSRR**: 여전히 order-of-magnitude placeholder. CMRR처럼 sympy 폐형식 재유도가
   필요하면 이번 세션의 `stage1_cmrr_sympy_derivation.py`를 템플릿으로 쓸 수 있다.
5. `docs/03-analysis/analog-topology-json-library.gap-findings.md` §26 — 세션 3/4의
   이력이 아직 이 파일엔 반영 안 됨(do.md에는 일부 반영). 필요해지면 정리.

## 배경 — analog-topology-json-library 기능이란

- **WHY**: topology netlist가 Python 코드 하드코딩이면 재현 불가능, agent마다 해석이
  달라짐 — 그래서 `topology.json` 하나를 유일한 소스로 둔다.
- **핵심 산출물**: `topology.json` 스키마(`netlist`/`symmetry`/`compensation`/
  `passive_elements`/`ideal_sources`/`ports`/`sizing_roles`/`device_roles`) +
  오케스트레이션 레이어(`load_topology`, `run_topology_pipeline`, `save_instance_json`,
  `optimize_full_circuit_budget` 등, 전부 `skills/analog-gmid-design/assets/
  {stick_diagram,sizing_recipe}.py`) + `topology_to_markdown.py`(connectivity 검토용
  표 생성기, 세션 3 신설).
- **권한 경계(중요, 항상 지킬 것)**: `netlist`/`passive_elements`/`ideal_sources`의
  connectivity(`source`/`drain`/`gate`/`terminals`)는 **사용자만 고친다** — Claude는
  절대 임의로 안 바꾸고, 사용자가 논문을 보며 불러주는 정정만 반영한다(대기열에 쌓았다가
  "한꺼번에 반영해"할 때 일괄 처리 — [[batch_topology_corrections]] 메모리 참고).
  반면 `device_roles`/`symmetry.matching_pairs`/`symmetry.dispositions`/
  `sizing_roles` 같은 **역할·메타데이터는 Claude가 connectivity로부터 분석해서
  업데이트해도 된다**(2026-08-03 사용자 명시 지시).
- **관련 문서**:
  - `docs/04-report/analog-topology-json-library.do.md` — 배치 7-5~7-5d 섹션이 최신.
  - `skills/analog-gmid-design/references/topology-extraction-checklist.md` §5 —
    `topology_to_markdown.py` 필수 사용 절차.
  - `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.md`
    — 이 회로의 connectivity 표(net별/소자별), topology.json 볼 때 이것부터 같이 볼 것.

## current_reuse_telescopic_ota 회로 — 지금까지 검증된 핵심 구조

- **1단(입력)**: PMOS 입력쌍(M1a/M1b, tail=Vx=M6∥M7) + NMOS 입력쌍(M4a/M4b, tail=Vy=M5)이
  **같은 입력**(Vip/Vim)을 공유하며 각자 캐스코드(M2a/M2b pmos, M3a/M3b nmos)를 거쳐
  출력노드(Vom1/Vop1)에서 **드레인끼리 합류**한다(직렬 캐스코드 아님 — current-reuse의
  핵심). `M2a.drain==M3a.source`라는 옛 가정은 **틀림**, `M2a.drain==M3a.drain==Vom1`이 맞음.
- **2단(Class-AB 출력) 교차결합**: Vom측 2단 내부노드는 실제로 **Vop1**과 동일 물리노드,
  Vop측 2단 내부노드는 **Vom1**과 동일(1단 차동출력이 반대쪽 2단 바이어스로 넘어감). 옛
  `Vg16`/`Vg26`이라는 net 이름은 완전히 폐기되고 `Vop1`/`Vom1`로 대체됨.
- **CMFB(Fig.5)**: M37a(gate=Voc)/M37b(gate=Voc_des)가 M38 tail을 공유하는 차동쌍, 양쪽
  부하 M36a/M36b는 **미러가 아니라 독립 diode 2개**. Voc_des는 M39/M40(PMOS diode 2개
  분압기)가 만드는 저임피던스 노드(소신호 v=0). Voc는 트랜지스터가 아니라 R1/R2(최종출력
  Vom/Vop 평균)가 구동.
- **bias-gen**: `M18_bg`(diode, drain=gate=Vbias1)를 `Iref`(ideal, 1.2µA, Vbias1→gnd)가
  구동, 나머지(M60/M61/M6/M8/M13/M22/M17)가 Vbias1을 gate로 공유하는 미러. M64가 diode
  (M63가 아님), M58/M63의 source는 각각 Vx/Vy(1단 tail과 공유). `Vbias_p`라는 net은
  소멸하고 `Vbias2`로 흡수됨.
- **CMRR**: open-loop(`telescopic_class_ab`)은 물리적으로 수 dB를 못 넘음(두 가지가 Vom1/
  Vop1에서 병렬 합류해 서로의 CM floor에 수렴) — 논문의 94.4dB를 설명하는 건 CMFB 루프
  (`telescopic_class_ab_cmfb`, 앵커 148.1dB/166.2dB).

상세 근거는 전부 `topology.json`의 `_correction_log_1`~`_correction_log_7`,
`sizing_recipe.py`의 `_cmrr_telescopic_class_ab*`/`_cmfb_amp_gain_diode_load` docstring,
`workspaces/current-reuse-telescopic-ota-report/spice/*.py`(sympy/ngspice 재현 스크립트)에
있음 — 이 파일에서 다시 요약 안 함.

## 작업 파일 위치

- `skills/analog-gmid-design/assets/topology_to_markdown.py` — connectivity 표 생성기.
  topology.json 손댈 때마다 실행할 것.
- `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.md` —
  위 스크립트 산출물(최신 connectivity 표, 자동 플래그 0건).
- `workspaces/current-reuse-telescopic-ota-report/rerun_symmetry.py` — symmetry 재생성
  재현 스크립트.
- `workspaces/current-reuse-telescopic-ota-report/spice/` — CMFB/CMRR sympy 유도 +
  ngspice 교차검증 스크립트 전부(cmfb_amp_gain_sympy_derivation.py,
  cmfb_cmrr_ngspice_crosscheck.py, stage1_cmrr_sympy_derivation.py,
  stage1_cmrr_ngspice_crosscheck.py).
- `workspaces/current-reuse-telescopic-ota-report/pending_topology_corrections.md` —
  세션 4에서 쓴 정정 대기열 로그(전부 APPLIED 상태로 종료됨, 다음 세션에 새 정정이
  생기면 이 파일 패턴을 그대로 재사용할 것).
- `workspaces/current-reuse-telescopic-ota-report/paper_pages/`,
  `fig*_zoom*.png` — 논문 PDF 렌더링/크롭 이미지. **git에는 안 올라감**(`.gitignore`,
  저작권 있는 논문 페이지 복제본이라 세션 4에 제외 결정) — 로컬에만 있으니 필요하면
  재사용, 지우지 말 것.

## 참고 — 사용자 협업 메모리 (자동 메모리 시스템에 저장됨, 요약만)

- 최종 보고는 항상 한글로.
- 상상으로 채우지 말고 근거·실제 확인 후 진행.
- topology.json이 유일한 토폴로지 소스 — 단, connectivity는 사용자 전용, role/matching
  메타데이터는 Claude가 분석해서 업데이트 가능(위 "권한 경계" 참고, 세션 4 신규).
- 장시간 실행은 `run_in_background: true`.
- 회로도 이미지/PDF 판독은 신뢰 못 함 — 반드시 `topology_to_markdown.py`로 net 기준 표를
  뽑아 세션에 출력하고 사람이 재확인할 것.
- topology 정정은 대기열에 쌓았다가 "한꺼번에 반영해" 지시가 와야 일괄 반영(세션 4 신규
  워크플로우, `pending_topology_corrections.md` 패턴).
- 복잡한 analog 회로 폐형식 재유도는 opus 에이전트(가능하면 git worktree 격리)에 위임이
  효과적 — 세션 3 CMFB, 세션 4 CMRR 둘 다 이 방식으로 성공.
- git commit 시 heredoc-in-`$()`이 bkit 훅에 막힘 — 파일로 메시지 작성 후 `git commit -F`.
