---
id: 20260930-b26-pre-test-strengthen
phase: 2
evidence_type: test-only
gate_change: no
---
## 의도

B26-1(`20260930-b26-rail-accessor-set`) 2차 검토(`_drafts/review2_b26_1.md` §3 E6·E7)가 찾은 경로를 이 card가 먼저 test로 고정한다. 이 경로들은 **기존 동작인데 기존 test가 실행하지 않거나 결과를 보지 않는다**.
B26-1은 이 경로의 호출문에 `rails=rails`를 붙이거나(새 문장, T1), 그 뒤 문장을 읽는다(T6·넓힌 T6). 그래서 이 경로가 B26-1의 V3 대상에 들어오는데, 지금 test로는 그 변이가 죽지 않는다.
경로 자체는 레일과 무관하다. euler-blocked 행 분할, 핑거증가 루프의 반환 경로, LUT 없는 spec의 matching 수리, 전체 감사 체크 3, stack 후보 경로, 포트 선언 경로, 넷 대소문자 충돌 보고, 구조 대칭 씨앗의 양방향이다.

**원칙 기본안(결정 아님 -- 근거)**:
* B26-1 card에서 이 몫을 면제하지 않는다. A1-a 묶기 면제는 '죽일 수 있는 변이'에 쓰지 않는다.
  근거는 이미 정한 원칙 두 개다. '우회/skip은 타당성 검토 후에만'(면제는 판정 범위 축소다)과 '결정은 원칙으로 기본안부터'(사용자 몫은 spec·회로 해석·약화 승인뿐이다)이다.
* 기존 동작을 고정하는 test를 **먼저** 더해 변이를 죽인다.
* 판정 기준은 약해지지 않는다. 엔진·도구·레지스트리·library는 바꾸지 않는다(test-only).
* 새 test는 base에서 PASS한다(기존 동작 고정, oracle (a)·(c)).
* 기존 동작이 문서화된 의도와 어긋나 보이는 곳은 test로 고정하지 않는다('거짓 기준값 금지'). 이번 측정에서 한 곳(`interdig_ok` backfill)이 그렇다.
  이 card는 그 두 문장(SR 11800·11879)을 죽이지 않고, 별도 red-green card 초안(`_drafts/draft_b26_backfill_audit.spec.md`)과 사용자 질문(`_drafts/b26_backfill_question.md`)으로 넘긴다.

**범위**: review2는 E6 17개·E7 12개(합 29)를 셌다(정의 N2(b)+넓힌 T6, review2 판 head).
이 card는 v4 모의 head(사이트 10·14를 B35로 넘긴 B26-1 개정판 상당)에서 다시 쟀다. N2d 대상 중 E6·E7 def만 골랐고, 생존은 **변이 id 34개**(E6 19, E7 15)다(표 1). 이 34개가 review2의 29개를 포함한다.
변이 id 34개는 base 문장으로 **32개**다. SR 9404·9406은 중첩 def(`_evaluate_row_split`)와 바깥 def(`optimize_full_circuit_budget`)에 두 번씩 나온다.
B26-1 사이트 자체(E1), def 기본값(E3), `_propose_*` 가드(E4)는 이 card에 넣지 않는다. B26-1 card의 계약 7(e)·4·14 몫이다(표 2).

**원칙 -- 정본은 topology 무관**:
* 모든 입력은 합성 넷리스트·합성 topology다(소자 이름 `M..`, 내부 넷 `n..`·`g..`·`vtail`). library 회로·소자 이름을 test에 쓰지 않는다.
* 레일 넷은 `vdd`·`gnd`만 쓰고, topology에는 `supply_nets: ["vdd", "gnd"]`를 선언한다. 그래서 B26-1 뒤에도 같은 판정이 나온다(계약 8).
* 등가 주장은 library 회로만으로 하지 않는다. 합성 입력으로 구별되는지 먼저 잰다(v1의 '씨앗 등가' 주장이 합성 입력으로 깨졌다 -- 계약 10).

## 관찰 가능한 계약

**공통 입력(계약 1~3)**:
* `toy_lut` 픽스처(conftest)를 쓴다.
* 입력을 만드는 데 쓰는 기존 공개 심볼(피검이 아니다): `size_transistor`, `SemiEmpiricalGmIdLUT.gm_gds_ratio`, `stick_diagram.build_stick_diagram`(계약 3의 `EULER_OK`). 클래스 `SizingContext`(필드 `sized`·`topology_path`)와 `Transistor`(필드 아래)는 생성자로만 쓴다.
* `r = size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=toy_lut, vds=0.6)`로 두고, `W0 = r.W`.
* 사이징 항목 `S = {"ID": r.ID, "W": W0, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0, "gds": r.gm / toy_lut.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0), "kind": "nmos", "vds": 0.6, "vsb": 0.0}`.
* 컨텍스트 `ctx(names) = sizing_recipe.SizingContext(sized={n: dict(S) for n in names}, topology_path=<계약 8의 합성 topology 파일 경로 문자열>)`.
* `Transistor`는 `sizing_recipe.Transistor`다. 이름과 kind는 위치 인자로, 나머지는 키워드로 준다(`source`·`drain`·`gate`·`n_fingers`·`finger_w`·`stack_id`). 주지 않은 필드는 기본값이다.
* 별 행 `STAR`: `M1(source="na", drain="nx", gate="g1")`, `M2(source="nx", drain="nb", gate="g2")`, `M3(source="nx", drain="nc", gate="g3")`.
  모두 `"nmos"`, `n_fingers=1`, `finger_w=W0`, `stack_id="row"`이다. 넷 `nx`는 차수 3, `na`·`nb`·`nc`는 차수 1이다.
  홀수 차수 넷이 4개인 연결 그래프라 한 번의 trail로 그릴 수 없다.
* 차동 쌍 `PAIR`: `Ma(source="vtail", drain="nda", gate="ga")`, `Mb(source="vtail", drain="ndb", gate="gb")`. 모두 `"nmos"`, `n_fingers=1`, `finger_w=W0`, `stack_id="seg1"`이다.
* 측정 기준: `metrics = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}`, `loose = [{"metric": "pair_area", "op": "<=", "value": 2 * W0 * 0.5e-6 * 3.0}]`.

1. **LUT 없는 spec의 matching-safety 수리(E6-a, `optimize_full_circuit_budget`)**
   * 입력 topology(계약 8 형식):
     * `netlist` = `PAIR`의 두 소자(`name`·`kind`·`source`·`drain`·`gate`)
     * `device_roles = {"Ma": {"gm_id_role": "", "L_role": ""}, "Mb": {"gm_id_role": "", "L_role": ""}}` -- 빈 문자열은 '선언했고 값 없음'이다. 자동 채움이 이 필드를 채우지 않고 L·gm/ID 유도도 하지 않는다.
     * `symmetry.matching_pairs = [{"names": ["Ma", "Mb"], "matching_sensitivity": "offset", "current_forced": False}]`
     * `sizing_roles = {"metrics": {"pair_area": {"type": "sum_area", "unit": "m^2", "devices": ["Ma", "Mb"]}}, "constraints": [{"metric": "pair_area", "op": "<=", "value": 2 * W0 * 0.5e-6 * 3}]}`
   * spec(**`lut_by_kind` 없음**): `{"known_sizing": {"Ma": S, "Mb": S}, "min_finger_w": 0.1e-6, "max_finger_w": 40e-6, "L_min": 0.1e-6, "gm_id_bounds": (2.0, 28.0), "stack_groups_override": {"pair_row": ["Ma", "Mb"]}}`.
   * `res = optimize_full_circuit_budget(<경로>, spec)`, `pr = res["pipeline_result"]`이면 다음이 성립한다.
     * (a) `"repaired_rows" in pr`이고 `"repaired_audit" in pr`이며 `"growth_rounds" not in pr`이다.
       근거: 코드 주석(sizing_recipe.py 9363~9367, a796468) "lut_by_kind가 없는 구형 spec은 gm/ID 재검증이 불가능하므로 기존 bare repair_matching_safety()로 폴백".
     * (b) `res["audit_ok"] is False`다. `pr["repaired_audit"].checks` 중 이름이 `"3c."`로 시작하는 체크는 정확히 1개이고 그 `.ok is False`다.
       근거: offset 쌍은 3c가 필수이고, `repair_matching_safety` docstring(stick_diagram.py 7555~7557) "`n_fingers`가 너무 작으면(예: 1) `common_centroid_layout()`의 회전-최적 경로 자체가 기하학적으로 `dx<=0.5`를 달성 못 한다". 핑거증가가 없는 경로라 그대로 남는다.
     * (c) `pr["repaired_rows"]`의 모든 키는 `"pair_row_repair"`로 시작하고, 그 행들의 소자 이름을 모아 정렬하면 `["Ma", "Mb"]`다.
       근거: `repair_matching_safety` docstring(같은 파일 7532) "행들(`f"{원래행}_repair{i}"`)로 대체한다".
     * (d) `{t.stack_id for t in pr["transistors"]} == set(pr["repaired_rows"])`다.
       근거: 코드 주석(sizing_recipe.py 9408~9412) "repaired_rows를 최종 정본으로 승격해 transistors/box_shape/audit_row_split을 덮어써서".
