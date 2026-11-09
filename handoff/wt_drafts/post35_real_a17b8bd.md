# post-35 재측정 -- 실제 병합 도구 `a17b8bd` (`--sim35` 없음)

작성 2026-10-02. 키트 `_drafts/post35_kit/remeasure.sh`(무수정 실행), 사용법 `_drafts/post35_remeasure.md`.
- 대상 rev `a17b8bd`(merge 20260930-v3-changed-stmt-scope = `0ef7430` test + `b70a05a` code, audit 브랜치), 옛 기준 `--old-rev 4a286f0`(기본).
  `a17b8bd`는 실제 저장소 객체에 있어 키트의 `clone --no-local`로 그대로 들어왔다 -- 키트 개조 불필요.
- 실행: `remeasure.sh --scratch /c/g274 --skip-slow a17b8bd`(exit 0) + 느린 블록을 같은 명령으로 따로 3번(`/c/g274/slow.sh a32b|a32p|noop` -- remeasure.sh 느린 블록 복사, SIM=0).
  무동작 미리보기 35분(20:53~21:28).
- 측정 뒤 audit 브랜치가 `a17b8bd` → `dafe5cf`(auditor 판정 기록 커밋)로 움직였다. `a17b8bd..dafe5cf`는 `.ai/verification/20260930-v3-changed-stmt-scope*`만 바꾼다(`tools`·`skills`·`workspaces` 차이 0) -- 이 결과는 `dafe5cf`에도 그대로 맞는다.
- 실제 저장소: HEAD `4a286f0`·status 해시·reflog 345 앞뒤 같음. refs 차이는 위 audit 브랜치 이동 1건뿐(오케스트레이터/auditor -- 보고만).
- 실행 중 `_drafts`에서 다른 agent가 바꾼 파일: `b26pre_backfill_post35_dryrun.md`, `b26_1_kit_selftest/out/records_u3_result.tsv`, `b26_backfill_briefs.md`, `backfill_launch.sh`, `draft_b26pre.spec.md`, `draft_b33.final.spec.md`(21:27).

## 0. 요약

84항목: **same 57 · changed 26 · skipped 1**(skipped = 본 실행의 `G1-REDTEAM --skip-slow` 표시 -- 느린 3개는 따로 돌려 아래에 있음).
changed 26 중 **실제로 고칠 곳이 있는 것은 줄 번호(LINES-G1·LINES-B33) 뿐**이고, 나머지는 기대된 변화(35 마커·출력 키·앵커)이거나 옛 기준선 쪽 문제다.

- V3 대상 수 7개 전부 옛 값과 같음(도구 대상 id와 scope_proto N2w 독립 계산 대칭차 0, `--out` 순서 = 생성 순서). `V3_WANT=4`(backfill) 그대로 유효.
- CARRY5 7실행 ok, **CARRY-FULL-b26u3 PASS**(실제 도구 출력, 생존 1 = U3 `stick_diagram:find_differential_pair_candidates:const-:body[8].body[3].body[1].body[0].iter.args[0].right`).
- 시제품 `install_proto.py`는 이미 `a17b8bd` 앵커로 재앵커된 판(`install_proto.py.pre-35.bak` 존재)이라 새 도구에 `installed 4`, 앵커 14 전부 1 → **공격 32 시제품 93/93 PASS, 단계 exit 분포 옛 기준과 같음**.
- 공격 32 base 93단계 FAIL, 단계별 exit 옛 기준과 같음.
- 무동작 미리보기 13케이스 전부 PASS(264단계). 34(6단계) PASS -- 계약 7 '34 결과 불변'과 맞음. 35(11단계) 새 케이스 PASS.

## 1. 옛 → 새 표

