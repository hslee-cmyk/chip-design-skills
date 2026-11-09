## dispute 기록

1차 시도(2026-10-07, base B1 `6df4bd7`, test 끝 T1 `c247a76`, code 끝 K1 `e92e6b8` -- 병합 안 함)에서 code-author가 K1에 dispute를 동봉했다(`Role: code` 커밋 `e92e6b8`, 경로 `docs/02-design/disputes/20260930-b26-rail-accessor-set.md`). 원문 그대로:

> ---
> id: 20260930-b26-rail-accessor-set
> spec_card: docs/02-design/specs/20260930-b26-rail-accessor-set.spec.md
> test_id: skills/analog-gmid-design/assets/tests/unit/test_selftest_sizing_recipe.py::test_s015_suggest_matching_finger_growth
> test_id: skills/analog-gmid-design/assets/tests/unit/test_selftest_sizing_recipe.py::test_s016_run_matching_safety_with_finger_growth
> ---
> ## 문제의 test
>
> `test_s015_suggest_matching_finger_growth`(1448행에서 `run_matching_safety_with_finger_growth` 호출)와
> `test_s016_run_matching_safety_with_finger_growth`(1494행) 둘. T1에서 이 두 test는 바뀌지 않았다(B1과 같다).
> 둘 다 fixture `s015_state`의 `SizingContext(sized=…)`를 그대로 넘기는데, 이 ctx는 `topology_path`를 주지 않아
> 기본값 `""`이다(`SizingContext.topology_path: str = ""`). 소자도 레일 선언 없는 합성 `Transistor` 목록(`Ma`/`Mb`)이다.
>
> ## 근거(oracle 또는 사용자 원문)
>
> spec card 계약 4 마지막 묶음: "시그니처가 안 바뀌는 뿌리(선언을 스스로 얻는다): … `run_matching_safety_with_finger_growth`·
> `_fixup_euler_blocked_rows`(`ctx.topology_path`)". 이 함수는 `repair_matching_safety(…, rails=…)`와
> `_branch_composite_pair(…, rails=…)`를 반드시 부르고(계약 4 시그니처, 기본값 없는 `rails`), 그 `rails`의 출처는
> `_topology_meta_cached(ctx.topology_path)["rails"]` 하나다(계약 3: 새 캐시·SR의 `rail_declaration` import 금지,
> 원칙 2: 이름 집합 폴백 금지).
>
> 구현 결과(자기 확인, 판정 증거 아님): 위 두 test가 `FileNotFoundError: [Errno 2] No such file or directory: ''`로
> 실패한다(`_topology_meta_cached("")` → `load_topology("")`). 나머지 A/tests 전체는 통과(1177 passed, 15 xfailed,
> 실패는 이 두 개뿐). 계약대로면 선언을 얻을 경로가 ctx에 없으므로 구현으로 풀 수 없다 -- 폴백(빈 경로면 이름 집합·빈 선언)을
> 넣으면 계약 2 '조용한 폴백 금지'를 어긴다.
>
> spec card 계약 12는 "새 키워드 인자를 받게 되는 함수를 직접 부르는 기존 test에 `rails=`를 더한다"고만 정하고
> (시그니처가 안 바뀌는 뿌리는 대상 밖), 선언 없는 ctx로 뿌리를 부르는 기존 test를 다루지 않는다. 계약 12 마지막 항목은
> `test_b26_backfill_interdig.py`만 '고치지 않는다'고 하며, 그 파일은 ctx에 `topology_path=str(path)`를 이미 넣는다(98행).
>
> ## 요청
>
> test-author가 `s015_state`의 `_l4d_ctx`에 레일을 선언한 tmp topology 파일 경로(`topology_path=`)를 넣도록
> `test_selftest_sizing_recipe.py`를 갱신한다(두 test의 판정·기대값은 그대로, `supply_nets` 선언 입력만 더함 -- 계약 12 둘째
> 항목의 규칙과 같은 종류: 그 넷리스트가 쓰는 넷 중 레일이던 것을 선언, 없으면 `[]`. 두 test의 소자는 `s`/`Na1`/`Vtail` 등으로
> 레일 이름 넷이 없으므로 `supply_nets: []`). 또는 spec card가 이 두 test를 계약 4 '뿌리'에서 빼는 다른 방식을 정한다.
> 결정은 사람이 한다. 이 결정 전까지 K1(1차 시도)에서 이 두 test는 실패로 남는다.

blob: 04ea6a2732fde2342f228c25e6444b7999b16309

결정(오케스트레이터 원칙 결정 -- `_drafts/user_decisions.md` '2026-10-07 B26-1 1차 시도 중 결정'의 줄 그대로):

> - [B26-1 dispute 처리(오케스트레이터 원칙 결정)] s015·s016 fixture에 topology 경로 없음 → 계약 12 '기존 test 입력 갱신'(판정 불변)으로 test-author가 tmp topology(supply_nets는 계약 12 다섯째 항목 규칙)를 더한다. 계약 4 뿌리 제외(card 개정)는 택하지 않음.

dispute '요청'의 첫째 방식(test 쪽 입력 갱신)을 택했다: test-author가 `test_selftest_sizing_recipe.py`의 fixture `s015_state`가 만드는 ctx에 레일을 선언한 tmp topology 파일 경로(`topology_path=`)를 더한다. `supply_nets` 값은 계약 12 다섯째 항목 규칙을 그 두 test의 소자 넷에 적용한 것이다. 두 test의 판정·기대값은 바꾸지 않는다. 계약 2(조용한 폴백 금지)·계약 3·계약 4(뿌리 목록)와 신규 시그니처는 바꾸지 않으므로 interface card는 그대로다. 기준 약화가 아니어서(판정·기대값 불변, 입력 추가) 승인 기록을 두지 않는다 -- 같은 모양의 선례: `20260929-probe-engine-dup` 2차 시도 dispute의 오케스트레이터 결정(`fb8ee35`). 순수 삽입이 아니어서 V5 발견이 나면(두 경로 밖 세 번째 경로) '승인 줄 배치' (6)대로 멈추고 사용자 승인을 따로 묻는다.

design 05 §12 '재시도'대로 이 절을 커밋한 뒤 세 worktree·브랜치를 정리하고 같은 id로 순서 1부터 다시 한다. 다시 하는 시도도 '두 번 시도 절차'의 1차 시도(병합 안 함)이고, 그 base B1은 이 절을 담은 gate `master`다. T가 바뀌므로 순서 3(`base_check.json`)과 K1 뒤 V3 측정은 새 T1·K1에서 다시 잰다. 중단된 시도의 산출물(T1·K1 diff, dispute 사본, 순서 3 출력)은 저장소 밖 `_drafts/b26_1_attempt1_r0/`에 보관한다(`SHA256SUMS`).
