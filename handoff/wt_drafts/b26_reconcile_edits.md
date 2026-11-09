# b26pre·B26-1 spec card를 통합 질문(`b26_survivor_final_question.md`)에 맞추는 편집 목록

작성 2026-10-01. 두 card 초안은 다른 agent가 개정 중일 수 있어 **고치지 않았다**. 아래는 적용할 편집 목록이다(Q1 1번 = 권고안 기준, 다른 답이면 표시한 줄만 바꾼다).
근거 측정: `_drafts/b26_reconcile/out/`(`plan_summary.txt`, `survivor_table.md`, jsonl), 통합 질문 '측정 요약'.

## A. `_drafts/draft_b26pre.spec.md`(v2, id `20260930-b26-pre-test-strengthen`)

1. **범위 정의를 승인 규칙으로**('의도' 범위 문단, '재현할 수치', 표 1 머리): "N2d 대상 중 E6·E7 def" → "승인 범위 규칙 N2(b)+넓힌 T6(`20260930-v3-changed-stmt-scope`, 분류기 `v3_scope_widen.py`) 대상".
   표 1을 둘로 나눈다: (주표) N2w 대상 생존 **18 변이 id**(= base 문장 16: LUT 없는 repair 2문장×2 def, euler fixup 3, finger growth 4 + backfill 2, E7 5) -- 이 card가 16 죽임, backfill 2는 결함 card;
   (참고표) 'N2d만' 문장(SR 11802·11803·11828·11835~11837, SD 3285 삭제·뒤집기·3286·4530, 씨앗 6) -- B26-1 V3 대상 아님, 이 card가 덤으로 죽인다(11802 제외).
2. **U2-a(SR 11802 등가 면제) 삭제**: N2w 규칙에서 11802는 B26-1 V3 대상이 아니라 면제가 필요 없다(`b26pre_v2_kill_map.md` §3과 같은 결론). 증명 스케치는 '참고'로만 남긴다.
3. **계약 11 추가 -- 차동 후보 trace 루프 범위**(시제품 `_drafts/b26_reconcile/proto_test_b26pre_trace.py` 2 test, 문장 그대로 옮김):
   * 입력 `BR(n)`: `Mt(nmos, gnd→ntail, gate nb)` + k = 1..n마다 `Mi<k>(nmos, ntail→no<k>, gate ni<k>)`, `Ml<k>(pmos, vdd→no<k>, gate nbp)`.
   * 호출 `find_differential_pair_candidates(BR(n))`(B26-1 뒤 `rails=rail_declaration({"supply_nets": ["vdd", "gnd"]})`), 결과를 `(direction, position, tuple(devices), shared_source)` 목록으로 펼친다.
   * (a) n=2: `[("vdd_to_gnd",1,("Mi1","Mi2"),"ntail"), ("gnd_to_vdd",1,("Mi1","Mi2"),"ntail"), ("layer1_fallback",None,("Mi1","Mi2"),"ntail")]`.
   * (b) n=3: 방향마다 `("Mi1","Mi2")`, `("Mi1","Mi3")`, `("Mi2","Mi3")` 순서(position 1, `"ntail"`), `vdd_to_gnd` 셋 다음 `gnd_to_vdd` 셋. 층위1 폴백 없음(그룹 크기 3).
   * oracle (a) 구성: branch 서명이 모두 같아 같은 그룹의 branch 쌍 (i<j)을 오름차순으로 비교, 위치 0은 source가 레일, 위치 2는 같은 소자(함수 docstring '같은 non-rail source 공유'·'방향별 1건').
     trace 진입은 아직 이름 `vdd`/`gnd`(B26-2 사이트)라 입력은 그 이름을 쓰고 topology가 아니라 넷리스트 직접 호출이다.
   * 죽이는 변이(실측 `out/trace_v4.jsonl`): `range(i + 1, …)`의 const+((a)에서 branch 후보 소실)·arith((b)에서 순서 변경). const−(`range(i, …)`)는 등가라 죽지 않는다(통합 질문 Q1).
   * 기준 PASS: b1(a796468+B34), backfill 수정 base, 정리 base 모두(`out/baseline.txt`·`plan_*_baseline.txt`).
