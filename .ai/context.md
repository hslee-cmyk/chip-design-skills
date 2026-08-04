# 세션 컨텍스트 (최종 갱신: 2026-08-04, 세션 6 끝)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 지금 상태 (다음 세션이 읽어야 할 것 1순위)

- **커밋 안 됨 — working tree에 변경사항 많음.** HEAD는 `35023ea`(세션5 핸드오프 커밋)에
  머물러 있고, 세션6의 모든 작업은 uncommitted. `git status --short`로 확인:
  - 수정: `sizing_recipe.py`, `stick_diagram.py`,
    `library/current_reuse_telescopic_ota.topology.json`,
    `library/{folded_cascode,nmcnr_amplifier,two_stage_ota}.topology.json`
  - 신규: `workspaces/current-reuse-telescopic-ota-report/spice/
    vg15_vop1_kcl_sympy_derivation.py`,
    `workspaces/current-reuse-telescopic-ota-report/structural_symmetry_probe.py`
  - **다음 세션은 커밋할지 먼저 사용자에게 물어볼 것**(세션6에서 커밋 지시 없었음).
- **self-test는 마지막까지(파일 끝, 3142줄) 전부 통과**(`selftest_session6f.log`,
  exit 0, Traceback/AssertionError 0건) — 오늘 만든 엔진 변경(A_signed, current_mirror/
  current_matched 분리, InfeasibleSizingError) 전부 회귀 없음 확인됨.
- **`run_harness.py`는 세션6의 모든 수정을 반영해서 아직 재실행 안 됨** — 세션5 이후
  세션6 초반까지 여러 차례 실행했지만 그때마다 새 버그가 나와서 고치고 다시 돌리는
  과정을 반복했다(아래 "세션6에서 발견·수정한 것" 참고). **마지막(가장 심각한) 수정인
  branch_symmetric 전면 재분류 이후로는 harness를 아직 안 돌려봤다** — 다음 세션
  최우선 작업.
- **직전 작업 중단 지점**: `nmcnr_amplifier.topology.json`의 `branch_symmetric`
  사용례(`{M104,M105}`, `{M106,M107}`)를 감사하던 중 사용자가 이 핸드오프 작성을
  요청해 중단됨 — 파일은 읽었고(아래 참고), 아직 손 안 댐. 다음 세션에서 이어서 할 것
  (아래 "미완료 작업" 1번).

## 세션 6에서 발견·수정한 것 (시간순, 전부 사용자와의 대화로 하나씩 파생됨)

### 1. Vg15/Vop1 DC centering — 사용자의 "swing 최대화" 가설 검증
사용자가 "M11a-chain과 M13-chain 전류를 같게 해야 Vom이 안 치우친다"는 가설을 제기.
검토 결과 그 가설의 인과관계는 틀렸지만(M9a/M9b 자신의 전류는 그 두 chain이 아니라
K_replica/kcl_battery_M9b로 결정, M13-chain 전류는 그 KCL에 아예 안 들어감 — Fig.7b가
두 chain 전류가 다르다고 실측 확인한 것과 일치), **"swing 최대화=DC bias centering"
원리 자체는 논문 Section II.B가 명시**("gate of M15 pushed to ~1.3V, M16 to ~0.5V" —
합=VDD 정확히 센터링)했음을 논문 PDF 직접 재확인(페이지 1-3, 텍스트 추출)으로 확인.
**신설**: `sizing_recipe.py`에 `rail_referenced_voltage`/`battery_centering_deviation`
metric 2종 추가(LUT VGS 역산으로 Vg15/Vop1 실제 DC 레벨 계산, `|Vg15+Vop1-VDD|` 편차를
constraint로 검증) — M11a=M13 강제 대신 논문 설계 의도를 직접 검증하는 쪽으로 구현.
tolerance(0.15V)는 정직한 한계로 문서화(SPICE 검증 전).

