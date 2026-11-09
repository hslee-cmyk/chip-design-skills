# UB-1 + NL-1 브리핑 (20261104-ub1-nl1)

## 공통

- 카드: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/ub1/20261104-ub1-nl1.spec.md`, `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/ub1/20261104-ub1-nl1.interface.md`
- 공통 브리핑: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md`
- 원칙: `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/CLAUDE.md` 33원칙, `C:/Users/HSLEE/Documents/Todoc/fpga/CLAUDE.md` '★graph 단일 정본'
- design: 41 §2.5(v1.16.4), 40 §3.8-2·§3.11-6 E-01·E-16, 42 D-UB1·D-GATE. S1 (가)·G1~G7 = 위임 A-35·A-36.
- 저장소: `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`. git은 `git -C <절대 경로>`. master 직접 커밋·reset·checkout·stash·push 금지.
- Bash: 맨 위 `set -e`는 동작하지 않는다. 순서가 중요한 명령은 `&&`로 잇거나 `bash -c 'set -e; ...'`로 돌린다. 파이프는 실패를 가리니 쓰지 않거나 pipefail을 건다. 경로는 절대 경로만 쓰고 `cd`에 기대지 않는다.
- Python: `C:\Python314\python.exe`, `PYTHONIOENCODING=utf-8`. LUT·13회로 실행 금지(측정은 LA-1 시점). 보고는 한글로 짧게.

착수 전제: design v1.16.4 master 병합. base에 IT-2c가 없으면 `_helpers_nodal` 겹침을 보고에 표지한다.

## test (`gmid-test-author`, sonnet)

- worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/ub1-test`, 브랜치 `role/test/20261104-ub1-nl1`. 임시 경로 `C:/Users/HSLEE/AppData/Local/Temp/la1s_ub1_test/`.
- 입력: interface card만. 엔진 소스 열람 금지. tests 안 helper는 읽어도 된다.
- 할 일: interface T-1~T-13(T-4f·T-5d·T-5e·T-10a·T-10b·T-12a 포함)와 '바뀌는 기존 test'. 함수 접두 `_ub1_`, 새 test 파일 0. 기대값은 닫힌 식과 `H.ref_solve`만 쓴다. 피검 함수로 기대값을 만들지 않는다.
- red: base 열을 base에서 재고 보고한다. 새 키워드 `TypeError`는 red로 세지 않는다. 허용 예외 = `AssertionError`, `Failed`, 신규 심볼의 `ImportError`·`ModuleNotFoundError`·`AttributeError`. `except Exception: pytest.fail` 금지.
- 커밋 `Role: test`. 끝나면 test 커밋, red 표, 애매한 계약을 보고한다. 해석이 갈리면 멈추고 보고한다.

## code (`gmid-code-author`, sonnet)

- worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/ub1-code`, 브랜치 `role/code/20261104-ub1-nl1`. 임시 경로 `C:/Users/HSLEE/AppData/Local/Temp/la1s_ub1_code/`.
- **엔진 읽기는 재작성 범위(지울 코드·소비자)로만(원칙 8).** as-built 구조·이름은 근거가 아니다. 계획·design과 다르면 as-built로 정하지 말고 멈추고 보고한다.
- 커밋 순서: (1) NL-1 `limit_matrix`·`capacitance_matrix`·`nodal_factor` 전 호출 자리 (2) `block_stamp_matrix` + `block_local_gain`·`block_gain_model_of`·`row_gains`·구조 칸 (3) E-01 (4) E-16 + `stage_b` `load_note`.
- graph 규칙: 새 필드·cache·memo·`sctx` 슬롯·값 칸 0(interface 표의 칸만). 옛 코드는 같은 변경에서 삭제한다(`_select`, attach 규칙, 조용한 `continue`, 'floating = 0 V'). `E/metrics/CONTRACT.md`, function-registry, `E/_module_map.py` 문언을 함께 고친다.
- 회로·소자 이름, 새 상수 0. 분기 없는 단자 스탬프. 전회로 C는 전하 넷이 있을 때만 조립한다.
- test가 틀렸다고 보면 고치지 말고 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/ub1-code/docs/02-design/disputes/20261104-ub1-nl1.md`에 쓰고 멈춘다. 기대값·기준선을 건드리지 않는다. 매 변경 뒤 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/ub1-code/skills/analog-gmid-design/gmid_engine/tests/` 전체를 돌린다.

## audit (`gmid-verification-auditor`, sonnet)

- worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/ub1-audit`, 브랜치 `role/audit/20261104-ub1-nl1`. 임시 경로 `C:/Users/HSLEE/AppData/Local/Temp/la1s_ub1_audit/`. 격리 복제본 안에서만 실행하고 끝나면 reflog·status를 확인한다.
- freeze(순서 3): test 커밋·base 확인, base red 재현, 허용 예외 타입 확인.
- 병합본 판정(순서 6): interface '판정 측정 (audit)' A-1~A-7과 보류 행, 판정 기록 `.ai/verification/20261104-ub1-nl1.json`. 작성자 보고는 증거가 아니다.
- 추가: **graph 규칙 위반 여부를 별도 항목으로**, G-10 계수, 블록 안 재계산(cProfile·중복 인자), tests/structure A~I, 회로 이름 0, 상수 0.
- 근거 재대조: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/ub1/ub0_code_compare.md` §1·§4. 판정 소비자가 나오면 멈춘다.
- 보류 다리는 **통과로 세지 않는다**. 판정 기록에 base sha를 적는다.
- 봉인 불변식: 이 card가 DC writer를 안 건드리는지 코드 경로로 확인하고 실측은 보류로 표지한다.
