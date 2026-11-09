# B33 kit dafe5cf 갱신 독립 검증 (review_b33_dafe)

검증자: 독립 agent(작성자 아님). 2026-10-06. 실제 저장소는 읽기 전용(`git -C`). scratch `C:/g296`(TMP/TEMP도 그 안)에서만 실행했고 끝에 삭제했다.
대상: `draft_b33.final.spec.md`(vs `.pre-dafe.bak`), `b33_launch.sh`(vs `.pre-dafe.bak`), `b33_kit/out/head_dafe5cf/`, `b33_kit/out/a33_dafe5cf.*`.

## 판정: minor 2건 (B 0, S 0)

## 1. 바뀐 범위 (절 단위 바이트 비교)
- spec: 12개 절 가운데 바뀐 절은 `## 의도`(64·67행 인용 줄)와 `## 작성 전 실측`(새 `(착수 재측정 2026-10-06 …)` 문단과 1·2·5항 줄 번호)뿐이다.
  `관찰 가능한 계약`, `판정 유형 근거`(redteam 표), `oracle`, `거부해야 할 입력`, `무동작`, `재현할 수치`, `결정 필요 항목`은 바이트까지 같다.
- launch: 293행 echo 문구만 바뀌었다(판정 로직은 바뀌지 않았다). `b33_briefs.md`는 `.pre-dafe.bak`과 같다.

## 2. 인용 줄 (`git show dafe5cf:<path>`)
| 인용 | dafe5cf 실제 | 결과 |
|---|---|---|
| mutate 519 `rch.reach` (inventory) | 519 | OK |
| mutate 621 `rch.build_graph(head_files)`, grep -c 1 | 621, 1 | OK |
| mutate 619 `_is_source` | 619 | OK |
| mutate docstring 12 `build_graph` | 12 | OK |
| mutate 661~662 `TimeoutExpired → "timeout"` | 661·662 | OK |
| mutate 720~725 `code == 0`이 아니면 `killed += 1`(725) | 720 if / 724 else / 725 killed | OK |
| rt.py `build_vrepo` 592, `a_vcase` 666 (0f23786 523·580) | 592·666 (523·580) | OK |
| sizing_recipe 6452 `super().__init__(message)`, `super().__` 1건 | 6452, 1건 | OK |
| reachability 69/97/160/175/223/230 | 같음 | OK |
| 0f23786 뒤 mutate를 바꾼 card = 34·35 | dd01d1d(34)·b70a05a(35) | OK |
| 계획 121·843 문구 | dafe5cf 기준 같음(7243f28에서는 843→845로 줄만 옮겨졌고 내용은 같다. pre는 grep -F로 내용을 비교한다) | OK |

## 3. 머리 수치 독립 재측정 (dafe5cf, 자작 `indep.py` -- kit의 m1을 쓰지 않음)
- 미도달: 두 도구의 **CLI main**을 `--base <빈 트리>`로 실행해 소스 def 494개가 전부 new_defs가 되게 했다. base 도구 115, 시제품 fixed 39. 직접 BFS: base 115(R3 적용 시 116), fixed R3 39. 미도달 집합은 0f23786 m1 목록과 base·개정 모두 같다.
- 누수: base(R3 없음) 66 → fixed(R3) 0.
- test 함수 556(mutate_changed.py 622~623 정규식). V3 쌍 35,946 → 47,452. 인벤토리 0: 82 → 19, 회귀 0. 중앙값 62 → 68. base 변형 간선 = HEAD 도구 간선.
- 188파일: `git diff --name-only 0f23786 dafe5cf -- <GRAPH_PREFIXES> reachability.py .ai/verification/` = 188.
- kit 재실행(`run_headline.sh`는 수정하지 않았다): m1은 시간 키와 `missing_sample`(set 순서에 따라 바뀌는 앞 12개 표본)을 빼면 작성자 출력과 같다. m5는 같다. m4는 작성자 출력과 같다: 기록 32, distinct 쌍 31, 31쌍 모두 PASS이고 base와 시제품의 unreached·uwa가 같으며, `--config`는 모두 head, new_defs가 있는 쌍은 4개다.
- 공격 33(`run_attack33.sh` 사본 -- clone에 `-c core.autocrlf=false`만 더했다): base 13 FAIL / 17 PASS, fixed 30 PASS. xout·bare·nosuper는 각각 1 FAIL, draft 6 FAIL, loose 9 FAIL. 210개 (도구·변형·단계) 판정·exit가 작성자 `a33_dafe5cf.jsonl`, `a33r3_0f23786.jsonl`과 모두 같다.
- 34·35 무동작 미리보기: 17단계(34 6·35 11), base와 시제품 모두 PASS, 차이 0.

