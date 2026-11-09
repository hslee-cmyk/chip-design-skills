# B41 -- `save_instance_json` V3 면제 4개(unbound) 분석과 선택지

측정 기준: gate master `36e170e`(면제 묶기 card 병합본 `5a602d4` 위 문서 커밋 둘). 저장소 무변경, 측정은 격리 복제본 `C:/g211/repo`(`36e170e`, origin 없음)와
`C:/g211/repoB`(`b29be01` + 스크래치 커밋)에서만. 도구 = 그 복제본의 `tools/gates/mutate_changed.py`(gate master 판, 사본 `C:/g211/gate`).
스크립트: `_drafts/b41_kit/`(`b41_measure.py`·`b41_kill.py`·`b41_run_a.sh`·`b41_run_a2.sh`·`b41_run_b.sh`, test 초안 `test_instance_scope_note.py`), 로그 `b41_kit/run_*.log`, 결과 사본 `b41_kit/{measure,kill_existing,kill_new,v3_e2e}.jsonl`·`v3_e2e.verdict.json`·`e2e.meta.txt`(`C:/g211`은 측정 뒤 삭제, 저장소 HEAD `36e170e`·status 시작과 같음).
(`b41_run_a.sh` 1차의 kill 단계는 pytest에 `--gmid-phase`와 `APPDATA`가 빠져 기준 실행 ERROR -- 고친 `b41_run_a2.sh`로 그 단계만 다시 돌았다. 측정 1단계 값은 1차 그대로.)

## 1. 네 변이가 하는 일

`save_instance_json`(SD `36e170e` 8973~9024행, 변이 14개). 본문: `body[0]` docstring, `body[1]` `data = {...}`, **`body[2]` `if pipeline_result.get('scope_note'): data['scope_note'] = pipeline_result['scope_note']`**,
`body[3]`~`body[5]` IC3 완전성 재검증, **`body[6]` `with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)`**.

| 변이 id(접두 `stick_diagram:save_instance_json:`) | 원문 → 변이 | 효과 |
|---|---|---|
| `stmt_delete:body[2]` | `if pipeline_result.get('scope_note'): …` → `pass` | `scope_note`를 넣어도 파일에 안 쓴다 |
| `stmt_delete:body[2].body[0]` | `data['scope_note'] = pipeline_result['scope_note']` → `pass` | 같음 |
| `const+:body[6].body[0].value.keywords[0].value` | `indent=2` → `3` | 파일 바이트만 다름 |
| `const-:body[6].body[0].value.keywords[0].value` | `indent=2` → `1` | 파일 바이트만 다름 |

네 id는 `070cf69`(DF-36 base)·`b29be01`(DF-36 병합)·`36e170e`에서 모두 같은 문장을 가리킨다(`measure.jsonl`).

### 1.1 scope_note 2개 -- 등가 아님, test로 죽는다

선언: docstring "`pipeline_result`에 `scope_note`(str)를 선택적으로 넣으면 그대로 옮겨 쓴다"(+ design 10 IC3 §5.5 선택 키). 지금 test 중 `scope_note`를 넣어 저장하는 것이 없다
(`test_ic3` `_OPTIONAL_TOP`은 손으로 만든 instance dict의 완전성 판정용, `save_instance_json`을 부르지 않음). 운영 경로(`workspaces/run_harness.py`)도 `scope_note`를 넣지 않고,
추적 instance.json 4개(`workspaces/*/…instance.json`)에도 키가 없다 -- 즉 기존 test 공백(백로그 B8 (5)와 같은 것)이다.

### 1.2 indent ±1 2개 -- 등가(파싱 결과 동일, 선언된 바이트 형식 없음)

실측(`b41_measure.py`, `36e170e` 작업 트리, library 회로 9개 전부 -- `run_topology_pipeline` + 다섯 필드 sizing + `scope_note`, 원본 def와 변이 def를 같은 입력으로 실행):
* 파싱 결과(정렬 직렬화 sha256): 9/9 회로에서 원본 = `const+` = `const-`.
* 파일 바이트: 9/9 회로에서 셋 모두 다름(예: `folded_cascode` 13,933 / 15,631 / 12,235 바이트, 파일럿 70,932 / 78,660 / 63,204).

