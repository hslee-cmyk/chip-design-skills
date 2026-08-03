# 설계 리포트(HTML) 규격 — 이 skill의 최종 산출물 정의

> 이 문서는 §1~§5(gm/ID sizing) + §6(stick diagram/layout 피드백 루프)를 마친 뒤 **반드시
> 생성해야 하는 최종 산출물의 형식**을 정의한다. 지금까지의 참조 문서들이 "어떻게 sizing/layout
> 판단을 내리는가"를 다뤘다면, 이 문서는 "그 판단과 결과를 어떤 문서로 남기는가"를 다룬다.
> 템플릿: `assets/report_template.html` (Example 1 IGS 실측 데이터로 채운 완전한 예시).

## PRE-FLIGHT — 리포트 작성을 시작하기 전에

**HTML을 쓰기 시작하기 전에, 아래 체크리스트를 처음부터 끝까지 순서대로 다시 읽고 각 항목의
실제 검증 근거(함수 호출과 그 결과)를 메모할 것.** 검증 작업 뒤 리포트를 조립하는 단계에서는
"이미 충분히 확인했다"는 느낌 때문에 뒷부분을 건너뛰기 쉽다 — 아래 27건은 전부 이 방식으로
실제 발생했다. **번호는 `SKILL.md`/`consistency-map.md`가 그대로 참조하므로 고정이다 —
삭제·재배열하지 않는다.** 18번만 사고가 아니라 교차검증 기록이다.

1. **증상**: `find_hub_merge_candidates()`를 stage 경계 안에서만 돌리고 전체로 돌리지 않아
   유효한 6-leaf 병합 후보를 놓침. **규칙**: 항상 stage 구분 없이 전체 소자 목록에 실행한다.
2. **증상**: `build_stick_diagram()`의 Euler trail을 검증 없이 "완성된 배치"로 취급 — 일부
   stack의 매칭 대칭이 실제로 깨져 있었음. **규칙**: Euler trail 존재와 `check_mirror_symmetry()`
   통과는 별개 — 반드시 둘 다 확인한다.
3. **증상**: `build_stick_diagram()`의 실제 반환값을 손으로 축약("대표 패턴")해 옮김 — 100핑거를
   8개로, `status`(open/closed)까지 반전됨. **규칙**: 함수의 실제 반환값을 그대로 쓴다 — 축약·
   재구성 금지.
4. **증상**: 논문 스키매틱을 직접 읽지 않고 "일반적인 2단 OTA 구조"로 Stage2 전체(~12개 소자)를
   상상해 채움. **규칙**: 원문 도면을 이미지로 직접 렌더링해 읽고 소자별 `{name, kind, source,
   drain, gate, role}` 표로 옮겨 적은 뒤에만 사이징을 시작한다(불확실한 연결은 "⚠ 가정"으로
   명시).
5. **증상**: `build_stick_diagram()`의 `rendered` 문자열 필드(사람이 훑어보는 monospace 요약)를
   그대로 `<pre>`로 리포트에 박아넣음 — 그림이 아니다. §1(topology)도 `renderSchematic()`을
   재사용하지 않고 좌표를 손으로 박은 1회성 SVG를 새로 작성. **규칙**: 데이터 계산과 시각화는
   별개 단계 — 둘 다 `report_template.html`의 `renderStack()`/`renderSchematic()`을 코드
   그대로 재사용한다. `rendered`는 디버그용이지 리포트 시각 자료가 아니다.
6. **증상**: §3(sizing)은 bias-gen/CMFB/class-AB까지 전부 사이징했지만 §5(stick diagram)는
   Stage-1 core만 만들고 나머지 sub-block을 통째로 빠뜨린 채 완료 보고. **규칙**: §3에서 확정된
   모든 소자는 §5에도 등장해야 한다(§1.5) — 사이징 완결성과 layout 완결성은 별개 검사다.
7. **증상**: 6번을 고쳐 sub-block별 stick diagram을 채웠지만 `find_matching_candidates()`를
   한 번도 호출하지 않아, CMFB의 진짜 차동쌍 M37a/M37b가 서술("매칭쌍")과 실제 배치(1핑거씩
   순서 나열)가 어긋난 채 남음. **규칙**: "존재하는가"와 "올바르게 배치됐는가"는 별개 질문 —
   존재 확인 후 반드시 `find_matching_candidates()`로 matching 정합성까지 확인한다.
8. **증상**: `find_matching_candidates()`를 sub-block별로 **따로** 돌려, bias-gen 기준 leg
   (M27/M28/M29)와 Class-AB(M8/M13)가 같은 gate net(vbias1)을 공유하는 진짜 current-mirror
   관계임을 놓침. **규칙**: 반드시 sub-block 경계 없이 전체 소자 목록에 한 번에 실행한다.
9. **증상**: 8번을 고쳐 전체 목록에 실행했지만, Stage-1 스크립트는 net 이름을 `Vbias1/VDD`
   (대문자)로, 나머지는 `vbias1/vdd`(소문자)로 지어 같은 물리 net이 다르게 취급되어 매칭이
   또 가려짐. **규칙**: 서로 다른 스크립트/세션의 sub-block을 합칠 때는 `find_matching_
   candidates()` 실행 전 net 이름을 정규화(대소문자 통일 등)한다.
10. **증상**: net 이름 정규화 후 재확인한 결과, 이 fully-differential 회로의 좌측 mirror
    branch(논문 M17-M26, 12개 소자)가 사이징조차 안 돼 있었음이 드러남 — 세션 초반 스스로
    만든 검증 자료에 "좌측은 완전한 거울"이라고 이미 적어놓고도 반영하지 않음. **규칙**: 이미
    확인·기록한 자료가 있으면 반드시 재참조한다(4·2번과 같은 뿌리).
11. **근본원인 정리**: 1~10번은 (a) connectivity가 매번 새 1회용 스크립트에 재입력돼 net
    이름이 드리프트하고, (b) 검증도 매번 "방금 고친 것"만 국부적으로 재확인하며, (c) "소스
    대비 전체 소자 수"를 세는 이른 게이트가 없었다는 3가지 공통 원인으로 수렴한다. **규칙**:
    개별 체크리스트 추가로는 근본 해결이 안 된다 — §1.6의 `run_full_circuit_audit()` 단일
    게이트로 정본 데이터 1벌 + "판정 누락이면 FAIL"을 스크립트로 강제한다.
12. **증상**: §8(floorplan) 첫 버전이 공유 블록을 세로로 쌓고 대칭쌍을 그 옆에 늘어놓기만 해
    "대칭은 맞지만 빈 공간만 늘린 box"가 됨. **규칙**: 아날로그 layout은 대칭/매칭뿐 아니라
    면적도 최소화해야 한다 — skyline bin-packing(Jyländki 2010) + symmetry-island 원리
    (ASF-B*-tree)로 실제 2D packing한다(`pack_floorplan_grouped()` 등, §1.7). 실측: aspect
    ratio 2.00→1.12.
13. **증상**: `evaluate_row_split_candidates()`가 "폭/높이 지배적이면 후보"로만 판단하고 실제
    분할 가능 여부(소자 diffusion을 반으로 가르지 않는지)는 확인하지 않음 — S1_TAILP(인터리브
    배치)는 안전 분할 지점이 0개인데도 후보가 될 뻔함. **규칙**: `find_diffusion_safe_split_
    points()`로 실제 소자 시퀀스의 분할 안전 지점을 확인하고, `splittable=False`면 그 지점에서
    자르지 않는다(§1.7).
14. **증상**: `find_diffusion_safe_split_points()`가 안전 지점을 찾아도(S1_PMOS/NMOS
    row0/1), 그 지점에서 자르면 `check_mirror_symmetry()`가 깨짐(전체 행은 대칭, 분할 후
    반쪽은 비대칭). **규칙**: diffusion 안전성과 matching 안전성은 별개 검사다 —
    `build_mirror_symmetric_pattern()`으로 만든 matching-critical 행은 diffusion만으로
    안전 판정하지 않는다.
15. **증상**: `pack_floorplan()`이 spine 전체를 평평하게 packing해 `cmfb_n1`(높이 2)이 CMFB
    나머지 행과 떨어져 Stage-1 블록 사이에 회로적으로 무의미하게 끼어듦. **규칙**: 기능 그룹
    (Stage-1/bias-gen/CMFB 등)은 `pack_group_as_unit()`/`pack_floorplan_grouped()`로 먼저
    내부 packing해 하나의 원자적 블록으로 상위 packing에 넘긴다. 실측: 제약을 걸었더니 오히려
    결과가 개선(aspect 1.125→1.00) — "제약=손해"라는 가정도 실측 없이는 하지 않는다.
16. **증상**: `classab_p2`가 실제 연결(vbias1 게이트)상 bias-gen 바로 옆이어야 하는데 packer가
    connectivity를 고려하지 않아 10칸 떨어짐. `net_weights` 신설만으로 효과 없었음 — 원인은
    `pack_to_height()`가 항상 "목표 높이를 만족하는 가장 좁은 폭"만 골라 배치 후보가 하나뿐
    이었기 때문. **규칙**: `net_weights`(신호선 근접) + `width_tolerance`(좁은 폭 근방 여러
    폭 후보 시도)를 함께 쓴다. 한 번 시도해 안 바뀌었다고 포기하지 말고 원인을 끝까지 추적한다.
