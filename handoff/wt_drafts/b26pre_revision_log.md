# b26pre spec card 개정 기록

## v1 → v2 (2026-10-01)

대상: `_drafts/draft_b26pre.spec.md`(id `20260930-b26-pre-test-strengthen`). 개정 전 사본 `_drafts/draft_b26pre.spec.v1.md`. 입력 검토 `_drafts/review_b26pre.md`(독립 검토).
새 파일: `_drafts/draft_b26_backfill_audit.spec.md`(red-green card 초안), `_drafts/b26_backfill_question.md`(사용자 질문 U-BF), `_drafts/b26pre_v2_kill_map.md`(B26-1 Q1 생존 대응), `_drafts/b26pre_v2_scripts/`(측정 스크립트·시제품).
측정: gate `master` `a796468`(HEAD). 저장소 쓰기·상태 변경 git 없음(`git archive`만). scratch `C:/g106`(base = archive, b34 = base + B34 사이트 1·2·3·11·11b -- 검토의 B34 패치가 `def_replace` 규칙으로 재현됨), 측정 뒤 삭제.

| 지적 | 처리 |
|---|---|
| B1 등가 후보 9개 중 8개 구별 가능 | 계약 10(구조 대칭 씨앗 양방향, `TAP_P`·`TAP_N` 두 test) 추가 -- 검토 §5 문장. 재실측: base·b34 둘 다 씨앗 6문장 6/6 죽음, 기준 PASS. 씨앗 6개·backfill 2개를 '등가' 주장에서 뺐다. 등가 후보는 SR 11802 하나(검토 §6 증명 스케치를 '생존 3문장의 판정'에 옮김). '원칙 -- 정본은 topology 무관'에 '등가 주장은 합성 입력으로 먼저 잰다' 한 줄 |
| B2 backfill 결함 고정 금지 | 이 card에서 SR 11800·11879를 고정하지 않음('의도' 원칙 기본안 마지막 항목, oracle 절). red-green card 초안(계약: 반환 `interdig_ok` = 반환 audit 3b, 루프 안·뒤 두 경로)과 사용자 질문(권고 = 고침) 작성. 주석 원문 인용 sizing_recipe.py:11784~11786, 11769~11770. 사전 측정: base red 2 failed, 수정 후보(두 줄 삭제) green 2 passed, `A/tests` 전체 회귀 없음 |
| S1 계약 2 비공개 함수 | 공개 `run_matching_safety_with_finger_growth(..., gm_id_bounds=(11.9, 12.1))`로 교체, 기대에 `n_fingers == 1` 추가. 재실측: SR 11696·11698·11700 죽음(+11828도 이 test가 죽임). 계약 8에 `_fixup_euler_blocked_rows`를 비공개 예시로 명시. B26-1 인계 문장에서 그 호출 제거 |
| S2 oracle (c) 분류·계약 5 인용 | oracle 절: (c) = 기준선 a796468(B26-1 동작 보존 전제), auditor 독립 재측정, '현재 출력 붙여넣기 아님'. docstring에 값이 없는 항목을 '(c) 기준선 값'으로 따로 나열. 계약 1·2·3·7 근거를 파일:줄 인용으로. 계약 5: `propose_vertical_stack_id_gap_fill` 인용 삭제 → `resolve_stack_layout` docstring 3번·`derive_horizontal_stack_groups` 문단과 `refine_…` docstring의 `vertical_stack_id_candidates` 서술, 'M1·M2 한 그룹'은 (c) 기준선 값. 실측: 후보 그룹 `M1·M2·M5` 한 그룹 |
| S3 계약 4 test 수 | hub(`("hub_merge","nmos","gnd")` 누락) 경우를 계약 4에 넣어 4 test. 총 17 = 1+1+5+4+1+2+1+2 |
| S4 필드 이름 | 'test-author가 쓰는 이름' 절 신설(진입점·결과 필드·반환 키·meta 키·체크 접두사). 시그니처는 HEAD에서 다시 읽음(`propose_vertical_stack_id_gap_fill` 포트 인자는 키워드 전용이 아니라 기본값 매개변수 -- 키워드로 준다고 적음). `build_stick_diagram`을 공통 입력 공개 심볼 목록에 추가 |
| S5 승인 줄 | 머리 `approval` 줄 삭제. U1을 '원칙 기본안(결정 아님)'으로. `merge_gate.gate_change_ok` 확인(gate_change yes일 때만 approval 확인). `approvals[]`는 오케스트레이터 몫, 맥락으로 `20260930-b26-before-phase3` |
| M1 scratch 경로 | '재현할 수치'에 사본을 다시 만드는 명령 4단계(`mk_g106.py`·`run_proto.py`·`kill_v2.py`) |
| M2 측정 단위 | 계약 9: base 문장(32 = stmt_delete 31 + cmp_flip 1)으로 정함, 변이 id(34)는 참고 |
| M3 `EULER_OK` 독립성 | oracle 절에 한 줄 |
| M4 `None` 처리 | 계약 7에 '`None`이면 빈 목록' |