2. **euler-blocked 연결 행의 그룹 분할(E6-b, 공개 진입점 `run_matching_safety_with_finger_growth` 경유)**
   * 호출: 합성 topology(계약 8, netlist = `STAR` 세 소자의 연결)를 쓰는 `ctx(["M1","M2","M3"])`로
     `res = run_matching_safety_with_finger_growth({"row": STAR}, [], {}, ctx, {"nmos": toy_lut}, {}, [], gm_id_bounds=(11.9, 12.1))`.
   * 기대(`rows = res["rows"]`):
     * `set(rows) == {"row_seg0", "row_seg1"}`다.
     * 두 행의 소자 이름 합집합을 정렬하면 `["M1", "M2", "M3"]`이고, 겹치지 않으며, 각 행이 비지 않는다.
     * 모든 소자의 `stack_id`는 자기가 든 행의 키와 같고, `n_fingers == 1`이다.
   * 근거:
     * 이 함수의 모든 반환은 euler 정리(`_fixup_euler_blocked_rows`)를 거친다(코드 주석 sizing_recipe.py 11784~11786).
     * 정리 함수 docstring: "1순위: `apply_and_revalidate_pair_adjustment()`로 매칭쌍 핑거증가, 안 되면 2순위: `find_min_crossover_layout_with_branch_composite()`로 그래프 이론상 항상 성공하는 그룹분할".
       gm/ID 범위 `(11.9, 12.1)`은 사이징 값 12.0 둘레로 좁아서 핑거증가 후보가 gm/ID 검증을 통과하지 못한다(입력 구성). 그래서 2순위로 간다.
     * 홀수 차수 넷이 4개이므로 trail이 최소 2개 필요하다(구성).
     * 세그먼트 이름 `<행>_seg<i>`와 '그룹분할은 순수 재배치라 W/n_fingers 불변'은 정리 함수 docstring·코드 주석의 서술이다. 이름 형식 자체는 (c) 기준선 값이다.
   * 어느 소자가 어느 세그먼트에 가는지는 계약이 아니다.
   * v1은 비공개 함수 `_fixup_euler_blocked_rows`를 직접 불렀다. 계약 8(비공개 도우미 금지)과 Phase 3 이동·개명 위험 때문에 공개 진입점으로 바꿨다. 같은 세 변이(SR 11696·11698·11700)가 죽는다(실측).
3. **핑거증가 루프의 반환 경로(E6-c, `run_matching_safety_with_finger_growth`)**
   * 모든 호출은 `lut_by_kind={"nmos": toy_lut}`, `gm_id_bounds=(2.0, 28.0)`이다.
   * 반환 공통 판정 `EULER_OK(res)`는 다음 둘이 함께 참인 것이다.
     * `res["audit"].checks` 중 이름이 `"1. euler["`로 시작하는 체크가 1개 이상이고 전부 `.ok`다.
     * `build_stick_diagram([t for v in res["rows"].values() for t in v])`의 모든 값이 `.status == "ok"`다.
   * 근거: 코드 주석(sizing_recipe.py 11784~11786) "이 함수의 **모든** 반환 지점에서 최종 rows/ctx를 내보내기 전에 반드시 이 euler 정리를 거치고 그 결과로 audit을 다시 계산한다".
   * (a) **라운드 0개 소진**
     * 호출: `({"seg1": PAIR}, [("Ma","Mb")], {("Ma","Mb"): "offset"}, ctx(["Ma","Mb"]), lut_by_kind, metrics, loose, max_rounds=0)`.
     * 기대: `growth_rounds == []`, `unresolved_pair == "unknown"`, `unresolved_reason == "max_rounds_exceeded"`, `audit.ok is False`.
       `"seg1" not in rows`이고 모든 행 키가 `"seg1_repair"`로 시작한다(루프가 돌지 않아도 마지막 수리 1회와 정리를 거친다). 소자 이름을 모아 정렬하면 `["Ma","Mb"]`다.
   * (b) **라운드 0개 + euler 정리**
     * 호출: 행 `{"seg1": PAIR, "row": STAR}`, `ctx(["Ma","Mb","M1","M2","M3"])`, 나머지는 (a)와 같다.
     * 기대: `EULER_OK(res)`.
   * (c) **처음부터 통과**
     * 호출: `({"seg1": PAIR}, [("Ma","Mb")], {("Ma","Mb"): "ratio"}, ctx(["Ma","Mb"]), lut_by_kind, metrics, loose)`, `max_rounds`는 기본값.
     * 기대: `unresolved_pair is None`, `unresolved_reason is None`, `growth_rounds == []`, `relaxed_pairs == []`, `audit.ok is True`.
       `rows`의 각 행을 `[(이름, n_fingers, stack_id), …]`로 펼치면 `{"seg1": [("Ma", 1, "seg1"), ("Mb", 1, "seg1")]}`다.
     * 근거: ratio 쌍은 3c가 필수가 아니다(3b만 필수). 같은 행에 인접한 두 소자로 이미 통과한다(docstring "(2) `ok`면 성공 종료").
   * (d) **실패 쌍의 소자가 행에 없음**
     * 호출: 행 `{"seg1": PAIR, "row": STAR}`, 매칭 쌍 `[("Ma","Mx")]`(`Mx`는 어느 행에도 없다), `{("Ma","Mx"): "offset"}`, `ctx(["Ma","Mb","M1","M2","M3"])`, metrics, loose.
     * 기대: `unresolved_pair == ("Ma","Mx")`, `unresolved_reason == "pair_not_found"`, `growth_rounds == []`, `relaxed_pairs == []`, `EULER_OK(res)`.
   * (e) **3c 실패 없음(euler만)**
     * 호출: 행 `{"row": STAR}`, 매칭 쌍 `[]`, `{}`, `ctx(["M1","M2","M3"])`, metrics `{}`, constraints `[]`.
     * 기대: `unresolved_pair is None`, `unresolved_reason == "only_3b_failures_left"`, `growth_rounds == []`, `audit.ok is True`, `EULER_OK(res)`.
   * `unresolved_reason` 문자열 `"max_rounds_exceeded"`·`"pair_not_found"`·`"only_3b_failures_left"`, `unresolved_pair == "unknown"`, 행 이름 `seg1_repair…`는 docstring에 없는 반환 리터럴이다 -- (c) 기준선 값이다.
