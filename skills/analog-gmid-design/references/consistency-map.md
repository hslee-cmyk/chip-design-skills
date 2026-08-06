# Consistency Map — analog-gmid-design

## 사용법

SKILL.md 원칙 수정 시:
1. 아래 맵에서 해당 원칙의 반영 위치 확인
2. 모든 반영 위치를 함께 업데이트
3. SKILL.md 내부 요약(핵심 원칙 표, §5 체크리스트)도 확인
4. **수정 후: `../skill-validation-prompt.md` 절차로 일관성 검증**

## 원칙별 반영 위치

| 원칙 | SKILL.md 섹션 | SKILL.md 내부 요약 | reference 반영 위치 |
|------|--------------|-------------------|-------------------|
| 목적 재정의(topology+spec 확정, 논문은 테스트케이스) | "이 skill의 목적" | 절대 원칙 표 #4 | known-incidents.md 사고4 |
| 함수 실제 호출(손 축약 금지) | 핵심 원칙 절대 원칙 표 #1 | §5 마지막 체크리스트 항목, §6 본문 | known-incidents.md 사고1, function-selection-map.md 전체 |
| 논문 원문 직접 확인(상상 금지) | 절대 원칙 표 #2 | - | known-incidents.md 사고2 |
| 리포트 시각화 코드 재사용 | 절대 원칙 표 #3 | §7 표 1행/5행 | known-incidents.md 사고3, design-report-spec.md §1 표, report_template.html |
| 모든 소자 확정("out of scope" 금지) | 절대 원칙 표 #4, §1.5 전체 | §4 표 마지막 행, §5 체크리스트 "모든 소자" 항목, §7 표 3행/본문 | known-incidents.md 사고4, function-selection-map.md §2, gm-id-methodology.md §6.4/§6.7/§10 |
| gm/ID 4대 핵심 원칙(fT→gm, gm/ID 자유변수, LUT 조회, moderate 출발점) | 핵심 원칙 목록 1~4 | §1 플로우차트 | gm-id-methodology.md §2.1/§5, §2.2/§4, §5.2 |
| **함수 우선순위 대원칙(harness → 원소 함수 → 그래도 없을 때만 새 코드)** | "핵심 원칙" 절, gm/ID 4대 원칙과 절대 원칙 표 사이 | - | function-selection-map.md §0(harness 5개 인덱스) |
| 동작점 선택 판단 기준 | §2 표 | - | gm-id-methodology.md §1.3/§5.2/§2.6/§7.1/§6.3·§7.2 |
| 회로별 적용 가이드(Intrinsic Gain Stage/Cascode/Current Mirror/Miller Op-Amp/3-stage OTA/Distortion/RF/Bias generator마다 어느 문서 §를 볼지 + 핵심 판단 지점) | §4 표 | - | gm-id-methodology.md §6.1~§6.7/§9/§10/§10.4/§11/§12, function-selection-map.md §2 |
| gm/ID 물리적 한계 판단(정방향↔역방향, 지수분할, LUT 상한) | §2.1 | - | sky130-worked-example.md §4, function-selection-map.md §1 |
| 검증 체크리스트(Definition of Done) | §5 | - | spice-verification-workflow.md §1/§2, function-selection-map.md §3 |
| Stick diagram/Euler trail 피드백 루프 | §6 | §6 플로우차트 | stick-diagram-euler-layout.md 전체, known-incidents.md, function-selection-map.md §3~§6 |
| box-shape FAIL 수용 전 분할비용 계산 | §6 플로우차트("§8.5 계산") | - | stick-diagram-euler-layout.md §8.5 |
| 최종 산출물 리포트 8섹션 규격(2026-07-28: 7→8, 물리 floorplan을 필수 섹션으로 승격) | §7 | §7 표 | design-report-spec.md 전체(PRE-FLIGHT 포함) |
| §5 stick diagram의 sub-block 커버리지 완결성(일부만 하고 나머지 생략 금지) — `check_stick_diagram_coverage()`로 기계적 확인(2026-07-28 신설, PRE-FLIGHT 사고27: 프로즈 절차만으로는 재발 방지 안 됨이 실증됨) | §5 체크리스트 항목 | - | design-report-spec.md §1.5, PRE-FLIGHT 사고6·27, function-selection-map.md §8, stick_diagram.py §6.62 `check_stick_diagram_coverage()` |
| sub-block 존재 확인 후 반드시 find_matching_candidates()로 matching 정합성까지 확인(존재≠올바른 배치), 반드시 sub-block 경계 없이 전체 목록에 실행(사고B: 나눠 돌리면 cross-block 매칭을 놓침) | §5 체크리스트 항목 | - | design-report-spec.md §1.5 4단계, PRE-FLIGHT 사고7·8 |
| **국부 재검증 금지 — run_full_circuit_audit() 단일 게이트**(사이징 전 소스 대비 총 소자 수 선언 + 정본 connectivity 1벌 + 판정 dict, 사이징 완료 후 매번 처음부터 전체 재감사) | §5 체크리스트 마지막 항목(단일 bullet로 통합) | - | design-report-spec.md §1.6, PRE-FLIGHT 사고9·10·11, function-selection-map.md §8, stick_diagram.py §6.6 `run_full_circuit_audit()` |
| 시각 검증 의무 | §7 마지막 단락 | - | design-report-spec.md §4 |
| **§8 floorplan은 빈 공간 없는 실제 2D packing이어야 함**(대칭만으로 box-shape 주장 금지, packing_density 필수 확인) + row-split 후보 발견 시 §3 사이징/§6 SPICE 재검증까지 되먹임 | §7 표 8번(2026-07-28 이전엔 "필수 섹션 밖의 확장"으로 잘못 문서화돼 있었다 — 힌트 없는 fresh agent 재현 테스트가 floorplan을 통째로 빠뜨려 리포트를 게시한 실제 사고 이후 필수 섹션으로 승격, PRE-FLIGHT 사고27) | - | design-report-spec.md §1.7, PRE-FLIGHT 사고12·27, function-selection-map.md §9, stick_diagram.py §6.7 `pack_floorplan()`/`evaluate_row_split_candidates()` |
| **box-shape를 위해 functional group을 여러 물리 행으로 새로 지을 때, matching-safety(interdigitation/common-centroid)까지 pair 종류(전류거울/차동쌍/캐스코드 대칭쌍)에 맞게 별도 검증** — Euler-validity/box-shape만으로는 매칭 소자쌍의 완전 분리 배치를 못 잡는다. 제안된 순서가 실제 손으로 재배열된 것이라면 `check_walk_sequence()`로 연속성까지 재검산 | (§6 후속 확장 — §8 floorplan과 연계) | - | design-report-spec.md §1.7 3.5단계 + PRE-FLIGHT 사고 20~26, function-selection-map.md §6/§9, stick_diagram.py `audit_row_split()`/`check_walk_sequence()` |
| 공정별 gm/ID LUT 생성(SPICE/Spectre 스윕) 준비 절차 | §3(LUT 준비, §1 스텝1의 LUT 조회 전제) | - | lut-generation-checklist.md 전체 |
| 표에 없는 topology/보상소자 함수 신규 유도 절차("스킵 근거 안 됨") | §1.5 본문(125행) | 절대 원칙 표 #4 요약과 동일 원칙 적용 | topology-fn-derivation-guide.md §1, topology_library.py |
| **topology library JSON**(`library/*.topology.json`) — topology의 connectivity+matching kind+위상보정 함수 참조를 재사용 가능한 데이터로 분리, 재사이징해도 재사용(2026-07-28 신설). **layout(finger 배분/row 분할/floorplan 좌표)은 사이징 결과값이라 이 JSON에 담지 않는다** — 구현 중 실측으로 확정된 원칙(처음엔 `layout` 가이드 필드를 뒀다가 폐기) | §1.5 말미("library JSON 확인"), §6 말미(`run_topology_pipeline()`), §7 표 8번(floorplan) | - | `docs/02-design/features/analog-topology-json-library.design.md` 전체, function-selection-map.md §10, stick_diagram.py §6.9 `load_topology()`/`run_topology_pipeline()`/`save_instance_json()`, sizing_recipe.py §6.5 `run_sizing_pipeline()`/`_COMPENSATION_REGISTRY` |
| SPICE 결과가 설계식/원문 예측과 어긋날 때의 근본원인 진단 절차 | §1 스텝5(반복/수렴) 연계 | - | topology-behavior-diagnosis-workflow.md 전체 |
| **`find_matching_candidates()` current_mirror/diff_pair 오탐 재검증(2026-08-06, 구현 완료·미커밋)** — gate만 보던 current_mirror에 gate+source 그룹핑(`idiom_matches=`), 우연히 같은 source+W를 갖던 diff_pair에 role 필터 추가, 캐스코드 대칭쌍은 `find_stacked_matching_candidates()`(복합소자 상속)로 별도 커버 | "Cross-Skill 참조" | - | analog-grammar-integration.md 전체, stick_diagram.py §1.7a~1.7c + self-test 30 |

## Cross-Skill 참조

| 원칙 | 본 skill | 참조 skill |
|------|---------|-----------|
| Sizing 결과 behavioral 모델 사전 검증 | Cross-Skill 참조 | verilog-a |
| AMS 검증환경 배치 | Cross-Skill 참조 | chip-verification |
| matching 후보 오탐(current_mirror/diff_pair)의 device role 기반 재검증 | Cross-Skill 참조, analog-grammar-integration.md | analog-grammar |

## 마커 규약 (이 skill 고유 — 다른 skill과 다름)

- **`[→§X]` / `[→references §X]`**: X는 **항상 `references/gm-id-methodology.md`의 섹션 번호**다
  (SKILL.md 자신의 섹션 번호가 아니다 — 이 skill의 §1/§2 초반부가 gm-id-methodology.md를
  요약하는 절이라 그 문서 번호를 그대로 쓴다). `references §` 접두어가 없어도 동일하게
  gm-id-methodology.md를 가리킨다 — 표기가 혼용되어 있으니 접두어 유무로 판단하지 말 것.
- **괄호 없는 `§X`(예: "§1.5", "(§8)", "§6 참고")**: 문맥상 가장 가까이 언급된 파일을 가리킨다 —
  파일명이 함께 명시돼 있으면(예: "stick-diagram-euler-layout.md §8.5") 그 파일, 명시가 없으면
  SKILL.md 자신의 섹션 번호(§1~§7, §1.5, §2.1).
- **용도**: 요약 항목이 어느 상세 섹션에서 유래했는지 추적.
- **수정 시**: 상세 섹션(gm-id-methodology.md 등) 번호가 바뀌면 이 SKILL.md의 마커도 반드시 동기화.

## 이 skill 고유 검증 항목 — "out of scope" 금지 원칙 위반 탐지

§1.5(모든 소자는 확정된 값을 가져야 한다) 도입 이후, 다음 패턴이 SKILL.md·reference 어디에도
없어야 한다(있으면 §1.5 위반):
- "~에 대한 gm/ID가 논문/스펙에 안 나온다"류 문구를 트랜지스터/수동소자 값 확정을 건너뛰는
  근거로 쓰는 서술.
- 정당한 예외(ESD/guard-ring/foundry DRC 등 §1.5 마지막 단락의 항목)가 아닌데 "out of scope"/
  "범위 밖"/"범위 제외"로 표기된 능동·수동 소자 값.
- `assets/report_template.html`의 `out_of_scope` 필드 예시 내용이 §1.5 예외 항목(ESD/DRC/메탈
  스택 선택)에서 벗어나 있는지(트랜지스터/R/C 값이 섞여 있으면 FAIL).

## 변경 이력

- 2026-07-30 (48차, 47차에서 LOW confidence로 남겨뒀던 bias-gen 배선 4곳 전부 사용자와
  재검증해 HIGH로 승격 — 사용자 요청 "M57,M58의 연결이 뭐가 불명확하지? ... 나와 검증해서
  고쳐놓자" → "미해결된 것도 함께 확인하자"): 47차가 남긴 LOW 항목 4개(M58/M57 배선,
  M64/M63 배선, M9a/M18a 게이트, M13/M17 역할)를 하나씩 이미지로 다시 짚어가며 확인.
  핵심 발견: (1) M58/M57의 "vdd" 라벨은 소스 연결이 아니라 **PMOS well/body bias 태그**였다
  — 실제로는 M61이 공급하는 stacked diode(두 게이트 모두 M57의 drain=Vbias_p에 함께
  묶임), M68의 drain도 그 노드에 연결돼 전류 루프를 닫는다. (2) M64/M63도 같은
  stacked-diode 패턴(M60→M64→M63→gnd, 두 게이트 모두 M63의 drain=Vbias3). (3) M9a/M18a의
  게이트는 대칭 가정(Vom1/Vop1)이 아니라 **각각 M11b/M20b의 drain**(자기 자신이 아닌 같은
  diode 체인의 다른 다이오드 노드) — 즉 M9a는 Vg15에서, M18a는 Vg25에서 diode-connected.
  (4) M13/M8/M22/M17은 전부 게이트가 Vbias1에 병렬 연결된 동일 구조임을 확인(기존
  paralleled-source 가정이 맞았음). `find_matching_candidates()`/`find_hub_merge_candidates()`
  재호출 + `run_full_circuit_audit()` 재검증(`ok=True`, 24개 group 전부 disposed) 통과.
  이제 topology.json 51개 소자 전부 HIGH confidence — LOW/MEDIUM 항목 없음.

  **교훈**(sky130-worked-example.md §13.5에도 기록): "vdd 라벨이 두 번 보인다"를 "두 소자가
  독립적으로 소스 연결된다"로 잘못 해석했다 — PMOS는 N-well 공정에서 body를 항상 VDD에
  묶어야 하므로 그 태그가 소스 연결과 무관하게 소자마다 반복 등장한다는 걸 놓쳤다. 반면
  "두 소자의 id가 정확히 같다(-1.534µ)"는 직렬 스택을 가리키는 강한 수치적 신호였는데,
  그 신호보다 (틀린) 시각적 라벨 해석을 더 믿은 게 오독의 원인이었다.

- 2026-07-29 (47차, `current_reuse_telescopic_ota.topology.json` 자체의 오류 3건 발견·수정 —
  harness 커버리지 감사(46차 이후 이어진 대화) 도중 배치 7-3(gm1/gm2 topology_fn) 논의 중
  사용자가 "논문처럼 풀어놓은 값을 그냥 쓴 거 아니냐"고 질문 → 실제 논문 PDF를 사용자가 제공한
  로컬 경로에서 열람 → 사용자와 함께 **본문+부록 전체를 처음부터 끝까지 재확인, 회로도는
  스키매틱 이미지로 직접 재판독**하며 topology.json 자체의 실오류 3건을 발견):
  1. **bias-gen 소자 9개(M27,M28,M29,M33,M34,M31,M32,M30,M35)가 전부 가상의 소자였음** —
     논문 III.C절의 "the other side of Vx and Vy is marked in Figure 3"는 오탈자(Figure 2가
     맞음)이고, Fig.4("biasing circuit")는 실제 회로가 아니라 Fig.2 아키텍처를 설명하는 참고
     다이어그램이라는 걸 사용자가 지적. 실제 bias-gen은 Appendix Fig.8(Cadence 자동 인스턴스
     이름 M18/M60/M61/M64/M63/M58/M57/M66/M68, Fig.4의 이름과 전혀 다름) — 사용자가 확대
     이미지를 직접 제공해 소자명/사이즈/DC 동작점 재확인.
  2. **Class-AB 2단의 Vop측(좌) 12개 소자가 통째로 누락** — Fig.1 전체 스키매틱엔 Vom측
     (Fig.3에 그려짐, 이미 모델링됨)과 별개로 Vop측 미러(M22/M20a/M20b/M17/M18a/M18b/M21/
     M19/M24b/M23a, 별도 그림 없이 Fig.1에만 존재)가 실제로 있는데 기존 버전은 M13/M25/M26
     3개 placeholder만 넣고 M26의 gate까지 Vom측 M16과 잘못 공유시켜놨었다 — Appendix Fig.7
     (2단 size/DC 동작점, 사용자가 고해상도 이미지 제공)로 Vop/Vom 양쪽 교차검증.
  3. **M9a(및 대응 M18a)의 극성이 nmos로 잘못 기재** — Monticelli floating current source는
     PMOS+NMOS 상보쌍인데 둘 다 nmos였다. Fig.7 DC 동작점의 id 부호(M46=-338.8n=PMOS,
     M45=857.2n=NMOS)로 정정.

  **소자 수 41→51개로 증가.** 수정 후 `find_matching_candidates()`/`find_hub_merge_candidates()`
  를 실제로 재호출해 `matching_pairs`/`dispositions`를 갱신(손 작성 아님 — 함수 실제 출력
  기반), `run_full_circuit_audit()`로 최종 검증(`ok=True`, 25개 candidate group 전부 disposed).

  전체 매핑표(Fig.6/7/8 appendix ↔ topology.json 이름 대응, local net명 ↔ main 회로 net명
  대응)는 `sky130-worked-example.md` §13에 기록 — 다음에 이 topology.json을 다시 손볼 때
  같은 재확인 작업을 반복하지 않도록 참조용으로 남김. `gap-findings.md` §4와
  `do.md` 배치 7-3에도 이 §13을 가리키는 참조 추가.

  **교훈**: "논문을 원문 그대로 재확인했다"고 기록된 이전 버전(39차 이전 세션, 2026-07-28)도
  실제로는 해상도가 낮은 스키매틱을 대충 훑고 확신도만 낮게 표시해뒀을 뿐, 진짜 오류(가상
  소자, 완전 누락된 절반의 회로, 극성 오류)를 잡지는 못했다 — "확신도 LOW로 표시했다"가
  "나중에 반드시 재확인된다"를 보장하지 않는다는 게 이번에 실측으로 드러났다. 사용자가 직접
  고해상도 이미지를 제공하고 라벨을 하나씩 짚어준 것이 결정적이었다 — AI 혼자 저해상도 PDF
  렌더링만으로는 이 오류들을 못 잡았을 것이다(첫 시도에서 "Vip"/"M68" 등을 실제로 오독했었음).