## 4. 지적
- **m1 (minor)** `결정 필요 항목` 264행은 여전히 `0f23786 523·580행`을 인용한다. rev가 표기돼 있으니 사실로는 맞다. 그런데 새 문단은 "인용 줄은 위 본문(… `rt.py` 592·666 …)"이라고 적어서 본문에 dafe 값이 있는 것처럼 읽힌다. 264행에 `dafe5cf` 592·666을 병기하거나, 새 문단의 "위 본문"을 "이 문단"으로 고친다(계약이 아닌 절이라 바이트 동일 원칙에 걸리지 않는다).
- **m2 (minor, 알림)** launch 293행의 출력 grep은 `"result": "killed"`를 찾으므로 726행을 출력한다. card 표기 720~725와 1줄 다르다. 출력 전용이라 판정에는 영향이 없고, 운영자가 보고 놀라지 않도록 적어 둔다.
- **상황 정보(결함 아님)**: 검증하는 동안 gate master가 `2183f2e`(B34 병합 + 판정 기록)로 움직였다. dafe5cf→2183f2e 사이 V7 그래프 입력은 78파일 바뀌었다. 문단의 마지막 문장(B34가 병합되면 다시 잰다)이 예고한 그대로이고, pre의 그래프 입력 대조가 이 상황에서 멈추도록 설계돼 있다. 착수 때 다시 재야 한다.

## 5. 작성자 주의 사항: 모래상자에서 pre가 막히는가
- 재현 결과(C:/g296): 복제본의 `gate_config.json` `gate_path`는 실제 gate 절대 경로다. `rp.load_env`는 실제 gate master(당시 7243f28)를 읽어 캐시 `<복제본>/.git/gmid-gate-cache/7243f28…`를 만든다. 한편 `cache_dir`는 `basename == git rev-parse gate/master`(복제본의 모래상자 gate, dafe5cf)를 확인한다. 두 값이 다르므로 `test`에서 실패하고 pre가 멈춘다. 작성자 주장이 맞다.
- 성격: fail-closed다. 거짓 PASS가 나지 않고, 실제 gate에는 읽기만 한다. 모래상자 gate와 실제 gate master가 같을 때(방금 복제한 경우)는 통과한다. 다르면 막힌다. 막히는 경우는 (a) 미래 상태 리허설(선행 card를 모래상자에 병합), (b) after-push 리허설, (c) 리허설 도중 실제 gate가 움직이는 경우다. (c)는 이번 검증 중에도 실제로 일어났다. 또 두 값이 같을 때도 캐시 내용은 **실제 gate의 게이트 코드**라서, 모래상자 gate에서 바뀐 게이트 코드는 리허설되지 않는다.
- 판정: B33 착수를 막지 않는다(실제 실행은 실제 gate 기준이다). 앞으로 모래상자 리허설을 막을 수 있으므로 고칠 가치는 있다. 다만 같은 `cache_dir` 패턴이 launch 스크립트 약 20개(`ensure_cache` 사용)에 공통으로 들어 있다. 그래서 b33만 고치지 말고 `launch_common.sh`에 복제본 모드 전용 `lc_cache_dir`를 하나 두는 편이 맞다. 예를 들어 LC_REAL=0일 때 모래상자 `gate/master`의 `tools/gates`를 복제본 common-dir 아래로 추출하고 같은 basename 규칙으로 확인한다. 백로그(minor, 인프라)로 둔다.

## 정리
실제 저장소 HEAD와 상태는 내가 바꾸지 않았다. 내가 실행하는 동안 HEAD가 2183f2e로 fast-forward됐는데, 다른 주체가 병합한 것이다. `C:/g296`은 삭제했다.
