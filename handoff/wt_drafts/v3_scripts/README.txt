V3 card 개정(2026-10-01) 측정 스크립트 -- review_v3_cards 반영, v3_cards_revision_log.md 참조.
측정 원본: gate master 7535799. 스크립트는 scratch 경로 C:/g60 을 쓴다(측정 뒤 C:/g60 은 지웠다).

재현 순서(Git Bash, $PY = C:/Python314/python.exe):
  1. mkdir -p C:/g60/base C:/g60/scripts C:/g60/out
     git -C <repo> archive 7535799 | tar -x -C /c/g60/base
     cp <이 폴더>/*.py <이 폴더>/run_cov_junit.sh C:/g60/scripts/
  2. bash C:/g60/scripts/run_cov_junit.sh        # 사본 전체 test 1회(약 5분): out/junit_base.xml(test별 시간), out/executed_lines.json(실행 줄 합집합)
     (사본에 .git이 없어 test_ts6_probe_relocate 2건 실패 -- 796 passed·2 failed·15 xfailed가 정상)
  3. $PY -B C:/g60/scripts/v3_scope_classify.py  # 정의별 대상 변이 수·시간·미실행 줄 변이(P9 실제/시뮬, B26-1 시뮬, B34 좁힌 초안) -> out/v3_scope_classify.txt/.json (몇 분)
  4. $PY -B C:/g60/scripts/v3_probes.py          # B1(docstring 경로 밀림)·B2(머리만 바꾼 변경의 자기 필드 변이 0, 데코레이터 NOOP) -> out/v3_probes.txt
  5. $PY -B C:/g60/scripts/v3_anchors.py         # decision 기록 11·원소 26·V3 모양 14, ①·묶기 해시 앵커, DF-36 면제 4개 문장 -> out/v3_anchors.txt
  6. $PY -B C:/g60/scripts/v3_b2_cases.py        # B2·S6 합성 사례에 개정 정의 적용 -> out/v3_b2_cases.txt
  7. $PY -B C:/g60/scripts/v3_c8_in_b26.py       # C8 load_topology 면제 문장 10개의 B26-1 head 경로·정의별 대상 여부 -> out/v3_c8_in_b26.txt

파일:
  sim_head.py          = _drafts/b26_v3_measure.py 사본(경로만 C:/g39 -> C:/g60). build_b26·build_p9 시뮬레이션 head.
  v3_scope_classify.py = 대상 분류기(card 계약 1 개정본 구현) + build_b34 + 미실행 줄 집계. 도구 함수만 읽기 전용 import.
  covplug.py           = pytest 플러그인(sys.monitoring LINE, 위치마다 첫 실행 뒤 DISABLE -- 합집합만). 하위 프로세스 실행은 잡지 않는다.
  out/                 = 이번 측정 출력(카드 수치의 출처).
주의: 인벤토리 시간은 기계 부하에 따라 변한다(이번 187~202 s, 2026-09-30 측정 177~192 s).

== 2026-10-01 추가 (A1-b 정정 'T6 넓힘' 재측정, v3_cards_revision_log.md §5) ==
scratch C:/g69(같은 HEAD 7535799 archive). 아래 세 스크립트와 v3_scope_classify/sim_head 사본은 경로 C:/g60 -> C:/g69로 바꿔 돌렸다(sed).
junit_base.xml·executed_lines.json은 위 2단계 출력을 재사용(엔진 소스 동일 -- 2단계를 다시 돌리지 않음).
  8. $PY -B C:/g69/scripts/v3_scope_widen.py     # 넓힌 T6(T6 나)를 더한 정의 N2w: P9 실제·B26-1 시뮬·B34 좁힌 초안 수·시간·미실행 줄 -> out/v3_scope_widen.txt/.json (약 5분)
  9. $PY -B C:/g69/scripts/v3_adv21.py           # 2차 검토 적대 21건을 표 설명대로 다시 써서 지금/N2b/N2w의 대상·weak 판정·변경 고유 -> out/v3_adv21.txt
 10. $PY -B C:/g69/scripts/v3_widen_boundary.py  # 넓힌 T6 경계(반복문 앞 문장·다른 블록·속성·메서드 수신자·두 단계) -> out/v3_widen_boundary.txt
  v3_scope_widen.py    = MatchW(원래 Match와 같은 맞춤 + 사이트 기록, 결과가 같음을 assert) + T6 나 + DEFS["N2w"]. 범위 card 계약 1의 구현 기준.

== 2026-10-01 추가 (gate master 0f23786 재측정, 착수 0단계 명령) ==
  scratch C:/g119(격리 복제본). 저장소는 git ls-tree/show로만 읽는다(reachability.py도 <rev> 판을 git show로 읽어 메모리에서 실행).
 11. $PY -B <이 폴더>/v3_decision_census.py --repo <R> --rev "$(git -C <R> rev-parse gate/master)" --out <scratch>/census.txt
      # decision 기록 수·원소 수(_approved_ids와 대조, 다르면 exit 1)·V3 모양 수(대상 영역/밖)·@ 접미사·묶기 해시 앞 16자
      # 출력 사본: out/v3_decision_census_0f23786.txt (13·36·23 = 14 + 9). a796468에서는 12·27·14 재현.
