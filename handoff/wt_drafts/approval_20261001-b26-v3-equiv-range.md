---
id: 20261001-b26-v3-equiv-range
date: 2026-10-01
target_kind: decision
target: <V3_MUTANT_ID>@<V3_BIND_HASH_64>
scope: 결정 U3 -- spec card 20260930-b26-rail-accessor-set(B26-1) V3 등가 변이 1개 면제: find_differential_pair_candidates의 range(i + 1, …) 상수 1 → 0(const-) -- 늘어난 j == i 짝은 a == b로 건너뛰어 동작이 같다. 묶기 = 20260930-v3-exempt-binding(변이 id@그 def 묶기 해시, 1차 시도 code 커밋 K1에서 auditor가 잼) -- 다른 변이·다른 def·해시가 다른 def는 덮지 않는다
---

## 사용자 원문

> 정리 2줄 + 면제 1 (Recommended)

(질문 2026-10-01 21:10 KST, 답 2026-10-01 21:14 KST(세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` AskUserQuestion `toolu_01KTtsbRiK7S3cv1coUsAyPw`, 질문 4개 중 [U3 등가]). 질문 원문(고치지 않고 그대로): "[U3] B26-1 V3 대상 301개 중 지금 코드에 대응이 있는 264개를 지금 test로 돌리면 50개가 살아남습니다(새 문장 37개는 B26-1 계약 test 몫, 병합본에서 auditor가 쟽니다). 26개는 B26-1 계약 test가, 18개는 앞선 test-only card b26pre(19 test, 엔진 변경 없음)가 죽이고, 2개는 이미 답하신 backfill 결함 수정으로 문장이 없어집니다. 남는 4개는 등가 변이(바꿔도 동작이 같음)라 어떤 test로도 죽지 않습니다: _propose_L_roles의 서로 중복인 None 가드 2개, open_terminals[0]→[-1](원소가 정확히 1개), range(i + 1, …)→range(i, …)(늘어난 j == i 짝은 a == b로 건너뜀). 등가 4개를 어떻게 처리할까요?"
선택지: "정리 2줄 + 면제 1 (Recommended)" -- "B26-1에서 동작 불변 정리 2줄로 등가 3개를 없애고, 정리로 못 없애는 range 1개만 변이 id@def 해시로 면제합니다(약화 승인 1건, 기록은 구현 뒤 auditor가 잰 해시로 병합 전 커밋)." / "등가 4개 모두 면제" -- "엔진 정리 없이 등가 4개를 변이 id@def 해시로 면제합니다(약화 승인 1건에 4개)." / "4개 모두 정리(C3 포함)" -- "면제는 0이지만 range 이중 루프를 itertools.combinations로 바꾸면 루프 본문 7문장이 새로 대상이 되어 생존 7이 생깁니다(권하지 않음)." / "test 보강 없이 면제" -- "b26pre 없이 남는 24개를 면제합니다. 죽일 수 있는 18개와 결함 2개까지 덮는 기준 약화입니다(권하지 않음).".)

## 범위 설명

덮는 것: V3 변이 id `<V3_MUTANT_ID>` 하나(`stick_diagram.py` `find_differential_pair_candidates`의 `range(i + 1, len(chains))` 첫 인자 `i + 1`의 상수 1을 0으로 -- U3 질문의 넷째 등가 변이). 원소는 묶기 card `20260930-v3-exempt-binding`의 `<변이 id>@<묶기 해시>` 형식이고, 해시 `<V3_BIND_HASH_64>`는 B26-1 **1차 시도** code 커밋 K1 `<K1_40>`(base B1 `<B1_40>`)의 그 def 원본 묶기 해시다 -- 출처는 1차 auditor `mutate_changed.py --base B1 --head K1` 판정 JSON의 `survivor_bindings`(보관 `<ARCHIVE_LABEL>attempt1_v3.json`), 오케스트레이터가 K1 def에서 같은 정의로 따로 계산해 일치를 확인했다. 보관 sha256: <ATTEMPT1_SUMS>.
2차 시도에서 code-author가 그 def를 K1과 같은 글자로 만들면(B26-1 card '두 번 시도 절차' 3) 병합본 head의 묶기 해시가 같아 이 면제가 적용된다. 해시가 다르면 이 기록은 적용되지 않고(`exempt_ignored` `hash_mismatch`) 재승인이 필요하다(B26-1 착수 조건 8 마지막 문장).
덮지 않는 것: 같은 def의 다른 변이, U3 질문의 나머지 등가 3개(`_propose_L_roles` None 가드 2개·`open_terminals[0]` -- B26-1 정리 C1·C2로 문장이 없어진다), 다른 def·다른 card의 변이, V4·V5·V7 면제 일체(이 원소는 `@`를 담아 V4·V7 id와 같지 않다).

<!--
채우는 법(B26-1 '두 번 시도 절차' 2 (a)⑥ -- 이 주석은 커밋 전에 지운다. 자리표시 6개 <V3_MUTANT_ID>·<V3_BIND_HASH_64>·<K1_40>·<B1_40>·<ATTEMPT1_SUMS>·<ARCHIVE_LABEL>도 모두 실제 값으로 바꾼다):
0. 이 초안이 기록 5 본문의 단일 출처다. b26_1_carry.sh records 단계는 `_drafts/b26_1_kit_selftest/fill_u3.py --draft <이 파일> --out .ai/approvals/<id>.md
   --state <carry 상태 파일> --archive <보관 디렉터리> --archive-label <A_LABEL> --src <보관 K1_SD.py> --jsonl <세션 jsonl>`로 이 초안을 채워 기록 5를 쓴다
   (옛 records heredoc 생성기는 지웠다 -- 지우기 전 같은 값에서 바이트가 같음을 쟀고, b26_1_kit_selftest/records_u3_test.sh가 b26_1_carry.sh.pre-u3.bak heredoc과
   `fill_u3.py --check-carry`로 계속 대조한다). <ARCHIVE_LABEL> = carry A_LABEL(실제 실행은 `_drafts/b26_1_attempt1/`).
1. 시점: B26-1 **1차 시도** code 커밋 K1 뒤, 1차 auditor가 `mutate_changed.py --base B1 --head K1`의 판정 JSON(stdout 한 줄)을 audit worktree
   `.ai/verification/20260930-b26-rail-accessor-set/attempt1_v3.json`에, `--out`을 `attempt1_v3.out.jsonl`에 남긴 뒤, 1차 정리 전(carry check·archive 뒤).
   커밋은 1차 정리(역할 브랜치 삭제) 뒤 기록 4(`20261001-b26-p9-signature-update`)·운반 blob·card 개정과 같은 `Role: doc` 커밋 하나, push는 2차 시도 착수 전(같은 절차 2 (b)→(c)→(d)).
2. <V3_MUTANT_ID>@<V3_BIND_HASH_64> = 그 판정 JSON `survivor_bindings`의 원소 하나(생존이 정확히 1개, id가 `^stick_diagram:find_differential_pair_candidates:const-:`로 시작,
   AST 경로 끝 노드가 `range(i + 1, …)`의 정수 1). 해시 = K1 트리 `stick_diagram.py`의 그 def 노드 원본(docstring·데코레이터 포함)
   `ast.dump(annotate_fields=True, include_attributes=False, indent=None, show_empty=False)` sha256, gate 인터프리터(3.14) -- `tools/gates/mutate_changed.py` `bind_hash`. 따로 계산해 일치를 확인한다.
3. <K1_40>·<B1_40> = 1차 code 커밋 K1, 1차 base B1(40자리 소문자 16진). <ATTEMPT1_SUMS> = 보관 디렉터리 SHA256SUMS의 attempt1_v3.json·attempt1_v3.out.jsonl·K1_SD.py 세 줄을
   `<이름> sha256 <해시>`로 바꿔 이름 순서 그대로 '; '로 이은 것(carry records와 같은 식).
4. 검증: `$PY tools/gates/merge_gate.py parse-approval .ai/approvals/20261001-b26-v3-equiv-range.md` exit 0, target_kind decision, target_list = [그 원소 하나].
   2차 시도에서 그 def가 K1과 같은 글자이면 병합본 head 묶기 해시가 같아 면제가 적용되고, 다르면 `exempt_ignored` `hash_mismatch`로 적용되지 않는다 -- 재승인(착수 조건 8).
선례 양식: `.ai/approvals/20261001-p10b-v3-equiv.md`(target_kind decision, target = 변이 id 목록 -- 묶기 card 전이라 해시 없음), 묶기 규칙 `.ai/approvals/20260930-v3-exempt-binding.md`.
-->
