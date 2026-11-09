# GL-1 독립 판정 (2026-11-04)

대상: `design/gl1` `5641364b`(40 §2.4.10·§10.4, 42 D-GL1), `wt/_drafts/evidence/2026-11-03/gl1/spec_card_draft.md`·`interface_card_draft.md`·`briefs.md`(관련 줄), 계획 N6.37·N6.3(master `7620f5ee`), 위임 A-28.

방법: 원 파일 읽기와 `git grep`만. 엔진 실행·측정 없음. 엔진·검사기 인용은 재작성 범위와 lint 대상 구문 확인뿐이다(원칙 8). 시제품 값은 작성자 측정(`facts_master_summary.txt`)을 agent 인용으로 읽었다.

## Major

**G1. 복사 등록부 면제가 G 확장 lint에 구멍을 낸다** (공허한 게이트, 문서 충돌)

- design 40 §2.4.10은 허용 모듈 목록을 '고정, 이 밖은 예외 없음'으로 적었고, interface §1도 허용 모듈 밖 예외를 두지 않는다. 그런데 spec card 재작성 범위 표('`copy_audit` 면제 재사용')와 `briefs.md`:54('copy_audit 면제')는 코드 주체에게 그 면제를 재사용하라고 시킨다.
- 그 면제는 등록된 정의 안의 규칙 D·E·G 위반을 건너뛴다(`structure_checks.py` `check_g`, `tests/structure/README.md`:100). master에 `layout/_copy_manifest.py`(199줄)가 있다.
- 결과 셋:
  - 등록된 복사 정의의 위반이 기준선에 안 든다. design이 걸린다고 적은 `layout/euler_graph.py`·`mirror_trail.py` `default_factory`, `layout/_helpers_alias.py` `cached_property`가 그 후보다. 등록 여부는 줄 단위로 대조하지 않았다.
  - 등록부에 정의를 올리면 G-8 위반을 면제받는 길이 남는다.
  - test 주체는 interface만 보고 픽스처에 등록부가 없어 toy가 전부 green이다. 그래서 어느 test도 이 차이를 잡지 못한다.
- **고칠 문언**
  - spec card 재작성 범위 표: '기존 `_mutable_value`, `_module_level`, `engine_files` 재사용. `copy_audit` 면제는 적용하지 않는다(design 40 §2.4.10 '이 밖은 예외 없음'). `check_g` 변경 0.'
  - `briefs.md`:54: 재사용 목록에서 'copy_audit 면제'를 지우고 '복사 등록부 면제 적용 금지'를 더한다.
  - interface §1.2 끝: '복사 등록부(`_copy_manifest.py`)에 등록된 정의도 면제하지 않는다. 규칙 D·E·G의 면제는 `check_g8`·`check_value_types`에 적용되지 않는다. 기존 위반은 기준선에 든다.'
  - interface §5 `rule_g8/bad` 행: '유효한 등록부에 등록된 정의 안의 `default_factory` 한 건 -- 위반으로 나옴(픽스처 꼴 = 기존 `rule_copy`)'.
  - design 40 GL-1 절 *① kind* 끝: '복사 등록부 면제는 적용하지 않는다.'

## 합격 항목

| 점검 | 판정 | 근거 |
|---|---|---|
| 구현 가능성 | 합격 | 허용 모듈 경로는 `core/run_counters.py`·`graft.py` 등 확인한 12개가 master에 있음(`graph_snapshot.py`·`compute_block.py`는 D40 인용). 도구의 `parents[5]` = 저장소 루트로 계산 맞음. `.column`·`.value` 리터럴 형식 실재(291·124자리) |
| `g8_memo_lookup_form` | 공허 아님 | 수신자 grep: `memo.lookup` 16, `memo.lookup_persistent` 6, `*.memo.lookup` 2 = 잡힘. 안 잡히는 `tables.lookup`·`self._lru.lookup`·`codecs.lookup`은 memo 아님 |
| 작성자 ≠ 기준 소유 | 합격 | 검사기 = code, 기대값 = test(소스 안 봄), 기준선 = 판정자, 수 증가 = `criteria_weakened` |
| 래칫 | 합격 | 키에 줄 번호 없음, 기준선 밖 키·수 증가 = `new`, 파일 없음·형식 오류 = 실패, skip·xfail 금지 |
| 엔진 동작 변경 누출 | 없음 | 브랜치 diff = design 문서 둘. card 계약 7 + 판정 1단계에서 `E/` 중 `tests/` 밖 diff 0 아니면 FAIL. `engine_code_fp`의 tests 제외는 함께 확인 |
| 계획 N6.37 | 합격 | 범위 (1)~(4), 완료 (1)~(5), 순서 모두 대응. `tools/` 아래 자리(N6.3 (v)) 맞음 |
| 위임 A-28 | 표지 일치 | R-G1~R-G4의 '원래 취지와 다름'이 spec card에 있음. 재검토 = LA-1 완료 13 |

