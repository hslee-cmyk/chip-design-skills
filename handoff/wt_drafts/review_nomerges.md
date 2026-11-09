# 독립 검증: `--no-merges` 제거 2건 (b26_1 engine_since, n63_p3/n63_check merge_class)

검증자: 작성자가 아닌 독립 agent. 2026-10-06. 모래상자는 C:/g353 하나만 썼고(TMP/TEMP도 그 아래), `cd`는 쓰지 않았다. 복제는 `git clone -c core.autocrlf=false --no-local`로 했다.
실제 저장소는 읽기만 했다. 시작 때와 끝날 때 `count-objects -v`와 `for-each-ref`가 같았다.
git 2.52.0.windows.1에서 `merge-tree --write-tree --no-messages`가 동작했다(아래 C 시나리오에서 rc=1 충돌 경로까지 실행됨).

## 판정 요약
- **B(차단): 없음**
- **S(중대): 없음**
- **minor 4건**: m1(n63_check 임시 객체 디렉터리 누수), m2(b26_1 주석이 실제 동작과 다름), m3(merge-tree가 복제본 객체의 mtime을 갱신함), m4(이전부터 있던 history simplification 사각지대)

## 1. 실제 범위: 변경 전후 동일
| 대상 | 범위 | old와 new 비교 |
|---|---|---|
| n63_p3 phase 2 | 5f643a9 / da03c0e | 새 키 `merges_clean: []`가 붙은 것 말고는 JSON 전체가 같음(n=31, ok) |
| n63_p3 phase 3 | 6c724de / 5f643a9 | 같음(n=2, ok). obs_tools_gates도 같음 |
| n63_p3 phase 3 | 6c724de / da03c0e | 같음(n=33, bad 31건이 old와 한 건도 다르지 않음) |
| n63_check | H=5f643a9, H=6c724de | 같음(n=31 / n=33, bad 목록 같음) |
| b26_1 engine_since | 7535799..6c724de | 출력 6줄이 같음(커밋 4개 2eb7e55·a410f31·2eb7e55·6bf510b, rc=0) |

실제 범위의 gate merge 5개(c851e54 등)는 엔진 pathspec에서 모두 한 부모와 TREESAME이라 rev-list에서 빠진다. 그래서 `merges_clean`이 빈 목록이다.
결과적으로 merge_class 경로는 실제 데이터에서 한 번도 실행되지 않았고, 아래 합성 시나리오가 이 경로의 유일한 실측 증거다.
real gate merge 5개는 모두 trailer `Change-Id: <card id>`를 달고 있다.

## 2. 합성 시나리오 (복제본 C:/g353/syn, 6c724de 위에 브랜치를 만들고 SD=stick_diagram.py 사용)
Change-Id는 p9-kcl-edges를 썼다. 이 id는 ALLOW_SD와 EXPECT16에 모두 들어 있다. 표의 n63 값은 old 대비 늘어난 항목만 적었다.

| 시나리오 | n63_check / n63_p3 (new) | old | b26_1 new | b26_1 old |
|---|---|---|---|---|
| A: 보통 --no-ff, 두 부모 모두 SD 수정, merge trailer Role doc + Change-Id p9 | `clean`, merges_clean=[eb8bcf4], bad 증가 0 | bad 같음 | merge가 목록에 나오고 Change-Id가 허용 목록에 있어 **통과** rc=0 | 통과 |
| A2: A와 같지만 merge에 trailer 없음 | `clean`, bad 증가 0 (거짓 멈춤 없음) | 같음 | **멈춤** rc=1 (Change-Id '') | 통과 |
| B: A에 merge에서만 한 SD 수정을 더함(evil), Change-Id 허용 | `evil` → bad에 추가(merge_only_paths=SD) | 놓침 | 통과(허용 Change-Id) | 통과 |
| B2: 두 부모 모두 엔진 미수정, merge에서만 SD 수정, Change-Id rogue | `evil` → bad | 놓침(p3 old ok=True) | **멈춤** | 통과(놓침) |
| B3: side만 SD 수정, merge가 SD를 더 수정, Change-Id rogue | `evil` → bad | 놓침 | **멈춤** | 통과(놓침) |
| C: 같은 줄 충돌을 제3의 내용으로 해결 | `evil` + "(충돌 병합)/(conflicted merge)" → bad | 놓침 | 통과(허용 Change-Id) | 통과 |
| C2: 충돌을 side 내용 그대로 해결(merge = p2와 TREESAME), main 쪽 rogue 커밋 | merge와 rogue 커밋 모두 목록에 없음 | old도 같음 | rogue 커밋이 보이지 않음 | old도 같음 → m4 |
| D: octopus(부모 4), clean 자동 병합 | `evil (부모 4개)` → bad (보수적, docstring에 적힌 대로) | 놓침 | merge가 나오고 Change-Id 허용 → 통과 | 통과 |
| E: side만 SD 수정(merge = p2와 TREESAME) | merge가 나오지 않음, side 커밋은 그대로 대조됨 | 같음 | 같음 | 같음 |