4. **전체 감사 체크 3 -- 처분 없는 후보(E7, `run_full_circuit_audit_from_topology`)**
   * 입력 topology(계약 8):
     * netlist: `M1(nmos, source="gnd", drain="nb", gate="nb")`, `M2(nmos, source="gnd", drain="nout", gate="nb")`, `Ma(nmos, source="ntail", drain="nda", gate="nga")`, `Mb(nmos, source="ntail", drain="ndb", gate="ngb")`
     * `_netlist_sections_structured = {"blk": {"devices": ["M1","M2","Ma","Mb"]}}`
   * 구성으로 정해지는 후보 키 4개(함수 docstring의 정의):
     * `("hub_merge","nmos","gnd")` -- M1·M2가 source를 공유한다.
     * `("hub_merge","nmos","ntail")` -- Ma·Mb가 source를 공유한다.
     * `("current_mirror","nmos","nb")` -- M1·M2가 gate를 공유한다.
     * `("diff_pair","nmos","ntail")` -- 레일이 아닌 같은 source에 gate가 다르다.
   * `symmetry.dispositions` = 이 4키 중 `omit` 하나를 뺀 나머지 각각 `{"tag": t, "kind": k, "key": n, "category": "real_match", "reason": "<아무 글>"}`.
   * 판정 대상 `c3` = 결과 `.checks` 중 이름이 `"3."`으로 시작하는 체크다. 정확히 1개여야 한다.
   * 기대(**네 경우, 각각 별개 test 함수** -- parametrize 문자열 id 금지):
     * `omit`이 없으면(4키 전부 처분) `c3.ok is True`다.
     * `omit`이 `("current_mirror","nmos","nb")`이면 `c3.ok is False`이고 `repr(omit)`이 `c3.detail` 문자열에 들어 있다.
     * `omit`이 `("diff_pair","nmos","ntail")`이면 위와 같다.
     * `omit`이 `("hub_merge","nmos","gnd")`이면 위와 같다.
5. **stack 배치의 후보 경로(E7, `resolve_stack_layout`)**
   * 캐스코드 차동 넷리스트 `CAS`(표기 `source→drain`):
     * `M1(nmos, ntail→nx1, gate ninp)`, `M2(nmos, ntail→nx2, gate ninn)`
     * `M1c(nmos, nx1→no1, gate nvc)`, `M2c(nmos, nx2→no2, gate nvc)`
     * `M3(pmos, vdd→no1, gate nvp)`, `M4(pmos, vdd→no2, gate nvp)`
     * `M5(nmos, gnd→ntail, gate nvb)`
   * 호출: `groups = resolve_stack_layout(CAS, [], {})`. override도 `vertical_stack_id` 선언도 없으므로 docstring 우선순위 3번 경로다.
     docstring(sizing_recipe.py 6507~6509): "declared가 통째로 비어있는 회로 … `refine_differential_and_mirror_relations()`의 `vertical_stack_id_candidates`(analog-grammar 기반 제안)로 폴백".
     같은 docstring은 3번 결과가 반환 전에 `derive_horizontal_stack_groups(transistors, groups, matching_pairs)`를 거친다고 적는다("먼저 kind로 쪼갠 뒤 … 선언된 매칭쌍만으로 그룹과 그룹을 잇는"). 여기서 매칭쌍은 `[]`다.
   * 기대:
     * 모든 그룹의 소자를 모으면 각 소자가 정확히 한 번 나온다(반환 계약 `{stack_id: [device_name, ...]}`, 같은 docstring).
     * 각 그룹의 kind는 하나다(같은 docstring "먼저 kind로 쪼갠 뒤").
     * **`M1`과 `M2`를 함께 담는 그룹이 있다** -- (c) 기준선 값(a796468).
       `refine_differential_and_mirror_relations` docstring은 `vertical_stack_id_candidates`가 "cascode-stack 등 composite 병합(물리적 그룹)과 differential-pair/mirror 관계(leg a/b 판정)를 합친 최종 `vertical_stack_id` 후보"라고 적는다.
       차동 쌍 두 다리가 공통 tail(`ntail`) composite에 함께 드는 것이 그 서술과 모순되지 않는다. 다만 어느 composite에 드는지는 docstring이 정하지 않으므로 기준선 값으로 둔다.
   * v1의 근거 인용(`propose_vertical_stack_id_gap_fill` docstring 2번)은 이 경로의 함수가 아니어서 지웠다. '마지막 폴백은 소자마다 혼자'는 피검 내부 동작이라 계약 근거에서 뺐다(계약 9의 변이 판정 설명에만 쓴다).
6. **vertical_stack_id 제안의 포트 경로(E7, `propose_vertical_stack_id_gap_fill`)**
   * 입력: 위 `CAS`, `device_roles = {"M1": {"vertical_stack_id": "colA"}}`.
   * (a) 포트 인자 없음: `proposals == {"M1c": "colA", "M3": "colA"}`. 2단자 내부 넷 `nx1`·`no1`의 직렬 KCL 엣지만 쓰이기 때문이다(`ntail`은 3단자).
   * (b) `inputs=("ninp","ninn"), outputs=("no1","no2"), biases=("nvb","nvc","nvp")`를 주면:
     * `proposals == {"M1c": "colA", "M2": "colA", "M2c": "colA", "M3": "colA", "M4": "colA"}`, `conflicts == {}`.
     * `components_used`를 원소별로 정렬한 뒤 정렬하면 `[["M1","M1c","M2","M2c","M3","M4"], ["M5"]]`다.
     * 근거: differential 관계 M1–M2가 두 컬럼을 잇는다(docstring 2번).
7. **넷 대소문자 충돌 보고(E7, `load_topology` meta)**
   * 입력 topology(계약 8), netlist:
     * `M1(nmos, ntail→no1, gate ninp)`, `M2(nmos, ntail→no2, gate ninn)`
     * `M3(pmos, vdd→no1, gate no1)`, `M4(pmos, vdd→no2, gate no1)`
     * `M5(nmos, gnd→ntail, gate nvb)`, `M6(nmos, gnd→NQ, gate nvb)`, `M7(nmos, gnd→nq, gate nvb)`
   * 기대: `meta["_device_roles_gap_fill_review_needed"]`를 목록으로 본다(값이 `None`이면 빈 목록). 그 원소 중 키 `"case_collisions"`를 가진 것의 값을 모은 목록이 정확히 `[{"nq": {"NQ", "nq"}}]`다.
   * 근거: `_scan_case_collisions` docstring(stick_diagram.py 928~930) "표기가 다른(대소문자만 다른) net이 있으면 `{lower: {실제 표기, ...}, ...}`로 반환한다".
     그 값이 `review_needed`의 `case_collisions` 항목으로 실리는 것은 (c) 기준선 동작이다.
8. **입력 규칙(B26-1 이후에도 판정 불변)**
   * 합성 topology 파일은 `tmp_path`에 쓴다. 최상위에 `"topology_name"`, `"schema_version": "2.0"`, `"supply_nets": ["vdd", "gnd"]`, `"netlist"`, `"symmetry"`를 둔다(`symmetry`가 따로 없으면 `{"matching_pairs": [], "dispositions": []}`).
   * 계약 2·3의 `SizingContext.topology_path`는 그 test가 쓰는 소자를 모두 담은 합성 topology 파일이다. 계약 3은 `PAIR`·`STAR`를 다 담은 파일 하나를 써도 된다.
   * 넷 이름 `vdd`·`gnd`는 레일로만 쓴다(소문자, 선언과 같다).
   * 새 test 파일은 하나다: `A/tests/contracts/test_b26pre_existing_paths.py`. test 함수 이름은 `test_b26pre_`로, 모듈 수준 도우미 이름은 `_b26pre_`로 시작한다.
   * 엔진 비공개 도우미(`_dc_replace`, `_fixup_euler_blocked_rows` 등 `_`로 시작하는 엔진 심볼)는 부르지 않는다. `stack_id`는 생성자 키워드로 준다.
   * `AuditResult`·`Transistor` 객체 자체를 `==`로 비교하지 않는다. 필드·이름 튜플로 비교한다.