## Minor (막지 않음, 문언 포함)

- m1. **`stale` 방치**: 줄임을 빠뜨리면 그 수만큼 나중 card가 위반을 되돌려도 `new`가 안 난다. §10.4 줄임 행에 더한다: '판정 기록 `reproduced_numbers`에 판정 커밋 기준 `stale` 수를 적고, 0이 아니면 FAIL.'
- m2. **대상 0 통과**: 진짜 트리 test가 대상 수를 단언하지 않아 검사가 파일을 못 읽어도 위반 0 + 전부 `stale`로 green이 된다. interface §3 진짜 트리 test에 'n_targets ≥ 1 단언'을 더한다.
- m3. **결과 객체 값 칸**: 프로젝트 규칙이 지목한 `EvalResult` 값 칸은 frozen 본문 제외로 ②가 못 잡고, 그 필드 다수가 `object` 주석이라 어차피 못 본다. 맡는 자리 (c) 소유표 대조는 손 판정이다. design ② 제외 문언('frozen dataclass 정의 자체')과 맞고 card도 표지했다. 판정 브리핑에 '`EvalResult`·`SearchFront`·`StageAResult`·`StageBResult`·`Layer0Result` 칸 diff를 (c)에서 본다'를 넣는다. 이름 목록은 프로젝트 규칙 예시이고 새 lint 규칙이 아니다.
- m4. **감사 도구 실효**: 작성자 시제품에서 공유 callee 149개 중 D 147, 감사 B 21개 중 회수 0(A-28 R-G4, agent 인용). 완료 (5)는 toy만 요구해 계획과 어긋나지 않지만, 실제 B 측정은 판정자 손 분류다. 판정 6단계에 '감사 B1~B15 중 도구가 B로 낸 수를 기록(합격 조건 아님, LA-1 완료 13 입력)'을 더한다.
- m5. **`--touching`과 메서드 호출**: `method_calls_unresolved`가 전체 합이라 바꾼 파일의 미해석 수를 볼 수 없다. N6.3 (ii) 범위 판단에 필요하다. `limits.json`에 `method_calls_unresolved_touching`을 더한다(`--touching` 없으면 칸 없음).
- m6. **N6.3 (iv) '선언 버전' 대조**: 인자 잎 표에 없어 그런 자리는 D로 간다. 표지 한 줄만 더한다.
- m7. **우회 가능 꼴**: `object.__setattr__(self, "a", {})`, `from collections import OrderedDict as OD`는 안 잡힌다. 앞의 것은 §2.4.10 ③ SC-a 몫이라 범위 밖이고 card 부록 C에 '만드는 card 없음'으로 이미 표지됐다. 뒤의 것은 '끝 이름' 규칙의 한계로 표지한다.
- m8. **판정자 쓰기 경로**: `g8_baseline.json`은 `.ai/verification` 밖이다. `gmid-verification-auditor` 정의는 판정 기록 중심이라 브리핑이 우선임을 audit 순서 6에 적는다(code agent 브리핑과 같은 꼴).

## 미확인

- `_copy_manifest.py` 등록 정의와 design이 든 위반 자리의 줄 단위 대조. 등록 건수를 세지 않았다. G1 판정은 면제 경로와 문서 충돌만으로 성립한다.
- master 전체 test 현재 상태(card 부록 C도 미측정 표지).
- ⑩ 결정 간 모순 점검은 O-225로 하지 않았다.

쓰기: 이 파일 하나.

verdict: Major 1
