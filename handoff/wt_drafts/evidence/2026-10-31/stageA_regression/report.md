# 단계 A '회귀' 조사 (325ee241 -> e1c455f8) -- 2026-10-31

조사 agent 보고를 오케스트레이터가 옮겨 적음(agent의 파일 쓰기가 거부됨). 원 실측 로그: 같은 폴더 `stageA_runs.jsonl`(12줄).

## 결론
엔진 회귀 아님. 측정 하네스 결함: `skills/analog-gmid-design/gmid_engine/tests/search/u13_real.py:85-88` `real_case`가 `<name>.topology.json`·`<name>.sizing_spec.json`만 임시 폴더로 복사 -- 단계 A가 읽는 형제 파일이 빠짐(오케스트레이터 직접 확인: 85-88행).

## 커밋 차이
`325ee241..e1c455f8` = b3a06768·840c0fea·7fdff45a·e1c455f8, `git diff --stat` = CLAUDE.md 1줄. feaf6ba2·a12b104f·d3221dfb는 325ee241의 조상(두 시점 공통) -- 원인 아님.

## 재현 (old = 325ee241, new = e1c455f8, run_stage_a)
| 회로 | old inplace | new inplace | old copy | new copy |
|---|---|---|---|---|
| current_reuse_telescopic_ota | ok | ok | stopped (`unsupported_rule_branch\|cs_output_low_impedance\|loop:M37a:Voc`) | 동일 |
| nmcnr_amplifier | ok | ok | review_needed (사유 없음) | 동일 |
| two_stage_ota_sf | ok | ok | stopped (`A1_load SCHEMA_REJECTED ref_unresolved`, 'two_stage_ota' 로드 실패) | 동일 |

inplace = library 경로 그대로(m_j1b/rerun/probe_engine.py 방식), copy = u13_real.real_case 방식(o200_v2/run_seal9_engine.py).

## 원인 파일
- current_reuse·nmcnr: `<name>.structure.json` 필요(graph/structure_load.py, pipeline/stage_a.py). 함께 복사하면 ok(new 실측).
- two_stage_ota_sf: spec `value_from_file: "two_stage_ota#gain_ss_db"`(library spec 55·76행) -> 형제 `two_stage_ota.sizing_spec.json`·`.topology.json` 필요. 둘 다 복사하면 ok.

## 영향
- `o200_v2/seal9_circuits.jsonl`의 세 회로 `stage_ab_not_ok`(seal9_evals 0)는 하네스 산물 -> 재측정 필요.
- cnr_ota·r2r_opamp·erfc_ota·rfc_ota·ngcc_3stage_ff 정지는 inplace와 같은 사유(하네스 무관).
- `real_case` 호출 16곳(오케스트레이터 git grep): 같은 위험 -- test 하네스 결함 백로그(엔진 결함 아님).

## 안전
임시 worktree 2개 제거, git status md5 시작·끝 동일, 엔진 소스 수정 0.