- 거짓 멈춤: 보통 gate merge에서 n63 두 스크립트 모두 0건이다(A, A2). b26_1도 card의 Change-Id가 달린 gate merge(A)는 통과한다.
- b26_1에서 trailer가 없는 보통 merge(A2)는 멈춘다. 지나치는 게 아니라 멈추는 방향이라 보수적이다. 실제 gate merge 5/5가 Change-Id를 달고 있으므로 운용상 문제는 없다고 본다.
- evil merge는 B, B2, B3, C에서 n63 new가 모두 잡았다. b26_1은 Change-Id 대조만 하므로 Change-Id가 허용 목록 밖인 B2, B3만 잡고, 허용 card의 evil merge(B, C)는 통과시킨다. 이것은 설계 범위("허용 Change-Id merge 통과") 안에 있다.

## 3. 임시 객체와 저장소 쓰기
- 복제본 syn의 `count-objects -v`는 합성 실행 전후 모두 count 178, in-pack 7282로 같았다. merge-tree 객체가 저장소에 들어가지 않았다.
- iso(실제 범위)는 실행 뒤에도 loose 0이고, pack mtime은 clone 시각 그대로였다.
- 실제 저장소: count-objects와 refs가 시작/끝에서 같았다.
- **m1 (n63_check.py)**: `atexit.register(shutil.rmtree, _OBJDIR, True)`가 Windows에서 읽기 전용(0444) loose 객체를 지우지 못한다. ignore_errors=True라서 조용히 실패하고 `n63_objs_*`가 TMP에 남는다.
  - 재현: 충돌 merge sc_C에서 2회 모두 남았다. 새 객체가 생기지 않는 sc_B에서는 남지 않았다. 직접 `shutil.rmtree(p, True)`를 실행해도 디렉터리가 남는 것을 확인했다.
  - n63_p3.py는 `tempfile.TemporaryDirectory`를 쓰므로(읽기 전용 처리 포함) 누수가 없었다.
  - 수정 제안: `TemporaryDirectory`를 쓰거나 `shutil.rmtree(..., onexc=chmod 후 재시도)`로 바꾼다. 저장소 쓰기는 아니고 TMP 누수다.
- **m3**: merge-tree가 이미 있는 객체를 다시 쓰려고 하면 git이 alternate(복제본 .git/objects)의 그 객체 mtime을 갱신(freshen)한다.
  - 실측: syn에서 sc_A의 tree 4개를 포함해 loose 17개의 mtime이 실행 중 바뀌었다. 내용과 개수는 그대로였다.
  - 두 docstring의 "복제본 .git은 그대로(the clone's .git is not written)"는 내용 기준으로는 맞지만 mtime 기준으로는 틀리다. 실제 저장소에서 직접 실행하는 일은 없으므로 영향은 없다. 문구만 고치면 된다.

## 4. 기타
- **m2 (b26_1_launch.sh 132행 주석)**: 주석은 "어느 부모와도 같지 않은 merge(evil merge)만 남기고 보통 merge는 거른다"고 적었다. 그런데 시나리오 A의 보통 merge(두 부모 모두 경로 수정, 자동 병합 clean)도 남는다(eb8bcf4가 목록에 나옴). 이 merge는 Change-Id로 통과하므로 동작은 맞고, 주석만 부정확하다.
- **m4 (이전부터 있던 사각지대, 이번 변경과 무관)**: merge가 한 부모와 TREESAME이 되도록 충돌을 해결하면(C2), 기본 simplification이 그 부모만 따라간다. 그래서 반대편 커밋(rogue Change-Id)이 old와 new 모두에서 보이지 않는다. 그 커밋의 내용은 H에 없으므로 "엔진 내용 변경" 관점에서는 무해하다. "카드 밖 커밋 0" 문장을 커밋 단위로 엄격하게 읽으면 빈틈이다.
- n63_p3에서 evil merge는 trailer와 상관없이 bad(`not k`)다. docstring의 "trailer 없으면 bad"보다 엄격하지만, 코드 주석("역할 커밋은 merge가 아니므로")과는 일치한다.

## 사용한 산출물 (모래상자, 삭제 예정)
C:/g353/run_real.sh, run_syn.sh, build_syn.sh, run_es.sh(engine_since를 sed로 그대로 추출), cmp_real.py, out/*.json·log. 끝나면 C:/g353 전체를 삭제한다.
