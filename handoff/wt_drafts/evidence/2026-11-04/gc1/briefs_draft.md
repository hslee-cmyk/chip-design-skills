# GC-1 브리핑 (S-1~S-8·J-1 위임 A-32 채택, O-226)

경로 변수는 쓰지 않는다. 저장소 = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`. 측정 폴더 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/gc1`. `<BASE>` = 착수 때 master 해시, `<MERGE_BASE>` = 병합 base 해시, 오케스트레이터가 채운다.

공통(모든 역할): `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md`의 안전·원칙 절을 읽는다. 엔진 운영 코드 변경 0. graph 단일 정본: 새 graph 필드·cache·슬롯 0, 자리가 없으면 멈추고 보고. git은 `git -C <절대 경로>`, 순서가 중요한 명령은 `&&`로 잇는다. reset·checkout·stash·push 금지. 트레일러 = `--trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"`.

**J-1(채택)**: checker는 code, 픽스처·기대값·표·부채는 test(원칙 18, WP-13).

## 순서 0. 오케스트레이터 -- card 커밋

독립 검증 뒤, 역할 agent 전에 한다. master에 직접 커밋하지 않는다. spec과 interface를 같은 커밋에 넣는다.

```bash
git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-card -b card/20261104-gc1-rule-l <BASE> \
&& cp C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/gc1/20261104-gc1-rule-l.spec.md C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/gc1/20261104-gc1-rule-l.interface.md C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-card/docs/02-design/specs/ \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-card add docs/02-design/specs/20261104-gc1-rule-l.spec.md docs/02-design/specs/20261104-gc1-rule-l.interface.md \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-card commit -m "docs(card): GC-1 규칙 L spec·interface card (A-32)" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ" \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-test -b role/test/20261104-gc1-rule-l card/20261104-gc1-rule-l
```

code worktree는 test 커밋 뒤에 만든다.

```bash
git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-code -b role/code/20261104-gc1-rule-l <test 커밋>
```

## 순서 2. [sonnet] test -- `gmid-test-author`

worktree = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-test`. 임시 경로 = `C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1test/`.

읽는 것은 둘뿐이다: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-test/docs/02-design/specs/20261104-gc1-rule-l.interface.md`, `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/gc1/baseline_items.jsonl`. 엔진 소스와 측정 폴더의 `measure_*`·`mg3_*`·`mg9_*`를 열지 않는다.