9. **변이 판정(auditor 측정 -- 영구 test 아님)**
   * 측정 단위는 **base 문장**이다(표 1의 32문장, SD 3285는 `stmt_delete`와 `cmp_flip` 두 변이로 센다 -- 그래서 32 = stmt_delete 31 + cmp_flip 1). 변이 id(34) 환산은 참고로만 적는다.
   * 표 1의 '죽음' 문장마다 base 변이를 만들어 이 card의 새 test 파일만 실행하면 실패한다(assert 실패 또는 예외).
   * 표 1의 '생존' 3문장(SR 11800·11802·11879)은 이 card가 죽이지 않는다. 처리는 '결정 필요 항목' U2다.
   * 결과는 판정 기록 `reproduced_numbers`에 적는다(test-only라 `red` 필드가 없다).
10. **구조 대칭 씨앗의 양방향(E7, `load_topology` → `_propose_gm_id_roles`·`_propose_L_roles`·`propose_device_roles_gap_fill`)**
   * 공통 netlist(계약 8 형식, 표기 `source→drain`):
     `M1(nmos, ntail→nd1, gate ninp)`, `M2(nmos, ntail→nd2, gate ninn)`, `M3(pmos, vdd→nd1, gate nbp)`, `M4(pmos, vdd→nd2, gate nbp)`, `M5(nmos, gnd→ntail, gate nvb)`.
   * (a) `TAP_P`: 공통 + `Mx1(nmos, gnd→nx1, gate ninp)`, `Mx2(nmos, gnd→nx2, gate ninp)`, `My(nmos, gnd→ny, gate ninn)`.
   * (b) `TAP_N`: 공통 + `Mx1(nmos, gnd→nx1, gate ninn)`, `Mx2(nmos, gnd→nx2, gate ninn)`, `My(nmos, gnd→ny, gate ninp)`(탭 세 소자의 입력 넷만 바꿈).
   * 각 경우 `_t, meta = load_topology(<경로>)`이면 다음이 성립한다.
     * `meta["_device_roles_autofilled"]["Mx1"]`과 `["My"]`의 `gm_id_role == "matching"`이고 `L_role == "mirror"`다.
     * `meta["_device_roles_autofilled"].get("Mx2", {})`에는 `gm_id_role`·`L_role` 키가 없다.
     * `meta["_matching_pairs_needs_review"]` 원소 중 `sorted(원소["names"]) == ["Mx1","My"]`인 것이 있다.
   * oracle (a) 구성 + docstring 규칙:
     * `find_structural_symmetry_candidates` docstring(stick_diagram.py 2686~): 규칙 3 "**정확히 하나**면 채택 … 0개나 2개 이상이면 이번 라운드는 보류", 라운드 내 순서 "알려진 단자 개수(len(known))가 많은(=더 확실한) 소자부터", 코드 주석 "동점이면 이름순".
     * 씨앗은 차동 쌍 gate `ninp↔ninn`(양방향)과 `vdd`·`gnd` 자기 자신이다(`_propose_L_roles` docstring "좌우 대응 seed로 자동 생성하고(+ `vdd`/`gnd` 자기자신 seed)").
     * 1라운드: `Mx1`(알려진 단자 source·gate 2개)의 기대 파트너는 nmos, source `gnd`, gate(반대 입력)이고 후보는 `My` 하나 → 채택. `Mx2`는 같은 기대 파트너의 후보 `My`가 이미 쓰였으므로 유일 후보가 없다 → 미해결.
     * `_propose_gm_id_roles` docstring "**자기 자신이 아닌 다른 소자로 실제로 풀리는 경우만** `"matching"`으로 확정 … 그 외(대칭 파트너를 못 찾음)는 이 dict에서 아예 뺀다".
       `_propose_L_roles` docstring "(2) … **자기 자신이 아닌 다른 소자**로 풀리면 -> `mirror`" 및 "tail 공급 소자도 아니고 구조 대칭 파트너도 없으면 이 dict에서 아예 뺀다".
       그래서 `Mx1`·`My`는 matching/mirror, `Mx2`는 키 없음이다. 구조 대칭 출처 매칭쌍 제안은 `Mx1/My`다.
   * 두 경우를 별개 test 함수로 둔다. 씨앗의 어느 방향이 빠졌을 때 결과가 바뀌는지는 탭이 어느 입력 넷에 몰렸는지에 달렸으므로 두 방향 모두 필요하다.
   * B26-1 뒤: 씨앗 `{net: net for net in rails.nets}`는 `supply_nets: ["vdd","gnd"]` 선언과 같은 집합이라 판정이 바뀌지 않는다.
   * 이 계약은 v1이 '등가 후보'로 올렸던 씨앗 한 방향 삭제 6개(SD 2100·2101·2176·2177·3985·3986)를 죽인다(독립 검토 `_drafts/review_b26pre.md` §5 문장, 재실측 6/6).

## test-author가 쓰는 이름(소스 열람 없이 쓸 수 있게)

interface card 도구 출력은 심볼 표뿐이라, 이 card가 결과 필드·반환 키 이름을 적는다(값은 위 계약).
* 피검 진입점(공개, 시그니처 불변 -- 이 card가 쓰는 인자만 적는다. 정확한 시그니처는 interface card 심볼 표가 정본이다):
  * `sizing_recipe.optimize_full_circuit_budget(topology_path, spec)` -- 나머지 매개변수는 기본값.
  * `sizing_recipe.run_matching_safety_with_finger_growth(rows, matching_pairs, pair_sensitivity, ctx, lut_by_kind, metrics_specs, constraints, gm_id_bounds=…, max_rounds=…)` -- 앞 7개는 위치 인자로 준다.
  * `sizing_recipe.resolve_stack_layout(transistors, matching_pairs, device_roles)`
  * `stick_diagram.run_full_circuit_audit_from_topology(topology_json_path)` -- 나머지 매개변수는 기본값.
  * `stick_diagram.propose_vertical_stack_id_gap_fill(transistors, matching_pairs, device_roles, inputs=…, outputs=…, biases=…)` -- 포트 인자는 키워드로 준다.
  * `stick_diagram.load_topology(json_path)` -- 반환 `(transistors, meta)`.
* 입력·판정에 쓰는 기존 공개 심볼: `sizing_recipe.size_transistor`, `sizing_recipe.SizingContext`, `sizing_recipe.Transistor`(= `stick_diagram.Transistor`), `stick_diagram.build_stick_diagram`, LUT 메서드 `gm_gds_ratio`.
* 결과 객체 필드:
  * `AuditResult.checks`(목록)·`.ok`(bool), `AuditCheck.name`(str)·`.ok`(bool)·`.detail`(str)
  * `StickResult.status`(`"ok"` | `"blocked"`), `build_stick_diagram(...)`의 반환은 `{행 키: StickResult}`
  * `Transistor.name`·`.kind`·`.n_fingers`·`.stack_id`
* 반환 dict 키:
  * `optimize_full_circuit_budget` → `pipeline_result`·`audit_ok`. `pipeline_result` → `repaired_rows`(`{행: [Transistor]}`)·`repaired_audit`(AuditResult)·`transistors`(목록), 그리고 없어야 할 키 `growth_rounds`.
  * `run_matching_safety_with_finger_growth` → `rows`·`audit`·`ctx`·`growth_rounds`·`unresolved_pair`·`unresolved_reason`·`relaxed_pairs`.
  * `propose_vertical_stack_id_gap_fill` → `proposals`·`conflicts`·`components_used`.
  * `resolve_stack_layout` → `{stack_id: [device_name, ...]}`.
* `load_topology` meta 키: `_device_roles_autofilled`(`{소자: {필드: 값}}`), `_matching_pairs_needs_review`(원소에 `names`), `_device_roles_gap_fill_review_needed`(`None`일 수 있다 → 빈 목록으로 본다).
* 체크 이름 접두사: `"1. euler["`, `"3."`, `"3c."`.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only다. code 커밋이 없고(엔진·도구·레지스트리·library 불변) 새 test 파일 하나만 더한다(`Role: test`).
* 모양: design 05 §9.2-4 표의 test-only 행 -- "`old..new^`는 첫 부모 사슬이고 전부 `Role: test`(1개 이상), `new`는 `Role: audit` 1개, 병합 없음, T = `new^`, K 없음".
* V2: 변경 전 test 집합이 base에서 통과시킨 것은 변경 후에도 모두 PASS해야 한다. 새 test도 base에서 PASS해야 한다(기존 동작 고정).
  시제품 실측(v2): HEAD(`a796468`) 사본과 HEAD+B34 사본 둘 다 **17 passed**다. `PYTHONHASHSEED` 0·1·7·123에서도 같다.
