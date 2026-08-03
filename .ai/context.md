# 세션 컨텍스트 (최종 갱신: 2026-08-03, 세션 4)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 세션 4 완료 요약 (2026-08-03) — 세션 3의 self-test FAIL 해소 + connectivity 대량 정정

세션 3이 마지막에 남긴 **self-test FAIL**(`M2a.drain==M3a.source` assert, 옛 직렬 캐스코드
가정)을 이번 세션에서 해소했다. 그 과정에서 사용자가 논문 원본 PDF를 직접 보며 한 문장씩
불러준 정정을 대기열(`workspaces/current-reuse-telescopic-ota-report/
pending_topology_corrections.md`)에 쌓았다가 "한꺼번에 반영해" 지시마다 일괄 반영하는
방식으로 진행했다(신규 워크플로우 — [[batch_topology_corrections]] 메모리 참고).

**topology.json 변경(전부 `_correction_log_6`/`_correction_log_7` + pending 파일에 근거
기록)**:
1. M14b.source: N14a14b → gnd (독립 diode 2단 스택으로 정정)
2. M17↔M22 drain 스왑
3. **교차결합 확정**: 옛 Vg16(Vom측 2단 내부노드)=Vop1, 옛 Vg26(Vop측)=Vom1 — net 이름
   자체가 Vom1/Vop1로 완전 대체됨
4. bias-gen 블록(M60/M61/M64/M63/M58/M57/M68) 전면 재구성 — M64↔M63 diode 위치 반전,
   M58/M63 source가 각각 Vx/Vy(1단 tail)로, Vbias_p net 소멸(Vbias2로 흡수)
5. 신규 `ideal_sources` 스키마 추가(Iref, 1.2µA, `implementable: false`) — passive_elements와
   달리 절대 구현되지 않는 모델링 소자를 스키마 레벨에서 구분
6. 신규 `ports` 필드(Vip/Vim/Vom/Vop의 differential I/O 역할 문서화)
7. `symmetry.dispositions`를 `find_matching_candidates()`/`find_hub_merge_candidates()`
   재실행으로 재생성(손 작성 아님, 재현 스크립트: `workspaces/current-reuse-telescopic-ota-
   report/rerun_symmetry.py`)

결과: `topology_to_markdown.py` 자동 플래그 **0건**(고아/무구동 net 전부 해소).

**CMRR/CMFB 폐형식 재유도(opus 배경 에이전트 위임, git worktree 격리)**:
- self-test assert의 stale 위상 가정(`M2a.drain==M3a.source`)을 5개 그룹의 실제 위상
  검증으로 교체
- `_cmrr_telescopic_class_ab()`의 숨은 버그 발견: 캐스코드 부스팅 계수에 입력쌍 gm이 아니라
  **캐스코드 소자의 gm**이 맞았음(ngspice 대조 오차 11.95dB→0.80dB)
- 덤으로 `_cmfb_amp_gain_5t_replica()`(세션3 산출물)도 topology.json의 `_correction_log_5`
  (M36a/M36b는 미러가 아니라 독립 diode)를 코드가 못 따라가고 있던 걸 발견해 `_cmfb_amp_
  gain_diode_load()`로 교체. CMFB 포함 CMRR 앵커 148.1dB/166.2dB로 갱신(구 104.6/122.6dB
  폐기)
- sympy 정확해 + ngspice 교차검증 모두 통과, topology.json은 읽기 전용으로 유지(byte-
  identical 확인)
- 신규 파일: `workspaces/current-reuse-telescopic-ota-report/spice/stage1_cmrr_sympy_
  derivation.py`, `stage1_cmrr_ngspice_crosscheck.py`

**최종 상태**: `python skills/analog-gmid-design/assets/sizing_recipe.py` self-test
**전체 통과(exit 0)**. 이 세션에서 `b63e394` 이후 전부 커밋(사용자 지시, 2026-08-03).

## 다음 세션 참고 (급한 TODO 없음, 아래는 알아두면 좋은 것)

