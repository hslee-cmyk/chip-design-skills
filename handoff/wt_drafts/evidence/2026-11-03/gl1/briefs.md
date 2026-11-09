# GL-1 역할 브리핑 초안 (card id `20261103-gl1`)

**base = `design/gl1`과 순서 0 커밋을 병합한 뒤의 master**(이 문서를 쓸 때 아직 병합 전이라 sha를 박지 않았다). 아래 명령에서 `role/test/20261103-gl1^`(test 커밋의 부모)이 그 base이고 `role/test/20261103-gl1`이 test 커밋이다. 브랜치에 test 커밋이 하나일 때만 맞다. worktree = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-test`, `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-code`, `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-audit`. 저장소 = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`. Bash는 `&&`로 잇는다(`set -e` 무효).

## 오케스트레이터 순서 (역할 agent에 시키지 않는다)

1. `design/gl1` master 병합(승인 A-29).
2. 순서 0 커밋(master 직접 금지, 문서 브랜치 → 병합): 같은 폴더 `spec_card_draft.md` → `docs/02-design/specs/20261103-gl1.spec.md`, `interface_card_draft.md` → `20261103-gl1.interface.md` **두 파일 함께**. `ls docs/02-design/specs/20261103-gl1.*`로 확인.
3. `git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-test -b role/test/20261103-gl1 master`(1·2 병합 뒤)
4. test agent → `git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-audit -b role/audit/20261103-gl1 role/test/20261103-gl1` → audit 순서 3 → `git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-code -b role/code/20261103-gl1 role/test/20261103-gl1` → code agent.
5. audit worktree에서 code 브랜치 `--no-ff` 병합(충돌 확인 뒤에만 suite) → audit 순서 6 → master 병합 → master 전체 test → worktree 정리.
6. GL-1 병합 전에는 엔진 코드 card를 병합하지 않는다(P:1514). 이후 모든 audit 브리핑에 §10.4 행 둘을 넣는다.

임시 경로(card 끝날 때 오케스트레이터가 지운다): `C:/Users/HSLEE/AppData/Local/Temp/la1s_gl1_test/`, `la1s_gl1_code/`, `la1s_gl1_audit/`.

---

## test agent `[sonnet]` (`gmid-test-author`)

```text
GL-1 test 작성. 공통 브리핑 C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md 를 먼저 읽는다.
입력: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-test/docs/02-design/specs/20261103-gl1.interface.md 만. worktree = C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-test (브랜치 role/test/20261103-gl1, base = design/gl1·순서 0 병합 뒤 master).
금지: 엔진 소스, tests/structure/structure_checks.py, 근거 스크립트 scan_shared_calls.py, wt/_drafts/evidence/2026-11-03/gl1/ 측정 파일 열람.
할 일: interface §5 자리의 픽스처와 test 네 파일. §1·§2 kind마다 위반과 바로 옆 경계, 허용 모듈, 같은 키 여러 건, 첫 줄·끝 줄. §3 형식 오류 전 항목. §4 표 전 case, 종료 코드 2 입력 전부, 바이트 동일(다른 PYTHONHASHSEED). S/README.md에 test 행.
기대값은 픽스처를 손으로 읽어 적는다. 피검 함수 출력을 옮기지 않는다. skip·xfail·넓은 except 금지. pytest.fail로 예외를 바꾸지 않는다. g8_baseline.json 을 만들지 않는다.
기존 test는 고치지 않는다. interface가 모호하면 추측하지 말고 멈춰 보고한다.
base 확인: OPENBLAS_NUM_THREADS=1 C:/Python314/python.exe -P -m pytest skills/analog-gmid-design/gmid_engine/tests/structure -q 를 test 쓰기 전과 뒤에 돌린다(cwd = C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-test, 결과를 임시 경로에 파일로). 뒤에는 새 test 전부 실패, 기존 test 그대로여야 한다.
임시 경로 C:/Users/HSLEE/AppData/Local/Temp/la1s_gl1_test/ 만. 프로세스 종료는 자기 PID만.
git: git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-test 만, `&&`로 잇는다. cherry-pick·apply·am·reset·checkout·stash·push 금지.
커밋 1개: git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-test commit -m "test(gl1): G 확장·값 타입 lint·래칫·감사 도구 toy" --trailer "Role: test" --trailer "Change-Id: 20261103-gl1" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
보고(한글, 짧게): 커밋 sha, 케이스 수, base 실패 목록, interface 모호점.
```