재측정 수치(v2 시제품 17 test):
* 기준: base·b34 × PYTHONHASHSEED 0·1·7·123 = 8회 모두 17 passed.
* 변이 32문장: 두 사본 모두 죽음 29, 생존 3(SR 11800·11802·11879), 문장별·죽인 test 이름까지 같음. 변이 id 환산 31/34.
* backfill 수정 후보: `A/tests` 전체(seed 1) 888 passed·15 xfailed·2 failed(`test_ts6_probe_relocate` `.git` 필요 2개, archive 사본 한계) / base 886 passed·15 xfailed·4 failed(같은 2개 + red 시제품 2개).

새로 드러난 것:
* 씨앗 6개와 SR 11802는 'N2d만' 문장이라 B26-1 card 규칙(N2w)의 V3 대상이 아니다. 그래서 U2-a(11802 등가 면제)는 B26-1 V3를 N2d로 잴 때만 필요하다(`b26pre_v2_kill_map.md` §3).
* B26-1 Q1의 N2w 생존 24개 중 16개를 이 card가 죽인다. 남는 8 = backfill 2(U-BF) + trace 범위 2(이 card 범위 밖) + 등가 4.

측정 중 gate `master`가 `0f23786`으로 움직였다(`d6a9778`·`0f23786`, `.ai/approvals/20261001-p10b-v3-equiv.md`와 P10b spec card만 -- 엔진·test 변경 없음, `git diff --stat a796468 0f23786`). 위 수치는 그대로 유효하다.

남은 것(오케스트레이터·사용자): U-BF 질문(`b26_backfill_question.md`), 결함 card 승인 뒤 머리 `approval` 줄, B26-1 Q1 문안 축소(대조 중인 agent 몫 -- `b26pre_v2_kill_map.md` §2).

## v2 → v3 (2026-10-01, 독립 2차 검토 반영)

입력 검토: `_drafts/review2_b26pre.md`(조건부 통과, B 0·S 4·minor 6). 개정 전 사본: `draft_b26pre.spec.v2.md`, `draft_b26_backfill_audit.spec.v2.md`, `b26_backfill_question.v2.md`, `b26pre_v2_kill_map.v2.md`.
측정: gate `master` `0f23786`(HEAD·master 같음, `skills`는 a796468과 같음). 저장소 쓰기·상태 변경 git 없음(`git archive`만). scratch `C:/g116`(측정 뒤 삭제).