| id | 옛 | 새 | status | 비고 |
|---|---|---|---|---|
| TOOL35-marker | 0 | 3 | changed(기대) | 기대 '0 → 1 이상' 충족. `b34_launch.sh:209`·`b26pre_launch.sh:244`·`backfill_launch.sh:255`의 착수 조건 통과 |
| SIMHEAD-engine | -- | 엔진 .py 차이 0 | same | |
| V3-P9 | 12/16 | 12/16 | same | out 28 |
| V3-BF | 4/93 | 4/93 | same | out 97, def 키 `sizing_recipe.py::run_matching_safety_with_finger_growth` |
| V3-B34 | 10/45 | 10/45 | same | |
| V3-B34-ids | 10/10 | 10/10 | same | |
| V3-B26v4 | 301/2,141 | 301/2,141 | same | auditor V10 p8 '301/2,442'와도 일치 |
| B26PRE-20 | 20/20 대상 | 20/20 대상 | same | '18 죽임' deferred |
| V3-B26A | 299/2,141 | 299/2,141 | same | |
| EQ4-b26a | 4 전부 대상 | 4/4 targeted | same | '4 → 1 생존' deferred |
| V3-B26v5 | 299/2,136 | 299/2,136 | same | |
| EQ4-b26v5 | range 대상·`[0]` 없음 | 같음 | same | |
| V3-B26U3 | 299/2,136 | 299/2,136 | same | |
| CARRY5-{p9,bf,b34,b26v4,b26a,b26v5,b26u3} | 계약 5 가정 | ok(20줄) ×7 | same | 실제 1차 출력 단정 deferred |
| CARRY-FULL-b26u3 | 모의 도구로만 정함 | PASS | same | `b26_1_carry.sh` check heredoc 무수정 통과 |
| G1-KEYS | 옛 8키 | 옛 8키 + `not_targeted`, `targets_by_def` | same | G1 키와 겹침 0 |
| G1-ANCH-* (12개) | 1 | 1 | same | |
| G1-ANCH-mc scope | 0 | 1 | changed(옛 쪽) | 키트가 이미 a17b8bd 앵커 -- 옛 도구(4a286f0)에서 0이 정상 |
| G1-ANCH-mc print | 0 | 1 | changed(옛 쪽) | 같은 이유 |
| G1-INSTALL | (옛 도구: '35 병합 전 판' 거부) | installed 4 | changed(옛 쪽) | 같은 이유. 새 도구에 설치 성공 |
| G1-OOG | 12줄·9파일 | 12줄·9파일 | changed(표시만) | 내용 같음, 더해진 줄 0(rev 접두가 달라 status만 changed) -- 사실상 same |
| G1-A32B-32-moved-defs | FAIL 93, exit {0:10,1:83} | 같음 | same | |
| G1-A32P-32-moved-defs | PASS 93, exit {0:32,1:61} | 같음 | same | |
| G1-NOOP-06·07·09·23·26·27f·29·v7_unwired | PASS | PASS(exit 같음) | same | 23-v4 169단계 |
| G1-NOOP-28-v3-gmid-options | FAIL(exit 2 ×4) | PASS | changed(옛 기준선) | 리허설과 같은 양상 -- 옛 기준선(`g1_kit/out/noop_base_4a286f0.*`, `C:/g225`) 실행 환경의 V3 exit 2. 35 효과 아님 |
| G1-NOOP-31-v3-git-history | FAIL(exit 2 ×3) | PASS | changed(옛 기준선) | 같음 |
| G1-NOOP-34-v3-exempt-binding | FAIL(exit 2 ×6) | PASS(exit {0:1,1:5}) | changed(옛 기준선) | 같음. 실제 35 도구로 34 PASS |
| G1-NOOP-v3_survivor | FAIL(exit 2 ×2) | PASS | changed(옛 기준선) | 같음 |
| G1-NOOP-35-v3-changed-scope | 없음 | PASS(11단계, exit {0:3,1:8}) | changed(새 케이스) | 기대대로 |
| LINES-35 not_targeted | [425](주석 자리) | [9, 632, 688, 695, 696, 699, 744] | changed(정보) | |
| LINES-35 targets_by_def | [] | [632, 690, 744] | changed(정보) | |
| LINES-G1·LINES-B33 | 아래 §2 | | changed(기대: `mutate_changed.py`만) | reachability·source_lint·rt.py·run_all 98행 전부 same |

## 2. 고쳐야 할 곳(줄 번호 -- 이 문서는 고치지 않음)

`tools/gates/mutate_changed.py` 줄만 밀렸다(`4a286f0` → `a17b8bd`). `reachability.py`(main 196, base_defs 224·227·231, new_defs 230·232·239, `_is_source` 175, `build_graph` 97, `reach` 160, `seen = reach` 223), `source_lint.py`(212·252·268), `rt.py` observe 줄, `run_all.py:98`은 같다.