17. **증상**: `sub_kind`/`_pack_by_subkind()`(폴러리티별 분리 packing)를 Stage-1에 적용하니
    그 그룹만 보면 packing_density가 더 높았지만, 전체로 보면 모양이 길쭉해져(19x4) 전체
    aspect ratio가 1.36→3.10으로 악화됨. **규칙**: 그룹 단위 지표(밀도)가 아니라 전체 결과에
    대한 aspect-ratio 근접도로 채택 여부를 판단한다 — 항상 실측 비교 후 채택.
18. **교차검증(사고 아님)**: harness/floorplan이 특정 회로 하나에만 맞는 건 아닌지 Maloberti
    PDF의 두 예제(`folded_cascode_example()`, `two_stage_ota_example()`)에 `run_full_
    circuit_audit()`/`pack_floorplan_grouped()`를 적용 — 둘 다 ALL PASS. 두 예제 모두 등폭
    3행 구조라 `row_split_candidates`가 3개 행 전부를 후보로 잡았고, 전부 `find_diffusion_
    safe_split_points()` 안전 지점 0개(강하게 interdigitate된 매칭 회로라 당연). **규칙**:
    안전 지점 0개는 "그 시퀀스를 그 자리에서 자르지 말라"는 뜻이지 "2행으로 나눌 방법이
    없다"는 뜻이 아니다 — 처음부터 2행으로 다시 지어야 한다(19번에서 실증).
19. **증상**: 18번의 재구성 중 `find_interleaved_symmetric_splits()`가 반환한 모든 후보로
    나눠도 `build_stick_diagram()`이 전부 `status="blocked"`(홀수차수 노드 4개, Euler 불가능)
    를 반환하는 dead end 발생 — 손으로 차수를 계산해보니 3개 net(tail/outA/outB)만으로 이미
    Euler 조건을 어김. **해결**: 반드시 쪼개야 하는 소자만 최소로 분할하고 나머지는 통째로
    유지, 후보마다 실제 Euler 조건을 재확인 — 두 예제 모두 6개 행 전부 `status="ok"` 달성.
    **규칙**: `check_box_shape()`/`evaluate_row_split_candidates()`는 행의 finger 수 **합**만
    비교한다 — 그 합의 실제 소자 조합이 Euler-realizable한지는 확인하지 않는다. box-shape
    PASS는 물리적으로 지을 수 있다는 보장이 아니다 — 분할 후 반드시 `build_stick_diagram()`으로
    재확인한다.
20. **증상**: 19번의 folded_cascode 2행 분할(M3+M5/M4+M6 통째로)이 Euler/box-shape는
    통과했지만 전류거울 매칭쌍 M3/M4가 완전히 분리 배치돼 interdigitation/common-centroid가
    전혀 없었음. **규칙**: interdigitation(행 내부 인접)과 common-centroid(전체 무게중심
    일치)는 서로 다른 성질이라 반드시 둘 다 별개로 확인한다 — 하나만 통과해도 다른 하나는
    깨질 수 있다. `audit_row_split()`으로 Euler→box-shape→interdigitation(3b)→
    common-centroid(3c)를 고정 순서로 강제한다. (부가 수정: `check_euler_condition()`의 시작
    노드 선택이 프로세스마다 달라지는 비결정성 버그도 `min()`으로 고정.)