- `symmetry.dispositions`는 이번 세션 변경 시점마다 재생성했지만, 앞으로 connectivity가
  또 바뀌면 다시 stale해질 수 있다 — `rerun_symmetry.py` 패턴으로 재확인 습관화할 것.
- Cc/Rz(Miller 보상)와 Iref(마스터 레퍼런스 전류원)는 값 일부가 미상(`value_ohm`/
  `value_farad`: null, Rz 특히) — 테이프아웃 전 SPICE로 채울 것.
- bias-gen(M60/M61/M64/M63/M58/M57/M68/M18_bg/M66/M68)이 사용자와 직접 재검증됐으니,
  이제 이 값들을 활용한 사이징(`optimize_full_circuit_budget()` 전체 회로 실행)을
  시도해볼 만하다 — 세션 3까지는 51개 소자 중 일부(6/51)만 하네스가 커버했었다.

1. **먼저 `python sizing_recipe.py`(`skills/analog-gmid-design/assets/`)를 다시 돌려서
   정확한 실패 지점을 재확인할 것.**
2. 이 assert 자체가 **옛(틀린) 위상 가정**(M2a.drain→M3a.source 직렬)을 전제로 만들어진
   것이므로 삭제/정정 대상이다. 그런데 **더 중요한 문제**: `_cmrr_telescopic_class_ab()`/
   `_cmrr_telescopic_class_ab_cmfb()`의 `Kp_prime = gmcp/(gdsp1*gdsp2)`
   (캐스코드 출력임피던스 부스팅 공식)도 "M2a가 M1a 위에 직렬로 쌓여 캐스코드 부스팅을
   만든다"는 **같은 틀린 가정**으로 유도됐을 가능성이 높다 — 지금 밝혀진 실제 구조(M2a/M3a
   drain이 Vom1에서 직접 합류, PMOS 경로와 NMOS 경로가 독립적으로 출력에 전류를 밀어넣는
   "current-reuse" 구조)에서는 이 공식이 안 맞을 수 있다. **CMRR 폐형식을 다시 한번(세
   번째) 재검토해야 할 가능성이 크다** — 이번엔 sympy로 M1a-M2a(PMOS 경로)와 M4a-M3a
   (NMOS 경로)가 Vom1에서 합류하는 정확한 소신호 회로를 처음부터 다시 세워야 한다.
3. 이 재검토 전에 **`topology_to_markdown.py`를 반드시 먼저 실행**해서 최신 connectivity를
   한 번 더 눈으로 확인할 것(아래 "신규 도구" 참고) — 이미지 판독 오류가 이번 세션에만
   최소 4~5건 나왔다.
4. bias-gen(M18_bg/M60/M61/M64/M63/M58/M57/M66/M68)은 이번 세션에 **재검증 안 함** —
   CMFB 에이전트가 M63/M64 근처를 스쳤을 수 있으나 사람이 직접 확인한 적 없음. `Vbias3`
   net에 `M63.drain`/`M63.gate`/`M64.gate`가 몰려있는 게 topology.md 표에서 보이는데,
   이게 맞는지 다음 세션에서 확인 필요.
5. PSRR은 이번 세션에도 손 안 댐 — 여전히 order-of-magnitude placeholder.
6. **아무것도 커밋 안 됨** — `b63e394`(지난 세션 커밋, CMFB 1차 오류 버전) 이후 전부
   working tree에만 있다. self-test가 다시 통과할 때까지는 커밋하지 말 것.

## 배경 — analog-topology-json-library 기능이란

- **WHY**: topology netlist가 Python 코드 하드코딩이라 재현 불가능, agent마다 해석이
  달라짐.
- **핵심 산출물**: `topology.json` 스키마(netlist/symmetry/compensation/passive_elements
  + sizing_roles/device_roles) + 오케스트레이션 레이어(`load_topology`,
  `run_topology_pipeline`, `save_instance_json`, `optimize_full_circuit_budget` 등,
  전부 `skills/analog-gmid-design/assets/{stick_diagram,sizing_recipe}.py`) +
  **신규(2026-08-03) `topology_to_markdown.py`**(connectivity 검토용 표 생성기).