바이트 차이를 보는 곳이 있는가:
* **E-INST**(`docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`, df36 판도 같음): `file_bytes_sha256`·`file_bytes_masked_sha256`를 **기록은 하지만**
  판정은 design 30 §10 E5 블록(1072~1073행)·E5 행(1112행)대로 파싱 해시(`field_sha256`·`raw_sha256` -- 이름과 달리 `json.loads` 뒤 정렬 직렬화 해시 -- ·`without_topology_ref_sha256`)만 비교한다.
  design 30에 `file_bytes` 언급 0건. 그리고 E-INST는 pytest가 아니라 V3 인벤토리가 아니므로 어차피 변이를 죽이지 못한다.
* **소비자**: `design_report.py`·`build_html.py`·test 모두 `json.load`로 읽는다.
* **선언**: instance.json의 들여쓰기·바이트 형식을 정한 문서 0건(`indent=2`는 C8 승인 범위 설명·면제 묶기 spec의 변이 묘사에만 나온다).
* **관찰 가능한 유일한 차이**: 하네스를 다시 돌리면 추적 파일 `workspaces/{current-reuse-telescopic-ota,folded-cascode,nmcnr-amplifier,two-stage-ota}-report/*.instance.json`이
  git diff로 바뀐다(지금 HEAD 내용은 indent 2). 이것을 계약으로 삼으려면 '바이트 형식 = indent 2' 선언이 먼저 있어야 한다 -- 지금은 없다.

판단: 선언된 계약 기준으로 등가. test로 죽이려면 없는 형식 계약을 새로 만들어야 하므로(원칙 '상수를 임의로 만들지 마라') test 대상 아님.

## 2. test 계약 초안과 kill 증명

초안 `_drafts/b41_kit/test_instance_scope_note.py`(test-only, 목적지 `skills/analog-gmid-design/assets/tests/contracts/`; 같은 이름 파일 없음):
* **S1** `pipeline_result["scope_note"]`가 비지 않은 문자열이면 쓴 파일 최상위 `scope_note`가 그 문자열과 같다. 기대값 = test가 만든 문자열 `f"부분 범위: {name} -- cells 1/3 (b41)"`(oracle (a)).
* **S2** 키를 넣지 않으면 파일에 `scope_note` 키가 없다(oracle (d) 선택 키). B41 변이를 죽이는 몫은 S1뿐이고 S2는 '항상 쓰는' 반대 방향 회귀를 막는다(빼도 B41 해소에는 지장 없음).
* 입력 = `test_df36_instance_relpath.py`와 같은 공개 경로(library topology → `run_topology_pipeline`, 소자마다 다섯 필드 sizing), library 회로 전부로 parametrize(회로 이름 0). 18 test, 3.5초.

kill 증명(`b41_run_a2.sh`, `36e170e` 복제본, 변이를 도구의 `mutants`·`_replace_def`로 넣고 test만 실행, `--gmid-phase=3 --gmid-strict=`):

| 실행 test | 기준 | `stmt_delete:body[2]` | `stmt_delete:body[2].body[0]` | `const+` indent | `const-` indent |
|---|---|---|---|---|---|
| 기존 대표(test_df36 전체·test_ic3 전체·test_s088) | 42 passed | 생존 | 생존 | 생존 | 생존 |
| 새 test 초안만 | 18 passed | **죽음**(1 failed) | **죽음**(1 failed) | 생존 | 생존 |

전체 도구 실행(p10과 같은 범위, `b41_run_b.sh`): 스크래치 복제본 `C:/g211/repoB`에서 `b29be01` + 새 test + 가상 승인 기록(indent 2개를 `@4a96ecf0…`로 묶음,
`target_kind: decision`) 커밋 `10c3e8d`을 만들고, gate master 도구로 `mutate_changed.py --base 070cf69 --head 10c3e8d --gmid-phase=2 --gmid-strict=` 실행 →
**exit 0 `PASS`, mutants 26, killed 24, exempt 2(indent 둘, `bind_hash` 4a96ecf0…), survivors 0**, `exempt_ignored` = C8 기록의 scope_note 두 원소 `unbound`(죽었으므로 무해), 533초.
p10(같은 범위, 새 test 없음) = FAIL·killed 22·생존 4와 비교하면 차이는 정확히 이 4개다.

## 3. 묶기 해시(`<id>@<hash>`)

도구 `bind_hash`(gate master 판) 값:

| 판 | `save_instance_json` 묶기 해시 | ① def 해시 |
|---|---|---|
| `070cf69`(DF-36 base, C8 형태) | `1dbcaa2d28611cac47116101d780dc40f997b913472497508f0b717ac5ac8100` | `9cb09766…` |
| `b29be01`(DF-36 병합) = `36e170e`(gate master) | **`4a96ecf0e82205e0828ea62f88e187b83a1096d557a97ae0b410b9f3cce2ceee`** | `11a55c19…` |

