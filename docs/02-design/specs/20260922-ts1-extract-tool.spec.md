---
id: 20260922-ts1-extract-tool
phase: 1
evidence_type: red-green
gate_change: no
---
## 의도

TS1(계획 N3.11)의 선행 도구. 인라인 self-test 블록(`if __name__ == "__main__":`)을 본문 그대로 `tests/legacy/`로 옮기고,
섹션 목록을 만들고, 소스에 인라인 self-test가 남았는지 재는 명령행 도구 `tools/migrate/extract_selftest.py`를 만든다.
정본 명세는 design `10-test-separation` v1.2 §5.1(섹션 경계·범주 규칙)·§5.2(명령·출력·exit code)이다 -- 이 card는 그것을 인용한다.
이 card 병합 커밋이 C2(TS1 이관)의 base가 된다.

## 관찰 가능한 계약

design §5.2 그대로. 요약:

1. `extract --source <모듈.py> --module <import 이름> --out <파일>`: 블록이 정확히 하나일 때 머리글(§5.2-5) + 블록 원문(`if __name__` 줄부터 블록 끝까지 줄 단위 그대로, 유일한 치환은 `<X>.path.dirname(<X>.path.abspath(__file__))` 조각 → `_ASSETS_DIR`)을 UTF-8·BOM 없음·LF로 쓴다. 블록 안에서 읽히고 저장되지 않는 비내장 이름 중 원본 모듈 최상위에서 묶이는 이름을 `from <module> import (<정렬된 이름>)` 한 줄로 가져온다(§5.2-3). 같은 입력이면 같은 바이트. exit 0.
2. `sections --source <.py> --out <json>`: §5.1 규칙의 섹션 목록 JSON(필드 §5.2 `sections` 목록).
3. `scan --root <디렉터리> [--out <json>]`: `<디렉터리>/*.py`(하위 제외)마다 블록과 인라인 self-test 여부 JSON. 인라인 self-test(범주 A 또는 B 섹션이 1개 이상인 블록)가 하나라도 있으면 exit 1, 없으면 0.
4. exit code: 0 성공 / 1 scan 발견 / 2 입력 오류(파일 없음, 블록 0개 또는 2개 이상, 파싱 실패) / 3 미해결 이름(목록 출력) / 4 지원하지 않는 구성(§5.2-2의 `__file__` 꼴 밖, `globals`·`locals`·`eval`·`exec`·`__import__` 호출, 원본이 `_ASSETS_DIR`을 이미 씀).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `tools.migrate.extract_selftest` | `*` | `(명령행 도구 -- 계약은 CLI, design §5.2)` |

## 판정 유형 근거

red-green. 도구가 없는 base에서 test가 실패하고(명령 실행 실패), 병합본에서 통과한다(design §9 C1).

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 입력: test가 작은 합성 모듈(블록 하나, 모듈 최상위 이름을 읽는 블록, `__file__` 꼴, 금지 호출, 블록 0·2개, 대·소 표지와 범주 A·B·C·D 섹션)을 만들고, 기대 출력(이관본 텍스트·섹션 목록·exit code)을 design §5.1·§5.2 문장에서 직접 정한다. 피검 도구 출력으로 기대값을 만들지 않는다. 실제 엔진 모듈에 대한 동등성은 C2(equivalence)의 몫이다.

## 거부해야 할 입력

블록 0개·2개 이상(exit 2), 없는 파일(exit 2), 미해결 이름(exit 3), `__file__`의 다른 꼴·`globals()`·`eval` 등(exit 4), 원본이 `_ASSETS_DIR`을 이미 씀(exit 4).

## library 회로 적용 여부

해당 없음(도구, 엔진·회로 선언 무관).

## 무동작 판정 입력(무발동 값)

해당 없음. `scan`에 인라인 self-test가 없는 디렉터리를 주면 exit 0.

## 재현할 수치

없음.

## 결정 필요 항목

없음.