### 2. KCL 엔진의 진짜 버그 발견 — `kcl_battery_M9b`/`kcl_battery_M18b` 공식이 틀렸었다
사용자 질문("M10과 M8은 같은 branch 전류인데 독립적이야?")을 계기로 Vg15/Vop1 노드의
실제 KCL을 `load_topology()` connectivity만으로(손타이핑 없이) sympy로 처음부터
재유도(`workspaces/.../spice/vg15_vop1_kcl_sympy_derivation.py`, 재현 가능) —
`I(M9b)=I(M8)-I(M9a)`, `I(M10)=I(M8)+I(M1b)-I(M4b)`가 정답인데, 기존 `kcl_battery_M9b`
theta는 `ID(M9b)=ID(M11a체인)+ID(M9a)`(틀림 — 근거였던 "Vg15 노드=M11b.drain/M9a.drain/
M9b.drain 3단자"라는 주장 자체가 실제 netlist와 다름, M11b.drain='N11b'·M9a.drain='Vop1'
로 확인됨)를 쓰고 있었다. **이 틀린 공식은 세션5까지의 모든 harness 실행에 실제로
영향을 미쳤다**(bounds=[1,1] 고정 theta라 grid search 매 조합마다 적용됨).
**엔진 신설**: `sizing_recipe.py`에 부호 있는 KCL 합을 표현하는 새 feed 타입
`"A_signed"`(`_feed_root_signed_sum()`) 추가 — 기존 `"A"` 타입은 양수 계수 합만
지원해서 뺄셈을 표현 못 했음.
**topology.json 반영**: `kcl_battery_M9b`/`kcl_battery_M18b`를 `A_signed`로 정정
(`ID(M9b)=ID(M8)-ID(M9a)`, `ID(M18b)=ID(M17)-ID(M18a)`), 옛 자유 theta
`r_sink_vop1vom1`(M10/M19)을 삭제하고 고정 KCL theta `kcl_sink_M10`/`kcl_sink_M19`로
대체(자유 theta 13→12개, 이후 아래 4번에서 다시 13개로).