쓰는 것(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-test/skills/analog-gmid-design/gmid_engine/tests/structure/` 아래): `rule_l_tables.py`, `rule_l_debt.py`, `test_rule_l.py`, `test_rule_l_reject_fixtures.py`, `fixtures/rule_l/`.
- `BASELINE`·`DEBT`는 `baseline_items.jsonl`을 그대로 옮긴다. 행을 고치거나 빼지 않는다. 이상해 보이면 멈추고 보고.
- 픽스처 표 전부. 기대 키는 손으로 적고 `check_rule_l`을 불러 만들지 않는다.
- 위반 집합 전체를 `==`로 비교. assert를 if·try 안에 두지 않는다.
- 회로·소자 이름 금지.

완료: 새 test가 `rule_l_checks` ImportError로 실패함을 보이고 커밋(`--trailer "Role: test"`). 실행 = `C:/Python314/python.exe -m pytest C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-test/skills/analog-gmid-design/gmid_engine/tests/structure/test_rule_l.py C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-test/skills/analog-gmid-design/gmid_engine/tests/structure/test_rule_l_reject_fixtures.py`.

## 순서 5. [sonnet] code -- `gmid-code-author`

worktree = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-code`(test 커밋 위). 임시 경로 = `C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1code/`.

쓰는 파일은 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-code/skills/analog-gmid-design/gmid_engine/tests/structure/rule_l_checks.py` 하나다. 다른 파일 변경 0. `structure_checks.py` import·재사용 금지. 엔진 import 금지, 표준 라이브러리만. 측정 폴더의 스크립트와 결과를 열지 않는다. 입력 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-code/docs/02-design/specs/20261104-gc1-rule-l.spec.md`, 같은 폴더 `.interface.md`.

- spec 계약 1~11 그대로. 풀지 못하면 위반(fail-closed), 광범위 except 금지.
- 재수출 이름이 같은 이름 하위 모듈보다 앞선다. 지역 변수에 가려진 이름은 풀지 않는다.
- 패턴을 넓혀도 F-G13 8자리를 못 잡으면 멈추고 보고. 자리를 조용히 빼지 않는다.
- `DEBT`·`BASELINE`·`PARAMS`·test를 고치지 않는다. 틀렸다고 보면 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-code/docs/02-design/disputes/20261104-gc1-rule-l.md`에 근거를 쓰고 멈춘다.
- 판정 시간은 구조 test 안에서 부담이 없게(반복 AST 파싱 금지, 호출 안 지역 구조만).

완료: `C:/Python314/python.exe -m pytest C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-code/skills/analog-gmid-design/gmid_engine/tests/structure` green, 규칙 H는 같은 경로에 `-m structure_test_mapping`. 커밋 `--trailer "Role: code"`. 규칙 H가 새 파일을 요구하면 보고하고, test가 표에 더한다(GD §1).

## 순서 3·6. [opus] audit -- `gmid-verification-auditor`

worktree = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-audit` 격리 복제본에서만. 작성자 보고를 증거로 받지 않는다. 임시 경로 = `C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/`.

재측정(엔진 사본, 저장소 안 건드림). 파이프 실패가 가려지지 않게 `bash -c`와 `pipefail`로 돈다.

```bash
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
mkdir -p C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/base C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/out \
&& bash -c 'set -o pipefail; git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills archive <MERGE_BASE> skills/analog-gmid-design/gmid_engine | tar -x -C C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/base' \
&& C:/Python314/python.exe -B C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/gc1/dump_tables.py C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/base/skills/analog-gmid-design C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/out/tables.json \
&& C:/Python314/python.exe -B C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/gc1/measure_rule_l.py C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/base/skills/analog-gmid-design/gmid_engine C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/out/tables.json C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/out \
&& C:/Python314/python.exe -B C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/gc1/measure_op_sites.py C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/base/skills/analog-gmid-design/gmid_engine C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/out/mg3_l5_op_sites.jsonl \
&& C:/Python314/python.exe -B C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/gc1/build_baseline.py C:/Users/HSLEE/AppData/Local/Temp/la1s_gc1audit/out
```

`unassigned`가 비어 있지 않으면 card id 배정 전에 멈춘다.

항목:
1. **V4·기대값**: 픽스처 기대가 손으로 쓴 값인지, 피검 호출·복사가 아닌지. 픽스처마다 oracle (a) 대조.
2. **거부 먼저**: 픽스처가 base에서 ImportError, 병합본에서 green. checker에 일부러 결함을 넣은 사본(규칙마다 한 건)으로 test가 실패하는지 본다.
3. **기준선**: 규칙 L 집합과 독립 스크립트 집합의 차이를 규칙별로 적는다. 차이 있으면 멈춘다(N3.1-6 (c)). 독립 스크립트는 card 작성 주체가 쓴 것이므로 **그대로 믿지 말고** F-G13 8자리, L-1 표본, L-1x 11개, S-3 9함수, S-4 2자리를 원 파일에서 직접 확인한다. 필요하면 자기 스크립트로 다시 잰다.
4. **GD-1(N3.1-2)**: 진입점·출력 함수를 N3.1-2 기준으로 다시 재어 `PARAMS`와 다른 자리를 판정 기록에 적는다. 넓게 잡힌 자리는 기준 약화 여부를 판단한다.
5. **부채**: (a)(b)(c), card id가 계획 card 표에 있음(f), 처리 어휘. `DEBT` = 병합 base 판 `baseline_items.jsonl`.
6. **지문**: 판정 기록에 지문 값, 대상 목록, 직렬화 규칙.
7. **범위**: 이 card diff가 `skills/analog-gmid-design/gmid_engine/tests/structure/` 아래와 card 문서뿐. 엔진 운영 코드 삭제·수정 0.
8. **N3.10 상위 개정 대조**(GD §7 검증자 항목): GC-1 범위 전수.
9. 결정성(두 번 실행 집합 동일), 구조 test 전체, 회로 이름 0, 상수 0, 원칙 점검표(원칙 26 묶음 2).

산출: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-gc1-rule-l-audit/.ai/verification/20261104-gc1-rule-l.json`. 보류 다리 해당 없음(엔진 무변경).

## 오케스트레이터 메모

- 병합 자리 = HC-1 + GC-8 바로 앞(S-8). 그 master에서 검증자가 독립 스크립트로 기준선을 다시 재고, `7620f5ee` 390항목 대비 늘어난 키마다 원인 card와 근거(소유표 소비자 또는 출력 전용 행)를 판정 기록에 적는다. 근거 없는 새 `L-1`·`L-2`·`L-4` 키는 부채로 넣지 않고 멈춰 그 card로 되돌린다. 그 뒤 test가 상수를 갱신하고 감사한다.
- 병합 뒤 HC-1 브리핑에 알림: 새 필드에 부채 금지(GC:663), 출력 전용 추가는 design 소유표 행 근거(J1, GD §3). GC-1 뒤 먼저 병합되는 다른 엔진 card가 생기면 그 card가 `DEBT`에서 해소 항목을 지우고 새 위반을 만들지 않는다.
- 설정 입구 진입점(`open_run` 등)은 OS-2 때 표 재검토.
- `la1_auto_decisions.md` A-32 기록은 오케스트레이터 몫.