- **관련 문서**:
  - `docs/03-analysis/analog-topology-json-library.gap-findings.md` §26 — 이번 세션
    미반영(아래 이력만 do.md에 반영됨, gap-findings.md는 다음 세션에서 정리 필요).
  - `docs/04-report/analog-topology-json-library.do.md` — 배치 7-5~7-5d 섹션이 최신
    (2026-08-03 세션 3 업데이트가 이 파일 맨 아래 근처, "배치 7-5 최종 실행 증거" 섹션
    바로 뒤에 추가됨).
  - `skills/analog-gmid-design/references/topology-extraction-checklist.md` §5 —
    `topology_to_markdown.py` 필수 사용 절차 신규 반영.
  - `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.md`
    — **신규**, 이 회로의 connectivity 표(net별/소자별). topology.json 볼 때 이것부터
    같이 볼 것.

## 이번 세션(세션 3) 진행 이력 — 매우 길었음, 순서대로

### 1단계 — CMRR 근사식 재유도 결과 검증 + 배경 프로세스 확인
지난 세션(세션 2)이 커밋한 `b63e394`(CMFB 포함 CMRR, -0.69dB→86dB)을 사용자가 "완전히
파악한 거지?"라고 확인 요청. 정직하게 "Fig.5 CMFB만 이미지로 확인했고 나머지 섹션(2단
Class-AB/bias-gen)은 재확인 안 했다"고 답변.

### 2단계 — 사용자가 논문 원본 PDF 제공, Fig.5 재확인 → CMFB netlist 오류 발견
사용자가 `G:\내 드라이브\work\Todoc\논문모음\A 126uW Current-Reuse Telescopic OTA with
Class-AB Output Stage.pdf` 경로와 Fig.5 이미지를 제공. 확대해서 보니 `b63e394`이 M36a/M36b
관계를 잘못 읽었음이 드러남(미러가 아니라 독립 diode 2개). 이 발견을 CMFB 재유도 배경
에이전트(opus)에 위임 → PDF **벡터 좌표 직접 추출**(PyMuPDF `get_drawings()`)로 재확정,
CMRR -0.69dB → **122.88dB**. 상세: do.md 배치 7-5c 섹션(위 §1898줄 이전, "배치 7-5c" 검색).
이 에이전트가 자체적으로 **또 다른 오류**(Fig.2의 `Vom1`이 `M1a.drain`이 아니라
`M2a.drain=M3a.drain`)를 발견했지만, 동시 편집 충돌을 감지하고 그 부분은 안 건드림
(`TOPO_OVERRIDE`로 우회) — 보고만 하고 사람에게 넘김.

### 3단계 — 사용자와 함께 2단 Class-AB netlist 전체를 실시간으로 재검증 (세션의 핵심)
에이전트가 CMFB를 고치는 동안, 사용자가 논문 Fig.1을 직접 보면서 **한 문장씩** 실제
connectivity를 불러주고 그걸 topology.json에 즉시 반영하는 방식으로 진행(이미지를 내가
스스로 재판독하는 대신 사용자가 정답을 불러줌 — 이미지 인식 신뢰 못 한다는 게 이번 세션의
핵심 교훈, 아래 "신규 도구/교훈" 참고). 실제로 고쳐진 것:

- **M8/M13(Vom측), M22/M17(Vop측)**: 원래 M11a/M20a 다이오드 스택 "위"에 직렬로 쌓인
  것으로 잘못 선언돼 있었음(`_confidence_note`엔 "병렬 전류원"이라고 이미 맞게 적혀
  있었는데 JSON 필드만 틀렸던 전형적 케이스) → **독립 병렬 전류원**으로 정정, drain은
  다이오드 스택 "아래"(M11b/M20b의 diode 노드)에서 합류.