| 지적 | 처리 |
|---|---|
| S1 backfill card oracle '(b) 문서화된 의도'는 4종에 없음 | 계약 1 oracle을 **(d) 사용자 결정**(U-BF 승인 기록 id 후보 `20261001-b26-backfill-interdig-fix`)으로, 입력은 (a) 구성(넷 차수로 euler-blocked, 좁은 gm/ID 범위로 완화). 관계 단언이 V4 (1)이 아닌 이유 한 줄(결정된 계약이 같은 반환 안 두 필드의 일치 자체). 두 코드 주석은 결정의 근거로만 인용. 검토의 선택안(구성 쪽 독립 단언)은 rows 모양 고정 때문에 넣지 않는다고 적음. U-BF 항목에 '기록 커밋 전 test-author에 넘기지 않음' |
| S2 backfill 계약에서 피검 함수가 interface card에 안 잡힘 | 계약 절 머리와 계약 1 제목에 `sizing_recipe.run_matching_safety_with_finger_growth`를 단독 백틱으로. gate 캐시 `interface_card.py`(`.git/gmid-gate-cache/0f237862c007f6a53122f2bdfb3c87e6366ec133/`)를 `C:/g116/ic`의 card 사본에 `--root C:/g116/base`로 실행: **4개** 추출(`sizing_recipe.run_matching_safety_with_finger_growth`, `sizing_recipe.size_transistor`, `sizing_recipe.GmIdLUT.gm_gds_ratio`, `sizing_recipe.SemiEmpiricalGmIdLUT.gm_gds_ratio`) -- v2는 1개 |
| S3 'test-author가 쓰는 이름'이 입력 절 밖 | 두 card 모두 '관찰 가능한 계약' 절 끝 '이름(입력·판정용)' 항목으로 옮김(b26pre는 `##` 절 → 굵은 항목, backfill은 '작성 전 실측' 끝 문단 → 계약 절 끝 목록). 내용은 그대로, interface card 범위 설명 문장만 고침 |
| S4 b26pre '의도'가 N2d만 변이까지 B26-1 V3 대상이라 말함 | 10행을 '일부 문장이 N2w 대상'으로 고치고 'N2w 18(Q1 E6 13·E7 5) / N2d만 16' 구분, 죽인 수 두 수치(N2w 16/18, N2d만 15/16) 따로 적기. B26-1 인계에도 같은 구분 한 줄 |
| m1 b26pre interface card에 비공개 심볼 4개 | 계약 절의 비공개 이름(_fixup_euler_blocked_rows·_scan_case_collisions·_propose_gm_id_roles·_propose_L_roles·_dc_replace) 백틱 제거 + '비공개, 호출 금지'. 재추출: **18개, 밑줄 시작 0개** |
| m2 계약 10 `Mx1` 단언이 '동점이면 이름순'(SD 2760 주석)에 기댐 | 단언을 'My는 matching/mirror, Mx1·Mx2 중 정확히 하나(X)가 matching/mirror, 나머지(Z)는 키 없음, 매칭쌍 제안에 sorted([X,My]) 있고 sorted([Z,My]) 없음'으로. 측정(`C:/g116/seedweak.py`, `0f23786` 사본): base 4 passed(v2·v3 단언 각 2), 씨앗 6문장 삭제 변이 각각 v2·v3 단언이 같은 방향 test를 죽임(6/6), 동점 순서 역전 변이(SD 2761 `item[0].name` → 이름 역순)에서 v2 단언 2 failed·v3 단언 2 passed. 손 추적 문장(My의 기대 파트너가 둘이라 보류) 추가 |
| m3 기준선 커밋 표기, 계약 3(e) 리터럴 | oracle 절 기준선 = '착수 시 gate master(지금 0f23786, 엔진 a796468과 같음, 다르면 auditor 재측정)'. 계약 5 '(c) 기준선 값(a796468)' → 'oracle 절'. 작성 전 실측 머리에 gate 이동 한 줄. (c) 목록 옆에 계약 3(e) `"only_3b_failures_left"` 고정의 V5 비용 한 줄(주석 11823~11826 인용, `0f23786` 사본에서 확인) |
| m4 질문 문안 | 11784~11786과 11769~11770 원문을 둘 다 인용, '두 주석을 합친 해석' 명시, offset 쌍 3b는 참고용 체크라 `audit.ok`는 3c로 계속 False(바뀌는 것은 `interdig_ok`뿐), gate 표기 `0f23786`(엔진 a796468과 같음). 검토 §8 계측(기존 suite 완화 1회·불일치 0회) 한 줄. 선택지 1에 'oracle (d)', 순서, B26-1 재측정 한 줄 |
| m5 순서·인계 | backfill card: 순서 'B34 → b26pre → 이 card → B26-1'(B34는 전이), B26-1 인계 '이 card 병합본에서 모의 head·V3 대상 수·Q1 재측정(E6 finger growth 6 → 4, AST 순번 당겨짐)'. b26pre B26-1 인계와 kill map §3에도 같은 줄 |
| m6 backfill fix의 B34 위 전체 회귀 미측정 | backfill card '재현할 수치'에 auditor 몫으로(착수 base = B34 병합본, 미병합이면 HEAD+B34 사본에서도). 판정 유형 근거 V2 줄에 'B34 없는 사본에서만' |

재검사(`C:/g116/run_ic.py`, gate 캐시 `role_paths.parse_spec_card`·`interface_card.py`, card 사본):
* b26pre `20260930-b26-pre-test-strengthen`: parse 통과(`phase 2`, `test-only`, `gate_change no`, `approval []`), interface card 18개(비공개 0).
* backfill `20261001-b26-backfill-interdig-final-audit`: parse 통과(`phase 2`, `red-green`, `gate_change no`, `approval []`), interface card 4개(피검 함수 포함).

남은 것(오케스트레이터·사용자): U-BF 질문(`b26_backfill_question.md`), 승인 기록 커밋 뒤 backfill card 머리 `approval` 줄, B26-1 card 인계 반영(Q1 문안 축소는 대조 중인 agent 몫), 범위 정책 card 병합 뒤 'N2d만' 판정 재확인(검토 §4 조건 1).

## v3 → v4 (2026-10-01, 통합 질문 정렬 -- `_drafts/b26_reconcile_edits.md` A1~A7)

대상: `_drafts/draft_b26pre.spec.md`. 개정 전 사본: `_drafts/draft_b26pre.spec.v3.md`(review2 반영판 -- 그 수정은 전부 유지).
입력: `_drafts/b26_reconcile_edits.md` A절, 통합 질문 `_drafts/b26_survivor_final_question.md`, 통합 측정 `_drafts/b26_reconcile/out/`, 사용자 결정 U-BF "결함으로 고침 (Recommended)"(`_drafts/user_decisions.md`).
측정: scratch `C:/g127`(a796468 archive = base, base + B34 코드 변경 = b34 -- `mk_g106.py`와 같은 치환), 측정 뒤 삭제. 저장소 쓰기·상태 변경 git 없음(`git -C … archive`만). gate 도구는 gate 캐시 경로 대신 `git archive 0f23786 tools/gates`(같은 판 -- 저장소 내부 경로 인자는 role_guard EL1이 막음).