* '거부 확인'은 V2의 red 대신 계약 9(auditor 변이 측정)로 한다. 기존 동작을 고정하는 test라 base에서 실패하는 커밋이 없고, 변이가 그 거부 입력이다.
* V3: code 변경이 없으므로 N/A다. 이 card의 몫은 B26-1의 V3 생존을 줄이는 것이고, 그 효과는 B26-1 auditor가 B26-1 병합본에서 잰다.

## oracle 종류와 출처

* 계약 2·4·6·10 -- (a) 구성 입력. 넷 차수·후보 키·KCL 엣지·대칭 후보 수가 넷리스트에서 손으로 정해진다(각 계약 문장에 근거를 적었다). 피검 함수를 불러 기대값을 만들지 않는다.
  계약 2의 세그먼트 이름 형식(`row_seg<i>`)과 계약 10의 역할 값 이름(`matching`·`mirror`)은 docstring에 적힌 값이다.
* 계약 1·3·5·7 -- **(c) 기존 동작 기준선**.
  * 기준선 = gate `master` `a796468`(B26-1 이전 known-good). 전제는 'B26-1은 이 경로에서 동작 보존 변경'이다(계획 N3.12.3: "기준선이 존재하고 동작 보존 변경이면 (c)").
  * 기대값은 '현재 출력 붙여넣기'가 아니다. 위 기준선의 동작이며, auditor가 그 기준선에서 독립으로 다시 잰다(`checks.V4.basis`의 `oracle 대조:`).
  * 각 (c) 항목은 '문서화된 의도와 모순 없음'을 확인했다(계약 문장마다 docstring·코드 주석을 파일:줄로 인용).
    docstring에 값 자체가 없는 항목은 **(c) 기준선 값**이라고 따로 적었다: `unresolved_reason` 리터럴 3개, `unresolved_pair == "unknown"`, `_repair<i>`·`_seg<i>` 행 이름 형식, 계약 5의 'M1·M2 한 그룹', 계약 7의 `review_needed` 항목 모양.
  * 계약 1의 빈 문자열 역할 값은 입력 구성이다.
  * (c) 고정이 결함을 굳힐 수 있는 곳(문서화된 의도와 어긋나는 기존 동작)은 이 card에 넣지 않았다. 확인된 한 곳(`interdig_ok` backfill, SR 11800·11879)은 별도 red-green card 초안으로 넘겼다.
* **판정기 독립성 한계(계약 3 `EULER_OK`)**: 둘째 조건이 피검 모듈의 `build_stick_diagram`으로 판정한다. 이 card가 노리는 변이(SR 쪽)에는 영향이 없다.
  `build_stick_diagram` 자체가 바뀌는 card에서는 반환 audit의 `"1. euler["` 체크만 보는 첫째 조건이 독립 판정이다.
* **작성자≠검증자**:
  * 기대값은 이 card 문장이 정한다. test-author는 interface card와 이 card만 보고 쓰고, 기대값을 피검 호출로 만들지 않는다(V4 (1)).
  * 시제품(`_drafts/b26pre_v2_scripts/proto_v2_test_b26pre.py`, scratch에서 실행)은 오케스트레이터 사전 측정 전용이다. 커밋하지 않고, test-author·auditor에게 건네지 않으며, 그 출력을 판정 기록의 증거로 쓰지 않는다.
  * 계약 9는 auditor 자신의 스크립트로 잰다.

## 거부해야 할 입력

새 test가 거부(실패)해야 하는 것은 엔진 변이다(계약 9). 대표는 다음과 같다.
* 계약 1: LUT 없는 수리 경로의 수리 호출 삭제, 결과 기록 삭제
* 계약 2: 그룹 분할 세 문장 삭제
* 계약 3: 핑거증가 루프의 성공 분기·pair_not_found 분기·3b만 남음 분기의 삭제, 루프 뒤 수리·정리·반환 삭제
* 계약 4: 체크 3의 current_mirror·diff_pair 후보 루프 삭제
* 계약 5: 후보 경로 분기 삭제
* 계약 6: 포트 분기 삭제, `relations` 검사 뒤집기, differential 엣지 추가 삭제
* 계약 7: case_collisions 보고 삭제
* 계약 10: 세 사이트(`_propose_gm_id_roles`·`_propose_L_roles`·`propose_device_roles_gap_fill`)의 씨앗 한 방향 삭제

통과해야 하는 것: base 엔진(HEAD, HEAD+B34 둘 다).

## library 회로 적용 여부

해당 없음(합성 입력만). 엔진이 바뀌지 않으므로 E-LIB·E-INST는 base와 같다.

## 무동작 판정 입력(무발동 값)

엔진·library·기존 test 전부 -- 판정이 base와 같다(test-only). 새 산출물 필드는 없다.

## 재현할 수치

auditor가 독립으로 잰다. 아래는 오케스트레이터 사전 측정이고 판정 수치가 아니다.

**사본 다시 만들기**(scratch는 측정 뒤 지운다. 스크립트 `_drafts/b26pre_v2_scripts/`):
1. `mkdir -p C:/g106/base && git -C <repo> archive a796468 -o C:/g106/base.tar && tar -xf C:/g106/base.tar -C C:/g106/base` (HEAD 사본)
2. `python -B mk_g106.py` → `C:/g106/b34` = base + B34 코드 변경(사이트 1·2·3·11·11b, `def_replace` 규칙 -- v1의 `v3_scope_classify.build_b34`와 같은 치환)
3. `python -B run_proto.py <base|b34> <seed…>` → 시제품을 `tests/contracts/test_b26pre_proto.py`로 넣고 실행(`C:/g106/out/baseline.txt`)
4. `python -B kill_v2.py <base|b34> 5` → 표 1의 32 base 문장 변이마다 시제품만 실행(`C:/g106/out/kill_<사본>.jsonl`). 변이 위치는 (최상위 def, 문장 첫 줄 글, def 안 순번)으로 사본마다 다시 찾는다.

**v1 측정(그대로 유효, 사본 C:/g87 -- 삭제됨)**:
* V3 대상 분류(`b26v4_classify`): v4 head 32 def, 2,442 변이, N2b 235, N2w 301, N2d 411. review2 판 head는 N2b 265로 review2 수치를 재현했다.
* E6·E7 def 10개의 N2d 대상 166개 중 대응 b1 변이가 있는 160개를 기존 test 인벤토리로 실행: **죽음 106, 생존 54**(대응 없는 6개는 B26-1의 새 문장 -- 범위 밖).
* 생존 54 = 표 1(E6·E7) 34 + 표 2(B26-1 자기 몫) 20.

**v2 시제품 판정**(2026-10-01, `C:/g106`, 시제품 = 계약 1~8·10 문장 그대로 쓴 **17 test** = 계약 1:1 + 2:1 + 3:5 + 4:4 + 5:1 + 6:2 + 7:1 + 10:2):
* 기준 PASS: base·b34 × `PYTHONHASHSEED` 0·1·7·123 = 8회 모두 `17 passed`.
* 표 1 base 32문장: **죽음 29, 생존 3**(SR 11800·11802·11879). base 사본과 b34 사본 결과가 문장별로 같다(죽인 test 이름까지).
  변이 id(34) 환산: 죽음 31, 생존 3(SR 9404·9406이 두 def에 나온다).