### 3. `r_classab_src`(M8/M13/M22/M17 한 theta) 분리 — 구조적 역할이 다름
사용자 지적("M8 branch와 M13 branch가 mirror구조라고 같은 전류를 가정하는 건 너무
단순화")을 계기로 재검토: M8/M17은 Vg15/Vg25(Monticelli 배터리 노드, 신호경로 규모)를
직접 공급하지만 M13/M22는 다이오드 체인(M14a/M14b, M23a/M24b)만 먹이는 하우스키핑
소자로 역할이 다름. **`r_classab_src`를 `r_classab_battery`(root=[M8,M17], 기존
bounds)와 `r_classab_diode_src`(root=[M13,M22], 하우스키핑 규모 bounds)로 분리**
(자유 theta 12→13개).

### 4. `matching_pairs`의 `current_mirror` 오분류 발견 → 새 kind `current_matched` 도입
위 3번을 반영하려는데 `symmetry.matching_pairs`에 `{M8,M13}`/`{M22,M17}`가
`current_mirror`(엔진상 "같은 전류"로 KCL 강제 병합)로 선언돼 있어 즉시 크래시("직렬
스택에 서로 다른 seed 전류가 섞여 있다"). 근본 원인: **"같은 gate 공유=같은 전류"라는
잘못된 가정이 `matching_pairs`에도 그대로 박혀 있었다**(disposition에도 "이미 진짜
매칭쌍"이라고 잘못 적혀 있었음). 사용자와 논의 끝에 **kind를 둘로 분리**:
- `current_mirror`(신규 의미): 구조적 사실만(같은 gate 공유) — **KCL 강제 병합 안 함**
  (`_kcl_pairs`에서 `branch_symmetric`과 함께 제외), `auto_mirror_ratios`도 이제 안 씀.
- `current_matched`(신규 kind): 옛 `current_mirror`가 하던 역할 그대로 승계(진짜 같은
  전류, KCL 강제 병합 + `auto_mirror_ratios` 1:1 기본값).
**영향 범위 전수 조사**: `sizing_recipe.py`(`_kcl_pairs`/`auto_mirror_ratios`),
`stick_diagram.py`(`select_layout_tool()` kind 화이트리스트, `audit_row_split()`의
`interdig_required` 판정) 전부 수정. **다른 3개 topology 파일**(folded_cascode,
nmcnr_amplifier, two_stage_ota)의 기존 `current_mirror`(전부 진짜 미러쌍)도
`current_matched`로 이름만 옮겨 기존 동작 보존(동작 변경 없음, self-test로 회귀 확인).
`current_reuse_telescopic_ota`엔 `{M8,M17}`/`{M13,M22}` current_matched +
`{M18_bg,M8,M13,M17,M22,M60,M61}`(M6 제외 — L_role이 다름) 구조적 current_mirror 신설.

### 5. 전역 구조 대칭 자동 탐지 함수 신설 — `find_structural_symmetry_candidates()`
사용자 질문("topology에서 좌우/상하 대칭을 판별하도록 확장할 수 없나?")을 계기로
`stick_diagram.py`에 신설(`find_matching_candidates()`류가 "같은 net 하나 공유"라는
국소 신호만 찾는 것과 달리, 이건 "netlist 전체를 net 재라벨링으로 자기 자신에 사상하는가"
라는 전역 구조/graph automorphism을 찾는다). `propagate_topology_forced_currents()`와
같은 고정점 반복 스타일. 두 transform:
- `"mirror"`(좌우): kind 보존, differential I/O(Vip↔Vim, Vop↔Vom) 시드에서 전파.
- `"dual"`(상하/극성): kind 반전(pmos↔nmos), vdd↔gnd 시드에서 전파.
**실제 회로에 돌려 검증**(`workspaces/.../structural_symmetry_probe.py`, 재현 가능):
mirror pass는 오늘 손으로 찾은 16개 좌우쌍을 **전부 정확히 재현**(conflicts=0,
unresolved=0). dual pass는 부분적(1단 diff pair·bias-gen 서브트리는 맞지만, Vop1/Vom1에
dual 짝 없는 소자(M9a/M10, M18a/M19)가 "단서 1개짜리끼리 우연히 매칭"되는 오탐 발생 —
라운드 내 "단자 많이 아는 소자부터 처리"로 정렬 순서를 바꿔봤지만 원천적으로 안 없어져서,
`low_confidence_pairs`(단서<2개) 필드로 정직하게 표시하는 쪽으로 마무리(사람이 반드시
재검토, 억지로 없애지 않음).

### 6. mirror 패스로 실제 stale/누락 `matching_pairs` 발견·수정
mirror 패스 결과를 현재 `matching_pairs`와 대조해서:
- **stale 4건**(세션5 `_correction_log_8`이 "재확인 필요"로 남겨뒀는데 방치돼 있었음):
  `{M11a,M14a}`→`{M11a,M20a}`, `{M11b,M14b}`→`{M11b,M20b}`, `{M20a,M24b}`→
  `{M14a,M23a}`, `{M20b,M23a}`→`{M14b,M24b}`.
- **누락 1건**: `{M10,M19}` — 신규 추가(current_matched, kcl_sink 값과 일치).
- **disposition도 stale**: Vbias1/Vbias4 disposition의 "이미 매칭쌍으로 기록됨" 주장이
  실제 파일과 안 맞았음 — 둘 다 정정.

### 7. `branch_symmetric` 전면 재감사 — 이 회로엔 0건으로 귀결
사용자 질문("진짜 좌우 대응이면 전류도 같아야 하지 않나? branch_symmetric 용도가
모호하지 않나?")을 계기로 남은 `branch_symmetric` 11건 전부를 theta 엔진으로 추적:
**전부 이미 수학적으로 전류가 강제되고 있었다**(compensation 그룹 공유, replica theta,
또는 KCL 직렬 사슬을 통한 전이적 강제). 전부 `current_matched`로 재분류
(M2a/M2b, M3a/M3b, M11a/M20a, M11b/M20b, M14a/M23a, M14b/M24b, M15/M25, M16/M26,
M9a/M18a, M9b/M18b, M36a/M36b). 부수 발견: `{M12,M10}`/`{M21,M19}`(옛 branch_symmetric)
는 애초에 정의 위반이었음(branch_symmetric="공유 노드 없음"이 정의인데 이 넷은
source=gnd·gate=Vbias4 **두 노드**를 공유) — `{M10,M12,M19,M21}` 구조적 current_mirror
하나로 재선언.

**결론(사용자와 합의)**: `current_reuse_telescopic_ota`의 "완전 대칭이어야 한다" 설계
원칙 하에서는, 진짜 좌우(mirror) 쌍이 전류가 다를 논리적 여지가 없다(다르면 그건
의도된 비대칭이 아니라 엔진 설계 누락 — 오늘 M11a/M20a가 실제 사례). **`branch_symmetric`
의 실질적 역할은 "발견됐지만 아직 전류 관계를 theta로 추적/확정 안 한 pending 상태"** —
`find_structural_symmetry_candidates(mirror)`가 새 후보를 찾으면 일단 이 kind로 표시하고,
theta 엔진 추적 후 강제되는 게 확인되면 `current_matched`로 "졸업"시키는 절차적 카테고리로
보는 게 맞다는 결론(아직 어디에도 문서화 안 함 — 다음 세션 후보).

**미완료**: 이 결론을 다른 topology 파일(`nmcnr_amplifier`의 `{M104,M105}`/`{M106,M107}`)
에도 적용해 검증해보자는 논의 중 중단(아래 "미완료 작업" 1번).

## 미완료 작업 (다음 세션 순서대로)

1. **`nmcnr_amplifier.topology.json`의 `branch_symmetric` 감사 마무리**(중단 지점).
   이미 읽은 내용: `{M104,M105}`/`{M106,M107}`이 `branch_symmetric`으로 선언돼 있고,
   그 자체 comment(37행)가 이미 "M104/M105, M106/M107은 자동탐지는 current_mirror로
   잡혔지만 VB2/VB3가 netlist 밖 외부 바이어스라 진짜 미러가 아니다 — 폴디드 캐스코드의
   대칭된 두 branch(레이아웃 매칭 필요하되 신호 관계상 미러 아님)"라고 명시적으로
   근거를 남겨뒀다 — **이 회로는 `sizing_roles`/`device_roles`가 아직 `null`**(58행
   `_device_roles_comment` 참고, "이번 세션 스코프는 topology 확정까지, 사이징은 다음
   배치")이라 **theta로 전류가 강제되는지 자체를 추적할 방법이 아직 없다** — 즉
   current_reuse_telescopic_ota와 달리 "엔진이 이미 강제하고 있었는지" 감사가 원천적으로
   안 되는 상태. `M102`/`M103`(diff_pair, compensation.stage_devices[0] 공유)이 
   `M104`/`M105`(각자 tail, VB2 고정 게이트)의 전류를 결정할 텐데, `M104`/`M105`
   자체의 개별 sizing 메커니즘이 아직 없다 — **이 회로는 branch_symmetric이 정말
   "다른 이유"(사이징 미완성이라 확인 불가)로 남아있는 사례일 수 있다**, 세션6 결론
   ("pending 상태" 재해석)과 맞는지 다음 세션에서 판단할 것.
2. **`run_harness.py` 재실행**(세션6의 모든 수정 반영 후 처음, 10분+ background 필수) —
   `optimize_full_circuit_budget()`이 실제로 완주하는지 확인. 자유 theta는 지금
   13개(세션5 끝과 같은 개수, 다만 구성은 달라짐: `r_sink_vop1vom1` 삭제, `r_classab_src`
   → `r_classab_battery`+`r_classab_diode_src`로 분리). `InfeasibleSizingError`가 음수
   KCL 조합을 제대로 건너뛰는지도 이번이 처음(도입 이후 harness 자체를 아직 안 돌려봄).
3. 완주하면 `result["audit_ok"]`/`result["metrics"]`(특히 세션6에서 추가한
   `classab_centering_dev_v` constraint) 확인 → 세션4 핸드오프 원래 "다음 단계"(Cc/Rz/
   Iref 값 채우기, PSRR 폐형식 재유도)로 이어가면 됨.
4. (선택) 세션6 결론 7번("branch_symmetric=pending 상태")을 `do.md`나 skill 문서에
   원칙으로 남길지 — 사용자가 제안했던 항목, 아직 미결정.
5. (선택) `find_structural_symmetry_candidates()`의 `"dual"` transform 오탐(low_confidence
   로 표시는 되지만 근본적으로 제거는 안 됨) — 더 나은 휴리스틱이 필요하면 재검토.

## 세션6에서 새로 생긴 엔진 개념 (다음 세션이 반드시 알아야 할 것)

- **`A_signed` feed type**(`sizing_recipe.py`): `{"type":"A_signed","root":...,
  "terms":[{"device":...,"sign":±1},...]}` — 부호 있는 KCL 합. 기존 `"A"`(전부 +부호
  합)의 일반화.
- **`InfeasibleSizingError`**(`ValueError` 상속, `sizing_recipe.py`): theta 격자점이
  물리적으로 불가능한 상태(예: `A_signed` 뺄셈이 음수)를 만들면 이 예외 — grid search
  루프가 이걸 "이 조합만 건너뛰기"로 처리(constraints 위반과 동일 취급), 그 외
  `ValueError`(선언 누락 등)는 여전히 즉시 크래시.
- **`current_mirror` vs `current_matched`**(matching_pairs kind, `sizing_recipe.py`+
  `stick_diagram.py`): `current_mirror`=구조적 사실(같은 gate 공유)만, KCL 병합 안 함.
  `current_matched`=진짜 같은 전류, KCL 강제 병합 — **옛 `current_mirror`의 엔진 역할은
  이제 `current_matched`가 담당**. 다른 topology 파일 작성 시 이 구분 반드시 지킬 것.
- **`find_structural_symmetry_candidates(transistors, seed_net_pairs, transform)`**
  (`stick_diagram.py`): 전역 좌우/상하 대칭 자동 탐지. `transform="mirror"|"dual"`.
  반환 `StructuralSymmetryVerdict(net_map, device_map, conflicts, unresolved,
  low_confidence_pairs)`. mirror는 신뢰도 높음(이 회로에서 100% 재현), dual은 실험적
  (검증 없이 신뢰 금지, 반드시 `low_confidence_pairs` 확인).
- **`branch_symmetric`은 "pending" 상태로 재해석**됨(위 7번 결론) — 새 topology
  작성 시 이 kind를 최종 분류로 쓰지 말고, theta 엔진 추적 후 `current_matched`로
  졸업시킬지부터 검토할 것.

## 배경 — analog-topology-json-library 기능이란 (세션5와 동일, 참고용 유지)

- **WHY**: topology netlist가 Python 코드 하드코딩이면 재현 불가능, agent마다 해석이
  달라짐 — 그래서 `topology.json` 하나를 유일한 소스로 둔다.
- **권한 경계(중요, 항상 지킬 것)**: `netlist`/`passive_elements`/`ideal_sources`의
  connectivity는 **사용자만 고친다**. `device_roles`/`symmetry.matching_pairs`/
  `symmetry.dispositions`/`sizing_roles`(theta 포함) 같은 **역할·메타데이터는 Claude가
  분석해서 업데이트해도 된다** — 세션6 전체가 이 경계 안에서 진행됨(connectivity는
  한 번도 안 건드림, 전부 메타데이터/엔진 수정).
- 논문에 없는 값은 "논문 인용"만으로 확정 짓지 말 것 — 세션6도 이 원칙 지킴(Vg15/Vop1
  centering metric에서 논문의 1.3V/0.5V 절대값 대신 "합=VDD" 위상적 관계만 가져옴).

## 작업 파일 위치

- `skills/analog-gmid-design/assets/sizing_recipe.py` — 세션6 대폭 수정(위 참고).
- `skills/analog-gmid-design/assets/stick_diagram.py` — 세션6 대폭 수정(위 참고).
- `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json`
  — 세션6 대폭 수정. `theta` 13개(구성 변경), `matching_pairs` 전면 재분류.
- `workspaces/current-reuse-telescopic-ota-report/spice/
  vg15_vop1_kcl_sympy_derivation.py` — Vg15/Vop1 KCL sympy 재유도(재현 가능, 다른
  노드에도 재사용 가능한 일반 구조).
- `workspaces/current-reuse-telescopic-ota-report/structural_symmetry_probe.py` —
  `find_structural_symmetry_candidates()` 실제 회로 검증 스크립트.
- `workspaces/current-reuse-telescopic-ota-report/rerun_symmetry.py` — symmetry
  재생성 재현 스크립트. 세션6에도 여러 번 재실행, 마지막까지 `ok=True`.
- `workspaces/current-reuse-telescopic-ota-report/run_harness.py` — 전체 회로 사이징
  실행 스크립트. **다음 세션 최우선 시작점**(위 "미완료 작업" 2번).
- 논문 원본 PDF: `G:\내 드라이브\work\Todoc\논문모음\A 126uW Current-Reuse Telescopic
  OTA with Class-AB Output Stage.pdf` — 세션6에 페이지 1-3(Table I, Section II.B/C/D
  본문) 텍스트 재추출해 Input CM range([576.5mV,900.1mV], VDD/2가 상한이지 중심이 아님)
  등 근거로 활용.

## 참고 — 사용자 협업 메모리 (자동 메모리 시스템에 저장됨, 요약만)

- 최종 보고는 항상 한글로.
- 상상으로 채우지 말고 근거·실제 확인 후 진행 — artifact/문서의 "확정" 표기도 맹신 금지.
- topology.json이 유일한 토폴로지 소스 — connectivity는 사용자 전용, role/matching/theta
  같은 메타데이터는 Claude가 분석해서 업데이트 가능.
- 장시간 실행은 `run_in_background: true`.
- 회로도 이미지/PDF 판독은 신뢰 못 함 — connectivity는 `topology_to_markdown.py`로
  net 기준 표를 뽑아 확인. 단, 논문 **본문 텍스트**(스키매틱 아님) 추출은 신뢰 가능
  (세션6에서 Table I/Section II.B 근거로 실제 활용, PDF 텍스트 추출 페이지 1-8).
- topology 정정은 대기열에 쌓았다가 "한꺼번에 반영해" 지시가 와야 일괄 반영
  (connectivity에만 해당 — 세션6은 메타데이터/엔진만 다뤄서 이 규칙 적용 안 됨).
- 논문에 없는 컴포넌트 값은 "논문 인용"만으로 확정 짓지 말 것 — 위상적/구조적 관계는
  가져오되 절대값은 독립 도출.
- 복잡한 analog 회로 폐형식 재유도는 opus 에이전트(가능하면 git worktree 격리)에 위임이
  효과적(세션6엔 발생 안 함 — sympy 직접 재유도로 충분했음).
- git commit 시 heredoc-in-`$()`이 bkit 훅에 막힘 — 파일로 메시지 작성 후 `git commit -F`.
- **세션6 신규**: 사용자가 반복 확인을 요청하지 않는 한, 이미 근거를 충분히 확보한
  분석 결론(connectivity 아닌 메타데이터/엔진 영역)은 다시 물어보지 말고 바로 실행할 것
  — "이건 네가 판단할 수 없는 문제인가?"라는 직접 피드백 받음.
