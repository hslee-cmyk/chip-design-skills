# Phase 2 완료 판정 -- auditor 브리핑 초안 (P10b 판정 기록 push 뒤 사용)

착수 조건: gate master에 P9·P10·P10b 판정 기록, B28(20260930-v3-history-clone) 판정 기록, design 20 E4 정정 + 승인 `20260930-phase2-e4-baseline`, design 20 E4 PT phase 정정(`_drafts/patch_e4_phase.py`) + 승인 `20260930-phase2-e4-phase`.
임시 경로: 이 작업 전용 `C:/g<번호>` 하나(그때 살아 있는 agent 경로와 대조해 배정). 가드: 격리 복제본(`--no-hardlinks --no-local`, origin 제거, `core.longpaths=true`, detach), `git -C`, `set -e`, 끝나면 reflog·status.

측정(대상 커밋 <H> = 마지막 판정 기록 커밋, 게이트 캐시 = <H>의 tools/gates):
- E0: reg_check exit 0 (P10b 이후라면 `--df23-inventory` 대조도).
- E1: `PT tests/contracts -k "dup_w_calc or dup_kcl_edges" -rA` 실패 0, **모듈별 수집 수**(test_dup_w_calc ≥1, test_dup_kcl_edges ≥1), 두 판정 기록(20260930-dup-w-calc, 20260930-p9-kcl-edges) checks.V2 PASS.
- E2: engine_dup_scan exit 0, 면제 아닌 발견 0, 면제 목록(20260929-p4-scan-exempt).
- E3: df23_inventory.json -- len(items) == totals.n_items, 모든 항목 phase ∈ 닫힌 집합, '동작을 정함' 항목 function 비지 않음, measured_at 커밋 엔진 blob = <H> 엔진 blob.
- E4(정정본 2회 -- 승인 `20260930-phase2-e4-baseline`·`20260930-phase2-e4-phase`): `PT2` 전체와 `PT2 --gmid-dod` 전체 두 실행 모두 실패 0(`PT2` = design 10 §10 `PT` 정의에서 `--gmid-phase=1`만 `--gmid-phase=2`로 바꾼 것, 수집 수 비교 안 함). 그리고 da03c0e 판과 <H> 판을 같은 복제본 경로에서 -- E-LIB hash 동일(9/9 로드), E-INST(파일럿·folded_cascode) without_topology_ref_sha256 동일 + <H> topology_ref = DF-36 계약 1 값(`topology_ref_equals_expected_contract1` true, 경로 문자열 잎 0) + da03c0e 판 `topology_ref_is_join_of_ASSETS_DIR` true. da03c0e 쪽은 DF-35 base 모드(e_inst_df35.py `<iso> <회로> base <out>`), <H>는 e_inst_df36.py `<iso> <회로> <out>`. 절차: 판을 바꾸기 전에 세 스크립트(e_lib.py·e_inst_df35.py·e_inst_df36.py, da03c0e 판에는 없음)를 <H> 판 `<iso>/.ai/verification/…`에서 `<iso>` 밖 임시 경로로 복사해 sha256을 기록하고 두 판에 같은 사본을 쓴다. `<out>`도 `<iso>` 밖. 실행은 `C:/Python314/python.exe -B -P <사본> …`. 판을 바꿀 때마다 `git -C <iso> checkout -- workspaces`·`git -C <iso> clean -fdx`.
- E5: `PT … -k new_topology -rA` PASS(수집 목록).
- N6.3: Phase 2 판정 기록 전부 V1~V10 PASS/N/A, merge·audit 커밋이 gate 조상, `git log da03c0e..<H> --no-merges -- A/*.py workspaces/run_harness.py A/library/*.json` 전부 card 커밋.
- 판별력 대조: E3는 P10 직전 커밋에서 FAIL, E1은 P9 직전 커밋에서 dup_kcl_edges 0 수집.
- 남긴 관찰(결정 D2 (a)): tests/probe_physical_consistency.py -- P3c 보류(B21, Phase 4), 스캐너 범위 밖 rail-set 재구현 1건(40행), 절대 경로 2개(33·38행).

오케스트레이터: 보고를 다시 계산하지 않고 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md`로 옮겨(머리: 대상 커밋·측정 주체·환경, E0~E5 표, N6.3, 남긴 관찰) 커밋, .ai/context.md Python 바이너리 append(삭제 0줄 확인).