## audit agent 순서 3 `[opus]` (`gmid-verification-auditor`)

```text
GL-1 순서 3(freeze). 공통 브리핑 C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md 먼저. worktree = C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-audit (role/audit/20261103-gl1, 머리 = role/test/20261103-gl1).
할 일: role/test/20261103-gl1 해시 기록, base(`role/test/20261103-gl1^`)에서 새 test가 실패하고 실패 원인이 새 함수·도구 부재임을 확인, 기존 test 그대로임을 확인, 새 test가 피검 출력을 복사하지 않았는지 기대값을 픽스처와 대조.
결과는 C:/Users/HSLEE/AppData/Local/Temp/la1s_gl1_audit/ 와 .ai/verification/20261103-gl1/base_check.json 에 쓰되 **커밋하지 말 것**(순서 6에서 한다).
격리 복제본 안에서만 git 실험, git -C + `&&`, reset·checkout·stash·push 금지. 보고: 한글, 짧게.
```

## code agent `[sonnet]` (`gmid-code-author`)

```text
GL-1 구현. 공통 브리핑 C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md 먼저. worktree = C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-code (role/code/20261103-gl1, 머리 = role/test/20261103-gl1).
입력: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-code/docs/02-design/specs/20261103-gl1.spec.md, .interface.md, design 40 §2.4.10 GL-1 절.
쓸 파일은 정확히 셋. agent 정의 경로표는 폐기된 표를 인용하므로 이 목록이 우선한다:
  skills/analog-gmid-design/gmid_engine/tests/structure/structure_checks.py (추가만, check_g 변경 금지)
  tools/audit/scan_shared_calls.py (신규, 표준 라이브러리만, 대상 엔진 import·exec 금지)
  skills/analog-gmid-design/gmid_engine/tests/structure/README.md (검사기 행)
엔진 소스, test, 픽스처, g8_baseline.json, conftest.py 를 쓰지 않는다. 엔진 위반을 고치지 않는다(동작 불변 card).
옮길 근거: wt/_drafts/evidence/2026-10-29/shared_pure_fn_audit/scan_shared_calls.py 의 해석 부분을 읽고 다시 쓴다(`_module_map` exec, 고정 순서 의존 제거). 전역 cache·memo를 새로 두지 않는다. 결과는 전부 정렬한다.
재사용: structure_checks.py 의 _mutable_value, _module_level, engine_files, rel, parse, Violation. 복사 등록부 면제 적용 금지.
완료 확인: OPENBLAS_NUM_THREADS=1 C:/Python314/python.exe -P -m pytest skills/analog-gmid-design/gmid_engine/tests -q (cwd = C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-code, 결과 파일로, background). **기대 red는 test_rule_g8_baseline_ratchet 하나**(기준선은 판정자 몫). 다른 실패는 고치거나 test가 틀렸다고 보면 docs/02-design/disputes/20261103-gl1.md 를 쓰고 멈춘다. test를 고치지 않는다.
임시 경로 C:/Users/HSLEE/AppData/Local/Temp/la1s_gl1_code/ 만. 프로세스 종료는 자기 PID만. 정본 자리가 필요해 보이면 만들지 말고 멈춰 보고한다(graph 규칙 6).
커밋 1개: git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-code commit -m "feat(gl1): G 확장·값 타입 lint·래칫·공유 호출 감사 도구" --trailer "Role: code" --trailer "Change-Id: 20261103-gl1" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
git: git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-code + `&&`, cherry-pick·apply·am·reset·checkout·stash·push 금지.
보고(한글, 짧게): 커밋 sha, 전체 test 수·실패, 계산식별 정본 확인표(새 필드 0), 모호점.
```

## audit agent 순서 6 `[opus]` (`gmid-verification-auditor`)

