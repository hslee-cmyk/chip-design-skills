verdict: Major 0

# FS-1 (20261107-fs1) 순서 3 동결 최종 판정 (재판정 4, A-193 MR-3)

## 대상과 격리
- test head는 `58952cb1`이다. audit worktree에 `git merge --no-ff`로 들였고, 병합 커밋은 `6f2ae8a7`이다. 엔진 변경은 0이다.
- 격리 복제본은 `C:/fzf1/iso4`다(`--no-hardlinks --no-local`, origin 제거). 실행 래퍼는 `C:/fzf1/run4.sh`, 출력은 `C:/fzf1/out4/eps.txt`·`r17.txt`다.

## 1. MR-3 -- 닫힘, 새 약화 0
- 판정 대상은 `58952cb1` 한 커밋이다(`search/test_find_front.py` +6 −2).
- Rz 단언: `1e2 <= rz <= 1e6`을 `P_RBOUNDS[0] <= rz <= P_RBOUNDS[1]`로 바꿨다. 입력 rbounds와 같은 상수 (1e3, 1e6)이다.
- Cz: `PZ_CBOUNDS = (1e-14, 1e-10)`을 입력 `cbounds`와 단언이 함께 참조한다. 값은 옛 리터럴 그대로다.
- 다른 단언·입력은 바뀌지 않았다.

## 2. RETIRED 미측정 front test를 대신 덮는 test의 base 실행 (pytest 하나씩)
| test | 착수 전 여유 | 결과 | 분류 |
|---|---|---|---|
| `search/test_eps_sweep.py::test_unmeasured_never_in_final_front` | 5.22 GB | 1 passed (1.3 s) | **통과** |
| `search/test_find_front.py -k r17` (3개) | 5.28 GB | 3 failed | **코드 없음**: `AttributeError: gmid_engine.sizing has no attribute 'WfCell'` |
| `search/test_find_front.py::test_passive_theta_circuit_front_measured` (같은 실행) | -- | PASSED | 통과 (MR-3 수정 확인) |

- R-17 3개의 실패 경로는 `_wb1_points` → `wb1_flow.r2_theta` → `fs1_wf.size_and_seal` → `hand_wf_default`(`fs1_wf.py:20`)다. FS-1 새 이름(WfCell)이 없어서 실패한다.
- 따라서 성질 대체는 다음과 같다.
  - sweep 분류 수준: base에서 통과한다(실측).
  - 실현 뒤 재분류 수준(R-17): 코드 뒤에 판정한다.

## 최종 freeze 판정
- **Major 0이다. code 착수 가능하다.**
- freeze T = `58952cb1`. 판정 기록 = audit `.ai/verification/20261107-fs1/base_check.json`(attempt 4, `code_start_allowed: true`).
- 앞 Major 처리: M-1·M-3·M-4는 r2에서, MR-1·MR-2는 r3에서, MR-3은 r4에서 닫혔다. M-2·M-5는 MR-1·MR-2를 거쳐 닫혔다.
- minor는 LA-1 재점검 입력이다.
  - `fs1_freeze_r2.md` n-1·n-2·n-4·n-7·n-9
  - `fs1_freeze_r3.md` r3-1·r3-2
- 미측정 범위(통과로 세지 않음):
  - `test_iv_matching_l`
  - search 전체, generality, `test_s0_layer_9circuits`
  - 2회로 연기, `search/test_canonical_order.py`, slow 표지 test
  - r3에서 중단된 전체 `--collect-only`
  - 위 범위는 순서 7 판정 V1 범위에서 다룬다.

## 운영
- 금지 명령(`python -`·`sed -i`·`cat > /dev/null`·heredoc)은 0회다.
- 끝날 때 python 프로세스는 0이다.