* v1(15 test) 대비 더 죽은 것: 씨앗 6문장(계약 10). SR 11828은 v1처럼 `test_b26pre_growth_only_3b_left`가 죽이고, 이제 계약 2 test도 죽인다(그룹 분할이 그 반환 경로를 탄다).
* 표 2(B26-1 자기 몫) 20개는 v1 측정에서 하나도 죽지 않았다(v2에서 다시 재지 않았다 -- 더한 test가 그 def의 다른 문장을 보지 않는다).

**표 1 -- E6·E7 생존 변이(34)와 새 test(시제품 v2)의 판정**

| 묶음 | 변이(head def·연산자·경로) | base 줄(a796468) | 문장(head) | 정의 | 시제품 v2 판정 |
|---|---|---|---|---|---|
| E6-b | `_fixup_euler_blocked_rows` `stmt_delete` `body[5].body[13]` | SR 11696 | `split = find_min_crossover_layout_with_branch_composite(row_transistor` | N2b/N2w/N2d | 죽음 (test_b26pre_euler_fixup_group_split) |
| E6-b | `_fixup_euler_blocked_rows` `stmt_delete` `body[5].body[14]` | SR 11698 | `by_name = {t.name: t for t in row_transistors}` | N2b/N2w/N2d | 죽음 (test_b26pre_euler_fixup_group_split) |
| E6-b | `_fixup_euler_blocked_rows` `stmt_delete` `body[5].body[16]` | SR 11700 | `for seg_idx, seg in enumerate(split['segments']):` | N2w | 죽음 (test_b26pre_euler_fixup_group_split) |
| E6-a | `optimize_full_circuit_budget._evaluate_row_split` `stmt_delete` `body[5].body[3].orelse[0]` | SR 9404 | `repaired_rows, repaired_audit = repair_matching_safety(rows, matching_` | N2b/N2w/N2d | 죽음 (test_b26pre_ofcb_lutless_repair) |
| E6-a | `optimize_full_circuit_budget._evaluate_row_split` `stmt_delete` `body[5].body[3].orelse[1]` | SR 9406 | `pr = dict(pr, repaired_rows=repaired_rows, repaired_audit=repaired_aud` | N2b/N2w/N2d | 죽음 (test_b26pre_ofcb_lutless_repair) |
| E6-a | `optimize_full_circuit_budget` `stmt_delete` `body[12].body[3].body[5].body[3].orelse[0]` | SR 9404 | `repaired_rows, repaired_audit = repair_matching_safety(rows, matching_` | N2b/N2w/N2d | 죽음 (test_b26pre_ofcb_lutless_repair) |
| E6-a | `optimize_full_circuit_budget` `stmt_delete` `body[12].body[3].body[5].body[3].orelse[1]` | SR 9406 | `pr = dict(pr, repaired_rows=repaired_rows, repaired_audit=repaired_aud` | N2b/N2w/N2d | 죽음 (test_b26pre_ofcb_lutless_repair) |
| E7 | `resolve_stack_layout` `stmt_delete` `body[5]` | SR 6573 | `if refined is not None and refined.get('vertical_stack_id_candidates')` | N2b/N2w/N2d | 죽음 (test_b26pre_resolve_stack_candidates) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[10]` | SR 11835 | `if a not in all_devs or b not in all_devs:` | N2d만 | 죽음 (test_b26pre_growth_pair_not_found) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[10].body[0]` | SR 11836 | `current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)` | N2d만 | 죽음 (test_b26pre_growth_pair_not_found) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[10].body[1]` | SR 11837 | `return {'rows': current_rows, 'audit': result, 'ctx': cur_ctx, 'growth` | N2d만 | 죽음 (test_b26pre_growth_pair_not_found) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[1]` | SR 11800 | `_backfill_interdig_ok(result)` | N2b/N2w/N2d | 생존 -- 등가 아님, 결함 card로(U2-b) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[2]` | SR 11801 | `if result.ok:` | N2w | 죽음 (test_b26pre_growth_already_ok) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[2].body[0]` | SR 11802 | `current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)` | N2d만 | 생존 -- 등가 후보(U2-a) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[2].body[1]` | SR 11803 | `return {'rows': current_rows, 'audit': result, 'ctx': cur_ctx, 'growth` | N2d만 | 죽음 (test_b26pre_growth_already_ok) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[7].body[1]` | SR 11828 | `current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)` | N2d만 | 죽음 (test_b26pre_growth_only_3b_left, test_b26pre_euler_fixup_group_split) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[11]` | SR 11877 | `current_rows, result = repair_matching_safety(current_rows, matching_p` | N2b/N2w/N2d | 죽음 (test_b26pre_growth_zero_rounds) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[12]` | SR 11879 | `_backfill_interdig_ok(result)` | N2b/N2w/N2d | 생존 -- 등가 아님, 결함 card로(U2-b) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[13]` | SR 11880 | `current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)` | N2w | 죽음 (test_b26pre_growth_zero_rounds_euler) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[14]` | SR 11881 | `return {'rows': current_rows, 'audit': result, 'ctx': cur_ctx, 'growth` | N2w | 죽음 (test_b26pre_growth_zero_rounds, test_b26pre_growth_zero_rounds_euler) |
| E7-seed | `_propose_L_roles` `stmt_delete` `body[7].body[2]` | SD 2176 | `seeds[ga] = gb` | N2d만 | 죽음 (test_b26pre_seed_tap_p) |
| E7-seed | `_propose_L_roles` `stmt_delete` `body[7].body[3]` | SD 2177 | `seeds[gb] = ga` | N2d만 | 죽음 (test_b26pre_seed_tap_n) |
| E7-seed | `_propose_gm_id_roles` `stmt_delete` `body[6].body[2]` | SD 2100 | `seeds[ga] = gb` | N2d만 | 죽음 (test_b26pre_seed_tap_p) |
| E7-seed | `_propose_gm_id_roles` `stmt_delete` `body[6].body[3]` | SD 2101 | `seeds[gb] = ga` | N2d만 | 죽음 (test_b26pre_seed_tap_n) |
| E7-seed | `propose_device_roles_gap_fill` `stmt_delete` `body[13].body[2]` | SD 3985 | `seed_net_pairs[ga] = gb` | N2d만 | 죽음 (test_b26pre_seed_tap_p) |
| E7-seed | `propose_device_roles_gap_fill` `stmt_delete` `body[13].body[3]` | SD 3986 | `seed_net_pairs[gb] = ga` | N2d만 | 죽음 (test_b26pre_seed_tap_n) |
| E7 | `propose_device_roles_gap_fill` `stmt_delete` `body[49]` | SD 4529 | `if disp.case_collisions:` | N2w | 죽음 (test_b26pre_case_collisions) |
| E7 | `propose_device_roles_gap_fill` `stmt_delete` `body[49].body[0]` | SD 4530 | `review_needed.append({'case_collisions': disp.case_collisions})` | N2d만 | 죽음 (test_b26pre_case_collisions) |
| E7 | `propose_vertical_stack_id_gap_fill` `cmp_flip` `body[2].body[1].test.ops[0]` | SD 3285 | `if relations is not None:` | N2d만 | 죽음 (test_b26pre_vsid_gap_fill_ports) |
| E7 | `propose_vertical_stack_id_gap_fill` `stmt_delete` `body[2]` | SD 3282 | `if inputs or outputs or feedbacks or biases or clocks:` | N2b/N2w/N2d | 죽음 (test_b26pre_vsid_gap_fill_ports) |
| E7 | `propose_vertical_stack_id_gap_fill` `stmt_delete` `body[2].body[1]` | SD 3285 | `if relations is not None:` | N2d만 | 죽음 (test_b26pre_vsid_gap_fill_ports) |
| E7 | `propose_vertical_stack_id_gap_fill` `stmt_delete` `body[2].body[1].body[0]` | SD 3286 | `edges.extend((rel['devices'] for rel in relations['differential']))` | N2d만 | 죽음 (test_b26pre_vsid_gap_fill_ports) |
| E7 | `run_full_circuit_audit` `stmt_delete` `body[16]` | SD 6892 | `for (kind, net), group in mc['current_mirror'].items():` | N2w | 죽음 (test_b26pre_full_audit_mirror_undisposed) |
| E7 | `run_full_circuit_audit` `stmt_delete` `body[17]` | SD 6894 | `for (kind, net), group in mc['diff_pair'].items():` | N2w | 죽음 (test_b26pre_full_audit_diffpair_undisposed) |

(b34 사본의 SD 줄은 B34 삭제 때문에 2100 → 2096처럼 앞으로 당겨진다. 표의 줄은 a796468 기준이다.)

**표 2 -- 같은 측정의 B26-1 자기 몫(20, 이 card 범위 밖 -- E1 = B26-1 계약 7(e), E3 = 계약 4 기본값, E4 = 계약 14)**

| 묶음 | 변이(head def·연산자·경로) | base 줄(a796468) | 문장(head) | 정의 | 시제품 판정(v1) |
|---|---|---|---|---|---|
| E4 | `_propose_L_roles` `stmt_delete` `body[2]` | SD 2165 | `if gm_id_roles is None:` | N2b/N2w/N2d | 생존 |
| E4 | `_propose_L_roles` `stmt_delete` `body[4]` | SD 2169 | `if candidates is None:` | N2b/N2w/N2d | 생존 |
| E4 | `_propose_gm_id_roles` `stmt_delete` `body[2]` | SD 2092 | `if candidates is None:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[40].body[12].test.ops[0]` | SD 4312 | `if y.source not in rails.nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[40].body[5].value.generators[0].ifs[0].values[0].ops[0]` | SD 4291 | `own_group_nets = {n for m in transistors if m.name != x.name and (devi` | N2w | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[40].body[5].value.generators[0].ifs[0].values[1].ops[0]` | SD 4291 | `own_group_nets = {n for m in transistors if m.name != x.name and (devi` | N2w | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[40].body[6].value.generators[0].ifs[0].values[1].ops[0]` | SD 4295 | `open_terminals = [n for n in (x.source, x.drain) if n not in rails.net` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[43].body[4].test.values[0].ops[0]` | SD 4359 | `if x.drain in rails.nets or x.drain in own_group_nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[43].body[4].test.values[1].ops[0]` | SD 4359 | `if x.drain in rails.nets or x.drain in own_group_nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[43].body[9].test.ops[0]` | SD 4381 | `if y.source in rails.nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `const+` `body[40].body[7].test.comparators[0]` | SD 4297 | `if len(open_terminals) != 1:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `const-` `body[40].body[8].value.slice` | SD 4299 | `open_net = open_terminals[0]` | N2w | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[36].body[1]` | SD 4160 | `if y is None or y.gate in rails.nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[40]` | SD 4281 | `for x in transistors:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[40].body[12]` | SD 4312 | `if y.source not in rails.nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[43]` | SD 4350 | `for x in transistors:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[43].body[4]` | SD 4359 | `if x.drain in rails.nets or x.drain in own_group_nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[43].body[9]` | SD 4381 | `if y.source in rails.nets:` | N2b/N2w/N2d | 생존 |
| E3 | `run_full_circuit_audit` `const+` `args.defaults[1]` | SD 6822 | `def run_full_circuit_audit(devices: dict, expected_counts: dict, dispo` | N2b/N2w/N2d | 생존 |
| E3 | `run_full_circuit_audit` `const-` `args.defaults[1]` | SD 6822 | `def run_full_circuit_audit(devices: dict, expected_counts: dict, dispo` | N2b/N2w/N2d | 생존 |

**생존 3문장의 판정**(독립 검토 `_drafts/review_b26pre.md` §6을 이 card 사본에서 다시 확인):
* **SR 11800·11879(`_backfill_interdig_ok` 사전 호출 삭제) -- 등가 아님.**
  * 구별 입력(합성): 한 행 `seg1`에 `Ma(src n2, drn n1, gate ga)`, `Mb(src n4, drn n2, gate gb)`, `Mp(src n2, drn n5, gate gp)`, 모두 nmos·`n_fingers=1`. 매칭 `[("Ma","Mb")]` offset, `gm_id_bounds=(11.9, 12.1)`.
  * 원본(a796468·b34 둘 다, `bf_repro.py`): `relaxed_pairs[0]["interdig_ok"] is False`, 같은 반환 `audit`의 `3b. interdigitation[Ma/Mb] [참고용 -- 이 kind는 필수 아님]`은 `True`, 반환 `rows`는 `{"seg1_seg0": [Mp], "seg1_seg1": [Mb, Ma]}`(max_rounds 1·2·3·5, metrics 있음·없음 모두).
  * 두 문장을 지우면 `interdig_ok`가 `True`(반환 audit과 같음)가 된다. 즉 **원본 쪽이 반환 audit과 어긋난 값**을 낸다.
  * 이 값을 '기존 동작'으로 고정하면 문서화된 의도(코드 주석 sizing_recipe.py 11784~11786 '반환되는 audit이 실제로 저장/보고될 최종 물리 구조와 항상 일치')와 어긋난 값을 정답으로 박는다. 그래서 이 card는 고정하지 않는다(U2-b).
* **SR 11802(성공 분기의 `_finalize` 삭제) -- 등가 후보.**
  * 증명 스케치(검토 §6): `result.ok`면 모든 행의 `1. euler[행]` 체크가 ok다. 그 판정이 `mirror_symmetric_trail`로 났다면 `check_walk_sequence`가 핑거 수 일치와 연속성을 확인한 완전한 walk가 있다는 뜻이고, 그러면 오일러 조건(연결·홀수 차수 ≤ 2)이 성립한다.
    따라서 정리 함수의 매칭쌍 없는 `build_stick_diagram(devs)[행].status`도 ok여서 정리는 입력을 그대로 돌려주고, audit은 같은 입력으로 다시 계산되며, backfill은 이미 같은 값으로 채워졌다. 남는 차이는 반환 객체의 동일성뿐이다(값 계약으로 관찰할 수 없다).
  * 실측(검토): 고정 battery 200건 + 무작위 400건(성공 분기 89건 포함) 차이 0.
  * 정의는 'N2d만'이다. B26-1 card 규칙(N2w)에서는 V3 대상이 아니다. N2d로 재는 경우에만 처리가 필요하다(U2-a).

## 결정 필요 항목

* **U1(원칙 기본안 -- 결정 아님)**: B26-1의 E6·E7 생존 변이는 면제하지 않고, 이 test-only card로 먼저 기존 동작 test를 더해 죽인다. 근거는 '의도'의 원칙 기본안이다.
  이 card는 `gate_change: no`라 머리 블록에 `approval` 줄이 필요 없다(`tools/gates/merge_gate.py`의 `gate_change_ok`는 `gate_change: yes`일 때만 card `approval`을 확인한다). 없는 기록 id를 적으면 판정 기록 로더 규칙 6이 거부하므로 적지 않는다.
  판정 기록 `approvals[]`에 무엇을 적을지는 오케스트레이터가 정한다. 비우지 않으려면 `20260930-b26-before-phase3`을 '맥락(B26-1 선행 준비)'으로만 적는다(그 기록의 범위 ③ 'B26-1을 Phase 2 중에'와 맞음, 'V3·V7 면제 일체'는 덮지 않음).
* **U2(이 card 밖의 처리 -- 이 card의 착수 조건이 아니다)**: 표 1의 생존 3문장.
  * (a) SR 11802 등가 면제 1건 -- B26-1 card의 A1-a 결정 몫(`target_kind: decision`, 변이 id@함수 해시). B26-1 V3를 N2w 규칙으로 재면 대상이 아니라 면제가 필요 없다. N2d로 재기로 하면 위 증명 스케치를 근거로 올린다.
  * (b) SR 11800·11879 -- **기존 결함으로 보이는 동작**이라 등가 면제 문구를 쓸 수 없다. red-green code card 초안 `_drafts/draft_b26_backfill_audit.spec.md`와 사용자 질문 `_drafts/b26_backfill_question.md`(권고 = 결함 수정 card를 B26-1 앞에)로 넘긴다.
    고치면 두 문장이 head에서 사라져 B26-1 V3 생존 대상이 없어진다. 고치지 않기로 하면 B26-1 V3에서 '알려진 결함 생존'으로 사용자 결정 기록이 필요하다.
* **U3(순서 -- 원칙 기본안, 결정 아님)**: **B34 병합 뒤, B26-1 병합 전**에 둔다.
  * 이 card는 B34와 독립이다. 시제품이 HEAD와 HEAD+B34에서 같은 결과를 내고, 대상 def가 B34의 4 def와 겹치지 않는다.
  * 그래도 B34 뒤에 둔다. 새 test(계약 7·10의 `load_topology`, 계약 5·6의 analog-grammar 경로)가 B34 def의 인벤토리를 늘려 B34 card의 인벤토리 수치('159·15·66·4 + k')를 낡게 만들기 때문이다.
  * B34가 늦어지면 B34 앞에 둘 수 있다. 그때는 B34 auditor가 인벤토리를 다시 재고(B34 card는 이미 '순서 3 뒤 재측정'을 적었다), 이 card 순서를 B34 card 착수 조건에 한 줄로 적는다.
  * backfill 결함 card(U2-b)를 고치기로 하면 그 card는 이 card와 독립이다(대상 문장이 겹치지 않고, 이 card의 test는 그 두 문장을 보지 않는다). 둘 다 B26-1 앞에 둔다.
  * 사용자 순서는 'P9 → P10 → P10b → V3 binding → V3 scope → B34 → **이 card**(→ backfill 결함 card, U2-b 결정 시) → B26-1'이 된다.
* **B26-1 card에 넣을 인계(오케스트레이터)**:
  * 착수 조건에 이 card 병합을 더한다.
  * 계약 12의 '넷리스트만 쓰는 직접 호출' 목록에 `test_b26pre_existing_paths.py`의 `resolve_stack_layout`(계약 5)·`propose_vertical_stack_id_gap_fill`(계약 6 두 호출)을 더한다. `rails`는 `rail_declaration({"supply_nets": ["vdd", "gnd"]})`다(`CAS`에 나오는 순서).
  * `run_matching_safety_with_finger_growth`·`optimize_full_circuit_budget`·`run_full_circuit_audit_from_topology`·`load_topology` 호출은 시그니처가 그대로이고 입력 topology가 `supply_nets`를 선언하므로 고치지 않는다(v2는 `_fixup_euler_blocked_rows`를 직접 부르지 않는다).
  * 'V3 계획'의 E6·E7 줄은 '선행 card로 base 32문장 중 29 죽임(변이 id 34 중 31), 남는 3 = U2'로 바꾼다. 문장별 대응은 `_drafts/b26pre_v2_kill_map.md`.
  * 표 2의 E1 15·E3 2·E4 3은 B26-1 자기 계약(7(e)·4·14) 몫으로 남는다. 이 측정의 E1(15)은 review2의 14와 다르다. 대상 정의(N2d)와 head 판(v4)이 달라서이고, B26-1 auditor가 B26-1 병합본에서 다시 잰다.

## 작성 전 실측

(재측정 HEAD = gate `master` `a796468`, 2026-10-01. 저장소는 읽기 전용, python `C:/Python314/python.exe -B`, scratch `C:/g106`(v2), 스크립트 `_drafts/b26pre_v2_scripts/`. v1 측정 scratch `C:/g87`은 지워졌다.)
1. **사실 문장 재측정**:
   * 표 1·2의 base 줄은 v4 head 문장 줄을 HEAD 사본과 difflib로 대응시켜 `b26pre_table.py`로 구했다(v1). v2는 `kill_v2.py`가 각 줄의 (def, 문장 글)을 HEAD 사본에서 다시 찾아 32줄 모두 확인했다.
   * 인용 줄(HEAD 사본 `sed -n`): sizing_recipe.py 9363~9367(bare repair 폴백 주석), 9400~9406(LUT 없는 분기), 9408~9412(정본 승격 주석), 6507~6509(`resolve_stack_layout` 3번), 11582~(정리 함수 docstring), 11769~11770(backfill 주석), 11784~11786(모든 반환 지점 주석);
     stick_diagram.py 928~930(`_scan_case_collisions`), 2686~(`find_structural_symmetry_candidates`), 2051~(`_propose_gm_id_roles`), 2114~(`_propose_L_roles`), 7532·7555~7557(`repair_matching_safety`), 6453~6461(`StickResult`), 6796~6806(`AuditCheck`·`AuditResult`).
   * LUT 없는 경로: `optimize_full_circuit_budget`의 `_lut_by_kind = spec.get("lut_by_kind")`. `_evaluate`의 `spec["lut_by_kind"][…]`는 `gm_id_role`이 있는 소자에서만 닿는다 -- 계약 1이 빈 역할 값을 쓰는 이유다(v1 실측: 역할 없이 두면 자동 채움이 `gm_id_role`·`L_role`을 채워 `KeyError: 'lut_by_kind'` 또는 L 유도 `ValueError`가 난다).
   * 계약 5 기준선 값(HEAD 사본): `refine_differential_and_mirror_relations(CAS)["vertical_stack_id_candidates"]["groups"]`에서 `M1`·`M2`·`M5`가 같은 후보 id, `resolve_stack_layout(CAS, [], {})`에서 `["M1","M2","M5"]` 한 그룹(kind 하나). `geometry_colocation_union(CAS, [])`는 소자마다 혼자다(변이 판정 설명용).
   * 시제품 17 test: HEAD 사본 17 passed(seed 0·1·7·123), HEAD+B34 사본 17 passed(같은 seed).
2. **이름 충돌**:
   * 새 파일 `test_b26pre_existing_paths.py`가 `A/tests/contracts/`에 없다.
   * `grep -rn "glob(" A/tests/`의 패턴(`*.topology.json`·`*.py` 전수 스캔)과 겹치지 않는다. 전수 스캔 test(GONE·이동 소비자·IC 표식·print)는 이 파일의 이름·문자열과 무관하다(삭제·이동 이름을 쓰지 않는다).
     독립 검토가 base 사본 contracts 전체에 같은 이름 파일을 넣고 돌려 607 passed·12 xfailed·2 failed(`.git` 필요 test 2개, archive 사본 한계)를 확인했다.
   * design 문서의 `-k` 필터(`"dup_"`, `"dup_w_calc or dup_kcl_edges"`)에 걸리지 않는다. `b26pre`는 `A/tests/`에서 0건이다.
3. **원칙의 계약화**: '정본은 topology 무관'은 계약 8(합성 입력, 선언 레일만)과 계약 10(합성 입력으로 등가 주장 반증)에 적었다. '작성자≠검증자'는 oracle 절과 계약 9(auditor 측정)에 적었다.
   '거짓 기준값 금지'는 oracle 절 (c) 항목과 U2-b(결함 의심 동작을 고정하지 않음)에 적었다. '만들면 배선'은 해당 없다(새 def 없음 -- 이 card는 운영 경로를 test로 고정할 뿐이다).
4. **쓰기 경로**: 새 test = gmid-test-author(`A/tests/**`, `tests/tools/**` 제외). spec card·interface card = 오케스트레이터. 계약 9 측정과 판정 기록 = auditor. 엔진·레지스트리는 바꾸지 않는다.
   test-author가 소스 없이 쓸 수 있게 결과 필드·반환 키 이름을 'test-author가 쓰는 이름' 절에 적었다.
5. **계획서 소비자**: 지우거나 옮기는 이름이 없다.
6. **미배선**: 새 def 없음.
7. **기존 계약 test**:
   * `grep -rln "run_matching_safety_with_finger_growth\|_fixup_euler_blocked_rows\|run_full_circuit_audit_from_topology\|resolve_stack_layout\|propose_vertical_stack_id_gap_fill\|case_collisions" A/tests/contracts` → 0건이다(selftest 3파일에만 있다).
   * 기존 test는 바꾸지 않는다. V5 없음.