```text
GL-1 판정. 공통 브리핑 C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md 먼저. 작성자 보고를 증거로 받지 않는다. worktree = C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-audit (병합본).
wt/_drafts/evidence/2026-11-03/gl1/ 의 facts·b_trace 파일은 판정이 끝나기 전에 보지 않는다.
1. 범위: git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-audit diff --name-only role/test/20261103-gl1^ HEAD. E/ 중 tests/ 밖 변경 0, tools/ 는 tools/audit/scan_shared_calls.py 하나, 기존 test·규칙 변경 0. 어기면 FAIL.
2. 기준선 생성(이 card 판정자 몫): 병합본 엔진에 check_g8 + check_value_types → baseline_doc(위반, "20261103-gl1-baseline", base 전체 sha(`git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-audit rev-parse role/test/20261103-gl1^`)) → dump_baseline → skills/analog-gmid-design/gmid_engine/tests/structure/g8_baseline.json. kind마다 행 하나 이상을 소스로 열어 손 확인, id·cached_property·default_factory 수는 grep으로 따로 센다. 위반이 아닌 것이 든 행은 FAIL로 보고(기준선에 넣어 덮지 않는다).
3. 전체 test: OPENBLAS_NUM_THREADS=1 C:/Python314/python.exe -P -m pytest skills/analog-gmid-design/gmid_engine/tests -q (background, 결과 파일). 0 failed. MemoryError 섞인 결과는 쓰지 않는다.
4. '실제로 거부': 격리 복제본(C:/Users/HSLEE/AppData/Local/Temp/la1s_gl1_audit/) 엔진에 kind마다 위반 한 줄 추가 → ratchet.new에 그 키. 위반 하나 지움 → stale. 줄만 밀기 → 둘 다 빔. 파일 삭제 → test 실패.
5. 결정성: 기준선 2회 바이트 동일, 도구 2회(다른 PYTHONHASHSEED) 네 산출물 sha256 동일.
6. 도구 진짜 트리 1회: class별 callee 수와 limits.json 기록. 합격 조건 아님. toy 표본은 손 분류 일치(test). 감사 B1~B15(wt/_drafts/evidence/2026-10-29/shared_pure_fn_audit.md §2.1) 중 도구가 B로 낸 수를 기록(합격 조건 아님, LA-1 완료 13 입력).
7. design ↔ 구현 gap(40 §2.4.10 GL-1 절 대 코드), interface 대 구현 대조. graph 단일 정본: 새 필드·cache·sctx 슬롯 0 별도 항목. 새 def 소비자, 회로 이름 0, 상수 0.
8. 판정 기록 .ai/verification/20261103-gl1.json(_schema.json, BOM 없는 UTF-8, Write). base_commit = base 전체 sha(`git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-audit rev-parse role/test/20261103-gl1^`), spec_card = docs/02-design/specs/20261103-gl1.spec.md, approvals = []. reproduced_numbers에 판정 커밋 기준 stale 수를 적고, 0이 아니면 FAIL. V1~V10 칸은 폐기 항목을 N/A로 하고 basis에 사유. V2.basis에 '다리: 정의 toy, 봉인·SPICE·변화표 = 대상 없음(엔진 소스 diff 0, 엔진 안 새 이름 소비 0)'과 '연기 시험 = toy로 대신, 사유 = 지나는 엔진 경로 없음'을 적는다. '미완료(보류 다리)'는 쓰지 않는다. 엔진 diff ≠ 0이면 이 문장을 쓰지 말고 FAIL.
9. 커밋 1개(g8_baseline.json + 판정 기록 + 증거): git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-gl1-audit commit -m "audit(gl1): 판정 기록, 기준선 20261103-gl1-baseline" --trailer "Role: audit" --trailer "Change-Id: 20261103-gl1" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
git: git -C + `&&`, reset·checkout·stash·push 금지. 끝나면 reflog·status 확인. 프로세스 종료는 자기 PID만.
보고(한글, 짧게): 판정, 커밋 sha, kind별 기준선 수, new·stale, 전체 test 수, 원래 취지와 다름, 미측정.
```
