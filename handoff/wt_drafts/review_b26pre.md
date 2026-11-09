# 독립 검토 -- `draft_b26pre.spec.md`(20260930-b26-pre-test-strengthen, test-only)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용(HEAD = gate `master` `a796468`), scratch `C:/g99`만 사용(끝나고 삭제).
측정 사본: `C:/g99/base` = `git archive a796468`, `C:/g99/b34` = base + B34 코드 변경(사이트 1·2·3·11·11b를 같은 `def_replace` 규칙으로 직접 적용).
초안이 쓴 scratch `C:/g87`은 이미 없다(재현은 아래 내 스크립트로 다시 했다).

## 0. 결론 요약

* 시제품 15 test는 HEAD·HEAD+B34 모두 PASS(PYTHONHASHSEED 0·1·7·123), 표 1 34개 중 25개를 죽인다는 수치도 그대로 재현됐다(두 사본 결과가 같다).
* **등가 후보 9개 중 8개는 등가가 아니다.** 합성 입력으로 원본과 구별된다(씨앗 6개 전부, `_backfill_interdig_ok` 삭제 2개 전부). 등가로 볼 수 있는 것은 SR 11802(성공 분기 `_finalize` 삭제) 하나뿐이다.
* 그래서 U2 (a) 권고(9개를 A1-a 묶기 면제로 올림)는 그대로 쓸 수 없다. 씨앗 6개는 이 card에 계약을 하나 더해 죽이면 된다(base PASS 확인). backfill 2개는 base 동작 자체가 문서화된 의도와 어긋나 보여서 **사용자 결정 항목**이 된다.
* 승인 줄: 이 test-only card에는 결정 승인이 필요 없다(게이트 요구 없음, U1은 원칙 기본안). 없는 기록 id를 가리키는 `approval` 줄은 지운다.

## 1. 차단(blocking)

### B1. '등가 후보 9개' 중 8개가 구별 가능하다 -- 면제가 아니라 계약으로 처리해야 한다

변이별 판정은 §6 표에 있다. 요점은 다음과 같다.

* **씨앗 한 방향 삭제 6개(SD 2100·2101·2176·2177·3985·3986)**
  * 초안 근거: '한쪽 gate만 씨앗에 있어도 같은 쌍이 풀린다', library 9회로 18경우 같음.
  * 반례: 차동 입력 넷 하나에 **다른 소자가 더 물려 있으면** 남은 방향만으로는 후보가 둘 이상이 되어 보류된다. `find_structural_symmetry_candidates` 규칙 3에 따라 후보가 정확히 하나일 때만 채택하기 때문이다.
    빠진 방향 쪽에서만 유일하게 풀리는 쌍이 그대로 미해결로 남는다.
  * 합성 회로(`C:/g99/tools/seed_probe.py`): 공통 부분은 `M1(nmos, ntail→nd1, g ninp)`, `M2(nmos, ntail→nd2, g ninn)`, `M3/M4(pmos, vdd→nd1/nd2, g nbp)`, `M5(nmos, gnd→ntail, g nvb)`다.
    * `two_on_ninp`: 여기에 `Mx1(nmos, gnd→nx1, g ninp)`, `Mx2(nmos, gnd→nx2, g ninp)`, `My(nmos, gnd→ny, g ninn)`을 더한다.
    * `two_on_ninn`: 같은 회로에서 ninp와 ninn을 서로 바꾼다.
  * 결과(`load_topology` meta, 공개 경로):
    * 2100·2176은 `two_on_ninp`에서 `_device_roles_autofilled`가 달라진다. M1~M4·Mx1·My의 `gm_id_role` 또는 `L_role`이 사라진다.
    * 2101·2177은 `two_on_ninn`에서 같은 일이 생긴다.
    * 3985·3986은 각 회로에서 `_matching_pairs_needs_review`의 `Mx1/My`(source=structural_symmetry) 제안이 사라진다.
    * 탭 하나짜리 회로(`one_on_ninp`·`one_on_ninn`, `Mx` 하나)로도 2100·2101·2176·2177은 구별된다.
  * 원본 출력은 PYTHONHASHSEED 0·7·99와 기본값에서 바이트 단위로 같았고, HEAD+B34 사본에서도 같았다.
  * library 9회로만으로 등가를 주장한 것은 원칙 '해결책은 일반화 -- 합성 입력으로 측정'에 어긋난다. 초안 자신도 '모든 입력은 합성'이라고 적었다.