21. **증상**: bot_row0/1에서 M7/M8(gate만 공유, source/drain은 완전히 다름 — "캐스코드
    대칭쌍")을 `matching_pairs`에서 누락. 확인 결과 이 쌍은 공유 노드가 없어 같은 행 안에서
    finger 단위 인접이 전수 탐색으로도 0건(그래프 이론적으로 불가능). **규칙**: `audit_row_
    split()`의 kind 분류에 `branch_symmetric`(같은 gate 공유 + source/drain 전부 다름)을
    추가 — 이 kind는 solo-row를 의도된 구조로 인정하고, 대신 "두 컬럼에 각각 정확히 하나씩
    있고 finger 수가 일치하는가"만 확인한다.
22. **대응**: "왜 이렇게 안 쓰는 게 많은가" 지적에 `stick-diagram-euler-layout.md` 전체를
    처음부터 재통독 — 21번의 근본원인(§2.6 캐스코드 대칭쌍 카탈로그)이 이 재독에서 나왔다.
    **규칙**: 막히면 관련 정본 문서를 부분이 아니라 처음부터 다시 통독한다("일부만 하고
    충분하다고 넘어가는 것"이 반복 실패 패턴).
23. **정정 2건**: (a) M5/M6이 정말 interdigitation 불가능한지 브릿지가 실재하는 300가지
    조합을 전수 탐색해 재확인 — 여전히 0건(pendant branch 구조상 그래프상 경로 자체가 없음),
    `branch_symmetric` 결론 유지. (b) `FloorplanResult.aspect_ratio`(전체 bbox 종횡비)를
    "1.5 이하" 하드 게이트로 오인해온 것을 정정 — 실제 하드 게이트는 `check_box_shape
    (row_widths)`(같은 스택 행들의 폭이 서로 비슷한가, 'ㄱ'자 회피)뿐이다. **규칙**: 직사각형은
    종횡비가 얼마든 유효한 box다 — `aspect_ratio`는 packing 효율 참고 지표로만 보고,
    `check_box_shape()` PASS만 하드 게이트로 본다.
24. **증상**: M7/M8이 diff_pair는 아니지만(23번 결론 유지), "differential pair처럼 stack
    분리+finger 조절로 common-centroid를 만들 수 있잖아"라는 재지적으로 solo 배치(dy=1.00
    FAIL) 대신 swap-대칭 분배(M7=row0:3/row1:2, M8=row0:2/row1:3)를 시도하니 dx=0.00/
    dy=0.20 PASS 달성. **규칙**: `audit_row_split()`은 solo 여부를 하드 게이트나 예외로
    특별취급하지 않고, 3c(common-centroid)가 실제 dx/dy를 항상 계산해 정직하게 판정한다 —
    `branch_symmetric`도 `diff_pair`와 같이 3c를 필수 게이트로 요구하고 3b(interdigitation)는
    참고정보로만 남긴다.
25. **증상**: finger 개수는 실제 채택안과 같지만 손으로 재배열한 순서가 반복 제안돼 매번 손으로
    그래프를 추적해 검증해야 했음(예: 4번째 단계에서 끊김 — vdd를 거치지 않고 X/Y를 못 넘어감).
    **규칙**: 이 검증을 즉석 스크립트 대신 `check_walk_sequence(transistor_sequence,
    transistors)`로 harness화한다 — finger 개수 일치 여부와 순서의 연속성(양쪽 시작점 다
    시도)을 함께 검증하고, 끊기면 `break_index`/`break_reason`을 반환한다. `build_stick_
    diagram()`이 직접 반환한 순서가 아니라 사람이 제안·재배열한 순서는 채택 전 반드시 이
    함수로 먼저 검산할 것(§1 표 5번).
26. **전량 재검증**: folded_cascode/two_stage_ota 두 회로의 저장된 최종 시퀀스 12개 행 전부
    (top/mid/bot_row0/1 × 2회로)를 `check_walk_sequence()`로 재검증 — 전부 `ok=True`,
    `finger_count_mismatch={}`:

    | 회로 | 행 | 시퀀스 | node_path |
    |---|---|---|---|
    | folded_cascode | top_row0 | M5,M5,M3,M4,M6,M6,M6,M6,M4,MP | X→outA→X→vdd→Y→outB→Y→outB→Y→vdd→tail |
    | folded_cascode | top_row1 | M6,M6,M4,M3,M5,M5,M5,M5,M3,MP | Y→outB→Y→vdd→X→outA→X→outA→X→vdd→tail |
    | folded_cascode | mid_row0/1(동일) | M1,M2,M2,M1,M1,M2,M2,M1,M1,M2 | X→tail→Y→tail→X→tail→Y→tail→X→tail→Y |
    | folded_cascode | bot_row0 | M11,M11,M10,M8,M8,M10,M9,M7,M7,M7 | gnd→vb1→gnd→Y→outB→Y→gnd→X→outA→X→outA |
    | folded_cascode | bot_row1 | MN,MN,M9,M7,M7,M9,M10,M8,M8,M8 | gnd→vb2→gnd→X→outA→X→gnd→Y→outB→Y→outB |
    | two_stage_ota | top_row0 | M3,M6,M6,M4,M4,M3 | D3→vdd→OUT→vdd→O1→vdd→D3 |
    | two_stage_ota | top_row1 | M6×6 | OUT→vdd→OUT→vdd→OUT→vdd→OUT |
    | two_stage_ota | mid_row0/1(동일) | M1,M2,M2,M1,M1,M2 | D3→CS→O1→CS→D3→CS→O1 |
    | two_stage_ota | bot_row0/1(동일) | M5,M7,M7,M7,M7,M5 | CS→gnd→OUT→gnd→OUT→gnd→CS |

    두 회로의 최종 저장 데이터(`folded_cascode_split.json`/`two_stage_ota_split.json`)
    전체가 `build_stick_diagram()`이 실제로 반환한 값 그대로이고 손으로 짜맞춘 행이 없음이
    함수 하나로 재현 가능하게 확인됐다.
27. **증상(힌트 없는 fresh agent 재현 테스트)**: gm/ID sizing(21개 소자)은 §1.5를 지켜 전부
    정확히 끝냈지만, 완성 리포트에 §8(floorplan) 섹션 자체가 없었고(`grep -c "floorplan"
    final_report.html` → 0), §5(stick diagram)도 stage-1 core + stage-2 output 6개 행뿐이라
    bias-gen/CMFB/Class-AB 소자 22개의 stick diagram이 통째로 빠져 있었다.
    - **원인1(floorplan 누락)**: `consistency-map.md`가 그동안 §8을 "필수 섹션 밖의 확장"으로
      문서화해둬, fresh agent가 스펙을 충실히 따른 결과가 오히려 누락이었다 — 스펙 자체의
      빈틈. **대응**: §1을 "필수 8개 섹션"으로 승격.
    - **원인2(stick diagram 부분 커버리지)**: §1.5가 이미 프로즈로 "집합 비교"를 경고했지만
      프로즈만으로는 실행이 강제되지 않아 재발. **대응**: `check_stick_diagram_coverage
      (sized_device_names, stick_diagram_devices)` 함수를 신설해 §1.5 5단계를 harness화.
    - **원인3(import≠call)**: fresh agent 스크립트가 `run_full_circuit_audit`를 import만
      하고 실제로 호출하지는 않았다(`grep -n "run_full_circuit_audit(" stick.py` → 0건).
      **대응**: 완료 보고 전 `grep`으로 실제 호출부 존재를 확인하는 절차를 SKILL.md DoD와
      이 PRE-FLIGHT에 명시.
    - **일반 교훈**: 1~26번은 "검증은 했는데 반영을 안 함"(반영 단계 실패)이었다. 27번은
      "검증 자체를 실행하지 않고도 게이트를 통과한 것처럼 보임"(실행 단계 실패, import가
      실행의 대리 증거로 오인됨) — 별도 실패 카테고리다.

**공통점**: 1~10번은 "이미 확인/계산했으니 나머지는 괜찮을 것"이라는 추정으로 실행/재확인을
건너뛴 사례다. 11번은 그 근본 원인(정본 데이터 부재, 국부적 재검증, 이른 게이트 부재)을
드러낸다. 27번은 게이트 함수가 **존재해도 호출되지 않으면 의미가 없다**는 별도 층위의
실패다. **아래 §1 표의 경고문은 한 번 읽고 지나가는 문장이 아니라 해당 섹션을 채우기 직전에
다시 확인해야 하는 게이트다** — §1.6의 harness가 이를 스크립트로 강제하지만, harness의 존재와
실제 호출은 별개이므로(27번) 완료 보고 전 grep으로 호출부 존재를 물리적으로 확인한다.

## 1.6 `run_full_circuit_audit()` — 되돌릴 수 없는 단일 게이트 (사고 11 대응)

> **이 섹션은 §1.5를 대체하지 않는다 — §1.5(모든 소자 확정)/§1.5 4단계(matching 판정)가
> "무엇을 해야 하는가"를 정의하고, 이 §1.6은 "그걸 다 했는지 사람이 판단하지 않고 스크립트가
> 판단하게 만드는 방법"을 정의한다.** 정본: `assets/stick_diagram.py`의
> `run_full_circuit_audit()` 함수(§6.6, docstring에 전체 파라미터 설명 있음).

**사이징을 시작하기 전에(순서 중요 — 사고10을 막는 지점)**:
1. 소스(논문/스펙)에서 이 회로의 **기능 블록별 소자 수를 먼저 선언**한다
   (`expected_counts = {"stage1": 11, "classab_right": 10, ...}`). Differential 회로면
   "출력이 2개인데 mirror branch가 있는가"를 여기서 반드시 답한다 — 이 시점에 답을 못 하면
   사이징을 시작하지 않는다(소스를 더 읽는다).
2. 모든 sub-block의 connectivity는 **하나의 정본 dict/파일**에만 적는다(`devices = {name:
   (kind, source, drain, gate, block)}`) — sub-block마다 새 스크립트에 다시 타이핑하지
   않는다. net 이름은 한 곳에서만 타이핑되므로 대소문자 드리프트(사고9)가 구조적으로
   불가능해진다.

**모든 sub-block의 sizing/stick diagram이 끝난 뒤(리포트 완료 선언 직전, 매번 처음부터
재실행)**:
3. `dispositions` dict에 지금까지의 §1.5 4단계 판정(false positive 포함) 전부를 채운다.
4. `run_full_circuit_audit(devices, expected_counts, dispositions, box_shape_checks,
   accept_fail_blocks={...})`를 호출한다 — 이 한 번의 호출이 소자 수 대조/net 이름 정규화
   확인/전체 목록 매칭+hub-merge 판정 대조/sub-block별 box-shape를 전부 실행한다.
5. 반환된 `AuditResult.ok`가 `True`가 아니면(또는 미판정 후보가 하나라도 있으면) 리포트를
   완료로 선언하지 않는다 — `result.checks`를 그대로 리포트 근거 자료로 남긴다.
6. **어떤 항목을 고쳤든, 그 항목만 재확인하지 않는다** — 4단계 전체를 처음부터 다시 실행한다
   (스크립트라 비용이 거의 없다 — "이번엔 이 pair만 재확인하면 되겠지"라는 국부적 판단
   자체를 하지 않는 게 이 harness의 목적이다).

**권장 사항 — 가능하면 자동화할 것**: 사람이 함수 출력을 읽고 HTML/JS로 "옮겨 적는" 단계
자체가 사고의 근원이다. 가능하면 리포트의 데이터 객체(`const REPORT = {...}` 등)를 손으로
타이핑하지 말고, 실제 함수 호출 결과를 JSON으로 직렬화(`json.dumps()`)해서 스크립트가
파일에 직접 쓰게 할 것 — 사람이 값을 옮기는 단계가 없으면 축약/재구성 자체가 물리적으로
불가능해진다. 마찬가지로 **§1/§5의 시각화 코드는 새로 작성하지 말고 `report_template.html`
을 파일 복사(`cp`)해서 시작점으로 삼을 것** — `<style>`과 렌더링 `<script>`를 통째로 가져오고
`REPORT`/`renderSchematic()` 호출부의 데이터만 이 회로에 맞게 바꾼다.

**추가 권장 — 사이징 전에 원문을 netlist로 먼저 옮겨 적을 것**: 4번 사고(Stage2 상상으로 채움)를
막는 가장 효과적인 방법은, gm/ID 사이징을 시작하기 전에 논문의 실제 도면(페이지 이미지를
직접 렌더링해서 읽을 것 — 텍스트 추출만으로는 소자 간 연결을 놓치기 쉽다)을 소자별
`{name, kind, source, drain, gate, role}` 표(간단한 `netlist.md` 파일 등)로 먼저 통째로
옮겨 적고, 이후 모든 사이징/stick diagram 작업은 그 표만을 근거로 진행하는 것이다 — 기억이나
"보통 이런 구조일 것"이라는 추정으로 단 하나의 소자도 채우지 않는다. 확신 없는 세부사항은
"⚠ 가정"으로 리포트에 명시 고지한다 — 침묵 속에 지어내지 않는다.

## 1.7 Floorplan(§8) → box-shape/sizing/SPICE 재검증 피드백 루프

> **library/*.topology.json이 있으면 먼저 확인할 것**: 이 topology가
> `assets/library/*.topology.json`으로 이미 등록돼 있으면, `run_topology_pipeline()`이
> 아래 피드백 루프(box-shape/matching-safety/floorplan/coverage)를 한 번에 계산한다 —
> `function-selection-map.md` §10, `analog-topology-json-library.design.md` 참고. 단,
> row 분할(matching-safety 위반 시 재배분)은 자동 탐색되지 않으므로 아래 절차를 여전히
> 직접 따라야 한다.

**배경(PRE-FLIGHT 12번)**: floorplan은 대칭·매칭뿐 아니라 면적도 최소화해야 하는 목표다 —
빈 공간을 늘어놓아 "box처럼 보이게" 만드는 것만으로는 부족하다. 특정 row가 전체 모양을
깨면 그 row의 finger 수를 조정하거나 2행으로 쪼개 packing할 수 있는지 따지고, 그 결과 바뀐
finger 수/parameter는 다시 sizing/SPICE로 피드백해 spec을 여전히 meet하는지 재검증하는 것
까지가 floorplan 단계의 일이다.

정본: `assets/stick_diagram.py`의 `pack_floorplan_grouped()`(spine을 기능 그룹별로 먼저
내부 packing 후 상위 packing, §6.7) — spine 안에 서로 무관한 기능 블록이 2개 이상이면
**`pack_floorplan()`을 직접 쓰지 말고 반드시 이걸 쓴다**(PRE-FLIGHT 15번: 평평한
`pack_floorplan()`은 CMFB의 한 행을 엉뚱하게 Stage-1 사이에 끼워 넣었다). 기능 그룹이
하나뿐이거나 대칭쌍만 있으면 `pack_floorplan()` 직접 호출도 무방하다.
`net_weights`/`width_tolerance`(신호선 근접 배치) + `evaluate_row_split_candidates()`/
`find_diffusion_safe_split_points()`도 함께 쓴다.

알고리즘 근거: Jyländki, *"A Thousand Ways to Pack the Bin"*(2010)의 skyline 휴리스틱, 그리고
analog placement 문헌의 symmetry-island/ASF-B*-tree 방식(Lin & Chang 등, *"Analog Placement
Based on Symmetry-Island Formulation"*) — 대칭쌍(그리고 기능 그룹도)을 사후 검증하는 게
아니라 애초에 갈라질 수 없는 하나의 유닛으로 다뤄 packing한다는 원리를 가져왔다. 전체를
simulated annealing급 B*-tree/sequence-pair 최적화기로 다시 짜는 것은 이 skill의 범위를
넘는다 — 이 구현은 그 핵심 아이디어를 결정론적으로 축소 구현한 것이다.

**절차**:
1. §5의 모든 stick-diagram stack을 `block_from_row_widths()`로 사각형(폭=최대 행 finger 수,
   높이=행 개수)으로 집계한다. 좌우 대칭 관계가 있는 stack은 `mirror_pairs`로 분류한다(무엇이
   대칭인지는 §1.5/§1.6에서 이미 판정된 사실을 그대로 재사용 — 여기서 새로 판단하지 않는다).
   나머지(spine)는 **회로의 기능 블록별로 그룹화한다**(예: Stage-1/bias-gen/CMFB) — 이
   그룹화가 이 절차에서 가장 중요한 회로 지식 반영 단계다: 같은 기능 블록에 속한 stack들이
   packing 중에 서로 갈라져 무관한 다른 stack 사이에 끼어들면 안 되기 때문이다. 각 그룹
   안에 같은 물리 diffusion/폴러리티(P측/N측)로 나뉘는 row가 있으면 `sub_kinds`(그룹별
   `{block_name: kind}`)로 표시해볼 수 있다 — `pack_group_as_unit()`이 폴러리티별 분리
   배치와 기존 방식을 **실제로 둘 다 계산해서 비교**하고 더 나은 쪽을 채택한다. 어느 게
   나은지 가정하지 말 것 — 그룹만 보면 나아 보여도 전체로는 악화될 수 있다(PRE-FLIGHT 17번).
   항상 실측할 것.
2. `pack_floorplan_grouped(spine_groups, mirror_pairs, gap, transistor_sequences={...})`을
   호출해 `FloorplanResult`를 얻는다 — **`transistor_sequences`(각 stack의 실제
   `build_stick_diagram()` 반환 시퀀스)를 반드시 채워서 넘긴다**(생략하면 3번의 diffusion
   안전성 확인이 스킵된다). `packing_density`(물리 면적/bbox 면적)가 이 단계의 핵심 지표다.
   **aspect_ratio만 보고 "box 모양이니 끝"이라고 판단하지 않는다** — 빈 공간을 늘어놓아도
   ratio는 낮게 나올 수 있다(PRE-FLIGHT 12번). 기능 그룹 제약이 packing_density를 반드시
   낮추는 것도 아니다(PRE-FLIGHT 15번, 오히려 좋아진 사례) — 매번 실측할 것이지 가정하지
   말 것.
2.5. **신호선 근접 배치(라우팅 거리 최소화)**: 서로 게이트/드레인 net을 공유하는 group/pair가
   있으면(예: bias-gen의 vbias1 leg → Class-AB의 M8/M13 게이트) `net_weights`(`{name:
   {other_name: weight}}`, 그룹 이름 또는 mirror_pairs의 오른쪽 소자 이름 기준)를 채워서
   2번의 호출에 같이 넘긴다. **`width_tolerance`(기본 2.0)도 반드시 켜져 있는 채로 둘 것** —
   이게 없으면 `pack_to_height()`가 가장 좁은 폭만 골라 애초에 배치 후보가 하나뿐이라
   `net_weights`가 아무 효과를 못 낸다(PRE-FLIGHT 16번 — "한 번 시도해서 안 바뀌었다"고
   포기하지 말고 원인을 끝까지 추적할 것). `height_tolerance`/`width_tolerance` 둘 다
   **box-shape(1순위)를 지키는 한도 안에서만** 배선 근접(2순위)에 쓰이도록 하는 예산이다 —
   값을 키울수록 배선은 더 가까워지지만 종횡비가 나빠질 수 있으니, 매 조정 후
   **`check_box_shape()`가 여전히 PASS인지**(행 폭 균일성, 'ㄱ'자 회피 — 진짜 하드 게이트,
   PRE-FLIGHT 23번) 다시 확인할 것. `aspect_ratio` 자체는 packing 효율 참고 지표일 뿐
   정사각형이어야 한다는 하드 요구가 아니다 — 직사각형이면 종횡비가 얼마든 유효한 box다.
3. `result.row_split_candidates`를 확인한다 — 특정 블록의 폭/높이가 bbox의 지배적인
   부분(기본 60% 이상)을 차지하면 후보로 잡힌다. **각 후보의 `splittable` 필드를 반드시
   확인한다** — `False`면(안전한 분할 지점이 하나도 없으면, 예: 이 회로의 S1_TAILP처럼 두
   소자가 finger 단위로 완전히 인터리브된 행) **그 시퀀스를 그 자리에서 자르는 분할은
   제안하지 않는다** — 소자 하나의 diffusion을 반으로 가르는 물리적으로 무의미한 분할을
   막기 위해서다(PRE-FLIGHT 13번). `diffusion_check`가 `"not_verified"`면(2번에서 시퀀스를
   안 줬으면) 후보를 그대로 채택하지 말고 먼저 시퀀스를 채워 다시 확인한다. **`splittable
   =True`라고 바로 쪼개도 되는 것도 아니다** — 그 행이 `build_mirror_symmetric_pattern()`으로
   만든 matching-critical 행이면(예: 이 회로의 S1_PMOS/S1_NMOS row0/row1) diffusion은 안
   깨져도 `check_mirror_symmetry()`가 깨질 수 있다(PRE-FLIGHT 14번) — 분할 전 반드시 그
   행의 대칭 여부(§1 표 근거)를 따로 확인하고, matching-critical이면 `common_centroid_
   layout()`식 재구성 없이는 분할하지 않는다.

   **`splittable=False`가 "이 행은 절대 못 쪼갠다"는 뜻은 아니다(PRE-FLIGHT 18번 교차검증
   결과)**: `find_diffusion_safe_split_points()`는 **이미 만들어진 한 행의 시퀀스를 그
   자리에서 자를 수 있는지**만 확인한다 — 안전 지점이 0개로 나오면 "이 시퀀스를 자르지
   말라"는 뜻이지 "이 소자들을 2행으로 나눌 방법이 없다"는 뜻이 아니다. 진짜 해법은 처음부터
   2행을 **다시 만드는 것**이다: 각 소자의 finger 수를 짝수로 만들고(또는 §2.5.4
   `find_interleaved_symmetric_splits()`로 홀수 조합의 불균등 분할을 구하고), 각 소자를
   정확히 절반씩 두 행에 나눠 `build_mirror_symmetric_pattern()`으로 배치한 뒤
   `check_mirror_symmetry()`로 재확인한다 — 이게 정확히 이 회로의 S1_PMOS/S1_NMOS row0/row1
   이 이미 만들어진 방식이다. Maloberti PDF의 folded cascode/2-stage OTA 예제(`assets/
   stick_diagram.py`의 `folded_cascode_example()`/`two_stage_ota_example()`)로 교차검증한
   결과, 두 예제 전부 원래의(round-robin으로 생성된) top/mid/bot 시퀀스가 안전 분할 지점
   0개였다(강하게 interdigitate된 매칭 회로라 당연한 결과) — 그렇다고 이 행들이 box-shape를
   못 맞춘다는 뜻이 아니라, "그 자리에서 자르기"가 아니라 "짝수로 나눠 다시 짓기"가 필요할
   뿐이다.
3.5. **행을 처음부터 다시 짓는 경우(위 3번 "짝수로 나눠 다시 짓기"), 반드시
   `audit_row_split(rows, matching_pairs, pair_kinds=None, max_ratio)` 하나만 호출한다 —
   Euler 검증→box-shape→matching(interdigitation+common-centroid) 확인을 손으로 순서대로
   따로 호출하지 않는다.** `build_stick_diagram()` status="ok"와 `check_box_shape()` PASS만
   확인하고 이 마지막 단계를 빼먹으면, 매칭 소자쌍의 interdigitation/common-centroid가
   전혀 없는 채로 통과할 수 있다(PRE-FLIGHT 20번 실제 회귀). **interdigitation과
   common-centroid는 서로 다른 성질이라 반드시 둘 다 별개로 확인해야 한다** —
   interdigitation(행 내부 국소 인접성)을 통과해도 common-centroid(두 소자 finger 위치의
   전체 무게중심 일치)는 깨질 수 있고 그 반대도 가능하다. `audit_row_split()`은 이 둘을
   `3b`/`3c`로 분리된 체크로 강제하며, 어느 쪽도 조용히 건너뛰지 않는다.

   **pair는 3종류로 나뉜다** — 전류거울(hub-leaf, 같은 gate + 같은 source/drain 노드도 공유),
   캐스코드 대칭쌍(`branch_symmetric`, 같은 gate 공유하지만 source/drain은 서로 완전히 다름 —
   §2.6, 예: folded_cascode의 M5/M6·M7/M8), 차동쌍(같은 source 공유 + 다른 gate). `branch_
   symmetric`은 공유 노드가 없어 같은 행 안에서 finger 단위 **interdigitation(3b)은 그래프상
   불가능**하다(전수 탐색으로 확정, 브릿지 소자가 있어도 마찬가지 — pendant branch 구조상
   두 소자가 절대 인접할 수 없다, PRE-FLIGHT 21·23번). **그러나 common-centroid(3c)는 여전히
   필수 게이트로 요구한다** — 두 소자를 양쪽 행에 **swap-대칭으로 나눠 분배**하면(예: M7을
   row0=3/row1=2, M8을 swap해서 row0=2/row1=3 — diff_pair를 2행으로 나누는 것과 같은 원리)
   실측으로 dx=0.00/dy=0.20까지 달성된다(각자 한쪽 행에 통째로 두면 dy=1.00 FAIL,
   PRE-FLIGHT 24번). 즉 이 kind에서 **인접(interdigitation)은 불가능해도 무게중심 일치
   (common-centroid)는 가능**하며, 3b/3c로 분리해뒀기 때문에 정확히 구분해서 요구할 수
   있다. solo(각자 한쪽 행에 통째로)는 여러 배치 선택지 중 하나일 뿐 자동으로 옳은 구조가
   아니다 — 실제 dx/dy를 계산해 판정한다.

   **나머지 두 종류는 어느 체크가 pass/fail을 좌우하는 필수 게이트인지가 다르다 — `stick-
   diagram-euler-layout.md` §2.7이 이미 확립한 기준이다**: **전류거울(같은 gate 공유)은
   interdigitation(3b)이 필수**이고 common-centroid(3c)는 참고 정보일 뿐이며, **차동쌍
   (같은 source 공유+다른 gate)은 common-centroid(3c)가 필수**이고 interdigitation(3b)은
   참고 정보다(PRE-FLIGHT 20번: 두 체크를 모든 쌍에 균일하게 강제했다가 이 기준으로
   정정됨 — two_stage_ota의 M3/M4는 전류거울이라 common-centroid dx=1.0은 애초에 실패가
   아니었다). `pair_kinds`를 안 주면 `audit_row_split()`이 `rows`에 들어있는 실제
   gate/source로 자동 분류한다(둘 다 아니면 `"unknown"` → 보수적으로 둘 다 필수) —
   `find_matching_candidates()`가 신규 후보를 "발견"할 때 쓰는 것과 같은 구조적 신호(gate
   공유/source 공유)를 재사용하되, 이미 확정된 쌍을 분류하는 것이라 그 함수가 추가로
   요구하는 W 일치는 필요 없다(행 분할용 `Transistor`는 `w`를 안 채우는 경우가 많아 W까지
   요구하면 분류가 항상 실패한다). 애매한 경우에만 `pair_kinds`로 수동 override한다.
   `matching_pairs`는 `find_matching_candidates()` 출력에서 뽑아 넘긴다.

   **`ok=False`가 나와도 억지로 통과시키지 않는다** — 일부 조합(작은 소자쌍이 더 큰 3번째
   소자와 같은 hub를 공유하는 경우)은 common-centroid가 그래프 이론적으로 도달 불가능할 수
   있다(실측: `two_stage_ota_example()`의 M3/M4=2f+2f + M6=8f, 최선의 dx=1.0~2.0이 0.5
   허용오차를 못 넘김 — hub-leaf 쌍은 1개 diffusion layer 안에서 AABB형 짝수 블록만 가능
   하다는 `common_centroid_layout()` 회전 경로의 이론적 제약이 직접 발현된 사례). 이럴 땐
   실패를 숨기지 말고 근본 원인(그래프 차수 제약)과 함께 리포트에 정직하게 남긴다 — §0의
   "확신 없는 세부사항을 침묵 속에 지어내지 않는다"는 원칙과 동일하다.

   **부가로 발견/수정한 것**: `check_euler_condition()`의 닫힌회로(0개 홀수차수) 시작 노드
   선택이 `g.nodes`(set)의 `next(iter(...))`에 의존해 **프로세스마다 다른 시퀀스**를
   반환했다(CPython 문자열 hash 랜덤화가 원인). 검증 게이트가 실행마다 PASS/FAIL이 바뀌면
   게이트로서 무의미하므로 `min()`으로 시작 노드를 고정해 재현 가능하게 만들었다(Euler
   circuit 유효성 자체는 시작 노드 선택과 무관하므로 판정 결과는 왜곡되지 않는다).
4. `splittable`이 `True`인 후보만(그리고 사용자가 실제로 쪼개기로 결정하면): 그 stack의
   소자 목록만 다시 `search_stack_finger_w()`/`check_multi_leaf_hub_parity()`로 2행 분할
   가능성을 확인하고, `check_box_shape()`로 그 stack 내부 비율도 재확인한다(§8.5와 동일
   절차, floorplan 레벨에서 한 번 더) — 3.5번(`audit_row_split()`)이 이미 이 확인을
   포함하므로, 새로 짓는 행이면 사실상 이 4번은 3.5번으로 대체된다.
5. **분할로 finger 수나 W가 실제로 바뀌면, §3(사이징 표)의 해당 소자 값을 갱신하고 §6(SPICE
   cross-check, `spice-verification-workflow.md` §1/§2)을 그 소자에 대해 다시 실행한다** —
   floorplan이 요구한 배치가 electrical spec을 깨지 않는지 확인할 때까지는 그 분할을
   최종으로 확정하지 않는다. "layout 결정이 electrical spec에 영향을 줄 수 있으면 반드시
   되돌아가 재검증한다"는 §6(stick diagram ↔ sizing 피드백 루프)의 원칙을 floorplan
   레벨로 한 단계 더 확장한 것뿐이다.
6. `pack_floorplan()`을 다시 실행해 새 배치를 확인한다 — 개선이 없거나 악화되면 분할을
   되돌리고 원래 배치에 대한 근거(예: S1_TAILP가 가장 넓은 행이지만 packer가 이미 흡수해
   전체 비율을 깨지 않아 분할 불필요로 판단한 사례)를 리포트에 남긴다.

## 0. 왜 필요한가

이 skill의 산출물은 사람(설계 검토자)과 **다음 단계를 이어받는 agent**(실제 layout을 그리는
agent, 또는 다른 회로에 재사용하려는 agent) 둘 다가 소비한다. sizing/stick diagram까지는
"무엇을 결정했는가"를 기록하지만, "그 결정을 실제 물리 layout으로 어떻게 옮겨야 하는가,
그리고 이 회로에서 성능에 결정적인 영향을 미치는 요소가 무엇인가"는 별도로 명시해야 한다.
이 문서는 그 빈틈을 메우고, 8개 섹션 전체를 매 설계마다 빠짐없이 산출물에 포함시키도록
규격화한다.

## 1. 필수 8개 섹션

| # | 섹션 | 내용 | 근거/생성 소스 |
|---|---|---|---|
| 1 | **주어진 topology** | 회로 스키매틱(소자명·극성·연결) — 원문 논문 그림을 그대로 캡처해 붙이지 않는다(저작권). 회로 이해를 바탕으로 직접 그린 원본 스키매틱(SVG 프리미티브: rails/devices/wires/dots/labels)만 사용. **⚠️`report_template.html`의 `renderSchematic()` 함수를 코드 그대로 복사해 재사용 — 손으로 좌표를 박은 1회성 SVG를 새로 쓰지 말 것(PRE-FLIGHT 5번)** | `assets/report_template.html`의 `renderSchematic()` (그대로 재사용) |
| 2 | **주어진 설계 spec** | fT(또는 GBW)·부하 C·target gain·phase margin 등 사용자/논문이 지정한 스펙 원문 그대로(임의로 파생시키지 않음) | 설계 입력 그대로 |
| 3 | **결정된 gm/ID parameter** | 소자별 gm/ID, L, VDS, ID, W, (해당되면) gain — `gm-id-methodology.md` §1 6단계의 최종 출력 | `sizing_recipe.py` / `topology_library.py`의 `topology_fn` 출력 |
| 4 | **stick diagram을 위한 결정사항들** | matching 그룹 탐지 결과, **⚠️stage-경계 병합 여부를 `find_hub_merge_candidates()`로 실제로 확인했는가(§4.1, 생략 금지 — 스테이지별로 먼저 나누고 시작하면 이 확인 자체가 누락된다, PRE-FLIGHT 1번)**, Case A/B 선택 근거(§4.2), box-shape 탐색 후보와 채택한 finger_w/n_fingers, 스냅 오차 트레이드오프, **⚠️matching-symmetry를 `check_mirror_symmetry()`로 실제로 검증했는가(Euler trail 존재와 매칭 대칭은 별개, PRE-FLIGHT 2번)**, **⚠️`check_box_shape()`가 FAIL이면 물리 행 분할(§8.2 step 4)로 실제 해소를 시도했는가, 시도하지 않기로 했다면 그 판단 근거로 "비율 임계값을 만족하는 데 필요한 물리 행 개수"를 실제로 계산해 남겼는가(§8.5 — 정성적 설명만으로 FAIL을 최종 결론 삼지 말 것)** — "무엇을 왜 그렇게 정했는가"의 **결정 추적(decision trace)** | `stick_diagram.py`의 `find_hub_merge_candidates()`/`check_multi_leaf_hub_parity()`/`search_stack_finger_w()`/`search_shared_finger_w()`/`check_box_shape()`/`check_mirror_symmetry()` |
| 5 | **완성된 stick diagram** | 각 stack의 실제 Euler trail(node_sequence/transistor_sequence), open path/closed circuit 여부 — **⚠️손으로 짜맞춘 패턴이나 "대표 패턴" 축약이 절대 아니라 `build_stick_diagram()`이 실제로 반환한 값 그대로(PRE-FLIGHT 3번)**. **⚠️⚠️그 값을 시각화할 때도 `report_template.html`의 `renderStack()` 함수를 코드 그대로 복사해 재사용 — `rendered` 문자열 필드를 `<pre>`에 텍스트로 덤프하는 것은 규격 위반(PRE-FLIGHT 5번)**. **⚠️⚠️⚠️§3에서 사이징된 소자 전부가 §5에도 등장하는가(PRE-FLIGHT 6번) — 아래 §1.5의 sub-block 커버리지 절차를 반드시 따를 것**. **⚠️⚠️⚠️⚠️`build_stick_diagram()`이 직접 반환한 게 아니라 사람이 제안·재배열한 순서(예: "이렇게 섞으면 안 되나")라면, 채택/게시 전 반드시 `check_walk_sequence(sequence, transistors)`로 먼저 검산할 것**(PRE-FLIGHT 25번 — finger 개수가 실제 채택안과 똑같아도 순서가 실제로 안 이어질 수 있다) | `stick_diagram.py`의 `build_stick_diagram()`(데이터, 정본) + `check_walk_sequence()`(제안된/재배열된 순서 검산) + `assets/report_template.html`의 `renderStack()`(시각화, 그대로 재사용) + §1.5(커버리지 교차검증) |
| 6 | **수정된 W 반영 시뮬레이션 검증** | box-shape 스냅으로 바뀐 실제 W로 **다시 돌린** SPICE 결과(gain/GBW/slew-rate/matching/전류 등)가 §5 체크리스트의 원 스펙을 여전히 만족하는지. 스냅 전/후 수치 차이와 그 원인을 명시(§5 "스냅이 무해하다고 가정하지 말 것") | SPICE 실측, `references/gm-id-methodology.md` §5 검증 체크리스트 재적용 |
| 7 | **Layout 실행 agent를 위한 가이드** | 아래 §2 참조 — 이 회로에서 실제로 성능을 좌우하는 요소를 지목하고, 그 요소별 구체적 layout 지침을 준다. 일반론이 아니라 **이 회로의 실제 소자/net 이름으로** 작성한다 | §2 체크리스트 + 이미 4/5에서 내린 결정(공유 finger_w, Euler trail 순서, common-centroid 배치)을 그대로 재사용 |
| 8 | **물리 floorplan** | 전체 회로(모든 sub-block 포함)를 실제 2D packing한 결과 — bbox, aspect ratio, packing_density, 빈 공간 없이 실제로 채워진 배치가 시각적으로 확인 가능해야 함. §5가 모든 소자를 커버해도 floorplan 자체가 없으면 물리 실현 가능성(빈 공간 없는 packing, 전체 bbox)을 아무도 확인한 적이 없는 것과 같다(PRE-FLIGHT 27번 — 힌트 없는 fresh agent가 이 섹션을 통째로 빠뜨린 채 "완료"로 보고했다) | §1.7 절차 + `pack_floorplan_grouped()`(§8) + `run_full_circuit_audit()`(ALL PASS 확인) |

⚠️ 8개 섹션 중 하나라도 빠지면 산출물 미완성으로 간주한다. 특히 **7번을 생략하고 6번에서
끝내는 관성**이나 **8번(floorplan)을 "선택적 확장"으로 여기고 생략하는 관성**(PRE-FLIGHT
27번)을 경계할 것 — sizing/stick diagram 결정은 layout을 실행할 agent에게 그대로 전달되지
않으면 그 결정이 실제 layout에서 지켜진다는 보장이 없고, floorplan이 없으면 그 결정들이
실제로 빈 공간 없이 물리 배치 가능한지 아무도 확인하지 않은 채로 남는다.

⚠️⚠️ **§1/§5의 시각 렌더링은 `assets/report_template.html`의 실제 렌더링 함수를 코드 그대로
복사해서 재사용한다 — 절대 새로 구현하거나 텍스트로 대체하지 않는다(PRE-FLIGHT 5번).** 이
파일은 "참고 예시"가 아니라 **재사용해야 하는 검증된 구현체**다: `renderSchematic(container,
schem)`(§1 — rails/devices/wires/dots/labels 구조화 객체를 받아 SVG를 그리는 범용 함수),
`renderStack(container, stackName, data)`(§5 — `build_stick_diagram()`의 실제 반환값을
받아 게이트 막대·레일·노드 브래킷이 있는 SVG를 그리는 범용 함수, 내부적으로
`groupRuns()`/`drawNetBrackets()`/`computeMaxDepth()`/`svgLine()`/`svgText()` 헬퍼를 쓴다)
둘 다 `<script>` 블록에 **그대로 붙여넣고**, 그 함수가 기대하는 구조화된 데이터 객체
(`schem`, `stackName`+`data`)만 이 회로에 맞게 채워 넣는다 — 함수 본문은 한 줄도 새로
쓰지 않는다. `build_stick_diagram()`의 `rendered` 필드는 사람이 터미널에서 빠르게 확인하는
디버그 출력이지, 리포트의 §5 시각 자료가 아니다 — 절대 혼동하지 말 것.

**검증 방법**: 완성된 HTML을 브라우저로 열었을 때 §5에 실제 SVG(세로 게이트 막대, 가로 레일 선,
노드 이름 브래킷)가 시각적으로 보여야 한다 — monospace 고정폭 텍스트 블록(`<pre>`)이 보인다면
그 자체로 규격 위반이다. §1도 마찬가지로, 소자마다 `renderSchematic()`이 그린 사각형 채널
심볼(폴리 게이트 색상 구분 포함)이 보여야 하며, 손으로 짠 절대좌표 텍스트 라벨 나열이 아니어야
한다.

## 1.5 §5(stick diagram)의 소자 커버리지 완결성 — "일부만 하고 나머지는 생략" 금지

> **새 topology를 처음 다루는 것이라면**: `assets/library/_TEMPLATE.topology.json`에서
> 시작해 connectivity+matching kind를 확정한 뒤(절차: `analog-topology-json-library.
> design.md` §4.5) 아래 커버리지 절차를 적용한다. 이미 등록된 topology(`library/*.
> topology.json`)라면 그 파일의 connectivity/symmetry를 재사용 — 처음부터 다시 해석하지
> 않는다.

**배경(PRE-FLIGHT 6번)**: §3(모든 소자 확정)과 §5(모든 소자의 stick diagram 존재)는 별개
검사다 — 사이징 단계에서 소자를 빠뜨리지 않는 것과 layout 단계에서 sub-block을 빠뜨리지
않는 것은 같은 종류의 실패를 서로 다른 단계에서 반복할 수 있다.

**규칙**: §3에서 값이 확정된 모든 소자는 §5에도 반드시 등장해야 한다 — 병합된 공유 stack의
일부로든, 독립된 자기 stack으로든. 순수 R/C 수동소자(Cc/Rz 등, 트랜지스터가 아니라
`stick_diagram.py`의 대상이 아닌 소자)만 예외이며, 그 경우도 §7에 배선 지침으로 반드시
다뤄야지 아무 언급 없이 사라지면 안 된다.

**절차 — 회로 전체를 한 번에 flatten해서 배치할 수 없을 때**:

1. **기능적 sub-block을 정의한다** — 회로 구조상 자연스러운 단위(예: Stage-1 core, Stage-2
   output, bias-generator, CMFB, class-AB floating-bias). 이 정의 자체가 이미 이 회로의
   topology 이해에서 나와야 한다(§1에서 이미 확정된 소자 역할 그대로 재사용).
2. **모든 sub-block 쌍에 대해 통합 가능 여부를 실제로 확인한다** — `find_hub_merge_candidates()`
   를 stack_id/sub-block 구분 없이 전체 소자 목록에 돌려 병합 후보를 찾고(§4.1), 후보가 있으면
   `check_multi_leaf_hub_parity()`/`search_shared_finger_w()`로 실현 가능성과 스냅 오차를
   확인한다. 통합이 실익보다 비용이 크면(§8.5 방식으로 행 개수 계산 등) 통합하지 않기로
   결정해도 된다 — **단, 그 결정은 "각 sub-block을 별도 stack으로 유지한다"는 뜻이지 "그
   sub-block의 layout을 생략한다"는 뜻이 아니다.**
3. **통합하지 않기로 한 sub-block도 반드시 자기 자신의 완결된 stick diagram을 갖는다** —
   `build_stick_diagram()`을 그 sub-block의 소자 목록만으로 호출해 Euler trail을 얻고,
   `check_box_shape()`로 그 sub-block 내부의 box-shape를 확인한다(다른 sub-block과 비율을
   맞출 필요는 없다 — 통합 안 하기로 했으니). 소자 수가 적어(1~2개) Euler trail이 사실상
   자명하더라도 생략하지 않는다 — "너무 작아서 stick diagram이 필요 없다"는 판단은 이 skill의
   판단이 아니라 사용자가 검토할 사안이다.
4. **소자 목록을 전체로 합치기 전에 net 이름을 정규화한다(예: 대소문자 통일), 그 다음
   `find_matching_candidates()`를 sub-block 구분 없이 전체 소자 목록에 반드시 실행한다**
   (2번의 `find_hub_merge_candidates()`와 정확히 같은 이유 — sub-block 경계를 넘는 매칭은
   sub-block별로 나눠 돌리면 원천적으로 보이지 않는다, PRE-FLIGHT 8·9번). Euler trail이
   나왔다고 끝난 게 아니다(PRE-FLIGHT 7번).

   - `find_matching_candidates()`가 반환하는 `current_mirror`/`diff_pair` 후보 각각에 대해
     실제 회로 기능상 매칭이 필요한지 판단한다 — **이 함수의 반환값은 후보일 뿐 확정이 아니다**.
     최소 5가지 패턴을 구분할 것: (a) **우연한 net 공유**(예: `[M37b, M40]` — 같은 net에 물린
     별개 기능의 소자, false positive, 기각), (b) **diode→mirror 직렬 체인**(예: `[M31, M32]` —
     한 소자가 diode로 만든 노드를 다음 소자가 게이트로 읽는 순차 구조, hub-leaf 병렬쌍이
     아니므로 interdigitation 대상이 아님), (c) **소비자가 바이어스 노드를 읽는 관계**(예:
     `[M15, M11b]`, `[M16, M9b, M14b]` — 작은 diode 소자가 만든 바이어스 노드를 훨씬 큰 출력
     소자가 게이트로 읽는 구조, 비율 매칭 개념 자체가 성립하지 않음, 기각), (d) **동적
     피드백 루프 공유**(예: `[M7, M36a]`, vcmfb — 정적 바이어스 레퍼런스가 아니라 피드백
     루프 신호를 공유할 뿐이라 interdigitation이 무의미, 기각), (e) **진짜 병렬 매칭쌍/
     기준-미러 관계**(예: `[M37a, M37b]`, `[M9b, M14b]`, 또는 sub-block 경계를 넘는
     `[M27, M28, M29, M8, M13]`, net 정규화 후에만 보이는 `[M6, M27, M28, M29, M8, M13]`) —
     이것만 아래 절차로 실제 처리한다. 판단 근거는 리포트에 반드시 남긴다.
   - 진짜 병렬 매칭쌍(하나의 hub + 서로 다른 leaf 2개 이상)은 `common_centroid_layout()`
     (`Transistor` 리스트를 그대로 넘기면 개수가 같으면 회전 경로(잔차 0), N=2에 비율이
     표에 맞으면 표 기반 경로, 그 외엔 탐색 경로로 자동 분기하며 0-crossover가 안 되면
     crossover로 폴백해 사실상 항상 성공한다)로 실제 row 배치를 계산하고, 반환된 `rows`를
     그대로 §5 stack 데이터로 쓴다 — 손으로 순서를 짜지 않는다. 서로 완전히 동일한
     connectivity를 가진 병렬 leg가 3개 이상이면(예: M27/M28/M29) 이미 순서 교환이 무의미
     하다 — 그냥 인접 배치로 충분하고, 억지로 swap 패턴을 적용할 필요는 없다.
   - **sub-block 경계를 넘는 기준-미러 관계**(예: M27/28/29 → M8/M13)는 먼저
     `build_graph()`+`check_euler_condition()`으로 한 물리 행으로 합칠 수 있는지 직접 확인한다 —
     대개 multi-leaf hub 홀짝 조건(`check_multi_leaf_hub_parity()`) 때문에 불가능하다(예:
     3-leg 기준 + 2개의 개별 leaf = 홀수차수 노드 4개 이상). 병합이 불가능하면 "물리적으로
     인접 배치"(짧은 게이트-net 배선)로 대체하고, 그 근거(미러비 정밀도가 얼마나 중요한지)를
     §7에 명시한다 — 이 판단은 이 skill이 자동으로 내리지 않고 사용자 확인을 받는다.
     소비자가 3개 이상이고(예: M5/M38/M12, 전부 vbias4 공유) 전부를 물리적으로 인접시키면
     이미 확정된 다른 sub-block의 인접 배치 근거와 충돌하는 경우, 억지로 하나를 골라 강제
     배치하지 않는다 — "이 net의 배선 길이/불일치를 3개 소비자 사이에서 최대한 균등하게
     맞추라"는 라우팅 우선순위 지침으로 §7에 명시하고, 최종 물리 배치는 floorplan 판단 영역
     (이 skill의 범위 밖)임을 정직하게 고지한다(§2 항목7).
   - 1핑거 소자를 매칭 처리하려면 최소 2핑거(짝수)가 필요해 W가 늘어날 수 있다(PDK 최소폭
     스냅과 같은 종류의, 그러나 별도의 오버사이즈 비용이다 — 반드시 별도로 명시한다). 이 핑거
     증가가 다른 sub-block의 box-shape 비율을 깨뜨릴 수 있으므로, 매칭 수정 뒤에는 **3번의
     `check_box_shape()`를 그 sub-block 전체에 대해 다시 실행**해야 한다(재조정이 필요하면
     §8.5 방식으로 비용을 계산해 결정할 것 — 다른 소자를 짝수 핑거로 늘려 균형을 맞추는 것도
     유효한 선택지다).
5. **완료 후 반드시 교차검증한다**: §3(sizing) 표에서 뽑은 전체 소자 이름 집합과, §5의 모든
   stack/sub-block에 등장하는 전체 소자 이름 집합을 **집합 비교**한다(눈대중 대조 금지 —
   두 리스트를 실제로 diff할 것). 일치하지 않으면(§3엔 있는데 §5엔 없는 소자가 하나라도
   있으면) 리포트는 미완성이다 — 3번으로 돌아가 빠진 sub-block의 stick diagram을 마저 만든다.
   **⚠️⚠️이 "집합 비교"는 눈대중이나 프로즈 절차로 남겨두지 말고 반드시
   `check_stick_diagram_coverage(sized_device_names, stick_diagram_devices)`를 실제로
   호출해서 확인한다**(PRE-FLIGHT 27번 — 이 5단계가 프로즈로만 존재하던 시기에 힌트 없는
   fresh agent가 정확히 이 단계를 건너뛰어 22개 소자의 stick diagram이 통째로 빠진 채
   리포트가 "완료"로 게시됐다 — 그 뒤 이 함수가 harness로 신설됐다). `sized_device_names`는
   §3 표에서 직접 뽑아야지, `run_full_circuit_audit()`에 넘긴 `devices` dict를 재사용하면
   안 된다 — 그 dict 자체가 애초에 sub-block 하나를 통째로 빠뜨린 채 구성됐을 수 있고, 그
   경우 같은 dict를 재사용하는 순간 같은 누락이 그대로 보이지 않게 된다(§1.6 참고).
6. 이 5단계는 **한 번 돌고 끝나는 절차가 아니라, 교차검증에서 불일치가 나오는 한 반복하는
   iteration이다** — sub-block 하나를 완성했다고 다음 sub-block으로 안 넘어가고 멈추는 것이
   실제로 발생한 사고이므로, "모든 sub-block을 다 커버했는가"(존재 여부)와 "각 sub-block의
   matching-critical 소자가 실제로 매칭 처리됐는가"(정합성)를 **둘 다** 마지막에 다시 확인하는
   단계를 워크플로우에서 건너뛰지 않는다.
7. **`check_stick_diagram_coverage()`가 PASS(§5 커버리지)라고 해서 §8(floorplan)까지
   자동으로 커버되는 게 아니다** — 이 함수는 "stick diagram 행에 등장하는가"만 확인하지,
   "그 소자가 실제 2D floorplan packing에 포함됐는가"는 별도 질문이다(PRE-FLIGHT 27번, 같은
   사고에서 §5/§8 둘 다 빠졌지만 원인과 검증 대상이 다르다). §8까지 마쳤는지는
   `run_full_circuit_audit()`의 `AuditResult.ok`와 floorplan 결과물(bbox/aspect/
   packing_density)이 실제로 존재하는지를 별도로 확인할 것 — §1 표 8번 참고.

## 2. 7번 섹션(Layout 가이드) 작성 체크리스트

**원칙: 일반적인 아날로그 layout 상식 나열이 아니라, 4/5번에서 이미 내린 결정과 이 회로의 실제
소자·net을 근거로 구체적으로 쓴다.** "매칭이 중요한 소자는 common-centroid로 배치하세요" 같은
문장은 그 자체로는 무의미하다 — "M2/M2b는 §4에서 확정된 Euler trail 순서
`M2,M2b,M2b,M2,M2,M2b,M2b,M2`대로 배치하고 양끝에 dummy finger를 추가하라"처럼 **이미 결정된
값을 그대로 실행 지침으로 옮겨야** agent가 별도 판단 없이 바로 쓸 수 있다.

체크리스트(해당하는 항목만 채우되, 회로에 존재하는 한 빠짐없이):

1. **Gain/고임피던스 노드** — 어느 net이 dominant pole(또는 그에 준하는 고임피던스 노드)인가.
   그 net의 기생 Cgd/Cdb/routing 커패시턴스가 직접 GBW/phase margin을 깎으므로, **배선 길이
   최소화·해당 net 위로 다른 신호선 교차 금지·junction 면적 최소화**를 명시한다.
2. **Matching-critical 소자군** — §4에서 병합/interdigitation/common-centroid를 적용하기로
   확정한 소자들: 그 **실제 finger 순서**(§5의 node_sequence/transistor_sequence)를 그대로
   배치 순서로 지정하고, dummy device 필요 여부(배열 양끝 edge effect 보정), 동일 orientation·
   동일 well 유지(응력/온도 gradient에 의한 Vt 미스매치 방지) 지침을 준다.
3. **고전류/전력 소자** — ID가 큰 branch(예: 3단 OTA의 출력단)는 electromigration(EM) 한도를
   넘지 않는 metal strap 폭·비아 개수를 명시. 발열이 큰 소자는 열구배가 위 2번의 matching 소자군에
   영향을 주지 않도록 배치 거리를 확보한다(공유 finger_w로 묶인 stack이면 특히 주의 — 물리적으로
   붙어있는 stack 간 열결합 가능성).
4. **민감 바이어스/신호 net** — 차동쌍의 tail 노드, 미러의 bias 노드처럼 작은 흔들림도 전체
   회로에 영향을 주는 net은 디지털 스위칭 소자·큰 전류 변화가 있는 net과 물리적으로 분리하거나
   guard-ring/shield로 격리할 것을 명시한다.
5. **보상 소자(Miller cap 등)** — 위상보상 커패시터가 있으면, 그 커패시터로 이어지는 배선이
   추가하는 기생 저항/커패시턴스가 설계식이 가정한 값과 얼마나 벗어나도 되는지(설계 여유) 명시.
6. **§4.1/§4.2에서 이미 확정된 stack 배치 자체** — 어떤 stack이 어떤 stack과 물리적으로
   합쳐졌는지(병합 stack), 어떤 stack이 독립 행으로 남았는지, 그 stack들의 상대적 배치 순서(좌우/
   상하)까지 — layout agent가 4/5번 섹션을 다시 해석할 필요 없이 바로 floorplan으로 옮길 수 있는
   수준으로 재진술한다.
7. **명시적으로 다루지 않는 것들에 대한 정직한 고지** — 이 skill이 실제로 검증하지 않은 항목
   (예: 정확한 ESD 규칙, foundry-specific DRC, 정확한 guard-ring 폭)은 "PDK/DRC 매뉴얼을 따로
   확인할 것"이라고 명시하고 임의로 숫자를 지어내지 않는다.

## 3. 사람 + Agent 이중 가독성 — 형식 요구사항

리포트는 **하나의 HTML 파일**로 만들되, 다음 두 겹을 모두 갖춘다:

1. **시각 렌더링 층**: 사람이 브라우저로 열어 읽는 층. `artifact-design` skill의 원칙(테마 대응,
   실제 콘텐츠 기반 typography, 겹침/overflow 없는 레이아웃)을 따른다. 표/스키매틱/stick
   diagram/SPICE 카드 모두 `assets/report_template.html`의 검증된 렌더링 함수(`renderSchematic()`,
   `renderStack()` — 여러 물리 행은 이 함수를 행마다 반복 호출해 그린다, 별도의 multi-row 전용
   함수는 없다)를 그대로 복사해 재사용한다.
2. **기계 판독 층**: 같은 HTML 안에 `<script>` 블록으로 순수 JS 객체 리터럴(`const REPORT = {...}`)을
   그대로 남긴다 — 시각 렌더링이 이 객체에서 파생되므로(렌더링 함수가 이 객체를 읽어 DOM을 그림),
   **두 층이 서로 어긋날 수 없다**(단일 source of truth). 다른 agent는 이 HTML을 직접 `Read`해서
   정규식/파싱 없이 이 객체 리터럴을 바로 이해할 수 있다(cross-origin iframe이라 브라우저 JS
   실행 컨텍스트에서는 접근 못할 수 있음 — 그래서 파일 자체를 읽는 경로가 항상 보장돼야 한다).
   7번(layout 가이드)도 이 객체 안에 구조화된 필드로 넣는다(자유 텍스트 문단이 아니라
   `layout_guide: {critical_nodes: [...], matching_groups: [...], power_branches: [...], ...}`
   형태) — agent가 필드별로 바로 소비할 수 있게.

## 4. 시각 검증 의무 — Artifact 배포는 그 수단일 뿐, 대상이 아니다

**이 skill의 모든 산출물(HTML 리포트)은 완료 보고 전에 반드시 시각적으로 검증해야 한다.**
"Artifact로 배포하는 경우에만" 적용되는 규칙이 아니다 — HTML 리포트 자체가 이 skill의 표준
산출물이므로, 그 산출물이 브라우저에서 실제로 어떻게 보이는지 확인하지 않고는 어떤 결과물도
완료로 보고할 수 없다. **아직 Artifact로 배포되지 않은 결과물이라도, 시각 검증이 필요하면
그 검증을 하기 위해 Artifact로 배포하고 `claude-in-chrome` 같은 브라우저 도구로 실제로
열어봐야 한다** — Artifact 배포는 목적이 아니라 시각 검증을 가능하게 하는 수단이다.

절차:

1. HTML을 생성(또는 수정)했으면, 아직 배포되지 않았더라도 시각 검증이 필요한 시점에
   `Artifact` 도구로 배포하고 브라우저 도구(`claude-in-chrome` 등)로 직접 연다.
2. 최소 각 섹션(1~7) 1곳 이상을 스크린샷으로 확인 — 텍스트 겹침, 표 overflow, 스키매틱 배선
   교차/끊김, stick diagram 라벨 겹침 여부를 실제로 본다(시각 검증으로만 찾아낸 실제 사례:
   mirror-wire label 겹침, M2b/M3b drain 미연결, 렌더러가 `schem` 파라미터를 무시하던 잠재
   버그 — 셋 다 데이터 구조는 문법적으로 멀쩡했다).
3. 문제를 발견하면 고치고 **다시 배포 후 재검증** — 한 번의 시각 확인으로 끝내지 않는다.
4. 시각 검증 없이 "생성 완료"/"반영 완료"라고 보고하지 않는다 — 데이터 구조가 문법적으로
   유효하다는 것과 실제로 브라우저에서 깨끗하게 렌더링된다는 것은 별개다. 이 원칙은 HTML
   리포트뿐 아니라 이 skill이 만드는 **모든 결과물**(수정된 아티팩트, 새로 만든 리포트, 기존
   리포트의 부분 수정)에 동일하게 적용된다.

## 5. 참고 — 기존 3-example 아티팩트와의 관계

`stick_artifact.html`(Example 1/2/3)은 1~6번을 이미 갖췄다. 7번(layout 가이드)만 신설
요구사항이다. 기존 아티팩트에 7번을 소급 반영할지는 별도로 판단할 것 — 이 문서는 **앞으로의
모든 산출물에 적용되는 규격**을 정의할 뿐, 기존 산출물을 자동으로 규격 위반으로 만들지 않는다.
