# E4 절차 문구 보강안 (드라이런 dryrun_phase2_e4.md 발견 -- 승인 필요 항목 포함)

1. 스크립트 출처: "세 스크립트는 Phase 2 마지막 병합본 판에서 복제본 밖 경로로 복사해 두 판에 같은 사본을 쓴다(da03c0e 판에는 없다)". `<out>`도 복제본 밖(`git clean -fdx`가 지운다). -- 절차 명확화.
2. 실행 옵션 `C:/Python314/python.exe -B -P <script>` 명시. -- 절차 명확화.
3. [기준 변경 -- 승인 필요] E4의 `PT` phase: design 20 §10이 design 10 §10 PT 정의(`--gmid-phase=1`)를 "그대로" 쓴다. Phase 2 DoD는 `--gmid-phase=2`(현재 Phase)로, `--gmid-dod` 실행을 함께 둔다(phase2_dod_brief와 일치). 기본안: `PT`를 `--gmid-phase=2`로 읽고 `--gmid-dod` 실행 추가.
4. 드라이런 결과(증거 아님): E-LIB hash 동일, E-INST without_topology_ref 두 회로 동일, 새 판 topology_ref = DF-36 계약 값, PT phase 2 기본·dod 모두 798 passed·15 xfailed, 메인 저장소 쓰기 0.

백로그 B38: gate master에 커밋된 instance.json 2개가 낡음(topology_ref 메인 절대 경로, folded_cascode sizing 값도 현재 생성과 다름) -- Phase 2 이전부터. 재생성은 기준선 변경(DEC-40, B14와 같은 자리).