* **`_backfill_interdig_ok` 삭제 2개(SR 11800·11879)**
  * 초안 근거: 완화 쌍의 행은 interdigitate 배치라 euler 정리 대상이 아니다.
  * 반례: 완화 쌍이 **공유 source가 없어** `repair_matching_safety`가 손대지 못하면(`ta.source != tb.source` → 그대로 둠) 원래 행에 남는다. 그 행이 euler-blocked면 수리 audit의 3b는 "sequence 없음" → False이고,
    `_finalize`의 그룹 분할 뒤 audit의 3b는 True가 된다.
  * 입력(`C:/g99/tools/bf_probe.py`의 `nohub_blocked`):
    * 한 행 `seg1`에 `Ma(src n2, drn n1)`, `Mb(src n4, drn n2)`, `Mp(src n2, drn n5)`, 모두 `n_fingers=1`이다.
    * 매칭은 `[("Ma","Mb")]`, `offset`이다. `gm_id_bounds=(11.9, 12.1)`로 두면 핑거증가가 gm/ID 위반이 되어 완화로 간다.
  * 결과:
    * 원본: `relaxed_pairs[0]["interdig_ok"] is False`.
    * 11800 삭제(max_rounds 2·3·5)와 11879 삭제(max_rounds 1): `True`.
    * 무작위 퍼즈 400건(`fz_probe.py`, 고정 시드)에서도 11800이 1건에서 달라졌다.
  * **중요**: 원본이 돌려준 `audit`의 `3b. interdigitation[Ma/Mb]`는 같은 결과에서 **True**다. 즉 base는 `interdig_ok=False`와 최종 audit 3b=True를 함께 돌려준다.
    이는 `_finalize` 주석('반환되는 audit이 실제로 저장/보고될 최종 물리 구조와 항상 일치')과 backfill 주석('새로 계산된 audit_result의 3b 체크로 채운다')의 취지와 어긋나는 **잠재 결함**으로 보인다.
    변이 쪽이 오히려 일관된 값을 낸다.
* **고칠 것**
  1. 이 card에 계약 10을 더해 씨앗 6개를 죽인다. 초안 문장은 §5에 있다. 시제품 판정 결과는 6/6 죽음, base PASS다.
  2. backfill 2개는 등가 면제로 올리지 않는다. B2의 결정으로 넘긴다.
  3. '등가 후보 9개의 근거'와 U2는 SR 11802 1개로 줄인다. 근거는 B3의 증명 스케치로 바꾼다.

### B2. backfill 2개는 base 동작 고정(oracle (c))으로 죽이면 결함을 굳힌다 -- 사용자 결정 항목

* test-only card는 base에서 PASS하는 test만 넣을 수 있다. 그래서 이 card로 11800·11879를 죽이려면 '`interdig_ok`가 False'를 고정해야 한다.
  그러면 위 불일치를 정답으로 박게 된다(원칙 '거짓 기준값 금지').
* 선택지(사용자 결정)
  * (권고) **red-green code card를 B26-1 앞에 둔다**. test는 '`relaxed_pairs[i]["interdig_ok"]`는 반환 `audit`의 `3b.…[a/b]` 체크의 `ok`와 같다'이고, 위 입력에서 base FAIL이다.
    수정은 `interdig_ok`를 최종 audit으로 채우는 것이다. 예를 들어 루프 안·루프 뒤의 사전 backfill을 지우고 `_finalize` 것만 남긴다. 그러면 두 문장이 사라져 B26-1 V3에 생존 대상이 없다.
  * 기존 동작을 고정한다(권고하지 않음 -- 결함 고정).
  * 백로그로 두고 B26-1 V3에서 '알려진 결함 생존'으로 면제한다. 등가가 아니므로 A1-a '등가' 문구로는 쓸 수 없다. 사용자 결정 기록이 필요하다.
* 이 결정은 엔진 동작을 바꾸므로 사용자 몫이다(메모리 원칙: 공유 엔진코드는 승인 후).

## 2. 고칠 것(should-fix)

### S1. 계약 2가 비공개 함수 `_fixup_euler_blocked_rows`를 직접 부른다