| 이름 | `4a286f0` | `a17b8bd` |
|---|---|---|
| `make_clone` 정의·호출 | 55·371 | **59·627** |
| `_rmtree_force` 정의·호출 | 63·464 | **67·740** |
| `_strip_doc` | 76 | **80** |
| `def_hash` | 86 | **90** |
| `changed_defs` 정의·호출 | 136·413 | **140·676** |
| `mutants` 정의·루프 | 194·423 | **198·691** |
| diff(`--diff-filter=AM`) | 362 | **618** |
| `_is_source` 사용 | 363 | **619** |
| `rch.build_graph(head_files)` | 365 | **621** |
| cat-file | 408 | **665** |
| `base_src =` | 410 | **667** |
| `TimeoutExpired` / `return "timeout"` | 404 / 405 | **661 / 662** |
| `killed += 1` | 449 | **725** |
| `rch.reach`(inventory) | 263 | **519** |
| 출력 `json.dumps` | 432·454·456·460·465 | **699(not_targeted 레코드)·708·730·732·736(ERROR)·741(PASS/FAIL)** |

적힌 곳:
1. `_drafts/draft_p3_g1.spec.md:274~276` -- '착수 재측정 2026-10-02(`4a286f0`)' 문단 (1): `make_clone 55`, `_rmtree_force 63·464`, `_strip_doc 76`, `def_hash 86`, `changed_defs 136·413`, `mutants 194·423`, diff 362, cat-file 408, `base_src 410`, 출력 465~468·456·460 → 위 표 값(출력 PASS/FAIL 741~, ERROR 732·736; 출력 키에 `not_targeted`·`targets_by_def` 추가). 같은 문단 273행 '35 … 미병합 -- 그 병합 뒤 1·2·5와 공격 32를 다시 잰다'에 이 재측정(공격 32 base·시제품 같음, 게이트 밖 호출 같음) 반영.
2. `_drafts/draft_p3_g1.spec.md:32`(`make_clone 53·323`, ERROR 398, `_rmtree_force 406`, `changed_defs` 호출 364)·`:288`·`:318`(362·374) -- `0f23786`/`7535799` 표기 줄. 판 표기를 유지할지 a17b8bd로 바꿀지 결정 필요(문구상 옛 판 값이라 그대로 둘 수 있음).
3. `_drafts/g1_briefs.md:26` -- `mutate_changed.py` 줄 표(`0f23786` 값: 53·323, 61·406, 74, 84, 88~100, 314, 359, 361, 362, 364, 374, 398·402·407). 같은 판단.
4. `_drafts/g1_briefs.md:113~114` -- '`36e170e..4a286f0` … 남은 선행(35·B33) 병합 뒤 시제품을 다시 쓰려면 앵커를 고친다': 35 재앵커 완료(키트가 a17b8bd 앵커, `installed 4`, 공격 32 시제품 93/93 PASS)로 갱신. `g1_briefs.md:406`의 '앵커는 `36e170e` 판' 문구도 `a17b8bd` 판(`install_proto.py.pre-35.bak` = 36e170e·4a286f0 판)으로.
5. `_drafts/draft_b33.final.spec.md:294~295` -- `mutate_changed.py` 215(`rch.reach`)·317(`build_graph`)·354-356(`TimeoutExpired`)·387-392(`killed`) (`0f23786` 값) → 519·621·661~662·725(그 주변 `code != 0` 분기). `:301`(`_is_source` 사용 315 → 619), `:67`(317 → 621), `:307`(317 → 621). (이 파일은 측정 중 21:27에 다른 agent가 바꿨다 -- 위 줄 번호는 그 수정 뒤 grep 값.)
6. G1 무동작 기준선 `g1_kit/out/noop_base_4a286f0.*`: 28·31·34·v3_survivor가 exit 2 FAIL인 기준선은 실행 환경 문제로 보인다(리허설과 같은 결론) -- 기준선을 다시 뜨거나 `g1_briefs.md` §0.7 ⑥ 비교 대상을 이 실행(`a17b8bd` 13/13 PASS)으로.

값이 같아 고칠 것 없음: `backfill_launch.sh:81` `V3_WANT=4`, `draft_b26_backfill_audit.spec.md:180`, `b34_briefs.md:14·250`, `draft_b26_1.spec.md` 'V3 계획'(301·299), `draft_b26pre.spec.md` 주표 20, `b26_1_carry.sh` check heredoc(실제 도구에서 PASS), `g1_briefs.md` §0.7 ③ 키(옛 8 + 35 두 키 -- 기대대로).

deferred(키트 범위 밖): b26pre '18 죽임', B26-1 '등가 4 → 1 생존', carry 실제 1차 출력 단정.

## 3. 원자료