indent 2개의 묶인 원소(승인 기록 `target:` 줄 그대로):
```
stick_diagram:save_instance_json:const+:body[6].body[0].value.keywords[0].value@4a96ecf0e82205e0828ea62f88e187b83a1096d557a97ae0b410b9f3cce2ceee, stick_diagram:save_instance_json:const-:body[6].body[0].value.keywords[0].value@4a96ecf0e82205e0828ea62f88e187b83a1096d557a97ae0b410b9f3cce2ceee
```
(넷 모두 묶는 안이면 같은 `@4a96ecf0…`를 `stmt_delete:body[2]`·`stmt_delete:body[2].body[0]`에도 붙인다.)

**중요한 한계(도구 정의에서 바로 나온다)**: V3 대상 = ① 해시(docstring 제외)가 base와 다른 def. ① 해시가 다르면 docstring 포함 전체 `ast.dump`인 묶기 해시도 반드시 다르다.
그러므로 `@4a96ecf0…` 원소가 적용되는 V3 실행은 **head의 `save_instance_json`이 지금과 같고 base가 그 이전 형태인 범위** -- 실제로는 DF-36 범위(`070cf69 → b29be01`) 재측정(p10)뿐이다.
`save_instance_json`을 **바꾸는** 앞으로의 card에서는 head 해시가 달라 이 원소가 적용되지 않는다 -- 그 card가 자기 head 해시로 다시 승인받아야 한다
(design 30 497행 B26-1 사례와 같은 논리: "그 def를 바꾸는 뒤 card는 … def 해시가 달라져 면제가 어차피 무효"). 지금 묶는 면제는 '미래 card 대비'가 아니라 'DF-36 재측정 PASS'용이다.
반면 test는 해시와 무관하게 앞으로의 모든 card에서 scope_note 변이 2개를 죽인다.

## 4. 어느 card가 언제 이 변이를 대상으로 삼는가

* **확정 순서**(design 30 §8.1 626~651행): 범위 정책(35) → B34 → b26pre → backfill → B26-1 → B33 → G1 → T0·FU·D0a·D0b → M1~M10 → F1 → F2.
  `_drafts`의 B34·b26pre·backfill·B26-1·G1·D0b 초안 중 `save_instance_json` 본문을 바꾸는 것 0건(D0b R-A4의 `_p3rd_probe` 인자는 합성 red 시나리오, B26-1 'leak2 4/4 적중'은
  head에 id가 존재한다는 측정이지 대상이라는 뜻이 아님). → **확정 순서 안에서 B41 변이를 V3 대상으로 삼는 card 없음.**
* **Phase 3 이동**: N3.10이 `save_instance_json`을 MOD9(`instance_report_builder.py`)로 보낸다. G1 이동 인식으로 옮긴 def는 V3 대상이 아니고(E2 ① 변이 0), 옮긴 뒤 변이 id 접두가
  `instance_report_builder:`로 바뀌어 `stick_diagram:` 원소(묶였든 아니든)는 더 이상 맞지 않는다(design 30 380행 D-21과 같은 결론).
* **범위 정책(35) 병합 뒤**(다음 card): 해시가 바뀐 기존 def에서 바뀐 문장·감싸는 제어문·삭제 지점 바로 뒤·같은 블록에서 바뀐 이름을 읽는 문장·바뀐 매개변수를 읽는 문장·`early_return`만 대상.
  정적 판단(이 본문 구조 기준): `body[1]` `data` dict만 바꾸면 `data`를 읽는 같은 블록 문장은 `body[4]`뿐이라 네 변이 모두 대상 밖. **대상이 되는 경우** = scope_note 분기 자체를 고침,
  `pipeline_result` 매개변수 변경(T3 -- 분기 2개), `with` 블록 안(`json.dump` 줄이나 그 앞 문장 삭제·`data`를 바꾸는 새 문장)을 고침(indent 2개).
* **후보**(Phase 3 뒤): Phase 4 CC-4(IC3 거부 `ValueError`를 실패 클래스로 -- `body[5]`만이면 대상 밖), CC-8(무동작 도구), DEC-77 front 저장(MOD9 목적 문구 "front 점 목록·선택 점·선택 근거를 저장",
  Phase 7b 이후로 보임 -- `data` 키 추가면 대상 밖, 쓰기 방식 변경이면 indent 대상). 어느 것도 초안이 없어 확정 아님.