- 2026-07-29 (46차, `current-reuse-telescopic-ota-report` 워크스페이스 — 설계 명시 instance-
  output JSON 누락 + 필수 감사 게이트 3개 import-only(미호출) 발견·수정 — 사용자 질문 "최종
  결과는 json으로도 출력되었어?" → "원래 design에 설계되어 있는 json 출력이 구현이 누락되어
  있네. 확인해." → "지금 다 고쳐줘"): `REPORT_DATA.json`(리포트 렌더링용 ad-hoc 데이터)은
  있었지만, `analog-topology-json-library.design.md`(140행)가 명시한
  `workspaces/<design>/<design_name>.instance.json`(`save_instance_json()` 표준 스키마 —
  topology_ref/sizing/netlist/floorplan/box_shape/audit_row_split/coverage)은 이 워크스페이스에
  하나도 없었다. `library/current_reuse_telescopic_ota.topology.json`(schema_version 2.0)이 이미
  존재하는데도 `stick.py`가 그걸 안 쓰고 `size_transistor()`/`build_stick_diagram()`을 손으로
  직접 조립해서 만들어졌다는 뜻 — 이번 세션 43차의 "harness 우선순위 대원칙" 위반이기도 했다.

  조사 중 더 심각한 걸 발견했다: `stick.py`가 `run_full_circuit_audit`를 import는 하지만 실제
  호출은 0건(grep 확인) — `design-report-spec.md` "사고27"에 이미 **정확히 이 실패 패턴**으로
  기록돼 있던 것과 동일 사례였다(그 사고 대응으로 §8 필수화·`check_stick_diagram_coverage()`
  신설·SKILL.md DoD grep 확인 절차는 추가됐지만, 이 워크스페이스의 실제 스크립트 자체는 그
  이후에도 고쳐지지 않은 채 남아 있었다). `check_stick_diagram_coverage()`/`audit_row_split()`도
  0건.

  **수정**:
  1. `stick_diagram.py`의 `save_instance_json()`을 확장 — `box_shape`/`audit_row_split`이
     단일 `BoxShapeVerdict`/`AuditResult` 또는 `{cell_name: verdict}` dict 둘 다 받도록
     (`_box_shape_json()`/`_audit_result_json()` 헬퍼 추가). 이 회로처럼 물리적으로 독립된
     cell이 3개(core_signal/bias_tail/stage2_output)인 경우 `run_topology_pipeline()`의
     "회로 전체에 combined box-shape 하나" 가정이 안 맞기 때문(cell을 넘나드는 단일 ratio는
     의미 없는 숫자가 된다) — 임시방편 대신 공유 함수 자체를 정당하게 확장했다. `scope_note`
     선택 필드도 추가(부분 스코프를 완료처럼 보이게 하지 않기 위함).
  2. `stick.py`에 각 `Transistor`의 `stack_id`를 명시(행 이름과 일치) + `audit_row_split()`을
     물리 cell 3개에 각각 호출(cell을 넘나드는 단일 호출은 무의미하므로) — matching_pairs/
     pair_kinds는 이미 계산된 `find_matching_candidates()`/`find_hub_merge_candidates()` 결과를
     최대한 재사용하되, 그 전수 스캔이 구조적 이유로 놓치는 쌍(M4a/M4b — Vy net을 M5와도
     공유해 hub_merge로 분류됨, M15/M25·M16/M26 — branch_symmetric)은 근거를 남기고 수동
     override했다. **실제 실행 결과 진짜 FAIL 2건 발견**(상상/추정이 아니라 실측): core_signal_
     cell의 전류거울 캐스코드 쌍(M2a/M2b, M3a/M3b)이 interdigitation FAIL(핑거가 실제 Euler
     trail에서 인접하지 않음), stage2_output_cell의 미러 출력쌍(M15/M25, M16/M26)이 common-
     centroid FAIL(|dx|=2.00, 허용오차 0.5 초과) — box-shape PASS·Euler-valid였지만 matching-
     safety는 전혀 확인된 적 없었던 상태였다는 뜻. 리포트에 감춰서 통과시키지 않고 §4에 정직하게
     추가했다(수정은 후속 작업으로 남김 — "지금 다 고쳐줘"의 범위는 누락된 게이트/JSON 산출이지
     실제 finger 재배치가 아니라고 판단).
  3. `check_stick_diagram_coverage()`도 실제 호출 — `sizing_results.json`의 그룹화/축약된 이름
     ("M15/M25 (barely-on Q-point)", "M14a/b")을 개별 소자 이름으로 전개하는 `_expand_device_
     names()` 헬퍼를 작성하는 과정에서 자체 버그 발견(첫 구현이 "M14a/b"를 "M14a"+"b"로 잘못
     쪼갬 — "b"라는 가짜 소자 이름이 생김) → prefix 재사용 로직으로 수정, 재실행해서 실제로
     `missing`이 M8/M11a/M11b/M13/M14a/M14b/M27-M40 등 정확히 이미 disclosure된 bias-gen/CMFB/
     Class-AB battery 집합과 일치함을 확인(정직하게 이미 공개된 gap이 유일한 gap임을 기계적으로
     재확인).
  4. `run_full_circuit_audit()`은 이 3개 cell(15개 소자, gate-level connectivity가 실제로 확정된
     범위)로만 스코프를 제한해 호출 — bias-gen/CMFB/Class-AB battery 내부 connectivity는 리포트
     자신의 `out_of_scope`에 이미 "gate-level 확정 아님"으로 명시돼 있어, 여기 감사에 포함시키면
     검증 안 된 connectivity를 지어내는 것이 되므로 정직하게 제외(`scope_note`로 명시).
  5. `build_report.py`/`build_html.py`에 위 3개 게이트 결과(`report_gates`)를 §4 끝에 추가
     렌더링(claude-in-chrome으로 실제 스크린샷 확인 — 콘솔 에러 없음, PASS/FAIL 색상 정상,
     레이아웃 정상).

  전체 파이프라인(`stick.py`→`build_report.py`→`build_html.py`) + skill self-test 3개
  (`stick_diagram.py`/`sizing_recipe.py`/`topology_library.py`) 전부 exit 0 재확인.

  **교훈**: "완료 보고 전 grep으로 실제 호출부 확인"이라는 절차가 이미 문서화돼 있어도
  (design-report-spec.md 사고27 대응), 그 문서화가 향한 곳은 스펙/원칙 문서였지 실제로 그
  사고를 유발했던 원본 워크스페이스 자체는 아니었다 — 사고가 "해결됨"으로 기록된 뒤에도
  정작 그 사고의 실제 증거였던 파일은 방치될 수 있다. 또한 게이트를 뒤늦게 실제로 연결하면
  이미 "완료"로 보고됐던 산출물에서 진짜 결함(matching-safety FAIL 2건)이 나올 수 있다 — 이건
  게이트가 실제로 일하고 있다는 증거이지 게이트 추가 자체의 실패가 아니다.

- 2026-07-28 (45차, `sizing_recipe.py`의 잔여 naming 비일관성 + 손 축약 위반 발견·수정 —
  사용자 요청 "남은 함수 비일관성 항목들도 순서대로 정리해줘"): 39~40차의 `check_`/`verify_`
  통일 작업은 스코프가 "`stick_diagram.py` 60개 함수"였다고 명시돼 있어(39차 changelog 원문),
  같은 세션에 한 번도 감사 안 된 `sizing_recipe.py`(13개)/`topology_library.py`(5개)를 다시
  훑었다. `topology_library.py`는 전부 토폴로지 고유명사라 이상 없음. `sizing_recipe.py`에서
  2건 발견:
  1. **`verify_quasi_static(fT, gm, Cgg, margin) -> bool`** — 39~40차가 `stick_diagram.py`에
     확립한 관례(구조/시퀀스가 어떤 속성을 만족하는지 판정하는 함수는 `check_*` + `*Verdict
     (ok)` dataclass)와 동일한 역할인데 이름도 `verify_`, 반환도 bare bool로 남아 있었다.
     `check_quasi_static()` + `QuasiStaticVerdict(ok: bool)`로 통일(호출부 2곳 — 데모,
     `find_optimal_sizing()` — 와 `function-selection-map.md` §1 표를 함께 갱신).
  2. **`find_optimal_sizing()`이 준정적 조건을 손으로 재구현하고 있었다**(핵심 원칙 절대
     원칙 표 #1 "함수 실제 호출(손 축약 금지)" 위반, harness 우선순위 대원칙과도 무관하지
     않음): `fT_dev = lut.fT(gm_id, L, VDS, vs); fnqs_ok = fT <= quasi_static_margin * fT_dev`로
     `check_quasi_static()`과 수학적으로 동일한 `fT<=margin*f_nqs` 비교를 별도로 계산하고
     있었다 — element 함수를 호출하는 대신 그 안의 공식을 그대로 베껴 쓴 것. `lut.fT()`가
     기준폭에서 잰 gm/Cgg 비(gm_ref/cgg_ref)이고, `gm`(고정 타깃)과 `lut.cgg_absolute(...,
     W)`(그 타깃 gm을 만드는 실제 폭에서의 절대 Cgg)의 비가 스케일링 불변성(폭에 비례해서
     gm/Cgg 둘 다 스케일되므로 비율은 폭 무관, `cgg_absolute()` 자체 docstring이 이 스케일링
     근거)으로 수학적으로 동일함을 확인한 뒤, 루프 안에서 이미 갖고 있는 `gm`(타깃)과 새로
     계산한 `Cgg=lut.cgg_absolute(gm_id, L, VDS, vs, W)`로 `check_quasi_static(fT, gm, Cgg,
     quasi_static_margin).ok`를 직접 호출하도록 교체(시그니처 변경 없음 — 일반적인
     (gm,Cgg) 인터페이스를 유지한 채 호출부만 고쳤다).

  self-test: `sizing_recipe.py` 전체 self-test exit 0 재확인(`find_optimal_sizing()` 데모의
  "1080개 후보 평가, 75개 실행가능" 등 수치가 리팩터 전후로 동일 — 스케일링 불변성 확인이
  실측으로도 검증됨), `stick_diagram.py` self-test exit 0(미변경, 회귀 없음 확인), 저장소
  전체 grep으로 `verify_quasi_static` 잔여 참조가 `.bkit/audit/`의 과거 로그(날짜 박힌 이력,
  수정 대상 아님) 외엔 없음을 확인.

  **교훈**: naming 통일 작업의 "완료" 선언은 실제로 감사한 스코프(이번엔 `stick_diagram.py`
  하나)에만 유효하다 — 같은 skill 안의 다른 파일(`sizing_recipe.py`)에 동일 패턴이 남아있어도
  자동으로는 안 잡힌다. 또한 naming 정리 도중 코드를 실제로 읽다 보면 이름만의 문제가 아니라
  "손 축약"(element 함수를 안 부르고 그 공식을 베낌) 같은 더 심각한 위반이 같은 자리에서
  발견될 수 있다 — grep만으로 끝내지 말고 관련 함수의 실제 호출부 본문까지 읽어야 이런
  이중 위반을 잡는다.

- 2026-07-28 (44차, `docs/04-report/analog-topology-json-library.do.md` "Do 단계 남은 일"
  점검 + 발견된 결함 수정 — 사용자 요청 "do 단계에서 남아있는 일이 무엇인지 정리해" →
  "바로 고쳐줘"): `do.md`가 "배치 4 진행 중"으로 낡아 있었는데 실제로는 배치 1~6 전부 실행된
  흔적(배치 6 산출물 `workspaces/current-reuse-telescopic-ota-report/final_report.html`
  존재)이 있어 점검한 결과 2가지 실결함 발견:
  1. **§8(물리 floorplan, 필수 섹션)이 `final_report.html`에 없음** — 근본 원인은 개별
     리포트가 아니라 `assets/report_template.html`("완전한 템플릿") 자체에 §1~§7까지만
     있고 floorplan 렌더러가 없었던 것(플로어플랜이 필수 섹션으로 승격된 시점 이후 템플릿이
     갱신 안 됨). `report_template.html`에 `renderFloorplan()`(§8) 신설 + 데모 REPORT
     객체에 실제 `pack_floorplan_grouped()` 실행 결과로 예시 데이터 추가, 같은 렌더러를
     워크스페이스의 `build_html.py`에도 이식, `stick.py`에 `pack_floorplan_grouped()` 호출
     추가(이 리포트가 실제로 커버하는 3개 셀만 — bias-gen/CMFB는 스틱다이어그램 자체를 이
     패스에서 안 만들었으므로 floorplan에도 정직하게 제외, `scope_note` 필드로 명시).
  2. **`workspaces/.../stick.py`가 이후 세션의 함수 rename(39~43차)으로 `ImportError`** —
     `generate_stick_diagram`/`detect_matching_candidates`/`verify_mirror_symmetry`(전부
     삭제된 옛 이름)를 import 중이었다. 현재 이름으로 갱신(`check_mirror_symmetry`는 반환이
     `MirrorSymmetryVerdict`로 바뀐 것도 함께 반영, `.ok` 접근으로 수정). `build_report.py`/
     `build_html.py`가 리포트 본문에 자기 방법론을 설명하며 인용한 옛 함수명도 갱신.
  3. **부수 발견**: `report_template.html`/`final_report.html` 둘 다 `<meta charset="utf-8">`가
     없어 로컬 서버로 열면 §/—/µ 등 비-ASCII 문자가 깨짐 — 둘 다 추가.

  claude-in-chrome으로 두 파일을 실제 로컬 서버에 띄워 §8 렌더링을 스크린샷으로 시각 확인
  (SKILL.md "모든 산출물은 완료 보고 전 반드시 시각 검증" 원칙 그대로 적용) — 처음엔 얇은
  행(box-shape proxy 단위 1칸)이 겹치는 라벨 문제를 발견해 `renderFloorplan()`의 scale
  계산을 "bbox를 화면에 맞추는 배율"과 "가장 얇은 블록도 18px는 보장하는 배율" 중 큰 쪽으로
  수정(가로 스크롤은 기존 `.stick-scroll` 컨테이너가 이미 처리) — 재확인 후 정상.
  `stick.py`→`build_report.py`→`build_html.py` 전체 파이프라인 재실행 exit 0, skill
  self-test(`stick_diagram.py`/`sizing_recipe.py`) exit 0도 재확인. `do.md`의 Status와
  §5 체크리스트에 배치 6 완료 확인 + 이번 사후 수정 내역 추가.

  **교훈**: "완전한 템플릿"이라 문서화된 자산도 스펙이 나중에 바뀌면(이번엔 floorplan 필수
  승격) 템플릿 자체를 갱신하지 않는 한 계속 낡은 채로 새 리포트에 복제된다 — 개별 산출물이
  아니라 템플릿을 고쳐야 재발하지 않는다. 또한 핵심 코드(`assets/*.py`)를 리네임할 때
  `workspaces/`처럼 그 코드를 직접 `import`하는 다운스트림 소비자가 있는지 확인하지 않으면,
  코드 자체의 self-test는 전부 통과해도 실제 산출물 재생성 경로가 조용히 깨질 수 있다 —
  이번 40차(함수 rename) 작업 때 `skills/` 안쪽만 grep했지 `workspaces/`는 스코프 밖으로
  뒀던 게 원인이었다.

- 2026-07-28 (43차, 함수 우선순위 대원칙 신설 — 사용자 요청 "harness/원소 함수/AI 작성
  순서를 반드시 지켜야 할 대원칙으로 skill에 박아줘"): 직전에 이 skill의 전체 함수를
  harness(오케스트레이션)와 원소 레벨로 분류해 보고한 것을 바탕으로, 사용자가 "이 skill의
  모든 작업은 harness 함수만으로 수행해야 하고, 세부 작업이 필요하면 원소 함수를 먼저 찾아
  쓰고, 구현된 함수가 아예 없을 때만 AI가 새로 작성한다"는 우선순위를 명문화하라고 요청.

  **구현**: `SKILL.md` "핵심 원칙" 절에 gm/ID 4대 원칙과 "절대 원칙" 표 사이에 **"함수
  우선순위 대원칙"**을 신설 — ①harness(`run_sizing_pipeline`/`optimize_multistage`/
  `run_full_circuit_audit`/`audit_row_split`/`run_topology_pipeline`) 우선 시도 →
  ②harness가 안 담당하는 세부 작업만 원소 함수 직접 호출 → ③둘 다 없을 때만 새 코드
  작성, 3단계로 명시. `function-selection-map.md`에 **`## 0. Harness(오케스트레이션)`**
  섹션을 신설(§1 앞, 기존 §1~§10 번호는 안 건드림) — 5개 harness 함수를 상황·상세 섹션
  포인터와 함께 한 표로 모아, 이 원칙을 실제로 따르려는 agent가 작업 시작 전 한 번에
  확인할 수 있게 했다. 5개 harness 각각의 상세 설명(호출 시그니처, 내부 호출 순서, 주의
  사항)은 이미 있던 자리(§1/§8/§9/§10)에 그대로 두고 중복 서술하지 않았다 — §0은 "이런
  harness가 있다"는 인덱스 역할만.

  **이 원칙이 기존 절대원칙 표 1번("함수가 있는데 손으로 재구성하지 말 것")과 다른 점**:
  1번은 "원소 함수 vs 손 계산"의 2단 비교였는데, 이번 원칙은 harness까지 포함한 3단
  우선순위(harness → 원소 → 새 코드)라는 점에서 상위 개념이다 — 특정 과거 사고에서
  나온 게 아니라 사용자가 지금 세운 아키텍처 원칙이라, known-incidents.md에 대응 사고를
  새로 만들지 않고 SKILL.md 본문에 직접 근거(왜: 이미 검증된 경로를 우회하면 반복된
  실패 패턴이 재현된다)와 함께 박아넣었다.

  self-test(`stick_diagram.py`/`sizing_recipe.py`) exit 0 재확인, `SKILL.md` word
  count(1588/5000)·description(946/1024자) 여유 재확인.

- 2026-07-28 (42차, SKILL.md + 전체 reference 파일 간결화 — 사용자 요청 "불필요한 설명...
  신설된 날짜들을... 본문에 중복된 내용들... 교훈적인 것들을... DO/DON'T로"): 41차
  validation 직후 진행. `SKILL.md`는 직접 정리(description 여유 6자→78자, 날짜 스탬프
  전체 제거, §5/§7 사이 중복 설명 통합, 서술체→직접 진술), 나머지 10개 reference 파일은
  4개 subagent에 병렬 위임(파일 간 편집 충돌 없음, 독립 작업) — `stick-diagram-euler-
  layout.md`, `design-report-spec.md`, `function-selection-map.md`+`known-incidents.md`,
  그리고 `gm-id-methodology.md`/`sky130-worked-example.md`+유틸리티 문서 4개(가벼운 손질만
  필요했음, 원래도 서술체가 거의 없었음). 공통 지시: (1) 날짜 스탬프 제거 — 이력은
  `consistency-map.md`/`gap-findings.md`에만(이 두 파일은 명시적으로 편집 대상에서 제외),
  (2) "사용자가 ~라고 지적했다"류 서술체를 직접 진술로, (3) 여러 차례 정정("처음엔 X, 그건
  틀려서 Y, 그것도 틀려서 Z")은 최종 결론만 남기고 압축, (4) 교훈을 DO/DON'T로 명확화,
  (5) 다른 파일과 중복되는 설명은 포인터로 대체. §-section 번호/앵커, 함수 시그니처,
  방정식·인용은 절대 변경 금지, 각 agent에게 실제 코드(`stick_diagram.py` 등) 대조
  재확인을 명시적으로 요구.

  **결과**(줄 수 before→after): `design-report-spec.md` 835→610(-27%),
  `stick-diagram-euler-layout.md` 1160→1103(-5%, 표/worked example 비중이 높아 삭제
  여지가 원래 적었음), `function-selection-map.md` 155→153(단어 수는 -6.6%),
  `known-incidents.md` 62→60(단어 수는 -21%), `gm-id-methodology.md`/
  `topology-behavior-diagnosis-workflow.md`/`spice-verification-workflow.md`는 편집 없음
  (이미 서술체 없는 교과서/절차 문서였음), 나머지 3개 유틸리티 문서는 문장 몇 곳만 직접
  진술로 전환. `design-report-spec.md`의 PRE-FLIGHT 사고 1~27번은 `consistency-map.md`/
  `SKILL.md`가 번호로 참조하므로 순서·번호 그대로 유지하고 각 항목만 "증상→(비자명한
  경우만 근본원인)→규칙" 2~3줄로 압축(예전엔 항목당 5~15줄).

  각 agent가 편집 후 실제 코드(`stick_diagram.py`/`sizing_recipe.py`/`topology_library.py`/
  `report_template.html`)의 `def`/`class`/JS `function` 전체 목록과 자신이 건드린 함수
  호출부를 grep으로 대조 재확인했고, 전체 self-test(`stick_diagram.py`/`sizing_recipe.py`)
  exit 0 재확인, Check 3(함수 시그니처) 재검증(builtin 오탐 제외 실질 위반 0건)까지 완료.

  **부수 발견**: 이 changelog 파일(`consistency-map.md`) 자체의 "## 변경 이력" 헤더가
  이전 편집 라운드(39~41차 삽입 과정) 중 실수로 사라져 있던 걸 42차 항목 추가 중 발견 —
  헤더 복원.

  **교훈**: "불필요한 서술 제거"는 단순 삭제가 아니라 압축이다 — 27개 PRE-FLIGHT 사고
  전부 정보 손실 없이 "증상→규칙"으로 줄일 수 있었던 건, 애초에 그 정보가 원래도 한두
  문장이었고 나머지는 전부 "어떻게 발견했는지"의 프레이밍이었기 때문이다. 반대로
  gm-id-methodology.md처럼 처음부터 서술체가 없는 문서는 억지로 편집하지 않는 게 맞다 —
  "전수검사"는 모든 파일을 똑같이 자르라는 뜻이 아니라 모든 파일을 확인하되 필요한 만큼만
  자르라는 뜻이다. 또한 파일을 병렬로 나눠 맡길 때도 "이 두 파일은 절대 건드리지 말 것"
  (changelog 파일)과 "여기 최근 이름이 이거다"(rename 이력)를 명시적으로 각 agent 프롬프트에
  박아두지 않았다면, 옛 함수명을 되살리거나 이력 파일을 건드리는 회귀가 났을 수 있다 —
  병렬 위임 시 "하지 말아야 할 것"을 각자에게 반복 명시하는 비용은 그로 인한 회귀를 막는
  비용보다 훨씬 싸다.

- 2026-07-28 (41차, `skill-validation-prompt.md` 전체 6-Check 검증 실행 — 사용자 요청
  "이 skill에 대해 validation과 일관성 검증을 수행해"): 40차까지의 대규모 rename 작업
  직후 실제로 실행. 결과 6/6 PASS(수정 후) — Check 3(코드 예제/함수 시그니처)과 Check 5
  (consistency-map 정합성)에서 실질적 결함을 발견·수정했다:
  - **Check 3 FAIL→수정**: (1) `stick-diagram-euler-layout.md`의 §6.62 worked example이
    `check_finger_width_compatibility()`의 옛 반환 타입(list)을 그대로 `for iss in issues`로
    순회하고 있었다(40차에서 dataclass로 바꾼 뒤 이 worked example만 놓침) — `verdict.issues`로
    수정. (2) SKILL.md §5 체크리스트가 `check_stick_diagram_coverage()`의 반환을 여전히
    `{"ok": True}`(dict literal)로 서술 — `.ok == True`로 수정. (3) `design-report-spec.md`가
    실제로 존재하지 않는 `renderCircuit()`/`renderMultiRowStack()`(존재하지 않는 세션
    아티팩트 `stick_artifact.html`의 함수로 잘못 인용)을 리포트 작성 지침으로 제시 — 실제
    `report_template.html`에 있는 `renderSchematic()`/`renderStack()`(다중 행은 이 함수를
    반복 호출)로 정정. (4) `function-selection-map.md`의 `check_symmetry_dispositions()`
    시그니처가 `-> dict`로 남아있던 것을 `-> SymmetryDispositionsVerdict`로 정정. (5)
    `stick-diagram-euler-layout.md`의 옛 `expand_interdigitation_pattern()`/
    `common_centroid_2row()` worked-example 호출 2건을 현재 API(`interdigitate_layout()`,
    `INTERDIGITATION_PATTERNS` 상수 직접 참조, `common_centroid_layout()`)로 재현 가능하게
    갱신(실제 실행으로 결과 일치 재확인함).
  - **Check 5 FAIL→수정**: (1) "공정별 gm/ID LUT 생성 준비 절차" 행이 "§1 스텝1, 본문
    173행"을 가리켰는데 실제 173행은 §2.1(물리적 한계 판단) 내용이었다(세션 중 문서 편집으로
    라인이 밀림) — "§3(LUT 준비)"로 정정. (2) 역방향 확인 중 SKILL.md §4(회로별 적용
    가이드 표)가 원칙별 반영 위치 맵에 아예 없었던 걸 발견 — §2 표와 동일한 격으로 새 행 추가.
  - **Check 1/2/4/6**: 전부 PASS(사소한 개선 1건: SKILL.md 절대 원칙 표 #1의 `§function-
    selection-map.md`라는 마커 규약 위반 표기 오류를 백틱 인용으로 정정). Check 6에서
    description 필드가 1018/1024자로 여유 6자뿐임을 확인(현재는 PASS, 향후 수정 시 주의).
  - self-test(`stick_diagram.py`/`sizing_recipe.py`) exit 0 재확인.

  **교훈**: Check 3에서 발견된 4건 전부가 40차(반환 타입 통일) 작업 직후의 잔여물이었다 —
  "코드를 바꾸고 self-test로 확인했다"는 것과 "그 코드를 설명하는 모든 문서의 worked
  example·시그니처 인용까지 다 훑었다"는 것은 별개였다. self-test는 실행 가능한 코드
  경로만 잡아내고, markdown 안의 예시 코드나 시그니처 인용문은 아무도 실행하지 않으므로
  정적 검증(이번 validation pass 같은)이 아니면 영영 안 잡힐 수 있었다.

- 2026-07-28 (40차, 함수 naming 비일관성 정리 나머지 5건 — `stick_diagram.py` 전체 API
  표면 재정리): 39차(`check_`/`verify_` 통일) 직후 사용자가 "반환타입은 다른 함수 모두
  바꾸고 진행하자. 나머지 함수 비일관성도 순서대로 정리해"라고 요청 — 39차에서 보고한
  나머지 5가지 항목(1. `detect_`/`find_` 혼용, 2. `check_*` 반환 타입 dataclass/list/
  dict/bool 혼용 완결, 3. `AuditResult` vs `*Verdict`, 4. `build_`/`generate_` 혼용,
  5. `interdigitate()`/`common_centroid_layout()` 이름 구조 비대칭, 6. `euler_condition`/
  `hierholzer` 동사 없음)를 순서대로 처리했다.

  **1) `check_*` 반환 타입 통일(순수 rename이 아니라 실제 구조 변경)**: 39차에서 미룬 반환
  타입 불일치를 마저 정리 — `check_box_shape`/`check_walk_sequence`(기존 `*Verdict`
  dataclass)를 기준으로, `check_finger_width_compatibility`(list) → `FingerWidthVerdict
  (ok, issues)`, `check_multi_leaf_hub_parity`(dict) → `MultiLeafHubParityVerdict(ok,
  kind, m_odd_leaves)`, `check_stick_diagram_coverage`(dict) → `CoverageVerdict(ok,
  missing)`, `check_symmetry_dispositions`(dict) → `SymmetryDispositionsVerdict(ok,
  case_collisions, undisposed)`, `check_mirror_symmetry`(bool) → `MirrorSymmetryVerdict
  (ok)`로 전부 dataclass화하고, `WalkVerdict`의 필드명도 `valid`→`ok`로 통일(다른
  `*Verdict` 전부와 일치시킴). 전 함수가 이제 `.ok`로 pass/fail을 읽는다. 호출부(self-test
  16곳 + `save_instance_json()`의 `pipeline_result["coverage"]` 접근)를 전부 bracket
  access(`["ok"]`)에서 attribute access(`.ok`)로 갱신 — `save_instance_json()`이 이미
  `box_shape`/`audit_row_split`(기존 dataclass)를 이런 식으로 수동 평탄화(flatten)해서
  JSON으로 쓰고 있던 기존 패턴을 그대로 재사용해 `coverage`도 동일하게 처리했다(새 패턴
  도입 아님). 부수 발견: `stick-diagram-euler-layout.md` §8 docstring에 `common_centroid_
  layout`(당시 이미 `_nway`로 개명된 뒤였는데 갱신이 안 된 채 남아있던 잔여 참조 2곳 +
  self-test 라벨 1곳)이 있었던 걸 이번에 함께 바로잡았다.

  **2) `detect_matching_candidates()` → `find_matching_candidates()`**: "찾는다"는 동일
  역할에 `find_`가 이미 다수(4개: `find_hub_merge_candidates`/`find_interleaved_symmetric_
  splits`/`find_diffusion_safe_split_points`/`find_min_crossover_layout`)였으므로 그
  쪽으로 통일. 순수 rename — self-test/모든 operational 문서 포함 전체 개명.

  **3) `AuditResult`(→`AuditCheck`) vs `*Verdict` 계열**: 실제로는 비일관성이 아니었다 —
  `AuditResult`는 `audit_row_split()`/`run_full_circuit_audit()` **두 `audit_*` 함수가
  이미 공유**하는 dataclass이고(내부에 `checks: list[AuditCheck]` + `.add()` 축적 메서드가
  있어 단일 속성만 담는 `*Verdict`류와 구조 자체가 다르다 — 여러 하위 체크를 모으는
  용도). 결론: **의도적으로 다른 이름을 유지** — "`*Verdict`=단일 속성 판정",
  "`*Result`=여러 sub-check을 모은 종합 판정"이라는 2단 구조를 명시적 관례로 문서화하는
  것으로 정리(코드 변경 없음).

  **4) `generate_stick_diagram()` → `build_stick_diagram()`**: "입력을 받아 새 구조를
  구성해 반환"하는 동일 패턴(`build_graph`/`build_mirror_symmetric_pattern`/`_build_rows_
  from_shares*`)에 이 함수만 다른 동사였다. 순수 rename.

  **5) `interdigitate()` → `interdigitate_layout()`, `common_centroid_layout_nway()` →
  `common_centroid_layout()`**: 38차로 두 함수가 기능적으로 동급이 된 뒤에도 이름 구조는
  여전히 비대칭(맨 동사 vs 동사+명사+`_layout`+`_nway`)이었다. `common_centroid_layout()`
  이 완전히 제거·흡수된 지금(37차) `_nway` suffix는 더 이상 다른 함수와 구분할 필요가
  없어 vestigial이었으므로 제거, `interdigitate()`는 `_layout` suffix를 붙여 대칭을
  맞췄다 — 이제 `interdigitate_layout()`/`common_centroid_layout()` 두 함수가 이름
  구조까지 대칭이다. `\binterdigitate\b`처럼 단어 경계를 명시한 치환으로 진행(단순
  문자열 치환 시 "interdigitated"/"interdigitation" 같은 영어 단어까지 오염시킬 위험이
  있어 실제로 사전에 grep으로 그 위험을 확인하고 피함).

  **6) `euler_condition()` → `check_euler_condition()`, `hierholzer()`는 그대로 유지**:
  `euler_condition(g) -> EulerVerdict`는 사실 1)에서 통일한 `check_*`→`*Verdict` 패턴과
  정확히 같은 모양이라 그 계열로 편입하는 게 자연스러웠다(rename). 반면 `hierholzer()`는
  그래프 이론의 표준 알고리즘 이름 그대로라 **의도적으로 유지** — 이 이름 자체가 이미
  도메인 전문가에게 통하는 표준 용어라, 억지로 동사형으로 바꾸면(예: `build_euler_trail`)
  오히려 그 인식 가능성을 잃는다고 판단했다.

  각 rename마다 `stick_diagram.py` 전체(정의+내부 호출+self-test)와 이 함수들을 참조하는
  모든 operational 문서(`function-selection-map.md`, `SKILL.md`, `stick-diagram-euler-
  layout.md`, `design-report-spec.md`, `known-incidents.md`, `docs/0*-*/features/
  analog-topology-json-library.*.md`, `library/*.topology.json`)를 함께 갱신하고, 매
  rename 직후 `stick_diagram.py`/`sizing_recipe.py` self-test exit 0을 재확인하며
  단계적으로 진행했다(한 번에 다 바꾸고 마지막에 몰아서 디버깅하지 않음). 이 문서와
  `gap-findings.md`의 날짜 박힌 과거 항목은 39차와 같은 기준으로 처리 — "이름 자체가
  주제인 항목"(없었음, 이번 5건은 전부 순수 동사/구조 정리라 그런 항목이 없었다)만
  보존 대상이었을 텐데 해당 사례가 없어 전부 최신 이름으로 갱신했다.

  **교훈**: "반환 타입까지 다 바꾸자"는 요청은 이름만 바꾸는 것보다 훨씬 큰 blast
  radius(모든 호출부의 접근 방식 변경)였지만, 미리 전 호출부를 grep으로 찾아 정확한
  접근 패턴(`["ok"]` vs `.get("ok")` vs 직접 bool 등)을 확인한 뒤 한 함수씩 순서대로
  고치고 즉시 self-test로 확인하는 방식으로 진행하니 실제로는 위험이 통제 가능했다 —
  "타입을 바꾼다"는 추상적 지시를 실행 가능한 단위(함수 하나, 호출부 grep, self-test
  1회)로 쪼갠 것이 핵심이었다.

- 2026-07-28 (39차, 함수 naming 비일관성 정리 1건 — `verify_*`를 `check_*`로 통일):
  38차 직후 사용자가 "이제 함수 이름을 살펴보자, 일관성이 없는 이름들을 list up해봐"라고
  요청 — 60개 함수 전체를 훑어 6가지 비일관성을 찾았다(동사 `detect_`/`find_` 혼용,
  `check_`/`verify_` 혼용+반환타입 흔들림, `build_`/`generate_` 혼용, 동사 없는
  `check_euler_condition`/`hierholzer`, `interdigitate_layout()` vs `common_centroid_layout()`의
  구조적 비대칭). 사용자가 그중 **`check_`/`verify_` 혼용**부터 정리하도록 지시(가장 심한
  케이스 — 7개 함수가 두 동사로 갈리고 반환 타입도 dataclass/list/dict/bool로 제각각이었음).

  **구현**: 순수 개명(동작/시그니처/반환 타입 변경 없음, 반환 타입 통일은 더 큰 별도 작업이라
  이번엔 손대지 않음) — `verify_mirror_symmetry`→`check_mirror_symmetry`,
  `verify_symmetry_dispositions`→`check_symmetry_dispositions`,
  `verify_walk_sequence`→`check_walk_sequence`(전부 `check_`로 통일 — 기존에 이미 `check_`
  계열이 4개로 다수였고, "이미 만들어진 구조/시퀀스가 어떤 속성을 만족하는지 판정"이라는
  동일 역할에 원칙적 구분 근거가 코드 어디에도 없었음을 재확인 후 결정). `stick_diagram.py`
  전체(정의+내부 호출+self-test, 16곳)와 이 함수들을 참조하는 모든 operational 문서
  (`function-selection-map.md`, `SKILL.md`, `stick-diagram-euler-layout.md`,
  `design-report-spec.md`, `skill-validation-prompt.md`, `docs/02-design/features/
  analog-topology-json-library.design.md`, `library/_TEMPLATE.topology.json`,
  `library/current_reuse_telescopic_ota.topology.json`)을 함께 개명했다. 이 문서(`consistency-
  map.md`)와 `gap-findings.md`의 **날짜가 박힌 변경 이력 항목(17/18/22/24/25차, §8/§17/§18)은
  옛 이름 그대로 보존**한다 — 그 항목들 자체가 "그 시점에 이 이름으로 만들어졌다"는 API
  이력을 기록하는 게 목적이라, 지금 이름으로 바꿔 쓰면 실제로 있었던 개명 사실 자체가
  지워진다(반면 design-report-spec.md/stick-diagram-euler-layout.md의 PRE-FLIGHT 사고
  서술은 이름이 아니라 프로세스 실수가 주제라 최신 이름으로 갱신해도 정보 손실이 없음 —
  같은 "역사 보존" 원칙을 사안별로 다르게 적용한 것).

  self-test: 개명 후 `stick_diagram.py`/`sizing_recipe.py` 전체 self-test exit 0 재확인
  (순수 rename이라 assertion 값 자체는 안 바뀜, 함수 참조만 갱신).

  **교훈**: naming 정리 요청이라도 전부 같은 방식(찾아서 다 바꾸기)으로 처리하면 안 된다 —
  "이 이름 언급이 API 역사 그 자체를 기록하는 문서(dated changelog)"인지 "이름이 우연히
  등장하는 인시던트 서술"인지를 파일별로 구분해서 적용해야, 정리하면서 오히려 과거 기록의
  정확성을 해치는 실수를 피할 수 있다. 반환 타입 불일치(dataclass/list/dict/bool 혼용)는
  이번 스코프에서 의도적으로 제외했다 — 이름만 바꾸는 것과 달리 모든 호출부의 접근 방식
  (`result["ok"]` vs `result.ok`)까지 바꿔야 하는 훨씬 큰 blast radius라 별도 확인 후
  진행하기로 함.

- 2026-07-28 (38차, `interdigitate_layout()`를 `common_centroid_layout()`와 동급으로
  재설계 — 내부 검증+crossover 폴백 흡수): 37차(`common_centroid_layout()` 완전 제거)
  직후 사용자가 naming 일관성을 지적("common_centroid는 layout이 붙었는데 interdigitate_layout는
  없다, 일관성이 떨어진다"). 확인해보니 실제 근거 있는 지적이었다 — `common_centroid_
  layout_nway()`는 내부에서 hub-leaf 검증(`_hubleaf_sequence_node_path()`)과 crossover
  폴백(`find_min_crossover_layout()`)을 전부 처리해 "무조건 성공하는 완성된 layout"을
  반환하는 반면, `interdigitate_layout()`는 순수 문자열/리스트 조합만 반환하고 검증은 호출자
  책임으로 남겨뒀다("이 경로는 결과가 1개 layer로 실현 가능한지 검증하지 않는다" —
  docstring에 명시돼 있었음, 실제 코드로 재확인). 사용자가 "interdigitate_layout도 fallback이
  있잖아"/"crossover routing 써서 fail 없애라고 한 것"이라고 되물어, `find_min_crossover_
  layout()` 도입(3~4차) 당시의 요청("이 함수에서 crossover routing이 최소인 조합을 찾아
  결과로 내라")이 실제로는 `common_centroid_layout()`에만 적용됐고
  `interdigitate_layout()`에는 통합된 적이 없었음을 코드로 재확인(자체 self-test 외 어디서도
  호출되지 않는 유틸이었고, docstring도 "무효하면 `common_centroid_layout(n_rows=1)`을
  대신 쓸 것"이라고 한 단계 위로 리다이렉트만 해뒀을 뿐이었다).

  **구현**: `interdigitate_layout(transistors, base=None, repeat=None) -> dict`로 시그니처를
  `common_centroid_layout()`와 동일한 스타일(`names`/`counts` 분리 인자 대신
  `Transistor` 리스트 하나)로 바꾸고, 반환도 동일 스키마(`rows`/`method`/`crossover_count`/
  `residual`/`isolated_pairs`)로 통일했다. `_try_interdigitation_table_match()`(`_try_
  pattern_table_match()`와 대칭 구조) 신설 — `base` 지정 시 `repeat`을 생략하면 표 전체를
  자동 탐색해 소자의 실제 `n_fingers`와 정확히 맞고 hub-leaf로도 유효한 항목을 찾는다
  (`method="pattern_table"`). 안 맞으면(또는 `base` 자체가 없으면) 기존 `_repair_row_
  parity()`+`_build_rows_from_shares()`/`_build_rows_from_shares_with_crossover()`(모두
  `common_centroid_layout()`의 탐색 경로가 이미 쓰던 헬퍼, 새 코드 추가 없이 그대로
  재사용)로 단일 행을 직접 구성·검증하고 필요하면 crossover 폴백까지 쓴다
  (`method="search"`). 이 과정에서 자연스럽게 옛 "base 없이는 정확히 2소자만" 제약도
  사라졌다 — `_build_rows_from_shares*()`가 애초에 Counter 기반이라 N>=1 소자 전부 지원.
  옛 round-robin 전용 `_proportional_round_robin()` 직접 계산도 더는 안 쓴다(그래프
  기반 구성이 개수만 보고 최적 순서를 자체적으로 찾아내므로 불필요).

  self-test: Test 12.6을 새 스키마로 전면 재작성(표 매칭 성공/실패, 3소자 무효 표가
  crossover 폴백으로 성공, base 없이 3소자도 이제 성공 — 예전엔 `ValueError`였던 케이스가
  base="ABC"와 정확히 같은 결과로 수렴함을 확인). Test 12.11(32개 base×repeat 전수 스윕)을
  `_hubleaf_sequence_node_path()` 외부 호출 방식에서 `interdigitate_layout()` 직접 호출로
  재작성 — 7개는 `method="pattern_table"`, 나머지 25개는 `method="search"`로 자동
  폴백해 **32개 전부 예외 없이 성공**함을 확인(이전엔 무효 여부만 확인하고 실제 배치는
  안 만들어줬다). 전체 self-test(`stick_diagram.py`/`sizing_recipe.py`) exit 0 재확인.
  `function-selection-map.md`/`stick-diagram-euler-layout.md`(§2.5.5/§2.7.2/§2.7.3/Test
  요약)의 옛 시그니처·"검증은 호출자 책임" 서술을 전부 갱신.

  **교훈**: naming 비일관성 지적("layout이 붙었는데 왜 하나는 없나")이 단순한 스타일
  문제가 아니라 실제 기능 격차(한쪽만 crossover 폴백+내부 검증을 갖춤)를 가리키는
  신호였다 — 사용자가 "fallback 있잖아"/"crossover로 fail 없애라고 했잖아"라고 되물었을
  때 바로 동의하지 않고 코드를 다시 열어 실제로 있는지 확인한 뒤(없었다) 정정한 것이,
  이 세션 내내 지켜온 "가정하지 말고 근거로 답하라" 원칙이 여기서도 실제로 틀린 전제를
  잡아낸 사례다.

- 2026-07-28 (37차, `common_centroid_layout()` 완전 제거 — `common_centroid_layout()`
  하나로 흡수 통합): 36차(탐색 경로 crossover 통합)까지 마친 뒤 사용자가 "common_centroid_
  layout은 이제 필요없지 않아?"라고 질문. 실측 비교 결과 `pattern_key=None` 경로(회전
  기반, N=2 대칭)는 nway와 완전히 동일한 출력을 내 중복이었지만, `pattern_key=...` 경로
  (`COMMON_CENTROID_PATTERNS` 문헌 표 기반, 예: `AAB`/`BAA`=2:1 비율)는 **중복이 아니었다**
  — 2:1 비율 케이스에서 nway 탐색 경로는 잔차 0.75까지 나오는데 표 경로는 잔차 정확히 0을
  낸다(직접 실행으로 확인, 가정 없이). 이 발견을 AskUserQuestion으로 "중복만 제거 vs 둘 다
  유지" 두 선택지로 물었으나 사용자가 거부하고 명확화를 요구, 이어서 "기능을 흡수해서
  common_centroid_layout만 남기면 안 되나?"로 최종 방향 확정 — 표 경로의 가치까지
  nway 안으로 흡수하고 옛 함수는 완전히 삭제하는 것.

  **구현**: `_try_pattern_table_match(names, leafs, hub_net, counts)` 신설 — N=2 전용,
  `COMMON_CENTROID_PATTERNS`의 2-소자 항목(3-소자 `ABCCBA`류는 명시적으로 skip)을 순회하며
  개수(`counts`)에 맞는 repeat를 찾아 두 가지 이름 순서(A/B ↔ B/A)로 각각
  `_common_centroid_from_pattern_table()`(기존 헬퍼, 그대로 유지)을 시도, 성공하면 반환,
  실패(`ValueError`, 예: `ABA`/`BAB`류 hub-leaf 무효)하면 계속 탐색, 끝까지 없으면 `None`
  (호출자가 탐색 경로로 폴백). `common_centroid_layout()`의 dispatch를 3단계로 재구성:
  ①`target_rows==n and all_equal` → 회전 정확 경로(`method="rotation_exact"`) ②`n==2 and
  target_rows==2` → `_try_pattern_table_match()`(`method="pattern_table"`, 실패시 ③으로)
  ③그 외 전부 → 탐색 경로(`method="search"`). `common_centroid_layout()`과
  `_common_centroid_from_graph()`(2-소자 전용 그래프 경로, `_common_centroid_nway_exact()`에
  완전히 superseded됨을 이미 확인한 상태였음) 둘 다 파일에서 완전히 삭제.

  self-test: Test 11을 `_common_centroid_from_pattern_table()` 직접 호출로 재작성
  (ABBA/BAAB 유효성, ABA/BAB 거부, ABCCBA 3-소자 거부 확인), Test 12를 `Transistor` 리스트
  기반 `common_centroid_layout()` 호출(9:9 홀수 케이스, `method=="rotation_exact"`
  단언)로 재작성, Test 12.5를 표 경로 vs nway 비교 + 2:1 비율 케이스에서 `method=
  "pattern_table"`/잔차 0.0 확인(구 탐색 경로의 잘못된 잔차 0.75와 대조)으로 재작성.
  branch_symmetric 테스트 구간의 옛 `common_centroid_layout()` 호출 2곳(M3/M4, 대응 쌍)도
  `common_centroid_layout([Transistor(...), Transistor(...)])` + `rows[i]
  ["transistor_sequence"].count(name)` 패턴으로 재작성. 전체 self-test(`stick_diagram.py`/
  `sizing_recipe.py`) exit 0 재확인. `function-selection-map.md`의 옛 `common_centroid_
  layout()` 단독 행 삭제 후 nway 행에 3단계 dispatch 설명으로 통합, `interdigitate_layout`/
  `run_topology_pipeline` 행의 잔여 참조도 `common_centroid_layout()`로 수정.

  **교훈**: "이 함수 이제 필요없지 않아?"라는 질문에 코드를 안 열어보고 "네, 중복이니
  삭제하겠습니다"라고 답했다면 `pattern_key=...` 경로의 잔차-0 이점을 통째로 잃을 뻔했다
  — 표면적으로 비슷해 보이는 두 함수도 실측 비교 전에는 "중복"이라 단정하지 말 것. 또한
  사용자가 "옵션 중 하나를 고르라"는 AskUserQuestion을 거부하고 명확화를 요구했을 때,
  제시한 선택지 자체가 사용자가 원하는 답(완전 흡수)을 담고 있지 않았다는 신호였다 — 선택지
  설계가 실제 요구를 못 담아내면 사용자는 고르지 않고 재질문한다는 것을 확인.

- 2026-07-28 (36차, `common_centroid_layout()` **탐색 경로**에도 crossover 폴백
  통합): 35차(회전 경로 통합) 직후 사용자가 "탐색 경로에도 crossover 폴백 추가해줘"라고
  요구. `_build_rows_from_shares_with_crossover()`를 신설 — 행 하나가 `_repair_row_
  parity()`(물리적 비용 없는 인접 행 간 재배정)로도 0-crossover가 안 되면
  `find_min_crossover_layout()`으로 최소 crossover 배치를 대신 쓴다(이 폴백 자체는
  그래프 이론상 항상 성공). `_common_centroid_nway_search()`의 candidate 정렬 기준을
  `(isolated_pairs, residual)`에서 **`(crossover_count, isolated_pairs, residual)`**
  로 확장(사전식 — crossover가 더 필요한 후보는 잔차/격리가 아무리 좋아도 항상 후순위,
  0-crossover phase가 하나라도 있으면 그게 항상 우선). `_build_rows_from_shares()`(기존
  0-crossover 전용, `None` 반환 시 폴백 트리거)는 그대로 유지 — 우선순위 구조(0-crossover
  먼저 시도, 안 되면 crossover)를 그대로 재사용.

  self-test: Test 12.10(n_rows!=N 260개 조합 전수 스윕)의 검증 로직을 flat
  `transistor_sequence` 단일-walk 검사에서 **각 `segments`를 독립적으로 검증**하는
  방식으로 수정(crossover가 있으면 flat 시퀀스 자체는 더 이상 단일 연속 walk가 아닌
  게 정상이므로) — 수정 전엔 이 스키마 불일치로 107건이 "무효 walk"로 오탐됐었다,
  수정 후 크래시/구조 오류/ValueError 전부 0건(crossover 총합 926으로 실제 폴백이 널리
  쓰였음도 확인). 추가로 별도 스크립트로 N=2~6 무작위 100개 조합(임의 개수+임의
  `n_rows`) 전수 스윕 — ValueError/실패 0건. 전체 self-test(`stick_diagram.py`/
  `sizing_recipe.py`) exit 0 재확인. function-selection-map.md 반영.

  **교훈**: 회전 경로에 적용한 변경(35차)을 탐색 경로에도 그대로 옮기면서, 그 경로의
  **자체 검증 테스트(Test 12.10)가 옛 스키마(단일 flat walk) 가정에 의존하고 있었다**는
  걸 뒤늦게 발견 — 새 기능을 기존 코드에 통합할 때는 그 코드가 의존하는 다른 곳(이번엔
  같은 파일의 self-test)의 암묵적 가정까지 함께 점검해야 한다는 걸 다시 확인했다.
- 2026-07-28 (35차, `common_centroid_layout()` 회전 경로에 `find_min_crossover_
  layout()` 통합 — "진짜 불가능" 사례 전부 crossover로 해결): 34차 직후 사용자가
  "common_centroid도 이 최소 crossover routing 조건을 추가하면 어떻게 되지?"라고 질문
  — 코드부터 짜지 않고 프로토타입으로 먼저 확인: N=3,count=3(예전 "진짜 불가능") 사례를
  `find_min_crossover_layout()`으로 만든 row_0(crossover=1)에 기존 회전(relabeling)을
  그대로 적용해보니 **잔차가 여전히 정확히 0**임을 확인했다 — 회전 증명(모든 소자가
  모든 열을 정확히 1번씩 방문)은 row_0가 어떻게 계산됐든(그래프 직접 계산이든 crossover를
  섞어 만든 것이든) 순수 relabeling이라는 사실만으로 성립하기 때문. 이전 34차에서 "진짜
  불가능"으로 판정했던 10개 조합(N=3~6, count가 N에 매우 가까운 경우) 전부 crossover
  1~2개로 해결됨을 실측 확인한 뒤 사용자 승인을 받아 통합.

  **구현**: `_common_centroid_nway_exact()`의 우선순위를 (1) 균등 분배 0-crossover 시도
  → (2) `_fix_block_parity()` 홀짝 보정 0-crossover 재시도 → (3) 그래도 안 되면
  `find_min_crossover_layout()`으로 최소 crossover 배치 폴백(신설) 순으로 재구성 —
  (3)까지 왔다는 건 홀수차수 노드가 4개 이상이라는 뜻이라 `find_min_crossover_layout()`은
  그래프 이론상 항상 성공한다, 즉 **`count>=N`이기만 하면 이 경로는 이제 절대 실패하지
  않는다**. 반환 스키마에 각 행마다 `"segments"`(crossover 경계로 나뉜 조각)/
  `"crossover_after"`(그 인덱스 다음에 crossover가 필요하다는 표시)를 추가하고, 최상위에
  `"crossover_count"`를 추가(탐색 경로도 스키마 일관성을 위해 항상 `crossover_count=0`/
  `segments`=행 전체 1개짜리로 맞춤 — 탐색 경로 자체엔 아직 crossover 폴백을 안 붙임).

  self-test에 Test 12.9b 신설 — 이전 "진짜 불가능" 10개 조합 전부 재확인(crossover_
  count>0, residual=0.0, 각 segment 독립 유효성) + 기존 0-crossover 케이스(N=2,count=4)
  무회귀 확인. 추가로 별도 스크립트로 N=2~8 × count=N~N+14(105개 조합) 전수 스윕 —
  실패 0건. 전체 self-test(`stick_diagram.py`/`sizing_recipe.py`) exit 0 재확인.
  function-selection-map.md 반영.

  **교훈**: "A에서 발견한 걸 B에도 적용하면?"류 질문을 받으면, 두 메커니즘이 서로 독립적
  으로 호환되는지(이번엔 "회전 증명이 row_0의 계산 방식에 의존하지 않는다"는 성질)를
  코드로 직접 확인한 뒤 통합하는 게, "당연히 되겠지"라고 가정하고 바로 합치는 것보다
  안전하다 — 이번엔 실제로 프로토타입에서 잔차=0이 그대로 유지됨을 확인했기 때문에
  안심하고 통합할 수 있었다.
- 2026-07-28 (34차, `find_min_crossover_layout()` 신설 — hub-leaf가 단일 diffusion으로
  안 될 때 최소 crossover routing 배치 계산): 33차(외부 문헌으로 "무효"=crossover 필요
  확인) 직후 사용자가 "이 함수에서 최소한의 crossover routing이 생기는 조합을 찾아 결과로
  내는 것으로 만들어달라, crossover 개수도 표시, 우선순위는 crossover가 안 생기는 연속
  diffusion"이라고 요구 — 그래프 이론(route inspection/Chinese postman 문제의 T-join
  표준 결과: 연결된 그래프에서 홀수차수 노드가 2m개면 전체 edge를 정확히 m개의 trail로
  쪼갤 수 있고 그보다 적게는 안 됨)을 적용해 `find_min_crossover_layout()`을 신설. 원리:
  홀수차수 노드 2m개를 2개씩 짝지어 m개의 가상 edge를 그래프에 추가하면 전체가 오일러
  회로가 되고, `hierholzer()`로 그 회로를 계산한 뒤 가상 edge 지점마다 끊어(가상 edge는
  버림) m개의 실제 trail로 분해한다 — crossover 개수 = m-1(trail을 이어붙이는 접합
  개수). 우선순위는 항상 0-crossover(기존 `check_euler_condition()`/`hierholzer()`가 이미
  처리하는 circuit/path 경우)를 먼저 시도하고, impossible일 때만 이 분해로 넘어간다.
  프로토타입으로 먼저 검증(ABC 3소자 1개씩 → crossover=1, ABCD → crossover=1, 6소자 →
  crossover=2, 전부 예측과 일치) 후 실제 구현, self-test(Test 12.12)에 이 사례들 + 각
  segment가 독립적으로 유효한 walk임을 `_hubleaf_sequence_node_path()`로 재확인 + N=1~6
  균등/불균등 개수 105개 조합 전수 스윕(공식 `crossover_count == max(0, odd_nodes//2-1)`
  과 정확히 일치, 소자 총 개수 보존, 각 segment 유효성)을 별도 스크립트로 검증 후 추가.
  function-selection-map.md 반영. **교훈**: 그래프 이론에 이미 알려진 정리(T-join/route
  inspection)가 적용되는 문제라는 걸 알아본 뒤에는, 손으로 알고리즘을 새로 고안하지 않고
  그 정리를 그대로 구현하는 게 가장 안전하다 — 직접 프로토타입으로 여러 사례(3,4,6소자)를
  검증해 공식이 실제로 들어맞는지 먼저 확인한 뒤에야 파일에 반영했다.
- 2026-07-28 (33차, `INTERDIGITATION_PATTERNS` 표 hub-leaf 유효성 전수 스윕 + 외부 문헌
  조사 — "무효"의 의미 정정): 사용자가 "n_rows=1인 경우는 interdigitate_layout()가 되는 것
  아니냐"고 질문 — 실측 비교 결과 다름을 확인(interdigitate_layout round-robin은 `ABAB...`로
  hub-leaf 무효, `common_centroid_layout(n_rows=1)`은 `build_graph`+`hierholzer`로
  실제 유효한 `ABBA`형 블록을 계산). 이어서 "interdigitate_layout도 패턴이 있잖아, 그건 오일러
  trail이 되는 것 아니냐"는 질문에 `base="AB"`만 repeat 1~3에서 우연히 유효하고 repeat=4·
  `ABA`는 무효임을 실측 확인. 사용자가 "이것도 n-way로 확장해서 검증해봐"라고 요구 —
  `INTERDIGITATION_PATTERNS`의 모든 (base,repeat) 32개 조합을 `_hubleaf_sequence_node_
  path()`로 전수 검증한 결과 **7개만 유효**(`base="A"` 전부 + `AB`의 repeat 1,2,3) —
  `ABC`/`ABCD`(3~4소자, 전체 repeat)와 `ABA`/`ABABA`/`AABA`/`AABAA`(2소자, 전체 repeat)는
  전부 무효. 사용자가 "외부 문헌을 조사해서 interdigitate_layout pattern이 어떻게 사용되는지
  확인해봐"라고 요구 — WebSearch로 AnalogHub("Matching patterns in layout")과 current
  mirror layout 문헌을 조사한 결과, 이 3소자 이상 패턴은 실무에서 안 쓰이는 게 아니라
  **crossover routing**(열 사이를 metal+via로 건너뛰는 배선)으로 구현하는 게 표준 기법임을
  확인 — 이 codebase의 hub-leaf 검증(`_hubleaf_sequence_node_path()`)은 "crossover 없이
  단일 연속 diffusion(1개 metal layer)만으로 되는가"라는 더 좁은 질문만 확인하는 것이지,
  "실무에서 못 쓰는 패턴"이라는 뜻이 아니었다. `interdigitate_layout()`/function-selection-map.md
  docstring에 이 구분을 명시적으로 반영(무효=crossover 필요, 실무 사용 불가가 아님).
  self-test(Test 12.11)에 32개 조합 전수 스윕 + 예상 유효/무효 집합과 정확히 일치하는지
  회귀 추가. **교훈**: "무효"라는 한 단어짜리 판정이 "이 세부 검증 기준에서 무효"인지
  "실무에서 못 쓴다"인지 구분하지 않으면 오해를 낳는다 — 외부 문헌으로 검증하니 이번
  경우 후자가 아니라 전자였다. 코드 안에서만 확인하고 끝내지 않고 실제 업계 관행까지
  조사한 게 이 구분을 정확히 하는 데 필요했다.
- 2026-07-28 (32차, `common_centroid_layout()` — `n_rows != N` 전수 스윕(N=2~6,
  n_rows=1~2N+1, 260개 조합), 잔차 지표의 두 가지 결함 발견/수정): 31차 직후 사용자가
  "나머지 n_rows도 스윕해봐(N보다 크거나 작은 경우)"라고 요구 — 크래시/구조 오류
  (무효 walk, 개수·행수 불일치)는 0건이었지만 **잔차 지표 자체에 두 가지 결함**을 발견.
  (1) `_common_centroid_residual()`이 길이 1인 행을 통째로 건너뛰는데, 어떤 소자가
  길이 1인 행에만 등장하고 길이 2 이상인 행엔 전혀 없으면 그 소자가 잔차 계산에서
  완전히 빠져(실측: A만 있는 길이2 행 + B만 있는 길이1 행 2개로 구성하면 residual=0.0 —
  B가 통째로 안 보이는데 "완벽"으로 잘못 보고됨) — 길이 1 행에 **중립값 0.5**(왼쪽/
  오른쪽 어느 쪽으로도 안 치우친 값)를 부여해 그 소자가 반드시 잡히도록 수정.
  (2) 더 근본적인 한계: 소자 하나가 통째로 자기 행에만 격리되면(다른 소자와 단 한 번도
  같은 행에 있어본 적 없음, 예: N=2/count=2/n_rows=4 -> `['A'],['B'],['A'],['B']`) 그
  자체는 각자 행 내부에서 대칭으로 보여 (1)을 고친 뒤에도 residual=0.0이 나올 수 있다 —
  n_rows가 총 finger 수 대비 너무 많으면(모든 행 길이가 1) 구조적으로 피할 수 없는
  상황. `_count_isolated_pairs()`(모든 소자쌍이 적어도 한 행에서 공존했는지 세는 함수)를
  신설해 `_common_centroid_nway_search()`의 정렬 기준을 `residual` 단독에서
  `(isolated_pairs, residual)` 튜플(사전식, 격리 적은 쪽 우선)로 바꾸고, 반환값에
  `"isolated_pairs"` 필드를 추가해 이 상황을 정직하게 드러낸다(회전 경로는 항상 N개
  소자 전부가 매 행에 있어 `isolated_pairs=0`이 보장됨을 함께 명시). self-test(Test
  12.10)에 전수 스윕(크래시/구조 오류 0건 확인) + 잔차 은닉 사례 재현/수정 확인 +
  격리 사례가 `isolated_pairs`로 드러남을 보이는 회귀 추가. **정직하게 남긴 한계**:
  `isolated_pairs`를 1순위로 넣어도, n_rows가 구조적으로 격리를 강제하는 경우(행 길이가
  전부 1일 수밖에 없는 경우)는 어떤 phase를 골라도 못 피한다 — 이건 탐색의 결함이
  아니라 그 `n_rows` 자체가 물리적으로 무리한 요구라는 신호로 이해해야 한다.
  **교훈**: "지표가 0이다"를 "완벽하다"로 곧이곧대로 믿지 말고, 그 지표가 측정하지
  못하는 실패 양상(이번엔 "격리")이 있는지 스스로 의심하는 습관이 필요하다 — 이번에도
  사용자가 스윕을 요구하지 않았다면 이 결함은 발견되지 않았을 것이다.
- 2026-07-28 (31차, `common_centroid_layout()` — 균등분배가 우연히 전부 홀수면
  포기하던 2차 버그 수정, N=2~6 전수 스윕): 30차 수정 직후 사용자가 "다른 n_rows 값
  (3,4,5)에서도 같은 버그 없는지 다 스윕해봐"라고 요구 — N=2~6 × count 다양(11가지)
  총 53개 조합을 `n_rows==N`으로 전수 실행. 30차 버그(dispatch 오류)의 재발은 없었지만
  (0건), **새로운 문제 발견**: N=4,count=20처럼 "최대한 균등하게" 나눈 배분([5,5,5,5])이
  우연히 전부 홀수라 오일러 조건이 깨지면 바로 `ValueError`를 냈는데, 실제로는 조금 덜
  균등해도 홀짝만 맞는 배분([6,6,4,4], 실측으로 유효 확인)이 있으면 회전 자체는 row_0의
  블록 배분과 무관하게 항상 잔차 0을 보장하므로(`_common_centroid_nway_exact()` docstring의
  증명) 그 대안을 시도조차 안 하고 포기하는 게 불필요한 실패였다(N=4/count=20,101,
  N=6/count=20,101 총 4건 확인). **해결**: `_fix_block_parity()` 신설 — 홀수 항목이
  2개보다 많으면(총합의 홀짝이 불변량이므로 최소 0개 또는 1개까지) 두 개씩 짝지어 1개씩
  주고받아(하나 +1, 하나 -1, 합계 불변) 짝수로 만든다. 오일러 조건 실패 시 이 보정을
  먼저 시도한 뒤에도 안 되면 그제서야 `ValueError`. 전수 스윕에서 남은 10건(예: N=3/
  count=3, N=4/count=4,5 등)은 재확인 결과 count가 n에 매우 가까워 **다른 partition
  자체가 수학적으로 존재하지 않는**(예: 4개 소자 합=5면 {2,1,1,1}이 유일한 분할) 진짜
  불가능 사례임을 확인 — 버그 아님. **부수 발견**: `count < n`(소자별 개수가 소자 수보다
  작음, 예: N=4에 각 2개씩)이면 균등분배 시 일부가 0개가 돼 `Transistor.__post_init__`의
  "n_fingers>=1" 체크에서 불명확한 에러로 죽던 것도 함께 발견해 `_common_centroid_nway_
  exact()` 진입부에 명확한 사전 `ValueError`로 교체. self-test(Test 12.9)에 N=2~6 전수
  스윕(회귀 없음 확인) + N=4/count=20 보정 성공 회귀 + count<n 명확한 에러 확인 추가.
  **교훈**: 버그를 하나 고친 뒤 "이 수정이 다른 파라미터 범위에서도 성립하는가"를 실제로
  스윕해서 재확인하는 게 중요하다 — 이번에도 원래 버그와는 다른 새 버그가 스윕 도중
  발견됐다(30차 버그의 재발이 아니라, 30차를 고치는 과정에서 건드린 코드 경로의 별도
  결함).
- 2026-07-28 (30차, `common_centroid_layout()` dispatch 버그 수정 — `n_rows`를
  N과 같게 명시해도 탐색 경로로 새던 문제): 29차 직후 사용자가 "2행/2소자처럼 swap으로
  해결되는 경우, finger를 늘려가며 실제로 최적이 나오는지 확인해보라"고 요구 — 직접
  스윕(`n_fingers`=2,4,6,8,10,20,50,101)해보니 `n_rows=2`를 **명시**하면(N=2와 정확히
  같은 값인데도) 탐색 경로로 가서 `n_fingers=2`일 때 residual=1.0(완전 실패)까지 나오는
  실제 버그를 발견. 원인: 그 시점 dispatch 조건이 `if n_rows is None and all_equal`이라
  "명시된 n_rows가 우연히 N과 같은" 경우를 걸러내지 못하고 무조건 탐색 경로로 보냈다.
  근본 원인은 탐색 경로(`_proportional_round_robin()`+`_slice_into_rows()`)가
  **하나의 선형(주기적) 시퀀스를 자르는 방식**이라 "두 행이 서로 swap된 관계"인 후보를
  구조적으로 생성할 수 없다는 것(실측: `M2,M2b,M2,M2b`를 2등분하면 phase를 몇으로
  바꿔도 항상 두 조각이 똑같다 — swap(`M2,M2b`/`M2b,M2`)은 이 방식의 candidate 공간에
  아예 없다). **해결**: dispatch 조건을 `if n_rows is None and all_equal`에서
  `if target_rows == n and all_equal`(n_rows를 결정한 뒤 검사)로 변경 — target_rows가
  소자 수와 같고 개수가 균등하면 `n_rows`를 사용자가 명시했든 기본값이든 항상 증명된
  최적(회전 경로, 잔차 0)을 쓴다. self-test에 이 버그를 정확히 재현하는 회귀
  (`n_fingers` 8가지 값 스윕, 전부 `method=rotation_exact`+`residual=0.0` 확인) 추가.
  **교훈**: "행 개수를 자유롭게 지정할 수 있게 해달라"는 요청을 구현할 때, "명시된 값이
  우연히 기존 특수 케이스와 같을 수도 있다"는 경계 조건을 실제로 스윕해서 확인하지 않으면
  이런 회귀가 조용히 남는다 — 사용자가 직접 finger 수를 늘려가며 확인해보라고 요구한
  덕분에 발견됐다.
- 2026-07-28 (29차, `common_centroid_layout()` 일반화 — 소자 개수/`n_rows` 자유
  지정, 휴리스틱 탐색 경로 추가): 28차 직후 사용자가 "이 함수를 `common_centroid_
  layout()`에 일반화 통합하고, 입력은 소자 N개+connectivity로, row 개수를 안 정하면
  최적안을, 정하면 그 제약 안에서 최적안을 내도록" 요청. 검토 결과 `common_centroid_
  layout()`(2-소자, 표/그래프 dispatch)과 합치기보다는 `common_centroid_layout()`
  자체를 일반화하는 게 더 적절하다고 판단(표 경로는 문헌 패턴 인용이 목적이라 성격이
  다름, 사용자도 "새 함수로 구현" 확인) — 시그니처를 `names/leafs/hub_net/count`에서
  `transistors: list, n_rows=None`으로 변경(Transistor 리스트에서 hub_net/leaf_of/counts를
  직접 추론). 소자 개수가 전부 같고 `n_rows` 미지정이면 기존 회전 경로(잔차 0, 증명된
  최적, `_common_centroid_nway_exact()`로 이름만 정리)를 그대로 쓴다. 그 외(개수가 다르거나
  `n_rows`를 N과 다르게 지정)는 새로 만든 휴리스틱 탐색 경로(`_common_centroid_nway_
  search()`) — 소자를 비율에 맞게 최대한 고르게 섞은 순서(`_proportional_round_robin()`,
  2-소자 `interdigitate_layout()`의 round-robin을 N-소자로 일반화)를 만들어 `n_rows`개로 균등
  분할(`_slice_into_rows()`)하고 잔차(`_common_centroid_residual()`)가 가장 작은 절단
  지점(phase)을 채택한다. **실측으로 발견한 문제와 대응**: 단순 분할만으로는 홀수차수
  leaf가 3개 이상이 되는 조합(예: A=6/B=4/C=2를 4행으로 나눌 때)이 나와 모든 phase가
  오일러 조건을 못 만족하는 경우를 확인 — 인접 행끼리 소자 1개씩 주고받는 보정
  (`_repair_row_parity()`)을 추가해 해결(잔차 0.7→0.17로 개선도 동반). self-test(Test
  12.7 새 시그니처로 갱신 + Test 12.8 신설 — 개수 다름/`n_rows`<N/`n_rows`>N/`n_rows`=N
  명시 4가지 케이스, 각 행을 `_hubleaf_sequence_node_path()`로 독립 재검증) 전부 통과.
  **한계를 정직하게 문서화**: 이 탐색은 증명된 최적이 아니라 candidate 생성+objective
  정렬 방식(`search_stack_finger_w()` 등과 같은 철학)이고, 잔차 지표가 행 내부 x위치만
  비교해 소자 개수 편차가 크면 y방향 비대칭까지는 못 잡는다는 한계를 반환값(`residual`/
  `method`)과 docstring에 명시. function-selection-map.md/stick-diagram-euler-layout.md/
  gap-findings.md 반영.
- 2026-07-28 (28차, `common_centroid_layout()` 신설 — hub-leaf 3-소자 이상 진짜
  common-centroid): 27차에서 사용자가 "`common_centroid_layout()`이 3-소자 패턴을 못 쓰는
  거냐"고 질문 — 확인 결과 맞다고 답한 뒤, "그럼 3-소자 지원을 추가해달라"는 요청에 착수하기
  전 `COMMON_CENTROID_PATTERNS`의 3-소자 패턴(`ABCCBA`/`CBAABC`)을 `_hubleaf_sequence_
  node_path()`로 실제 검증하니 **모든 repeat에서 실현 불가능**(`None`)함을 발견 — hub-leaf
  구조는 서로 다른 leaf로 전환할 때 반드시 hub를 거쳐야 하는데, 3개 leaf 사이에서는 이
  조건이 항상 깨진다(2-소자 `ABA`/`BAB` 불가능과 같은 이유가 더 강하게 나타남). 사용자에게
  "3-소자 hub-leaf 자체를 재조사"하도록 확인받아, 진짜 3-way hub-leaf 구조가 가능한지(블록
  형태 `AABBCC`는 유효 경로임을 확인) + 2행만으로 common-centroid가 되는지(수식/실측 둘 다
  확인한 결과 **2행으로는 3개 소자 열평균이 절대 안 맞고, N개 소자엔 N개 행이 필요**함을
  발견)까지 재확인 후 사용자 승인을 받아 `common_centroid_layout()`를 새 함수로
  구현했다. 원리: N개 leaf가 전부 hub 하나에만 연결되므로 이름을 순환 회전해도 그래프
  automorphism이 성립하고(swap의 N-소자 일반화), row_0을 실제 계산한 뒤 나머지 N-1개 행은
  회전만으로 생성하면 N개 행 전체에서 모든 소자가 모든 열을 정확히 1번씩 지나가 열평균이
  항상 일치함을 이론(각 열마다 회전이 정확히 한 소자만 배정한다는 증명)과 실측(N=3, 열평균
  전부 2.5) 둘 다로 확인. self-test(Test 12.7)에 N=3 검증 + 각 행 독립 재검증(구성 로직을
  그냥 믿지 않고 `_hubleaf_sequence_node_path()`로 재확인) + 3-소자 표 패턴이 실제로 무효임을
  보여주는 대조군 + N=2 회귀(swap과 동등) + 실패 케이스(오일러 불가능/길이 불일치/중복
  이름) 전부 추가. function-selection-map.md §... 반영. **교훈**: "함수를 확장해달라"는
  요청을 받으면 확장 범위(파라미터 추가)만 보지 말고, 그 확장이 실제로 의미 있는 결과를
  낼 수 있는지(이 경우 표의 3-소자 패턴 자체가 hub-leaf에 안 맞음)부터 코드로 검증할 것 —
  "호출은 되지만 항상 실패하는 기능"을 만드는 건 지원이 아니다.
- 2026-07-28 (27차, 함수 병합 — "유사 기능은 하나가 파라미터로 분기" 관점 재감사, 실제 병합
  2건 + hub_merge 누락 발견/수정): 26차에서 "확실한 중복만 헬퍼로 뽑고 3건은 기각"했는데,
  사용자가 "포팅 후 삭제가 아니라 하나의 함수가 분기해서 두 기능을 다 하는 병합"으로 의도를
  정정하며 common_centroid 쌍(unit_cell_common_centroid_layout/common_centroid_2row)의 병합
  가능성을 재질문 — 실제로 코드를 짜보니 두 내부 알고리즘은 그대로 두고 진입점만 합치는
  낮은 리스크 리팩터임을 확인. (1) **`common_centroid_layout(pattern_key=None)`**로 병합 —
  `pattern_key` 지정 시 표 기반(비율/카탈로그 패턴), 미지정 시 그래프 기반(임의 1:1 짝수
  조합)으로 분기. 병합 중 실측으로 대칭(1:1) 케이스에서는 두 경로가 문자 그대로 같은 패턴을
  냄을 확인(행 순서만 다름 — 이전 세션 답변 "서로 다른 결과"는 오답이었다, 실제 실행으로
  정정). 또한 표에 3-소자 패턴(`ABCCBA`/`CBAABC`)이 있는데 옛 함수는 그걸 주면 `KeyError`로
  불명확하게 죽는 잠재 버그를 발견 — 명확한 `ValueError`로 교체. (2) 같은 관점 재검토 중
  `expand_interdigitation_pattern`/`interleave_counts` 쌍도 정확히 같은 구조(표 기반
  비율/다소자 vs round-robin 임의개수)임을 새로 발견 — **`interdigitate_layout(names, base=,
  repeat=, counts=)`**로 병합. 둘 다 이 파일 안에서 실제 호출된 적이 없었다(감사 중 발견) —
  병합하며 두 경로 모두에 self-test를 처음으로 추가. (3) 병합 과정에서
  `verify_symmetry_dispositions()`가 `find_hub_merge_candidates()`(hub_merge 후보)를 아예
  체크하지 않는다는 걸 발견(사고1과 같은 종류의 gap) — 세 tag(`current_mirror`/`diff_pair`/
  `hub_merge`) 전부 검사하도록 수정. 실제 `current_reuse_telescopic_ota.topology.json`에
  재적용하니 6개 hub_merge 후보(vdd/gnd 공급 레일 공유 2건, 캐스코드 스택 중간 노드 공유
  2건, 이미 current_mirror/diff_pair로 처리된 것과 같은 소자쌍이 hub_merge로도 잡힌 2건)가
  미처리로 드러나 전부 `false_positive_shared_supply_rail`/`false_positive_cascode_stack_node`
  등 근거와 함께 dispositions에 추가. 전체 self-test(stick_diagram.py/sizing_recipe.py 둘 다
  exit 0) + JSON 유효성 재확인. function-selection-map.md/consistency-map.md/
  design-report-spec.md/SKILL.md/stick-diagram-euler-layout.md 전부 동기화(단, PRE-FLIGHT
  사고 번호가 붙은 순수 역사적 서술은 원래 함수명 그대로 보존 — 그 시점에 실제로 존재했던
  이름이므로).
- 2026-07-28 (26차, 함수 중복 감사 — 확실한 중복 2건 헬퍼 추출, 나머지는 검증 후 기각):
  사용자가 "모든 함수를 전수로 살펴 중복/불필요 함수를 찾고, 27건 PRE-FLIGHT 사고와
  교차검증해서 승인 후 고치라"고 요구 — stick_diagram.py 46개/sizing_recipe.py 13개/
  topology_library.py 5개 전 함수를 나열하고 실제 코드 바디를 읽어 대조했다. **확인된 진짜
  중복 2건**: (a) net 대소문자 스캔 로직이 `run_full_circuit_audit()` 2번 체크와
  `verify_symmetry_dispositions()`(25차 이전 24차에서 신설) 0단계에 복붙돼 있었다 —
  `_scan_case_collisions(net_names)` 헬퍼로 추출해 양쪽이 호출하도록 교체. (b)
  `skyline_pack_best_width()`/`pack_to_height()`가 "폭 후보를 `width_steps`개로 스윕하며
  `skyline_pack()` 반복 호출" 루프를 복붙 — `_sweep_widths()` 헬퍼로 추출, 각 함수는 선택
  기준(ratio 최근접 vs target_height 이하 중 최소폭/배선비용)만 그 위에 적용하도록 교체.
  둘 다 순수 리팩터(동작 변화 없음), 전체 self-test(stick_diagram.py/sizing_recipe.py 둘 다
  exit 0) 재확인 완료. **검증 후 기각된 후보 3건**: `search_unit_cell_sizing`/
  `search_stack_finger_w`/`search_shared_finger_w`(unit-cell/Case A/Case B로 각각 다른
  제약이라 통합 시 오히려 나빠짐), `unit_cell_common_centroid_layout` vs
  `common_centroid_2row`(후자가 임의 개수까지 처리하는 상위호환이지만 전자는 논문 패턴표
  대조용으로 별도 존재 이유 있음 — docstring 보강만 남겨둠), missing-names set-difference
  패턴(`check_stick_diagram_coverage()` vs `run_topology_pipeline()` 인라인 체크 — 각 1줄이라
  헬퍼 추출 실익 낮음, 보류). 27건 PRE-FLIGHT 사고 전체 재확인 결과, (a)를 제외한 나머지
  사고들이 만든 함수는 전부 그 시점에 없던 새 능력이었다(기존 함수로 풀 수 있었는데 새로
  만든 경우 없음) — 함수 삭제 대상 없음. function-selection-map.md/이 항목 반영.
- 2026-07-28 (25차, `run_topology_pipeline()`에 sizing_overrides 누락 검사 추가 — 사고27
  재발 방지, 자체 발견): 24차 직후 "나머지 중요 사고 방지 로직도 확인해보라"는 요구에 따라
  점검하다가, `run_topology_pipeline()`에 소자를 `sizing_overrides`에서 빠뜨려도 조용히
  `n_fingers=1`/`stack_id=None` 기본값으로 처리되고, `split_into_stacks()`가
  `stack_id=None` 소자를 `(kind,"unspecified")` 폴백 그룹으로 흡수해버려
  `check_stick_diagram_coverage()`가 "이름은 어딘가 있다"고 통과시키는 걸 실측으로 발견(M11로
  재현) — 사고27(사이징은 됐는데 layout이 통째로 빠짐)과 정확히 같은 실패 유형이 이 함수
  안에서 재발할 수 있었다. 함수 시작에 `missing_overrides = {t.name for t in transistors} -
  set(sizing_overrides.keys())` 체크를 추가해 비어있지 않으면 즉시 `ValueError`. Test 26.5로
  회귀 확인.
- 2026-07-28 (24차, `verify_symmetry_dispositions()`에 net 이름 대소문자 스캔 추가 —
  사고9 재발 방지): 23차(`linked_topology_files`) 직후 사용자가 "예전에 겪었던
  대소문자 문제(사고9 — 서로 다른 스크립트가 `Vbias1`/`vbias1`로 다르게 명명)가 이번에도
  반영됐냐"고 확인 — 실제로 **반영 안 돼 있었다**. `run_full_circuit_audit()`에는 이
  검사(2번 체크, net-name case consistency)가 있지만 새 topology-JSON 파이프라인엔 아예
  없었다. `linked_topology_files`로 여러 파일(서로 다른 시점/작성자 가능)을 병합하는
  기능을 막 추가한 직후라 이 위험이 특히 컸다. `verify_symmetry_dispositions()`의 0번
  단계로 net 이름 대소문자 스캔을 추가(자동 통일 없이 FAIL만 — 원본 수정은 사람 몫).
  self-test로 `Vbias1`/`vbias1` 불일치를 실제로 잡아내는지 확인, 기존 3개 topology JSON엔
  대소문자 문제 없음 확인. Design §4.5 3-2/function-selection-map.md §10 반영. 상세:
  gap-findings.md §9.
- 2026-07-28 (23차, `linked_topology_files` 신설 — 회로가 여러 JSON으로 쪼개져도 사고8
  재발 방지): 22차 직후 사용자가 "다단계 회로면 모든 단계로 확장해서 매칭관계를 따지도록
  강제하고 있냐"고 질문 — 지금까지 예제(folded_cascode/two_stage_ota/current_reuse_
  telescopic_ota)는 전부 회로 하나=파일 하나였기 때문에 `find_matching_candidates()`가
  항상 전체 netlist를 봤지만, 이건 "우연히 안전한" 구조이지 강제된 게 아니었다(향후 소자
  수가 많은 회로를 stage별로 여러 topology JSON으로 쪼개면 사고8이 재발할 위험). 사용자가
  구체적 해법을 제안 — "각 json에서 나머지 화일들을 연결하는 필드를 둬서, 읽을 때 전체를
  읽어서 전체구조를 한번에 보도록 강제". `load_topology()`에 `linked_topology_files`(형제
  파일 목록, 방사형 — 그룹 안 모든 파일이 서로를 전부 나열) 지원을 추가 — 이 필드가 있으면
  어느 형제 파일을 진입점으로 읽든 자동으로 전부 병합해서 반환한다. 합성 2-파일 테스트로
  "형제 파일을 자동으로 합치는지" + "cross-file matching 후보(MSIG/MBIAS1/MBIAS2가 서로
  다른 파일에 있어도 같은 gate net을 공유하면 찾아지는지)"를 self-test로 회귀 확인
  (Test 21.6). `_TEMPLATE.topology.json`/function-selection-map.md §10/Design §4.6 반영.
  기존 3개 example은 전부 단일 파일 유지(`linked_topology_files: []`) — 실제로 쪼갤 필요가
  생기기 전까지는 채우지 않는 게 기본.
- 2026-07-28 (22차, verify_symmetry_dispositions() 신설 — 매칭 후보 누락 방지 하드 게이트):
  21차 수정 직후 `current_reuse_telescopic_ota.topology.json`을 재검증하니
  `find_matching_candidates()`가 찾은 후보 중 여럿이 `matching_pairs`에 조용히 빠져
  있었다(M6/M8/M13 공유 Vbias1을 M8/M13만 기록, M27/M28/M29 3-leg 미러를 pairwise 2항목으로
  쪼개 기록). 사용자가 "이 함수는 후보만 추출하니, AI가 실제로 검증·확정한 후 JSON에
  기록하도록 강제하라"고 요구 — `run_full_circuit_audit()`의 "every candidate has a
  recorded disposition" 체크와 같은 원리를 `verify_symmetry_dispositions(transistors,
  matching_pairs, dispositions)`로 topology-authoring 단계에 이식(`detect_matching_
  candidates()` 바로 다음에 추가). `symmetry.dispositions` 필드를 스키마에 추가(기각 사유
  기록용). self-test(Test 21.5)로 "빠뜨리면 FAIL" 회귀 확인, 실제 telescopic OTA 9개 후보
  전부 disposition 처리 후 `ok=True`. `folded_cascode`/`two_stage_ota`도 재검증 — 이미
  완전했음. Design §4.5에 3-1번 필수 단계로 추가, `_TEMPLATE.topology.json`/
  function-selection-map.md §10 반영. 상세: gap-findings.md §8.
- 2026-07-28 (21차, find_matching_candidates() diff_pair 요구조건 수정 — 배치 5 시연 중
  발견): `library/current_reuse_telescopic_ota.topology.json`으로 배치 5(논문→JSON 시연)를
  진행하며 `find_matching_candidates()`를 호출했더니 `diff_pair`가 항상 빈 dict로
  나왔다. 원인: 그 함수 448행이 `w is None`이면 후보를 건너뛰는데, topology 저작 단계엔
  W가 아예 없다. 처음엔 "diff_pair는 이 함수에 의존하지 말고 수동으로 확인"하도록 Design
  §4.5를 고쳤으나, 사용자가 근본적으로 다른 지적을 했다 — "이 함수 이름 자체가 '매칭 후보
  탐지'다. AI가 모든 소자쌍을 수동으로 훑지 않도록 후보를 미리 좁혀 토큰을 아끼는 게 존재
  이유이고, 이건 사이징 전/후 상관없이 항상 유효한 이점이다. 우회하지 말고 함수 자체를
  고쳐야 한다." 이 지적을 받아 `find_matching_candidates()`의 diff_pair 로직을 수정 —
  W는 있으면(사이징 후) 오탐 방지용 추가 필터로 여전히 작동하지만, W가 없으면(사이징 전)
  구조적 신호(같은 kind+source, 다른 gate, 정확히 2개)만으로 후보를 낸다. 재시험 결과
  M1a/M1b·M4a/M4b·M37a/M37b가 즉시 diff_pair 후보로 나왔고, bias-gen의 의심스러운
  M31/M32 후보(같은 배치에서 이미 Euler 결함으로 확인된 sub-block)까지 자동으로
  표면화됐다. 기존 self-test 전체 회귀 없음. Design §4.5 절차는 원래대로("함수를 그대로
  호출") 되돌림. 상세: `docs/03-analysis/analog-topology-json-library.gap-findings.md` §3.
- 2026-07-28 (20차, topology library JSON 신설 — `layout` 필드 3차 수정 끝에 폐기): 19차
  직후, 사용자가 "topology netlist가 Python 코드 하드코딩이라 새 topology마다 코드를 새로
  짜야 하고 재현 안 됨"을 지적 — topology당 JSON 1개(`library/*.topology.json`)로 분리하는
  작업을 시작했다. 처음엔 netlist(연결성+n_fingers/finger_w/w/stack_id)와 `layout` 필드
  (groups/row_splits/adjacency_guide)까지 topology JSON에 담으려 했으나, `run_topology_
  pipeline()`을 실제 구현하며 두 번 실패를 거쳐(1차: finger 개수만 저장 → box-shape 균등성
  깨짐, 2차: transistor_sequence까지 저장 → Euling trail이 유일하지 않아 여전히 사이징
  의존적) 사용자가 근본 원인을 지적: "matching 배치(interdigitation/common-centroid)는
  finger 개수가 정해져야 계산 가능한데, 그건 사이징 결과값이다 — topology 단계엔 없어야
  한다." 이 지적으로 `layout` 필드를 topology JSON에서 완전히 제거하고 스키마를 connectivity
  (`netlist`: name/kind/source/drain/gate만) + `symmetry`(matching kind, connectivity만으로
  결정되므로 사이징 무관) + `compensation`(topology_library.py 함수 이름 참조, allowlist
  조회)으로 재설계했다(schema_version "1.0"→"2.0"). layout(finger 배분/row 분할/floorplan
  좌표)은 전부 `run_topology_pipeline(topology_json_path, sizing_overrides)`가 사이징
  이후에만 계산해 instance-output JSON에 남긴다 — row 분할 자동 탐색은 하지 않고(FAIL이면
  `search_stack_finger_w()`/`common_centroid_2row()`로 호출자가 재조정), `run_full_circuit_
  audit()`도 `dispositions` 판단이 필요해 의도적으로 미포함했다. 별도로 `two_stage_ota.
  topology.json`의 `compensation`을 처음엔 "역산 검증 안 됨"을 이유로 `null`로 뒀다가,
  사용자가 "이미 있는 함수 아닌가? 연결해야 하지 않나?"라고 지적 — 이 필드의 판단 기준이
  "현재 W값의 역산 여부"가 아니라 "회로 구조가 그 함수가 모델링하는 구조와 일치하는가"임을
  재확인하고 `miller_ota_topology`로 연결했다. `folded_cascode.topology.json`/`two_stage_
  ota.topology.json`/`_TEMPLATE.topology.json` 3개 파일 생성, connectivity diff=0 확인,
  `stick_diagram.py`/`sizing_recipe.py` self-test에 Test 26 + 오케스트레이션 데모 추가,
  기존 함수 시그니처는(`audit_row_split()`에 일시 추가했다 되돌린 것 포함) 최종적으로 전부
  무변경. 상세: `docs/02-design/features/analog-topology-json-library.design.md` 전체.
- 2026-07-28 (19차, check_stick_diagram_coverage() 신설 + floorplan 필수 섹션 승격): 18차까지
  하드닝을 마친 뒤, 새 background agent를 새 context로(이전 대화 힌트 전혀 없이, 이 skill
  문서만 참조하도록) 띄워 별도 논문(126uW Current-Reuse Telescopic OTA)을 처음부터 구현시키는
  블라인드 재현 테스트를 수행했다. gm/ID sizing은 21개 소자 전부 §1.5대로 정확히 끝냈지만,
  사용자가 완성된 리포트를 보고 "근데 왜 floorplan은 없지?", "그리고, 왜 stage1만 한 것
  같지?"를 연달아 지적 — §8(floorplan)이 리포트에 전혀 없었고(`grep -c floorplan
  final_report.html` → 0), §5(stick diagram)도 stage-1 core + stage-2 output 6개 행뿐
  bias-gen(9)/CMFB(7)/Class-AB(6) 소자 22개가 통째로 빠져 있었다. 원인 3가지: (1)
  `consistency-map.md`(이 문서) 자신이 §8 floorplan을 "필수 섹션 밖의 확장"이라고 명시해뒀던
  것 자체가 스펙 결함 — fresh agent는 오히려 스펙을 충실히 따른 것이었다. (2) §1.5 5단계의
  "집합 비교"가 프로즈 절차로만 존재해 실행이 강제되지 않았다. (3) fresh agent의 스크립트가
  `run_full_circuit_audit`를 **import만 하고 실제로 호출하지 않았다**(`grep -n
  "run_full_circuit_audit(" stick.py` → 0건) — 이미 있던 게이트조차 "쓴 척만" 한 상태였다.
  대응: (a) design-report-spec.md/SKILL.md의 "필수 7개 섹션"을 "필수 8개 섹션"으로 승격, 8번
  물리 floorplan 추가 — 위 31행의 "필수 섹션 밖" 문구를 정정. (b) `stick_diagram.py`에
  `check_stick_diagram_coverage(sized_device_names, stick_diagram_devices)` 신설(§6.62) —
  §1.5 5단계의 "집합 비교"를 실제 코드로 고정, Test 25로 이 정확한 사고(22개 소자 누락)를
  재현해 검출을 확인함(self-test suite 전체 exit 0 확인). (c) SKILL.md DoD·design-report-
  spec.md PRE-FLIGHT·function-selection-map.md §8에 "import ≠ call — 완료 보고 전 반드시
  `grep`으로 실제 호출부 존재를 확인할 것"을 명시적 절차로 추가. design-report-spec.md
  PRE-FLIGHT 27번에 상세 기록.
- 2026-07-27 (18차, verify_walk_sequence() 전량 재검증): 17차에서 `verify_walk_sequence()`를
  만든 직후, 사용자가 즉석 스크립트가 아니라 이 정식 함수로 folded_cascode/two_stage_ota의
  **저장된 최종 시퀀스 12개 행 전부**(각 회로 top_row0/1, mid_row0/1, bot_row0/1)를 하나씩
  실제 재검증하라고 요구 — 12개 전부 `valid=True`, `finger_count_mismatch={}`로 확인됨.
  §1 표 5번의 "손으로 짜맞춘 패턴이 아니라 `build_stick_diagram()`이 실제로 반환한 값
  그대로"라는 경고를 이 세션에서 처음으로 **전량 사후 재검증**한 사례 — 두 회로 최종
  JSON(`folded_cascode_split.json`/`two_stage_ota_split.json`) 데이터가 실제로 손댄 흔적
  없이 함수 계산 결과 그대로임을 함수 하나로 재현 가능하게 확인했다. design-report-spec.md
  PRE-FLIGHT 26번에 12개 행의 실제 시퀀스·node_path 표로 기록.
- 2026-07-27 (17차, verify_walk_sequence() 신설 — 제안 순서 독립 검산): 16차 이후 사용자가
  top_row0/bot_row0의 실제 채택 순서를 두고 "이렇게 다르게 섞을 순 없나"며 finger 개수는
  실제 채택안과 똑같지만 손으로 재배열한 순서를 여러 번 제안(예:
  `M3,M4,M6,M6,M5,MP,M5,M6,M6,M4`). 매번 Bash로 즉석 그래프 추적 스크립트를 짜서 "실제로는
  안 이어짐"을 확인해줬는데(예시는 4번째 단계 M5에서 끊김 — M6,M6로 Y에 돌아온 뒤 X/outA에만
  닿는 M5로 못 넘어감), 이 검증을 매번 새로 짜는 대신 `verify_walk_sequence(transistor_sequence,
  transistors)`로 harness에 고정 — finger 개수 일치 + 연속성(양쪽 시작점 시도)을 확인하고
  끊기면 정확한 위치/이유를 반환한다. "finger 개수가 맞다"와 "순서가 실제로 이어진다"는
  완전히 별개 질문임이 재확인됨. design-report-spec.md PRE-FLIGHT 25번 + §1 표 5번 항목,
  function-selection-map.md §6, stick_diagram.py Test 24(무효 시퀀스 재현 + 유효 시퀀스
  확인 + finger 불일치 대조군) 추가.
- 2026-07-27 (16차, branch_symmetric common-centroid 실제 달성): 15차 직후 사용자가 "M7과
  M8은 differential pair야?"라고 물어 구조적으로 아니라고 답했더니(source가 다름, gate만
  공유해 current_mirror로 분류) "그래도 아까 예시로 든 것처럼 분해해서 common-centroid로
  배치할 수 없냐"고 재차 제안 — 14차의 "branch_symmetric은 interdigitation도
  common-centroid도 적용 불가"라는 결론이 **절반만 맞았음**이 드러났다. interdigitation
  (그래프상 인접)은 여전히 불가능(재확인)하지만, M7/M8을 solo(한쪽 행에 통째로)가 아니라
  양쪽 행에 swap-대칭으로 분배(M7=row0:3/row1:2, M8=row0:2/row1:3)하면 실측 dx=0.00/
  dy=0.20까지 달성됨을 확인(solo는 dy=1.00으로 FAIL). `audit_row_split()` 재설계 — solo를
  하드 실패(1차)로도, "의도된 구조" 예외(14차)로도 특별취급하지 않고 3c가 항상 실제 dx/dy를
  계산해 정직하게 판정하게 했다. `branch_symmetric`은 이제 `diff_pair`처럼 3c가 필수 게이트다.
  folded_cascode의 M5/M6·M7/M8을 이 swap-분배로 재구성해 실제 common-centroid PASS 달성(JSON/
  floorplan 재생성, bbox·aspect 불변). design-report-spec.md PRE-FLIGHT 24번,
  function-selection-map.md §9, stick_diagram.py Test 23 갱신(solo FAIL 재현 → 분배 PASS
  확인 → 대조군).
- 2026-07-27 (15차, box-shape 지표 혼동 정정): 14차 직후 사용자가 두 가지를 지적 — "(1)
  differential pair는 stack 분리+finger 조절로 common-centroid를 만들 수 있잖아, (2) box는
  직사각형을 포함하는 거야, 정사각형일 필요는 없어." (1)은 재검증: M3/M4/MP가 같은 행에서
  vdd로 X-Y를 실제로 잇는 300가지 조합을 전수 탐색해도 M5/M6 인접 사례 0건(브릿지가 실재해도
  마찬가지) — pendant branch 구조상 그래프 경로 자체가 없다는 결론 재확인, `branch_symmetric`
  유지. (2)는 실제로 이 세션 내내 있던 혼동을 정확히 짚었다 — `FloorplanResult.aspect_ratio`
  (전체 bbox 종횡비)를 "1.5 이하=정사각형에 가까워야 함"인 하드 게이트처럼 취급해왔는데, 진짜
  하드 게이트는 `check_box_shape(row_widths)`(같은 스택에 쌓이는 행들의 **폭이 서로 비슷한가**
  — 다르면 'ㄱ'자/계단 모양)이고, 전체 bbox는 직사각형이면 종횡비가 얼마든 유효하다.
  folded_cascode의 top/bot 10폭 2행 분할 자체는 유효하지만(mid가 이미 10폭 2행이라 20폭
  1행 그대로 두면 'ㄱ'자가 났을 것 — 20:10=2:1도 어차피 check_box_shape() 기준 FAIL), "종횡비를
  낮추려고"라는 근거는 틀렸었다. `skyline_pack_best_width()`/`pack_group_as_unit()`의
  `target_ratio=1.0` 기본값도 같은 혼동의 근원 — 이건 packing 효율을 위한 소프트 선호일 뿐,
  하드 게이트가 아니다. design-report-spec.md PRE-FLIGHT 23번 + §1.7 2.5단계 문구 수정(aspect
  ratio 하드 체크 → check_box_shape() 하드 체크로 교체).
- 2026-07-27 (14차, branch_symmetric kind + skill 전체 재통독): 13차의 folded_cascode
  M3/M4 수정 직후, 사용자가 "bot_row0/row1에서 M7과 M8은 왜 한군데 몰아두었지?"라고 지적 —
  M7/M8(gate=bias4 공유)을 `matching_pairs`에 넣어본 적이 없었다(M9/M10만 확인). 넣어보니
  실제로 `solo-row FAIL`. `stick-diagram-euler-layout.md` §2.6 재확인: M5/M6·M7/M8은 gate만
  공유하고 source/drain은 서로 완전히 다르다("캐스코드 대칭쌍", M3/M4의 hub-leaf 구조와는
  다른 하위 종류) — 수백 개 finger 분배 조합 전수 탐색 결과 이런 쌍은 한 행 안에서
  finger 단위로 인접할 방법이 그래프상 0건(공유 노드가 없어 경로 자체가 없음). 즉 "한쪽
  컬럼에 통째로"는 회귀가 아니라 이 kind의 유일한 실현 가능 구조 — `audit_row_split()`에
  `branch_symmetric` kind 추가(solo-row를 결함이 아닌 의도된 구조로 취급, "컬럼당 finger
  수 일치"만 확인). 사용자 확인 후 `pack_floorplan(mirror_pairs=...)`으로 실제 좌우 물리
  배치까지 강제해봤으나, 그 메커니즘이 "작은 쌍 여럿을 세로 스택 하나로 묶는" 용도라 컬럼
  2개짜리 큰 케이스엔 안 맞아 오히려 악화(aspect 3.33→10.67) — 억지로 끼워맞추지 않고
  정직하게 scope 밖으로 남김. 이어서 사용자가 "왜 안 쓰는 게 그렇게 많나 — skill을 통째로
  읽고 harness로 고정시킬 수 있는 건 모두 고정해"라고 요구해 `stick-diagram-euler-layout.md`
  전체(§0~§10)를 재통독 — branch_symmetric 발견 자체가 이 재독(§2.6)에서 나왔다. 이 문서의
  §10 자체가 "일부 항목만 하고 충분하다 여기는 것"을 이미 명문화된 반복 실패 패턴으로
  경고하고 있었다(2026-07-25 기존 서술). design-report-spec.md PRE-FLIGHT 21~22번,
  function-selection-map.md §9, stick_diagram.py Test 23(M5/M6·M7/M8 재현 + finger 불일치
  대조군) 갱신, JSON/리포트 재생성.
- 2026-07-27 (13차, matching 회귀 + harness화): 사용자가 12차의 folded_cascode 2행 분할
  결과를 보고 "matching pattern은 왜 적용이 안 됐지?"라고 지적 — 실제로 M3+M5를 row0
  통째로, M4+M6을 row1 통째로 배치해 전류거울 쌍 M3/M4(source=vdd 공유)의
  interdigitation/common-centroid가 전혀 없었다(Euler+box-shape는 둘 다 PASS라 놓쳤음).
  기존 `common_centroid_2row()`로 재구성해 해결. 이어서 사용자가 "이건 script로 harness하게
  만들어서 절대로 함수 실행 순서를 빼먹지 않게 만드는 방향으로 개선해"라고 요구 —
  `audit_row_split()` 신설(Euler→box-shape→matching을 고정 순서로 강제하는 단일 게이트).
  첫 버전은 matching을 "인접성 하나"로만 확인했는데, 사용자가 다시 지적: "interdigitation과
  common centroid 둘 다 살펴보는 과정을 추가하라고 한거야, 하나만 하면 어떻게?" — 3b(행
  내부 인접성)/3c(전체 무게중심 일치)로 분리, 실제로 두 성질이 갈리는 사례를 발견
  (two_stage_ota의 M3/M4=2f+2f + M6=8f: interdigitation은 통과하나 common-centroid는
  dx=1.0~2.0으로 실패 — hub-leaf 1-layer AABB 블록 제약 때문에 그래프 이론상 더 못 줄임,
  6가지 소자 순서 전부 확인함). 이 검증 과정에서 `check_euler_condition()`의 닫힌회로 시작 노드
  선택이 `set` 순회(`next(iter(...))`)에 의존해 **동일 입력이 프로세스마다 다른
  transistor_sequence를 반환**하는 비결정성 버그도 발견 — 검증 게이트가 실행마다 뒤집히면
  무의미하므로 `min()`으로 고정해 재현 가능하게 만듦(Euler 유효성 자체엔 영향 없음).
  design-report-spec.md PRE-FLIGHT 20번 + §1.7 3.5단계, function-selection-map.md §9 갱신,
  stick_diagram.py Test 22 추가(회귀 재현 → 수정 확인 → two_stage_ota의 "한계"까지 자동 검증).
  **곧바로 4번째 수정**: 사용자가 "interdigitation/common-centroid 판별은 matching 특성을
  분석해서 해야 하는데 기존 기준(§2.7)은 왜 안 쓰나 — mirror는 interdigitation이 적합하고
  효율적이고, 차동쌍은 offset/CMRR 민감도 때문에 common-centroid가 필요하다"고 지적. 첫
  버전의 `audit_row_split()`은 모든 쌍에 3b/3c를 똑같이 강제해 two_stage_ota의 M3/M4(실은
  gate=D3 공유 전류거울)를 "해결 안 된 common-centroid 한계(dx=1.0)"로 오판했었다 — 실제로는
  mirror라 interdigitation만 필수였고 dx=1.0은 원래 문제가 아니었다. `pair_kinds` 파라미터
  추가(수동 override) + `rows`의 실제 gate/source로 자동 분류(`find_matching_candidates()`와
  같은 구조적 신호, W 비교 불필요)하도록 재구성 — kind에 따라 3b/3c 중 하나만 필수 게이트로
  삼고 나머지는 참고정보로 강등. 이어진 질문("JSON으로 회로 정보를 기술할 거면 이 정보도
  넣어서 matching pattern을 자연스럽게 고를 수 있게 하는 더 발전된 방법이 있냐")에 대해
  AskUserQuestion으로 세 옵션(자동+override/완전자동/완전수동) 제시 → 사용자가 "자동 분류 +
  수동 override 허용"을 선택. design-report-spec.md §1.7 3.5단계, function-selection-map.md §9,
  stick_diagram.py Test 22(kind-aware 재판정 + 진짜 차동쌍 대조군 FAIL 케이스) 갱신, 아티팩트
  리포트도 "한계"였던 서술을 "잘못된 기준 적용으로 인한 오탐"으로 재작성.
- 2026-07-27 (12차, 리포트 완성): 사용자가 "two 예제 회로도 실제로 리포트로 완성해봐"라고
  요구 — 11차의 `row_split_candidates` 지적(폭 같은 행 3개, box-shape 미달)을 실제로 고치는
  과정에서 `folded_cascode_example()`의 top/bot 2행 분할 첫 시도가 전부
  `build_stick_diagram()` `status="blocked"`로 실패(모든 후보 조합 포함). 손 계산으로 근본
  원인 확인: M5/M6을 3+3(홀수)으로 나누면 outA/outB가, MP를 1+1로 나누면 tail이 각 행에서
  홀수차수가 되어 3개 홀수노드(Euler 조건 위반, 0 또는 2개만 허용)가 M3/M4 분할과 무관하게
  고정됨. 고침: M3+M5, M4+M6을 통째로 한 행씩(X-side/Y-side 컬럼), 양쪽을 다 건드리는 MP만
  1+1 분할 — 6행 전부 `status="ok"`. 이 교훈을 `two_stage_ota_example()`에 바로 적용하니
  6행 전부 첫 시도에 성공(재현됨). **일반 교훈**: `check_box_shape()`는 finger 수 합만
  비교해 Euler-realizability를 전혀 보장하지 않는다 — 첫(잘못된) 분할도 box-shape는
  PASS를 반환했었다. design-report-spec.md PRE-FLIGHT 19번에 추가, 두 회로 모두
  `pack_floorplan_grouped()`(aspect 1.25/1.33, density 75%/75%)+`run_full_circuit_audit()`
  (ALL PASS)까지 실행해 Artifact 리포트로 완성.
- 2026-07-27 (11차, 교차검증): 사용자가 "다른 예제 회로에도 이 harness랑 floorplan 적용해서
  검증해봐"라고 요구 — Maloberti PDF 검증 예제 `folded_cascode_example()`(13 소자)/
  `two_stage_ota_example()`(7 소자)에 `run_full_circuit_audit()`+`pack_floorplan_grouped()`를
  그대로 적용. harness는 두 예제 모두 4개 체크 ALL PASS(일반화 확인). floorplan은 두 예제 다
  "폭이 같은 행 3개"라 그대로 쌓으면 box-shape 목표를 못 맞췄고, `row_split_candidates`가
  이를 올바르게 잡아냈다 — 다만 3개 행 전부 `find_diffusion_safe_split_points()` 결과 안전
  지점 0개(강하게 interdigitate_layout된 매칭 회로). 이를 계기로 "0개=분할 불가"가 아니라 "그
  자리에서 자르지 말고 처음부터 2행으로 다시 지어야 한다"는 구분을 design-report-spec.md
  §1.7 3단계에 명확히 추가. PRE-FLIGHT에 사고 아닌 교차검증 기록으로 18번 추가.
- 2026-07-27 (10차): 사용자가 "cmfb_n1은 top/bot을 합친 것인데, 다른 cmfb 행과 높이를 맞춰
  옆으로 배치하면 P/N 영역이 구분되면서 더 compact해지지 않을까 — 같은 diffusion에 속한
  행이면 이렇게 확인하는 것도 보강해달라"고 요구. `sub_kind`/`_pack_by_subkind()` 신설(폴러리티
  별로 나눠 공통 높이로 packing 후 옆으로 배치, flat 방식과 실제 비교). 처음엔 그룹 자체의
  packing_density로 골랐는데 Stage-1에 적용하니 모양이 10x9→19x4로 길쭉해져 전체 회로
  aspect ratio가 1.36→3.10으로 악화되는 걸 발견 — "그룹만 보면 나은 선택이 전체로는 더 나쁜
  선택"이었던 사례. 밀도 대신 aspect-ratio 근접도로 선택 기준을 바꿔 해결(Stage-1의 해로운
  분할을 올바르게 거부, CMFB는 동률이라 결과 불변). design-report-spec.md §1.7 1단계에
  sub_kinds 사용법 추가, function-selection-map.md §9 갱신. PRE-FLIGHT 사고 17건으로 갱신.
- 2026-07-27 (9차): 사용자가 "배치는 신호선과 근접한 곳에 위치시키면 좋겠어, routing delay가
  없어지지"라고 요구 — §7 layout_guide(수 턴 전 Correction #3에서 "classab_p2는 bias-gen
  바로 옆에 둬야 한다"고 이미 명시)와 실제 §8 좌표를 대조해보니 10칸이나 떨어져 있는 실제
  모순 발견. `net_weights`(실제 vbias1~4/vcmfb 연결) + `skyline_pack()` 가중 거리 tie-break
  신설. 1차 시도는 효과 없음 — `pack_to_height()`가 항상 가장 좁은 폭만 골라 배치 후보가
  하나뿐이었던 게 원인, `width_tolerance` 신설(좁은 폭 근방 후보들 중 실제 배선 비용
  `_total_wire_cost()`가 최소인 것 채택)로 해결. 실측: y-거리 10→5, aspect ratio
  1.00→1.36(목표 1.5 이내 유지), bbox 18x18→19x14. design-report-spec.md §1.7에 2.5단계
  추가, function-selection-map.md §9 갱신. PRE-FLIGHT 사고 16건으로 갱신.
- 2026-07-27 (8차): 7차 수정 직후, 사용자가 "다른 stack들도 diffusion-safe 체크 실제로 다
  돌려봐"라고 요구해 이 회로의 29개 행 전부를 검사한 결과, `find_diffusion_safe_split_points()`
  자체의 한계를 발견 — S1_PMOS/S1_NMOS row0/row1은 diffusion-safe 분할점이 있지만
  `build_mirror_symmetric_pattern()`으로 만든 matching-critical 행이라 그 지점에서 자르면
  `verify_mirror_symmetry()`가 깨짐(실측 확인). diffusion 안전성과 matching 안전성이 별개
  검사임을 §1.7/function-selection-map.md §9에 명시. 이어서 "cmfb_n1은 왜 어중간하게 중간에
  배치돼 있지?"라는 별도 지적으로 `pack_floorplan()`이 기능 그룹(Stage-1/bias-gen/CMFB)을
  전혀 모른 채 순수 공간 최적화만 하다가 CMFB의 한 행을 Stage-1 사이에 끼워 넣은 사고 발견 —
  `pack_group_as_unit()`/`pack_floorplan_grouped()` 신설(기능 그룹을 대칭쌍과 같은 원리로
  원자적 유닛 취급). 실측: 이 제약이 오히려 결과를 개선(bbox 18x16→18x18, aspect 1.125→1.00,
  density 33.7%→47.8%). PRE-FLIGHT 사고 15건으로 갱신.
- 2026-07-27 (7차): 6차 수정 직후, `evaluate_row_split_candidates()`가 "폭/높이가 지배적이면
  후보"라고만 판단하고 실제로 안전하게 쪼갤 수 있는지(소자의 diffusion을 반으로 가르지
  않는지)는 확인하지 않던 것을 사용자가 지적("packing할 때 MOS의 diffusion 영역이 고려돼서
  엉뚱하게 split되는 문제가 없도록"). `find_diffusion_safe_split_points()` 신설 — 실제
  `transistor_sequence`에서 어느 소자도 양쪽으로 갈리지 않는 분할 지점만 인정. 이 회로의
  S1_TAILP(M6:M7 7:3 인터리브)로 실측 확인 결과 안전 분할 지점 0개(정상 동작). `pack_floorplan()`
  에 `transistor_sequences` 인자 추가, design-report-spec.md §1.7 절차에 `splittable` 필드
  확인을 필수 단계로 반영. PRE-FLIGHT 사고 13건으로 갱신.
- 2026-07-27 (6차): §8(floorplan) 첫 버전이 공유 블록을 세로 한 줄로 쌓고 좌우 대칭쌍도 그
  순서 그대로 나열하기만 해 "대칭은 맞지만 빈 공간을 늘어놓아 box 모양처럼 보이는" 상태였던
  것을 사용자가 직접 지적("면적도 작게 만드는 게 target, 빈 공간을 없애야 의미 있다") —
  skyline/bottom-left 2D bin-packing(Jyl&auml;nki 2010) + 대칭쌍을 하나의 유닛으로 다루는
  symmetry-island 원리(analog placement 문헌, ASF-B*-tree)로 재작성. `pack_to_height()`로
  spine과 좌우 pair-stack의 목표 높이를 맞추는 joint search 추가(독립 최적화 시 결합 결과가
  길쭉해지는 문제 발견 후 수정). `evaluate_row_split_candidates()` 신설 — row-split 필요성
  진단 + §3 사이징/§6 SPICE 재검증 피드백 요구사항을 design-report-spec.md §1.7로 문서화.
  실측: aspect ratio 2.00→1.12, bbox 18x22→18x16. function-selection-map.md §9 추가,
  skill-validation-prompt.md 원칙 수 16→17건 갱신, PRE-FLIGHT 사고 12건으로 갱신.
- 2026-07-27 (5차, 근본원인 대응): 4차 수정 직후 사용자가 "CMFB/Class-AB도 net 이름 정규화
  확인해봐"라고 요구해 재감사한 결과, net 이름 문제가 아니라 Class-AB **출력단이 우측 branch
  뿐이고 좌측 mirror branch(논문 실제 번호 M17-M26, 12개 소자)가 통째로 미사이징** 상태임을
  발견 — 사용자가 이어서 "왜 이런 누락이 계속 발생하지? 국부적으로 검증하지 말고 전체를
  조망해야 하는 것 아니냐"고 근본 원인을 직접 질문. 원인 재구성: (a) connectivity가 매번 새
  1회용 스크립트에 재타이핑돼 net 이름이 드리프트, (b) 검증도 매번 "방금 고친 것"만 국부
  재확인, (c) 사이징 전 "소스 대비 총 소자 수"를 세는 이른 게이트 부재. 대응: `stick_diagram.py`
  §6.6에 `run_full_circuit_audit()` 신설(정본 데이터 1벌 + 판정 dict + 소스 대비 소자 수
  매니페스트를 받아 소자 수/net 이름/전체 목록 매칭+hub-merge/box-shape를 단일 호출로 감사,
  미판정 후보 있으면 무조건 FAIL) — 실제 Xie&Chen 51개 소자 인벤토리(좌측 branch 포함)에
  돌려 22개 매칭/hub-merge 후보 전부 판정 후 ALL PASS 확인. design-report-spec.md §1.6 신설,
  SKILL.md §5 체크리스트를 이 단일 게이트 호출 하나로 통합, function-selection-map.md §8 추가.
  PRE-FLIGHT 사고 11건으로 갱신(10~11번은 근본원인 자체).
- 2026-07-27 (4차): 3차 수정 직후, Stage-1을 만든 스크립트가 net 이름을 `Vbias1/VDD`(대문자)로,
  bias-gen/CMFB/Class-AB를 만든 스크립트가 `vbias1/vdd`(소문자)로 — 같은 물리 net을 다르게
  이름 붙인 탓에 Stage-1의 M6/M5가 이미 찾은 미러 그룹(vbias1/vbias4)에서 빠져 있던 사고 발견 —
  사용자가 직접 요구("Stage-1도 find_matching_candidates() 전체 목록으로 다시 돌려서
  확인해봐"). design-report-spec.md §1.5 4단계에 "net 이름 정규화를 전체 목록 실행보다
  선행" 규칙 추가, false positive 판단 기준을 5가지 패턴(우연한 net 공유/직렬 체인/소비자-
  바이어스 관계/동적 피드백 공유/진짜 매칭쌍)으로 재확장, 3개 이상 소비자가 얽혀 물리적
  인접이 다른 제약과 충돌할 때는 라우팅 우선순위 지침으로 대체하는 절차 추가. PRE-FLIGHT
  사고 9건으로 갱신.
- 2026-07-27 (3차): 2차 수정 직후, `find_matching_candidates()`를 CMFB/Class-AB 각
  sub-block에 **따로따로** 돌린 탓에 bias-gen M27/M28/M29(gate=vbias1)와 Class-AB
  M8/M13(gate=vbias1)의 진짜 cross-sub-block current-mirror 관계를 완전히 놓친 사고 발견 —
  사용자가 직접 지적("S2와 bias-gen은 여전히 소자 1개에 게이트 1개인데, 뭘 수정했다는거지?").
  design-report-spec.md §1.5 4단계를 "각 sub-block에"에서 "sub-block 구분 없이 전체 소자
  목록에"로 수정(find_hub_merge_candidates()의 §4.1 전체-목록 요구사항과 동일한 논리),
  false positive 판단 기준을 3가지 패턴(우연한 net 공유/직렬 체인/진짜 매칭쌍)으로 세분화,
  cross-sub-block 매칭은 병합 가능성을 check_euler_condition()으로 먼저 확인하고 불가능하면 물리적
  인접 배치로 대체하는 절차 추가. PRE-FLIGHT 사고 8건으로 갱신.
- 2026-07-27 (2차): 위 수정 직후, 같은 리포트에서 §1.5 4단계(sub-block 커버리지)만 지키고
  `find_matching_candidates()`를 한 번도 호출하지 않아 CMFB의 실제 차동쌍 M37a/M37b가
  1핑거씩 나열만 된 채(interdigitation/common-centroid 없이) 방치된 사고 발견 — 사용자가
  직접 지적("M37a/M37b가 매칭되어 있는 것처럼 보이지 않는다, box형으로 finger를 결정해서
  만든 것으로 안 보인다"). design-report-spec.md §1.5에 4단계(matching-detection 실행 +
  false positive 판단 + common_centroid_2row() 재배치 + box-shape 재검증) 신설(기존 4/5번은
  5/6번으로 재번호), SKILL.md §5 체크리스트에 find_matching_candidates() 실행 확인 항목
  추가, PRE-FLIGHT 사고 7건으로 갱신.
- 2026-07-27 (1차): fresh 세션 재현 테스트에서 §5(stick diagram)가 Stage-1만 다루고 bias-gen/
  CMFB/class-AB floating-bias sub-block을 통째로 빠뜨린 채 완료 보고된 사고 발견 — 사용자가
  직접 지적("stick diagram이 왜 stage1만 있지?"). design-report-spec.md §1.5(sub-block 커버리지
  완결성 절차) 신설, SKILL.md §5 체크리스트에 §3↔§5 소자 목록 diff 항목 추가, PRE-FLIGHT
  사고 6건으로 갱신.
- 2026-07-25: SKILL.md 전면 재작성(2407→1370 단어, 586→357줄) 이후 최초 생성. §1.5 신설,
  function-selection-map.md/known-incidents.md/spice-verification-workflow.md 3개 reference
  분리에 맞춰 맵 작성.
