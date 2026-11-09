# TB-1 브리핑 (card id `20261104-tb1-theta-class`)

변수는 오케스트레이터가 채운다: `BASE` = base sha(GL-1·IT-1 + IT-2·EO-1 범위 4·card C·design v1.16.4·A-31 포함 master).
공통 경로: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md`, 저장소 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/CLAUDE.md` 33원칙, `C:/Users/HSLEE/Documents/Todoc/fpga/CLAUDE.md` graph 단일 정본.
공통 규칙: 순서가 중요한 명령은 `&&`로 잇는다(맨 위 `set -e` 동작 안 함), 파이프 금지, `git -C <절대 경로>`만, reset·checkout·stash·push 금지. Python = `/c/Python314/python.exe`, `PYTHONIOENCODING=utf-8`. 트레일러 = `--trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"`. 엔진 인용은 재작성 범위에만. as-built 결정 금지, 모르면 멈추고 보고. 보고는 한글.

## test (gmid-test-author)

```text
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-test (브랜치 role/test/20261104-tb1-theta-class, BASE)
읽기: C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/tb1/20261104-tb1-theta-class.interface.md 만. 소스 열람 금지.
임시: C:/Users/HSLEE/AppData/Local/Temp/la1s_tb1test/
```

T-T1~T-T11을 쓴다. T-T12는 interface §5가 채워진 뒤 동결한다. 기대값은 §1·§2 규칙과 toy에 직접 넣은 `dc_colour`·`orbits`에서 손으로 낸다. 피검 함수로 만들지 않는다. T-T6 고리 밖 base red toy를 못 찾으면 멈추고 보고한다. 지운 대상은 `retired_tests`, 이름 동률 기대값 교체는 `broken_tests`에 이유를 적는다.

```bash
cd /c/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-test/skills/analog-gmid-design && PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 /c/Python314/python.exe -m pytest -q gmid_engine/tests/sizing -p no:cacheprovider --collect-only -k "test_ic or g10 or rule_g or rule_k_" > C:/Users/HSLEE/AppData/Local/Temp/la1s_tb1test/collect.txt
git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-test add skills/analog-gmid-design/gmid_engine/tests && git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-test commit -m "test(TB-1): theta_class 분류·종속 멤버 선택·W4 동률" --trailer "Role: test" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
```

보고: 작성 test, red 예상, `-k` 수(base와 함께), `retired_tests`·`broken_tests`, 커밋 sha.

## code (gmid-code-author, sonnet)

```text
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-code (브랜치 role/code/20261104-tb1-theta-class, test 커밋)
읽기: 같은 폴더 20261104-tb1-theta-class.spec.md, .interface.md, design 40 §2.4.8·§3.7-4·§3.2-3, 41 §4.7-1 2·§5.3.3
임시: C:/Users/HSLEE/AppData/Local/Temp/la1s_tb1code/
```

- 재작성 범위 표대로. OrderHints·`TIE_ROOT`는 같은 변경에서 삭제. 채택된 J-T1~J-T7만 따른다.
- 저항 방향 규칙을 넣지 않는다(A-30). `dependent_facts`를 `build_kernel_context` 인자로 넘기지 않는다.
- `structure.json`은 `rule_hash` 줄만 고친다. connectivity·사실 내용 변경 금지.
- 새 cache·memo·슬롯·사본 금지. 모듈 수준 `ThetaClass` 상수, 새 클래스 가변 속성 금지(`ratchet.new` 0).
- test를 고치지 않는다. 틀렸다고 보면 `docs/02-design/disputes/20261104-tb1-theta-class.md`를 쓰고 멈춘다.

```bash
cd /c/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-code/skills/analog-gmid-design && PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 /c/Python314/python.exe -m pytest -q gmid_engine/tests/sizing gmid_engine/tests/graph gmid_engine/tests/structure -p no:cacheprovider > C:/Users/HSLEE/AppData/Local/Temp/la1s_tb1code/run.txt
git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-code add -A skills/analog-gmid-design docs/03-analysis && git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-code commit -m "feat(TB-1): theta_class 필드, 종속 멤버 선택 재작성, W4 동률 정지" --trailer "Role: code" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
```

보고: 지운 코드·grep, 바뀐 배선, graph 정본 점검, 재계산 점검, `tests/structure`, 깨진 test, 커밋 sha.

## audit (gmid-verification-auditor)

```text
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-audit (브랜치 role/audit/20261104-tb1-theta-class, 격리 복제본 안에서만)
기록: .ai/verification/20261104-tb1-theta-class.json
임시: C:/Users/HSLEE/AppData/Local/Temp/la1s_tb1audit/ (케이스마다 append)
```

interface §6 T-1~T-8을 잰다. 작성자 보고는 증거로 받지 않는다. `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/tb1/measure_gcb7.py`의 S0 경로를 참고할 수 있다(평가 0, LUT 0). 연기 시험 후보 = `current_reuse_telescopic_ota`, `pushpull_follower_buffer`. 회로마다 프로세스를 나눠 순차, background 실행, 여유 메모리 2 GB 아래면 중단. 예외나 직전에 없던 정지 사유면 병합 금지로 보고한다.

판정 기록: '미완료(보류 다리: 변화표·E-1 = LA-1 측정 시점, SPICE = OP-5·CL-1)', M-KV1c 미측정, nmcnr `RL` 재점검(A-30), §5 표를 채운 주체 = 오케스트레이터(작성자 ≠ 기대값 분리). 전체 test 체계는 0 failed가 합격이고, base에 실패가 남으면 목록을 올리고 판정을 멈춘다.

```bash
git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-audit add .ai/verification/20261104-tb1-theta-class.json && git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-tb1-audit commit -m "audit(TB-1): 판정 기록" --trailer "Role: audit" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
```