* **결론 -- 해소 시한**: 강제 시한 없음. 늦어도 'MOD9의 `save_instance_json` 본문(scope_note 분기·`with`/`json.dump`)을 바꾸는 첫 card의 spec card 작성 전'.
  그때 scope_note 2개는 test가 없으면 V3 FAIL, indent 2개는 그 card 승인에서 그 card head 해시로 묶어야 한다(지금 묶어 둘 수 없음 -- §3).
  p10 기록(DF-36 범위 재측정 FAIL, 생존 4)은 지금 그대로 남는다.

## 5. 사용자 질문(초안)

**[B41] DF-36 면제 4개(`save_instance_json`) 처리**

사실:
1. 면제 묶기 card 병합(`5a602d4`, gate master `36e170e`)으로 C8 승인 `20260922-ic3-v3-exempt`의 `save_instance_json` 원소 4개는 해시가 없어 적용되지 않는다.
   병합본 도구로 DF-36 범위를 다시 재면 26 중 22 죽음·**생존 4 = 이 4개**(판정 기록 `20260930-v3-exempt-binding` p10, 1014초).
2. 둘(`scope_note` 복사 문장 삭제)은 **등가가 아니다** -- docstring이 약속한 기능인데 그것을 부르는 test가 없다. test 초안(library 9회로 × 2계약, 18 test·3.5초)이
   두 변이를 죽이고 기존 test 42개로는 넷 다 산다(격리 복제본 실측).
3. 둘(`json.dump` `indent=2` → 3/1)은 **등가다** -- 9/9 회로에서 파싱 결과 같고 바이트만 다르다(`folded_cascode` 13,933 → 15,631/12,235). E-INST 판정·보고서·test는 모두 파싱 값을 본다.
   바이트 형식 선언은 없다(달라지는 것은 하네스 재실행 때 추적 instance.json 4개의 git diff뿐).
4. 지금 묶을 수 있는 해시는 `4a96ecf0…`(현재 `save_instance_json`) 하나다. 이 해시는 그 함수가 바뀌면 같이 바뀌므로, 지금 묶은 면제는 **DF-36 범위 재측정에만** 적용되고 앞으로
   그 함수를 고치는 card에는 적용되지 않는다(그 card가 자기 해시로 다시 승인받는다).
5. 확정 순서(35 → B34 → … → Phase 3 F2) 안에 이 변이들을 V3 대상으로 삼는 card는 없다. Phase 3에서 함수가 MOD9로 옮겨지면 id 접두가 바뀐다. 범위 정책(35) 뒤에는 그 문장 근처를
   고치는 card만 대상으로 삼는다.

선택지:
* **(가) test card + indent 2개 묶인 면제 (Recommended)** -- test-only card 1개(초안 그대로, 판정 증거 = 변이 2개 kill 재현)로 B8 (5) 공백을 영구히 메우고,
  indent 2개는 '등가' decision 승인 기록에 `@4a96ecf0…`로 묶는다. 효과: DF-36 범위 재측정 생존 0(아래 실측), 앞으로 scope_note 분기를 고치는 card가 V3에서 막히지 않음.
  격리 복제본 실측: 이 조합으로 DF-36 범위 V3 = PASS, 26 중 killed 24·exempt 2·생존 0(533초).
  indent 등가 근거(사실 3)는 그 기록에 남아 뒤 card가 자기 해시로 다시 묶을 때 인용한다. 비용: card 1개(test 커밋·auditor) + 승인 기록 1개.
* **(나) 4개 모두 묶인 면제** -- decision 승인 기록 1개(`@4a96ecf0…` 4원소). DF-36 재측정은 생존 0이 되지만 scope_note test 공백은 남고, 그 분기를 고치는 card는 test를 그때 보강하거나 등가가 아닌
  변이를 다시 면제받아야 한다(사실 2 -- 등가 아닌 변이를 면제하는 셈).
* **(다) 그대로 둠** -- 확정 순서상 필요한 card가 없다. p10 기록(생존 4)을 그대로 두고, `save_instance_json`(MOD9) 본문을 고치는 첫 card의 spec card 작성 때 (가)의 test를 그 card의 test에
  넣고 indent는 그 card 승인에서 묶는다. 비용 0, 대신 B41이 그때까지 열린 채 남는다.
* (참고, 권하지 않음) **(라) 바이트 형식 계약** -- 'instance.json = indent 2' 를 선언하고 바이트 test로 indent 변이까지 죽인다. 지금 그 형식을 쓰는 소비자가 없어 새 계약을 만드는 일이다.