4. **test 수**: 17 → **19**(계약 11 두 test 별개 함수, 이름 `test_b26pre_trace_two_branches`·`test_b26pre_trace_three_branches_order` 후보). '재현할 수치'의 '시제품 17' 문장과 계약 9의 변이 판정 대상에 trace 2 변이 id를 더한다.
5. **B26-1 인계 문장**: 계약 12 '넷리스트만 쓰는 직접 호출' 목록에 계약 11의 `find_differential_pair_candidates` 두 호출을 더한다(`rails`는 `rail_declaration({"supply_nets": ["vdd", "gnd"]})`).
   'V3 계획'의 E6·E7 줄은 "b26pre가 16 + trace 2 죽임, backfill 2는 결함 card, 등가 4는 Q1"로.
6. **순서**(U3 원칙 기본안): "B34 → 이 card → backfill 결함 card → B26-1".
7. (변경 없음 확인) v2의 계약 10(씨앗)은 그대로 둔다 -- N2w 대상은 아니지만 기존 동작 test 공백이고 base PASS다. 판정 기준 약화 아님.

## B. `_drafts/draft_b26_1.spec.md`(v4, id `20260930-b26-rail-accessor-set`)

1. **'V3 계획' 2 표 교체**: "옮긴 264: 기존 인벤토리가 죽임 150, 추가 계약 근사가 죽임 87, 생존 27" → 통합 측정 "옮긴 264: 기존 test 죽임 214, **기존 test 생존 50** = B26-1 계약 26(E1 14·E3 6·E5 2·7(c) 1·'V3 계획' 4 직접 호출 3) + b26pre 16 + trace 2 + backfill 결함 2 + 등가 4".
   '기존 인벤토리만으로의 생존 수는 재지 않았다' 문장 삭제(이제 50으로 잼). `_metric_kcl_residual` 3개는 '직접 호출 근사 1 test로 죽음 실측'으로.
2. **'남는 24' 표 교체**: E6 13 중 backfill 2는 '등가 아님 -- 결함(U-BF), backfill card가 문장 삭제'로 분리, 나머지 E6 11 + E7 5는 'b26pre card(test-only)'로, trace 2는 'b26pre 계약 11'로. 등가 4 근거는 그대로(통합 질문과 같은 문장).
3. **'V3 계획' 3·U3 문안**: 질문 초안 경로를 `_drafts/b26_survivor_final_question.md` Q1로. '앞선 test-only card 크기 추정(10~14 test)' → 'b26pre 19 test(1 파일)'. 등가 처리 기본안을 C1·C2 정리 + range const− 1건 해시 면제로(C3 `itertools.combinations`는 측정상 새 생존 7 -- 하지 않는다).
4. **(Q1 1번이면) 계약 추가 -- 동작 불변 정리 2줄**(code-author, 'V3 필수'):
   * `_propose_L_roles`: 두 번째 `find_differential_pair_candidates(…)` 호출 뒤의 `if candidates is None: return None` 삭제(남는 `gm_id_roles` 가드의 삭제 변이는 계약 14 E4가 죽인다 -- 측정 B).
   * `propose_device_roles_gap_fill`: `open_net = open_terminals[0]` → `(open_net,) = open_terminals`.
   * 관찰 가능한 동작 불변(등가 근거 1~3). V3 대상 수: 299(정리 없음과 같은 수, `classify_planC12.txt`).
   (Q1 2번이면 이 항목 없음, 4개 면제. 3번이면 C3까지 넣고 새 생존 7 처리 계약 필요.)
5. **'V3 계획' 1 대상 수**: backfill card 병합 뒤 base라 v4 head 대상 301 → **299**(backfill 두 문장이 base에서 사라짐). auditor 재측정 문장은 그대로.
6. **착수 조건 8 교체**: "U3 결정 -- b26pre card 병합 + backfill 결함 card 병합(U-BF 1번) + 등가 면제 승인 기록 커밋(Q1 1번이면 1건, 2번이면 4개 1건)". 승인 필요 목록 ①도 같게.
7. **계약 12 직접 호출 목록**: b26pre 새 test 파일의 `resolve_stack_layout`(계약 5)·`propose_vertical_stack_id_gap_fill`(계약 6 두 호출)·`find_differential_pair_candidates`(계약 11 두 호출)을 더한다. backfill card test 파일(`test_b26_backfill_interdig.py`)은 시그니처 그대로라 고치지 않는다.
8. **U4·U5**: 문안 경로를 통합 질문 Q2·Q3로(내용 같음).
9. `_drafts/b26_1_survivor_question.md`·`_drafts/b26_backfill_question.md`는 통합 질문으로 대체됐다고 머리에 한 줄(삭제는 하지 않음).