* 이 card의 원칙(공개 진입점), 계약 8('엔진 비공개 도우미는 쓰지 않는다'), Phase 3 모듈 분할 때 이동·개명 위험과 충돌한다.
* 공개 경로로 같은 변이를 죽일 수 있다(실측, `C:/g99/proto2/test_b26pre_v3.py`).
  * 호출: `run_matching_safety_with_finger_growth({"row": STAR}, [], {}, ctx(["M1","M2","M3"]), {"nmos": toy_lut}, {}, [], gm_id_bounds=(11.9, 12.1))`.
  * 기대: 행 키 `{"row_seg0","row_seg1"}`, 소자 이름 합집합 `["M1","M2","M3"]`(겹침 없음, 빈 행 없음), 각 소자 `stack_id == 행 키`이고 `n_fingers == 1`.
  * 근거: 좁은 gm/ID 범위에서 핑거증가 후보가 거부되면 docstring '2순위' 그룹 분할로 간다.
  * base에서 PASS(seed 0·1·7), SR 11696·11698·11700이 모두 죽는다.
* 참고: 계약 3(b)는 넓은 범위 `(2.0, 28.0)`에서 STAR를 **핑거증가**(M1 → 2핑거, 행 이름 `row` 유지)로 푼다. 그래서 3(b)로는 그룹 분할이 고정되지 않는다(실측).

### S2. oracle 분류 -- '작성 시 base에서 잰 값'은 계획 N3.12.3이 금지한 '현재 출력 붙여넣기'로 읽힌다

* 계획 688행: "피검 함수 호출이나 피검 식 복사, **현재 출력 붙여넣기로 기대값을 만들지 않는다**. 기준선이 존재하고 동작 보존 변경이면 (c)".
* 계약 1·3·5·7을 (c)로 두려면 다음처럼 적어야 한다. 기준선은 gate `master` `a796468`(B26-1 이전, B26-1이 이 경로에서 동작 보존이라는 전제의 known-good)이다.
  auditor는 그 기준선을 독립으로 다시 잰다(`checks.V4.basis`의 `oracle 대조:`).
* 'docstring과 맞는다'는 근거는 값이 실제로 docstring에 있는 항목에만 쓴다. `unresolved_reason` 리터럴, `_repair<i>`, `_seg<i>`처럼 코드에만 있는 값은 (c) 기준선 값이라고 적는다.
* B2가 보이듯 (c) 고정은 결함을 굳힐 수 있다. 그래서 각 (c) 항목에는 '문서화된 의도와 모순 없음'을 확인했다는 줄을 둔다. 초안은 대부분 그렇게 했지만 계약 5는 아니다(아래).
* 계약 5 근거 정정
  * 초안은 '`propose_vertical_stack_id_gap_fill` docstring 2번'을 인용한다. 이 함수는 계약 5의 경로가 아니다.
  * `resolve_stack_layout` 3번 경로는 `refine_differential_and_mirror_relations(transistors)["vertical_stack_id_candidates"]`를 `derive_horizontal_stack_groups`(kind 분리 + 선언 매칭쌍 병합, 여기서는 `[]`)로 넘긴다.
  * 그래서 'M1·M2가 한 그룹'은 candidates가 공통 tail 컬럼으로 묶은 결과다. 이 함수의 docstring을 인용하고 (c) 기준선이라고 적는다.
  * '마지막 폴백은 소자마다 혼자'는 피검 내부 동작이라 계약 근거에서 뺀다. 변이 판정(계약 9)에만 쓰인다.

### S3. 계약 4의 test 수와 시제품이 다르다

* card는 '세 경우를 각각 별개 test'(전부 처분, mirror 누락, diff_pair 누락)라 적었다. 시제품에는 `test_b26pre_full_audit_hub_undisposed`(hub_merge gnd 누락)가 더 있다.
* card 문장대로 쓰면 14 test이고, '시제품 = 계약 문장 그대로 쓴 15 test'(재현할 수치)와 어긋난다.
* hub 경우는 구성 oracle (a)이고 base PASS다. 계약 4에 넣거나 수치를 14로 고친다.

### S4. test-author가 소스 없이 쓸 수 있게 필드 이름을 card에 적는다

