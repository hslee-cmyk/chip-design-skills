---
id: 20260930-df36-instance-relpath
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

계획 DF-36(담당 Phase 4, 순서 DF-35 다음 -- 사용자 지시 2026-09-30 "DF-36도 같이 진행해"로 앞당김): `instance.json`이 `topology_ref`에 topology의 **절대 경로**를 써서
worktree·격리 복제본마다 산출물이 달라지고, 무동작 판정의 비트 동일 비교가 경로 때문에 거짓 FAIL을 낸다(auditor들이 매 card 경로 치환·정규화 우회를 했다).
계획의 고칠 방향대로 **저장소 루트 기준 상대 경로**(`/` 구분)로 저장한다. A = `skills/analog-gmid-design/assets`.

범위: `stick_diagram.save_instance_json`이 **저장하는 값**만 바꾼다. 같은 인자로 파일을 여는 IC3 재검증(`load_topology(topology_json_path)`)은 원래 경로를 그대로 쓴다.
저장소 루트는 엔진 모듈 자신의 위치에서 유도한다(`stick_diagram.py`는 `<루트>/skills/analog-gmid-design/assets/`에 있다). 회로·파일 이름을 읽지 않는 경로 규칙이라 topology 무관.

**저장소 밖 topology는 거부한다**(오케스트레이터 기본안 -- 조용한 기본값 금지 원칙): 저장소 루트 밖 topology로 `save_instance_json`을 부르면 `ValueError`이고 파일을 쓰지
않는다(절대 경로를 조용히 대신 쓰지 않는다). 이로써 판정 경로 밖 스크립트(`workspaces/two-stage-ota-report/check_box_shape*.py`, 옛 smoke 스크립트 -- Temp 아래 topology)가
깨진다 -- 판정 경로 밖이라 U-02 3항과 같은 취급(필요하면 그때 저장소 안 경로로 고친다).

기존 설계 문서 `docs/02-design/features/analog-topology-json-library.design.md:143`의 예시 `"library/folded_cascode.topology.json"`(assets 기준)은 계획서(저장소 루트 기준)와
다르다 -- 계획서가 정본이므로 이 card의 문서 커밋에서 예시를 `skills/analog-gmid-design/assets/library/folded_cascode.topology.json`으로 고친다.
추적된 옛 `*.instance.json` 6개(절대 경로)는 재생성하지 않는다(기준선 변경이라 별도 DEC-40 -- B14와 같은 자리).

## 관찰 가능한 계약

1. 저장소 안 topology로 `save_instance_json(path, topology_json_path, …)`을 부르면, 쓴 파일의 `topology_ref`가 저장소 루트 기준 상대 경로이고 구분자는 `/`만, `./`·`..`·
   역슬래시·드라이브 문자·앞 `/`가 없다(00-common §8.2 `diff_path` 정규화 규칙과 같은 모양). 값은 `<루트>`에 이어 붙이면 그 topology 파일과 같은 실제 파일이다.
2. `topology_json_path`가 절대 경로든 cwd 기준 상대 경로든(같은 파일) 저장값이 같다. 출력 `path` 위치(저장소 밖 tmp 포함)와 무관하다.
3. 같은 입력을 두 다른 체크아웃(메인·worktree·복제본)에서 저장하면 `topology_ref`가 같다(경로 누출 없음 -- 00-common §11.4 '경로 누출 검사': 문자열 값에 그 체크아웃 루트가 없다).
4. 저장소 밖 topology(예: tmp 아래 복사본) → `ValueError`, 출력 파일이 생기지 않는다. 결핍 입력의 기존 IC3 거부(`ValueError`, 파일 없음)는 그대로.
5. **동작 보존**: E-INST에서 `topology_ref`를 뺀 나머지 필드가 base와 바이트 동일하다. `topology_ref`는 계약 1의 값이다(base와 다름 -- 이 card가 고치는 것).
6. 문서: `analog-topology-json-library.design.md:143` 예시를 저장소 루트 기준으로(문서 커밋).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: base에서 계약 1·3(절대 경로)과 계약 4(저장소 밖 topology를 받아 씀)가 실패한다. 병합본에서 green. E-INST는 의도적으로 바뀌므로 동작 보존은 계약 5의 '나머지 필드 동일'로 판정한다.

## oracle 종류와 출처

(a) 구성: 기대 상대 경로는 test 파일 위치에서 구한 저장소 루트와 입력 topology 경로로 test가 만든다(피검 출력으로 만들지 않는다). (c) 동작 보존: 나머지 필드 = base 실행 결과.

## 거부해야 할 입력

저장소 밖 topology → `ValueError`, 파일 없음. 판정기 자기 점검: 역슬래시·`..`·`./`·드라이브 문자·앞 `/`가 있는 값 → 거부.

## library 회로 적용 여부

library 회로(파일럿·`folded_cascode`·`two_stage_ota` 등)로 저장 → 계약 1. E-INST(파일럿·`folded_cascode`)로 계약 5.

## 무동작 판정 입력(무발동 값)

엔진의 다른 함수·library·기존 test 전부 -- 판정이 base와 같다(`test_ic3`·`test_s088`은 `topology_ref` 값을 판정하지 않는다 -- 사전 조사).

## 재현할 수치

없음.

## 결정 필요 항목

없음(사용자 지시로 앞당김, 저장소 밖 거부는 원칙 기본안 -- 보고 때 알린다).

## 작성 전 실측

(사전 조사 기준 c4e5fef, DF-35 병합 뒤 base 34bc75e에서 줄 번호 재확인 -- stick_diagram 8984·9006 불변, run_harness 호출 491→492)
1. 사실: `stick_diagram.py:8984` `"topology_ref": topology_json_path,`(가공 없음), `:9006` 같은 인자로 `load_topology`. 운영 호출자 `run_harness.py:492`(`topo` = `LIBRARY_DIR` 절대 경로 -- DF-35 뒤에도 그 체크아웃의 절대 경로).
   `topology_ref` 값을 열어 쓰는 코드 0건(엔진·하네스·tests·probes·tools). 추적 instance.json 6개 모두 절대 경로, 경로가 든 문자열 값은 `topology_ref` 하나.
2. 이름 충돌: `A/tests/contracts/test_df36_instance_relpath.py` -- 이름 glob 충돌 없음, 내용 전수 스캔 test 대상(삭제 이름 참조·print 판정 토큰 금지).
3. 원칙: 경로 규칙은 회로 무관, 계약 1~4에 명시.
4. 쓰기 경로: `stick_diagram.py` = code-author, 설계 문서 예시 = 오케스트레이터 문서 커밋, test = test-author.
5. 계획서 소비자: 바꾸는 이름 없음(키 이름 불변). 계획 DF-36·CC-8 순서 확인.
6. 미배선: 새 def 없음(헬퍼를 만들면 `save_instance_json`이 부르므로 배선됨).
7. 기존 계약 test: `test_ic3`(키 존재만)·`test_s088`(값 미판정) 조정 불필요.