`/c/g274`는 이 보고 뒤 삭제했다. 표 원본(table.txt)·results.jsonl은 아래 그대로:
- 결과 84항목, `{'changed': 26, 'same': 57, 'skipped': 1}`.

```
status    item                                                       old                                new                               
changed   TOOL35-marker                                              null                               0 -> 3                            
same      SIMHEAD-engine                                             null                               엔진 .py 차이 0(4a286f0..rev)         
same      V3-P9                                                      12/16                              12/16                             
same      CARRY5-p9                                                  가정(계약 5 문장)                        ok(20줄)                           
same      V3-BF                                                      4/93                               4/93                              
same      CARRY5-bf                                                  가정(계약 5 문장)                        ok(20줄)                           
same      V3-B34                                                     10/45                              10/45                             
same      CARRY5-b34                                                 가정(계약 5 문장)                        ok(20줄)                           
same      V3-B34-ids                                                 10/10                              10/10                             
same      V3-B26v4                                                   301/2141                           301/2141                          
same      CARRY5-b26v4                                               가정(계약 5 문장)                        ok(20줄)                           
same      B26PRE-20                                                  20/20 대상                           20/20 대상                          
same      V3-B26A                                                    299/2141                           299/2141                          
same      CARRY5-b26a                                                가정(계약 5 문장)                        ok(20줄)                           
same      EQ4-b26a                                                   등가 4 전부 대상                         find_differential_pair_candidates:
same      G1-A32B-32-moved-defs                                      FAIL(93단계, exit {'0': 10, '1': 83} FAIL(93단계, exit {'0': 10, '1': 83}
same      V3-B26v5                                                   299/2136                           299/2136                          
same      CARRY5-b26v5                                               가정(계약 5 문장)                        ok(20줄)                           
same      EQ4-b26v5                                                  range const- 대상, [0] const- 없음(C2) find_differential_pair_candidates:
same      G1-A32P-32-moved-defs                                      PASS(93단계, exit {'0': 32, '1': 61} PASS(93단계, exit {'0': 32, '1': 61}
same      V3-B26U3                                                   299/2136                           299/2136                          
same      CARRY5-b26u3                                               가정(계약 5 문장)                        ok(20줄)                           
same      CARRY-FULL-b26u3                                           spec·모의 도구로만 정한 모양(m1~m4)          PASS: stick_diagram:find_different
changed   LINES-G1|mutate_changed.py|^def _strip_doc                 [76]                               [80]                              
changed   LINES-G1|mutate_changed.py|^def changed_defs               [136]                              [140]                             
changed   LINES-G1|mutate_changed.py|^def def_hash                   [86]                               [90]                              
changed   LINES-G1|mutate_changed.py|_rmtree_force\(                 [63, 464]                          [67, 740]                         
changed   LINES-G1|mutate_changed.py|changed_defs\(base_src          [136, 413]                         [140, 676]                        
changed   LINES-G1|mutate_changed.py|in mutants\(                    [423]                              [691]                             
changed   LINES-G1|mutate_changed.py|json\.dumps\(                   [432, 454, 456, 460, 465]          [699, 708, 730, 732, 736, 741]    
changed   LINES-G1|mutate_changed.py|make_clone\(                    [55, 371]                          [59, 627]                         
same      LINES-G1|reachability.py|^def main                         [196]                              [196]                             
same      LINES-G1|reachability.py|base_defs                         [224, 227, 231]                    [224, 227, 231]                   
same      LINES-G1|reachability.py|new_defs                          [230, 232, 239]                    [230, 232, 239]                   
same      LINES-G1|redteam/lib/rt.py|observe                         [63, 69, 70, 647, 696, 699, 701, 7 [63, 69, 70, 647, 696, 699, 701, 7
same      LINES-G1|redteam/run_all.py|line98                         if "observed_equals" in exp and re if "observed_equals" in exp and re
same      LINES-G1|source_lint.py|[^f] compare\(|=\s*compare\(|\+= c [268]                              [268]                             
same      LINES-G1|source_lint.py|^def compare                       [212]                              [212]                             
same      LINES-G1|source_lint.py|^def main                          [252]                              [252]                             
changed   LINES-B33|mutate_changed.py|_is_source                     [363]                              [619]                             
changed   LINES-B33|mutate_changed.py|except subprocess\.TimeoutExpi [404]                              [661]                             
changed   LINES-B33|mutate_changed.py|killed \+= 1                   [449]                              [725]                             
changed   LINES-B33|mutate_changed.py|rch\.build_graph\(head_files\) [365]                              [621]                             
changed   LINES-B33|mutate_changed.py|rch\.reach                     [263]                              [519]                             
changed   LINES-B33|mutate_changed.py|return "timeout"               [405]                              [662]                             
same      LINES-B33|reachability.py|^def _is_source                  [175]                              [175]                             
same      LINES-B33|reachability.py|^def _refs                       [69]                               [69]                              
same      LINES-B33|reachability.py|^def build_graph                 [97]                               [97]                              
same      LINES-B33|reachability.py|^def reach                       [160]                              [160]                             
same      LINES-B33|reachability.py|new_defs =                       [230]                              [230]                             
same      LINES-B33|reachability.py|seen = reach                     [223]                              [223]                             
changed   LINES-35|mutate_changed.py|not_targeted                    [425]                              [9, 632, 688, 695, 696, 699, 744] 
changed   LINES-35|mutate_changed.py|targets_by_def                  []                                 [632, 690, 744]                   
same      G1-KEYS                                                    ["tool", "verdict", "targets", "mu ["tool", "verdict", "targets", "mu
same      G1-ANCH-rch new_defs                                       1                                  1                                 
same      G1-ANCH-rch print                                          1                                  1                                 
same      G1-ANCH-rch main                                           1                                  1                                 
same      G1-ANCH-mc strip_doc def_hash                              1                                  1                                 
same      G1-ANCH-mc read_tree                                       1                                  1                                 
same      G1-ANCH-mc loop                                            1                                  1                                 
changed   G1-ANCH-mc scope                                           0                                  1                                 
changed   G1-ANCH-mc print                                           0                                  1                                 
same      G1-ANCH-sl import                                          1                                  1                                 
same      G1-ANCH-sl compare def                                     1                                  1                                 
same      G1-ANCH-sl before                                          1                                  1                                 
same      G1-ANCH-sl main                                            1                                  1                                 
same      G1-ANCH-sl print                                           1                                  1                                 
same      G1-ANCH-rt observe                                         1                                  1                                 
changed   G1-INSTALL                                                 mutate_changed.py가 card 35(2026093 installed 4                       
changed   G1-OOG                                                     12줄·9파일                            12줄·9파일                           
skipped   G1-REDTEAM                                                 null                               --skip-slow                       
same      G1-NOOP-06-v4-expected-from-subject                        PASS(2단계, exit {'0': 1, '1': 1})   PASS(2단계, exit {'0': 1, '1': 1})  
same      G1-NOOP-07-v4-assert-under-if                              PASS(2단계, exit {'0': 1, '1': 1})   PASS(2단계, exit {'0': 1, '1': 1})  
same      G1-NOOP-09-v6-broad-except                                 PASS(2단계, exit {'0': 1, '1': 1})   PASS(2단계, exit {'0': 1, '1': 1})  
same      G1-NOOP-23-v4-boundary                                     PASS(169단계, exit {'0': 94, '1': 75 PASS(169단계, exit {'0': 94, '1': 75
same      G1-NOOP-26-gate-output-utf8                                PASS(42단계, exit {'0': 4, '1': 8, ' PASS(42단계, exit {'0': 4, '1': 8, '
same      G1-NOOP-27f-v6-reconfigure-except                          PASS(16단계, exit {'0': 16})         PASS(16단계, exit {'0': 16})        
changed   G1-NOOP-28-v3-gmid-options                                 FAIL(4단계, exit {'2': 4})           PASS(4단계, exit {'0': 4})          
same      G1-NOOP-29-v4-decision-exempt                              PASS(4단계, exit {'0': 1, '1': 3})   PASS(4단계, exit {'0': 1, '1': 3})  
changed   G1-NOOP-31-v3-git-history                                  FAIL(3단계, exit {'2': 3})           PASS(3단계, exit {'0': 1, '1': 1, '2
changed   G1-NOOP-34-v3-exempt-binding                               FAIL(6단계, exit {'2': 6})           PASS(6단계, exit {'0': 1, '1': 5})  
changed   G1-NOOP-35-v3-changed-scope                                null                               PASS(11단계, exit {'0': 3, '1': 8}) 
changed   G1-NOOP-v3_survivor                                        FAIL(2단계, exit {'2': 2})           PASS(2단계, exit {'0': 1, '1': 1})  
same      G1-NOOP-v7_unwired                                         PASS(1단계, exit {'1': 1})           PASS(1단계, exit {'1': 1})          
합계 84항목: {'changed': 26, 'same': 57, 'skipped': 1}
```
