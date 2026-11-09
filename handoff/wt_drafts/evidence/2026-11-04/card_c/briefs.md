# XRUN-F1 card C 브리핑 (card id `20261103-xrunf1c`)

변수는 오케스트레이터가 채운다: `BASE` = base sha(GL-1·IT-1 + IT-2·EO-1 범위 4 + 로더·A-31 포함 master).
공통 경로: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md`, 저장소 `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/CLAUDE.md` 33원칙, `C:/Users/HSLEE/Documents/Todoc/fpga/CLAUDE.md` graph 단일 정본.
공통 규칙: 순서가 중요한 명령은 `&&`로 잇는다(맨 위 `set -e` 동작 안 함), 파이프 금지, `git -C <절대 경로>`만, reset·checkout·stash·push 금지. Python = `/c/Python314/python.exe`, `PYTHONIOENCODING=utf-8`. 엔진 인용은 재작성 범위에만. as-built 결정 금지, 모르면 멈추고 보고. 보고는 한글.

## test (gmid-test-author)

```text
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-test (브랜치 role/test/20261103-xrunf1c, BASE)
읽기: C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/card_c/interface_card.md 만. 소스 열람 금지.
임시: C:/Users/HSLEE/AppData/Local/Temp/la1s_ctest/
```

C-T1~C-T14를 쓴다. 기대값은 정의에서 손으로 내고 `open_run()`만 쓴다. C-T11이 red 핵심이고 assertion 실패여야 한다.

```bash
cd /c/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-test/skills/analog-gmid-design && PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 /c/Python314/python.exe -m pytest -q gmid_engine/tests/search -p no:cacheprovider --collect-only -k "test_ic or g10 or rule_g or rule_k_" > C:/Users/HSLEE/AppData/Local/Temp/la1s_ctest/collect.txt
git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-test add skills/analog-gmid-design/gmid_engine/tests && git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-test commit -m "test(card C): 평가 예산 상한" --trailer "Role: test" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
```

## code (gmid-code-author, sonnet)

```text
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-code (브랜치 role/code/20261103-xrunf1c, test 커밋)
읽기: 같은 폴더 spec_card.md, interface_card.md, design 40 §2.4.5·§2.4.14 C 행
임시: C:/Users/HSLEE/AppData/Local/Temp/la1s_ccode/
```

재작성 범위 표대로, 옛 코드는 같은 변경에서 삭제. 전역 이름 관찰 지점 유지. 새 필드·칸 0, `S3Index`는 `total_of` 참조만. `index_bound`가 `len(blocks) × (E_total + 1)`과 다르면 멈추고 보고. test를 고치지 않고, 틀렸다고 보면 dispute를 쓰고 멈춘다.

```bash
cd /c/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-code/skills/analog-gmid-design && PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 /c/Python314/python.exe -m pytest -q gmid_engine/tests/search gmid_engine/tests/structure -p no:cacheprovider > C:/Users/HSLEE/AppData/Local/Temp/la1s_ccode/run.txt
git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-code add -A skills/analog-gmid-design docs/03-analysis && git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-code commit -m "feat(card C): 평가 예산 상한, 게이트 예약, 색인 상한" --trailer "Role: code" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
```

## audit (gmid-verification-auditor)

```text
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-audit (브랜치 role/audit/20261103-xrunf1c, 격리 복제본 안에서만)
기록: .ai/verification/20261103-xrunf1c.json
임시: C:/Users/HSLEE/AppData/Local/Temp/la1s_caudit/ (케이스마다 append)
```

interface 4절 C-1~C-8을 잰다. 전체 test 체계는 0 failed가 합격이고, base에 실패가 남으면 목록을 올리고 판정을 멈춘다. 작성자 보고는 증거로 받지 않는다. 연기 시험 = `common_gate_amplifier`, `two_stage_ota` 선언 E_B 40 + `two_stage_ota` 유도 1회. 회로마다 프로세스, 순차, background, 여유 메모리 2 GB 아래면 중단. 예외나 직전에 없던 정지 사유면 병합 금지로 보고. `eval_budget` 칸의 뜻 갈림과 `residual_probe` 수정을 확인 항목으로 본다. 기록은 '미완료(보류 다리: 변화표 = LA-1 측정 시점, SPICE = OP-5·CL-1)'.

```bash
git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-audit add .ai/verification/20261103-xrunf1c.json && git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261103-xrunf1c-audit commit -m "audit(card C): 판정 기록" --trailer "Role: audit" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"
```