* interface card 도구 출력은 심볼 표뿐이다(md_sync 검토 S4 선례). card에 다음을 명시한다.
  * `AuditResult.checks`·`.ok`, `AuditCheck.name`·`.ok`·`.detail`, `StickResult.status`
  * `pipeline_result` 키 `repaired_rows`·`repaired_audit`·`transistors`, `optimize_full_circuit_budget` 반환 키 `pipeline_result`·`audit_ok`
  * `propose_vertical_stack_id_gap_fill` 반환 키 `proposals`·`conflicts`·`components_used`
  * meta 키 `_device_roles_gap_fill_review_needed`(None일 수 있음 → 빈 목록으로 본다)
* 계약 3의 `EULER_OK`가 쓰는 `build_stick_diagram`도 '입력/판정에 쓰는 기존 공개 심볼' 목록에 넣는다.

### S5. 승인 줄(검토 항목 4)

* 게이트: `merge_gate.py` 721~738행은 `gate_change: yes`일 때만 card `approval`을 확인한다. 이 card는 `gate_change: no`라 필수가 아니다.
  반면 auditor가 card 줄을 판정 기록 `approvals[]`로 옮기면, 로더 규칙 6(`rule6_dates_approvals`)이 '승인 기록 파일이 없다'로 거부한다.
  **없는 id(`20261001-b26-pre-test-strengthen`)를 단 채로 커밋하면 안 된다.**
* 선례
  * P10(test-only)은 덮는 design 승인 `20260923-20-dead-code-dup-design`을 적었다.
  * md_sync(test-only)는 덮는 design 승인이 없었다. 검토가 이미 받은 사용자 답을 decision 기록으로 옮기라고 권했다(새 질문 없이).
  * ts 계열 3 card는 줄 없이 판정 기록에 design 10 승인을 적었다.
* 이 card
  * U1('면제하지 않고 test 먼저')은 원칙 기본안이다. 원칙은 '우회/skip은 타당성 검토 후에만'과 '결정은 원칙으로 기본안부터'이고, A1-a 면제를 죽일 수 있는 변이에 쓰지 않는 것은 이미 정한 규칙의 적용이다. 사용자 결정 몫이 아니다.
  * 순서(B34 뒤·B26-1 앞)는 B26-1의 착수 조건을 하나 더하는 것이다. 승인 `20260930-b26-before-phase3` ③의 범위(B26-1을 Phase 2 중에) 안에서의 작업 순서라 보고 한 줄로 충분하다.
  * 그 기록은 'V3·V7 면제 일체'를 덮지 않는다고 명시했다. 남는 사용자 결정(B2 backfill 처리, SR 11802 등가 면제)은 이 card가 아니라 B26-1 card·결함 card의 승인 기록 몫이다.
* **고칠 것**: 머리의 `approval` 줄을 지운다. U1을 '결정 필요 항목'에서 '원칙 기본안(근거)'으로 옮긴다.
  판정 기록 `approvals[]`에 무엇을 적을지는 오케스트레이터가 정한다. 관례상 비우지 않으려면 `20260930-b26-before-phase3`을 '맥락(B26-1 선행 준비)'으로만 적는다. 그 기록의 범위 문장과 맞는지 확인한 뒤에 한다.
  U2는 B1·B2 반영 뒤 '11802 등가 면제 1건(B26-1 card의 A1-a 결정)'과 'backfill 결함 처리(B2)' 두 줄로 바뀐다.

## 3. 사소(minor)

* M1. 근거 경로 `C:/g87`은 지워졌고, 스크립트(`b26pre_proto_run.py`·`b26pre_kill.py`·`seed_equiv.py`)가 그 경로를 하드코딩한다. 재현 절차를 '사본을 다시 만드는 명령'으로 적는다. 이 검토는 `C:/g99`에서 다시 만들어 같은 수치를 얻었다.
* M2. 표 1의 34행 중 SR 9404·9406은 중첩 def와 바깥 def에 두 번씩 나온다. base 문장 기준으로는 32개(죽음 23, 생존 9)다. 계약 9의 auditor 측정 단위를 '변이 id' 또는 'base 문장' 중 하나로 정해 적는다.
* M3. `EULER_OK`가 피검 모듈의 `build_stick_diagram`으로 판정한다. 이 card 변이(SR 쪽)에는 영향이 없지만, 판정기 독립성 한계로 oracle 절에 한 줄 적는다. 대안은 반환 audit의 `1. euler[` 체크만 보는 것이다.
* M4. 계약 7: `meta["_device_roles_gap_fill_review_needed"]`가 `None`이면 빈 목록으로 본다는 문장을 더한다. 시제품은 `or []`를 쓴다.