| 편집 | 처리 |
|---|---|
| A1 범위를 승인 규칙으로 | '의도' 범위 문단을 N2w(범위 정책 card N2(b) + 넓힌 T6, 분류기 `v3_scope_widen.py`)로. 표 1을 **주표**(N2w 20 = E6·E7 18 + trace 2, 이 card 18 죽임, backfill 2는 결함 card)와 **참고표**(N2d만 16, B26-1 V3 대상 아님, 15 죽임)로 나눔. '범위 측정' 문단에 통합 측정(301·264·생존 50 = 26 + 18 + 2 + 등가 4) |
| A2 U2-a 삭제 | SR 11802 등가 면제 항목 삭제(N2w 대상 아님 -- 처리 불필요). 증명 스케치는 '참고'로 남김. 계약 9의 '생존 3' 문장, 표 판정 칸, '이 card가 죽이지 않는 3문장의 판정' 머리를 같은 뜻으로 |
| A3 계약 11 추가 | trace 루프 범위(`BR(n)`, n = 2·3, 별개 test 2개). 시제품 문장에서 **한 가지를 바꿈**: `layer1_fallback` 원소를 판정에서 뺐다(`TR(r)` = trace 방향 원소만). 근거: 코드 주석(SD 1584~1596, a796468) '못 찾던 것만 보충'인데 n = 2에서 trace가 이미 찾은 쌍이 폴백 원소로 한 번 더 나온다(중복 판정 키에 방향 라벨) -- card 자신의 '거짓 기준값 금지' 원칙. 죽이는 변이는 같다(아래 측정). (b)의 순서는 docstring에 없어 (c) 기준선 값으로 표시. 인용 줄은 a796468 사본에서 `grep -n`으로 확인(1504·1507~1509·1539~1540·1567·1584~1596) |
| A4 test 수 17 → 19 | 판정 유형 근거 V2, '재현할 수치'(v4 측정 절·사본 단계 5), 작성 전 실측 1, oracle 절((a)에 계약 11, (c) 목록에 계약 11 순서), '거부해야 할 입력'에 계약 11, '이름' 항목에 `find_differential_pair_candidates` 진입점·반환 키 |
| A5 B26-1 인계 | 계약 12 직접 호출 목록에 계약 11 두 호출 추가(`rails = rail_declaration({"supply_nets": ["vdd", "gnd"]})`), 'V3 계획' E6·E7 줄 = 'b26pre가 16 + trace 2 죽임, backfill 2는 결함 card, 등가 4는 Q1', 대상 301 → 299(backfill 병합 base) |
| A6 순서 | U3 = 'B34 → 이 card → backfill 결함 card → B26-1'. Phase 값 충돌(Q-B34-PHASE)을 통합 질문과 함께 묻는다는 줄 추가 |
| A7 계약 10 | 변경 없음(N2w 대상 아니지만 기존 동작 test 공백, base PASS -- 참고표에 남김) |

재측정(`C:/g127`, 시제품 19 = v2 시제품 17(계약 10은 v3 단언으로 바꿈) + 계약 11 2(`layer1_fallback` 제외 판)):
* 기준: b34·base × `PYTHONHASHSEED` 0·1 = 4회 모두 `19 passed`. 변이 측정 뒤 b34 seed 1 재실행 `19 passed`(원본 복원 확인).
* trace 변이(b34 사본, 계약 11 test만, seed 1): const+(`range(i + 2, …)`) 2 failed, arith(`range(i - 1, …)`) 1 failed(`test_b26pre_trace_three_branches_order`), const−(`range(i + 0, …)`) 2 passed(등가). 원소 포함 판(`out/trace_v4.jsonl`)과 같은 결과.
* 재검사(gate `0f23786` `tools/gates` archive의 `role_paths.parse_spec_card`·`interface_card.py`, card 사본 `C:/g127/ic/`, `--root` = b34 사본): parse 통과(`phase 2`, `test-only`, `gate_change no`, `approval []`, 절 11개), interface card **19개**(v3 18 + `stick_diagram.find_differential_pair_candidates`), **밑줄 시작 0개**.

남은 것(오케스트레이터·사용자): 통합 질문 Q1~Q3 + Q-B34-PHASE(AskUserQuestion), `layer1_fallback` 중복 원소의 백로그 등록 여부(오케스트레이터), backfill card 승인 기록 커밋 뒤 그 card 머리 `approval` 줄.