- **M11b/M20b의 diode 노드가 M8/M22의 drain과 별개 노드**라는 걸 처음엔 못 갈라서 하나로
  묶어버렸다가(`Vg15`로 잘못 통합), 사용자가 "M15의 gate는 M8의 drain에만 연결"이라고
  정정 → `Vg15`(=M8.drain=M15.gate=M9a.source=M9b.drain)와 `N11b`(=M11b의 diode
  노드=M9a.gate=M12.drain, 신설)로 **노드 분리**.
- **M12(Vom)/M21(Vop)**: `Vg15`가 아니라 `N11b`로 연결 확정 — `VDD→M11a→M11b→N11b→
  M12→GND`가 M8과 무관한 **독립 2-다이오드+싱크 서브회로**임을 사용자가 확정. 이 서브
  회로의 전류는 논문 II.B절("M11a/M11b가 subthreshold 영역") 인용 근거로 자유 비율
  theta `r_diode_M11a`/`r_diode_M20a`(root=[M11a,M11b,M12]/[M20a,M20b,M21] 셋을 동시
  시드, `r_classab_src`와 같은 root=list 패턴)로 재구성. 옛 `kcl_diode_M11a`
  (M8+M13→M11a KCL 합 가정)는 폐기.
- **M9a/M9b(Monticelli floating current source)**: 직렬 스택이 아니라 `Vg15`↔`Vg16`
  사이에 **병렬로 걸린 구조**로 재확정 — `M9a`(pmos): source=gate=`Vg15`, drain=`Vg16`.
  `M9b`(nmos): drain=`Vg15`, source=`Vg16`, gate=`N14a14b`(=M13.drain, M14a의 diode
  노드). `M18a`/`M18b`(Vop측)도 대칭 반영.
- **M10(Vom)/M19(Vop)**: `M12`/`M21`과 마찬가지로 `gnd`에서 독립적으로 소스, drain은
  `Vg16`/`Vg26`.
- **M13(Vom)/M17(Vop)**: drain이 `Vg15`/`Vg25`가 아니라 `N14a14b`/`N24b23a`
  (M14a/M24b의 diode 노드)로 확정.
- **M14a/M14b(그리고 대칭 M24b/M23a)**: `M14a.source=M14b.drain=Vg16`,
  `M14a.gate=M14a.drain=M14b.source=N14a14b` — 서로 반대 방향 다이오드.
- **M1a/M2a/M3a/M4a(그리고 M1b/M2b/M3b/M4b, 1단 입력쌍)**: 세션 막바지에 큰 정정 —
  M2a/M3a가 직렬 캐스코드(M2a.drain→M3a.source)가 아니라 **drain끼리 Vom1에서
  합류**하는 구조(PMOS 경로 M1a→M2a와 NMOS 경로 M4a→M3a가 각각 독립적으로 Vom1에
  전류를 밀어넣는 진짜 "current-reuse" 구조). `M1a.drain=M2a.source="N1a2a"`(신설),
  `M4a.drain=M3a.source="N3a4a"`(기존 이름 재사용), `M2a.drain=M3a.drain="Vom1"`(이동).
  Vop측도 대칭(`N1b2b`/`N3b4b`/`Vop1`) 반영. **이 정정이 옛 self-test assert를
  깨뜨림(위 "지금 당장 이어서 할 일" 참고) — CMRR 공식 자체도 재검토 필요할 수 있음.**

### 4단계 — R1/R2(CM 감지 저항) 추가 논의
`Voc`가 dangling(구동 소자 없음)으로 계속 플래그되는 걸 보고 사용자가 "R1/R2 소자를 왜
안 넣어?"라고 질문 → `netlist`(kind: pmos/nmos)에 그냥 섞으면 `.kind`를 참조하는
227곳(`stick_diagram.py` 203 + `sizing_recipe.py` 24)이 깨질 위험이 있어, **별도
`passive_elements` 배열**(사이징 엔진이 안 읽음, connectivity 기록 전용)을 신설해
R1/R2를 넣음. `_known_dangling_nets`(근거 있는 "해소된" dangling net 설명, 예:
`Voc`→R1/R2)도 신설.