## 4. 재측정 결과(검토 항목 2·5)

* 사본: `C:/g99/base`(a796468 archive), `C:/g99/b34`(base + B34 사이트 1·2·3·11·11b). 시제품 파일은 그대로 `tests/contracts/test_b26pre_proto.py`로 넣었다.
* 기준 PASS: 두 사본 × PYTHONHASHSEED 0·1·7·123 = 8회 모두 `15 passed`.
* 변이(`C:/g99/tools/kill.py`):
  * base 줄 32개 문장(stmt_delete 31 + SD 3285 cmp_flip)을 `pass`로 바꾸거나 비교를 뒤집어, 시제품 파일만 실행했다(PYTHONHASHSEED=1).
  * HEAD: 죽음 23, 생존 9(SD 2100·2101·2176·2177·3985·3986, SR 11800·11802·11879). HEAD+B34(줄을 문장 글로 대응): 결과가 **완전히 같다**.
  * 변이 id 기준 34로 환산하면 25 죽음·9 생존으로 초안과 같다. 죽인 test 이름도 초안 표와 같다.
* 전체 contracts 디렉터리에 새 파일(`test_b26pre_existing_paths.py` 이름)을 넣고 실행했다(base 사본): 607 passed, 12 xfailed, 2 failed.
  2 failed는 `test_ts6_probe_relocate`의 `.git` 필요 test 2개다(archive 사본의 한계, 초안 인벤토리 주석과 같다). 전수 스캔 test(GONE·이동·IC 표식)와 충돌이 없다.
* 이름: `b26pre`는 저장소 `*.py`에 0건이다. 새 파일 이름이 `glob("*.py")` 스캔 대상이 되지만 위 실행에서 문제가 없었다.
  `==`는 `Transistor`(dataclass)·dict·list·tuple·set·str에만 쓰였고, `AuditResult` 객체 비교는 없다.

## 5. 더할 계약 초안 -- 씨앗 6개(B1의 고칠 것 1)

**10. 구조 대칭 씨앗의 양방향(E7, `load_topology` → `_propose_gm_id_roles`·`_propose_L_roles`·`propose_device_roles_gap_fill`)**

* 공통 netlist(계약 8 형식): `M1(nmos, ntail→nd1, gate ninp)`, `M2(nmos, ntail→nd2, gate ninn)`, `M3(pmos, vdd→nd1, gate nbp)`, `M4(pmos, vdd→nd2, gate nbp)`, `M5(nmos, gnd→ntail, gate nvb)`.
* (a) `TAP_P`: 공통 + `Mx1(nmos, gnd→nx1, gate ninp)`, `Mx2(nmos, gnd→nx2, gate ninp)`, `My(nmos, gnd→ny, gate ninn)`.
* (b) `TAP_N`: 공통 + `Mx1(…, gate ninn)`, `Mx2(…, gate ninn)`, `My(…, gate ninp)`(입력 넷만 바꿈).
* 각 경우 `_t, meta = load_topology(<경로>)`이면 다음이 성립한다.
  * `meta["_device_roles_autofilled"]["Mx1"]`과 `["My"]`의 `gm_id_role == "matching"`이고 `L_role == "mirror"`다.
  * `meta["_device_roles_autofilled"].get("Mx2", {})`에는 `gm_id_role`·`L_role` 키가 없다.
  * `meta["_matching_pairs_needs_review"]` 원소 중 `sorted(names) == ["Mx1","My"]`인 것이 있다.
* oracle (a), 구성 + `find_structural_symmetry_candidates` docstring 규칙(유일 후보만 채택, 알려진 단자가 많은 소자부터·동점은 이름순)
  * 씨앗 `ninp↔ninn`, `vdd`·`gnd` 자기 자신.
  * 1라운드: `Mx1`(알려진 단자 source·gate 2개)의 기대 파트너 = nmos, source gnd, gate(반대 입력)이고, 후보는 `My` 하나 → 채택. `Mx2`는 후보가 이미 소비되어 없음 → 미해결.
  * `_propose_gm_id_roles`: 자기 아닌 파트너 → `matching`. `_propose_L_roles`: → `mirror`. 구조 대칭 출처 매칭쌍 제안은 `Mx1/My`다.
* 두 경우를 별개 test 함수로 둔다. 씨앗의 어느 방향이 빠지는지는 후보 소자 순서에 달렸으므로 두 방향 모두 필요하다.
* 실측(이 검토, `C:/g99/out/seed_mut.txt`): 원본 두 경우 모두 위 세 판정 참이다. 2100·2176은 (a)에서, 2101·2177은 (b)에서, 3985는 (a)에서, 3986은 (b)에서 거짓이 된다. 6/6이 죽는다.
* B26-1 뒤: 씨앗 `{net: net for net in rails.nets}`는 `supply_nets: ["vdd","gnd"]` 선언과 같은 집합이라 판정이 바뀌지 않는다.

## 6. 변이별 등가 판정표

| 변이(base 줄) | 문장 | 초안 | 이 검토 판정 | 구별 입력 / 근거 | 관찰점 |
|---|---|---|---|---|---|
| SD 2100 `_propose_gm_id_roles` | `seeds[ga] = gb` | 등가 후보 | **등가 아님** | `two_on_ninp`(`one_on_ninp`로도 됨) | `_device_roles_autofilled` M1~M4·Mx1·My `gm_id_role` 소실 |
| SD 2101 같은 함수 | `seeds[gb] = ga` | 등가 후보 | **등가 아님** | `two_on_ninn`(`one_on_ninn`) | 같음 |
| SD 2176 `_propose_L_roles` | `seeds[ga] = gb` | 등가 후보 | **등가 아님** | `two_on_ninp`(`one_on_ninp`) | `L_role` 소실, `_device_roles_gap_fill_review_needed` 변화 |
| SD 2177 같은 함수 | `seeds[gb] = ga` | 등가 후보 | **등가 아님** | `two_on_ninn`(`one_on_ninn`) | 같음 |
| SD 3985 `propose_device_roles_gap_fill` | `seed_net_pairs[ga] = gb` | 등가 후보 | **등가 아님** | `two_on_ninp` | `_matching_pairs_needs_review`의 `Mx1/My` 제안 소실 |
| SD 3986 같은 함수 | `seed_net_pairs[gb] = ga` | 등가 후보 | **등가 아님** | `two_on_ninn` | 같음 |
| SR 11800 루프 안 backfill | `_backfill_interdig_ok(result)` | 등가 후보 | **등가 아님**(base 쪽이 불일치 출력) | `nohub_blocked`, offset, `gm_id_bounds=(11.9,12.1)`, max_rounds 2·3·5. 무작위 퍼즈 400건 중 1건 | `relaxed_pairs[0].interdig_ok`: 원본 False / 변이 True(반환 audit 3b는 True) |
| SR 11879 루프 뒤 backfill | `_backfill_interdig_ok(result)` | 등가 후보 | **등가 아님**(같음) | 같은 입력, max_rounds=1 | 같음 |
| SR 11802 성공 분기 `_finalize` | `current_rows, cur_ctx, result = _finalize(...)` | 등가 후보 | **등가**(근거 보강) | 구별 입력 없음. 고정 battery 200건 + 무작위 400건(성공 분기 89건 포함) 차이 0 | 증명 스케치: `result.ok` ⇒ 모든 행 `1. euler[행]` ok. 그 판정이 `mirror_symmetric_trail`로 났다면 `check_walk_sequence`가 핑거 수 일치와 연속성을 확인한 완전한 walk가 있다는 뜻이고, 그러면 오일러 조건(연결·홀수차수 ≤2)이 성립한다. 따라서 정리 함수의 매칭쌍 없는 `build_stick_diagram(devs)[행].status`도 ok여서 입력을 그대로 돌려주고, audit은 같은 입력으로 재계산되며, backfill은 이미 같은 값으로 채워졌다. 남는 차이는 객체 동일성뿐이다(값 계약으로 관찰 불가) |

## 7. 측정 파일(scratch, 검토 뒤 삭제)

`C:/g99/tools/{mk_b34.py, kill.py, seed_probe.py, seed_mut.py, bf_probe.py, fz_probe.py, sr_mut.py}`, `C:/g99/out/*`.
핵심 수치는 이 문서 §4·§6에 옮겼다. 다시 재려면 이 문서의 입력 정의(§1 B1, §5)로 재구성한다.