### 5단계 — 신규 도구: `topology_to_markdown.py` + skill 업데이트 (중요, 앞으로 항상 쓸 것)
사용자가 "네가 생각보다 그림을 잘 인식 못하네"라고 지적 — 앞으로 topology.json을 만들거나
고칠 때마다:
1. `skills/analog-gmid-design/assets/topology_to_markdown.py <json경로>` 실행 →
   net별/소자별 connectivity 표를 `<name>.topology.md`로 저장 **+ 세션에도 출력**.
2. 고아 net(단자 1개)/구동 소자 없는 net을 자동 ⚠️ 플래그, `_known_dangling_nets`로
   해소된 것은 ℹ️로 구분.
3. `passive_elements`(R/C 등, netlist 스키마 밖)도 표에 포함.

`references/topology-extraction-checklist.md` §5와 `SKILL.md`에 **필수 절차**로 반영
완료. 메모리에도 저장(`feedback_schematic_image_reading_unreliable`).

## 작업 파일 위치 (신규/누적)
- `skills/analog-gmid-design/assets/topology_to_markdown.py` — **신규**, connectivity 표
  생성기. topology.json 손댈 때마다 실행할 것.
- `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.md` —
  **신규**, 위 스크립트 산출물(최신 connectivity 표).
- `workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py`,
  `spice/cmfb_amp_gain_sympy_derivation.py`, `spice/cmfb_cmrr_ngspice_crosscheck.py` —
  CMFB 재유도 에이전트 산출물(sympy/ngspice 교차검증 재현용). 미커밋.
- `workspaces/current-reuse-telescopic-ota-report/paper_pages/` — 논문 PDF를 페이지별
  600dpi로 렌더링한 이미지(`page_NN_hires.png`) + 크롭들. 다음 세션에서 bias-gen 재확인
  시 재사용 가능(`page_08_hires.png`가 Fig.8 bias-gen).
- `workspaces/current-reuse-telescopic-ota-report/selftest_*.log` — 이번 세션 여러 차례
  self-test 실행 로그(로컬만, git 미추적).

## 참고 — 사용자 협업 메모리 (관련, 이번 세션 갱신분 포함)
- 최종 보고는 항상 한글로.
- 상상으로 채우지 말고 근거·실제 확인 후 진행 — 이번 세션 전체가 이 원칙의 반복 적용
  (매번 "확인해주셔서 감사합니다"로 끝나는 패턴).
- topology.json이 유일한 토폴로지 소스.
- 장시간 실행은 `run_in_background: true`.
- git commit 시 heredoc-in-`$()`이 bkit 훅에 막힘 — 파일로 메시지 작성 후 `git commit -F`.
- 복잡한 analog 회로 폐형식 재유도는 opus 에이전트 위임이 효과적.
- **(세션 3 신규, 중요) 회로도 이미지/PDF 판독은 신뢰 못 함** — 반드시
  `topology_to_markdown.py`로 net 기준 표를 뽑아 세션에 출력하고 사람이 재확인할 것.
  텍스트로 소자를 하나씩 나열하는 것보다 net 기준으로 뒤집은 표가 "두 노드를 하나로
  착각"하는 유형의 오류를 훨씬 잘 드러낸다.
- **(세션 3 신규) 동시 편집 위험**: 배경 에이전트와 내가 같은 topology.json을 동시에
  건드리면 충돌 가능 — 에이전트에게 작업을 맡길 때는 건드릴 파일 범위를 명확히 알려주고,
  겹치면 에이전트가 스스로 회피하도록 유도할 것(이번 세션 CMFB 에이전트는 실제로 이걸
  잘 감지하고 회피했다 — `TOPO_OVERRIDE` 패턴 참고할 만함).
