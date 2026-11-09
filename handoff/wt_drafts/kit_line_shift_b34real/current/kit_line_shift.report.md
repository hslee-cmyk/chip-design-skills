# kit_line_shift 보고 -- old `7243f28` -> new `2183f2e`

초안은 고치지 않았다. 패치 = `kit_line_shift.patch`(high·medium만).

## 줄 대응(덩어리)

* SD @ base `b1`(file stick_diagram.py): 18 덩어리 -1029,4+1029,3 -1047,2+1046,2 -1058,1+1057,1 -1300,1+1299,1 -1380,2+1379,2 -1529,2+1528,2 -1672,1+1671,1 -1887,2+1886,1 -2066,2+2064,2 -2148,1+2146,1 -2237,1+2235,1 -2345,2+2343,2 -3070,2+3068,1 -3267,1+3264,1 -3352,2+3349,1 -3359,3+3355,1 -3507,2+3501,2 -3913,2+3907,2
* SR @ base `b1`(rev 7243f28): 1 덩어리 -6510,3+6510,2
* SD @ base `old`(rev 7243f28): 22 덩어리 -1029,4+1029,3 -1047,2+1046,2 -1057,2+1056,2 -1073,2+1071,0 -1089,2+1085,0 -1304,1+1299,1 -1384,2+1379,2 -1533,2+1528,2 -1676,1+1671,1 -1891,2+1886,1 -2070,2+2064,2 -2152,1+2146,1 -2241,1+2235,1 -2349,2+2343,2 -3074,2+3068,1 -3271,1+3264,1 -3356,2+3349,1 -3363,3+3355,1 -3370,2+3359,0 -3376,2+3363,0 -3515,2+3501,2 -3921,2+3907,2
* SR @ base `old`(rev 7243f28): 1 덩어리 -6510,3+6510,2
* SD @ base `p0`(rev cd64170): 25 덩어리 -1029,4+1029,3 -1047,2+1046,2 -1057,2+1056,2 -1073,2+1071,0 -1089,2+1085,0 -1304,1+1299,1 -1384,2+1379,2 -1533,2+1528,2 -1676,1+1671,1 -1891,2+1886,1 -2070,2+2064,2 -2152,1+2146,1 -2241,1+2235,1 -2349,2+2343,2 -3023,5+3016,0 -3032,1+3020,0 -3041,8+3029,3 -3085,2+3068,1 -3282,1+3264,1 -3367,2+3349,1 -3374,3+3355,1 -3381,2+3359,0 -3387,2+3363,0 -3526,2+3501,2 -3932,2+3907,2
* SR @ base `p0`(rev 7243f28): 1 덩어리 -6510,3+6510,2

## 개수

| 신뢰도 | 개수 |
|---|---|
| high | 47 |
| medium | 94 |
| remeasure | 2 |
| already-new | 102 |
| anchored | 32 |
| low | 8 |
| ambiguous | 186 |
| (그중 이동 0인 high·medium) | 14 |
| 패치에 넣은 인용 | 127 |

## 이동하는 인용(high·medium)

| file:line | 엔진 | base | 옛 인용 | 새 인용 | 신뢰도 | 패치 | 근거 |
|---|---|---|---|---|---|---|---|
| draft_b26pre.spec.md:14 | SR | old | 11800 | 11799 | medium | Y |  |
| draft_b26pre.spec.md:14 | SR | old | 11879 | 11878 | medium | Y |  |
| draft_b26pre.spec.md:15 | SR | old | 11802 | 11801 | medium | Y |  |
| draft_b26pre.spec.md:15 | SR | old | 11803 | 11802 | medium | Y |  |
| draft_b26pre.spec.md:15 | SR | old | 11828 | 11827 | medium | Y |  |
| draft_b26pre.spec.md:15 | SR | old | 11835 | 11834 | medium | Y |  |
| draft_b26pre.spec.md:15 | SR | old | 11837 | 11836 | medium | Y |  |
| draft_b26pre.spec.md:15 | SD | old | 3285 | 3278 | medium | Y |  |
| draft_b26pre.spec.md:16 | SR | old | 11802 | 11801 | medium | Y |  |
| draft_b26pre.spec.md:27 | SR | old | 11800 | 11799 | medium | Y |  |
| draft_b26pre.spec.md:27 | SR | old | 11879 | 11878 | medium | Y |  |
| draft_b26pre.spec.md:32 | SR | old | 9404 | 9403 | medium | Y | def-ok(optimize_full_circuit_budget) |
| draft_b26pre.spec.md:32 | SR | old | 9406 | 9405 | medium | Y | def-ok(optimize_full_circuit_budget) |
| draft_b26pre.spec.md:67 | SD | old | 7555 | 7541 | medium | Y | def-ok(repair_matching_safety) |
| draft_b26pre.spec.md:67 | SD | old | 7557 | 7543 | medium | Y | def-ok(repair_matching_safety) |
| draft_b26pre.spec.md:71 | SR | old | 9408 | 9407 | medium | Y |  |
| draft_b26pre.spec.md:71 | SR | old | 9412 | 9411 | medium | Y |  |
| draft_b26pre.spec.md:80 | SR | old | 11784 | 11783 | medium | Y | def-outside(_fixup_euler_blocked_rows) |
| draft_b26pre.spec.md:80 | SR | old | 11786 | 11785 | medium | Y | def-outside(_fixup_euler_blocked_rows) |
| draft_b26pre.spec.md:86 | SR | old | 11696 | 11695 | medium | Y |  |
| draft_b26pre.spec.md:86 | SR | old | 11698 | 11697 | medium | Y |  |
| draft_b26pre.spec.md:86 | SR | old | 11700 | 11699 | medium | Y |  |
| draft_b26pre.spec.md:92 | SR | old | 11784 | 11783 | medium | Y |  |
| draft_b26pre.spec.md:92 | SR | old | 11786 | 11785 | medium | Y |  |
| draft_b26pre.spec.md:169 | SD | old | 3285 | 3278 | medium | Y |  |
| draft_b26pre.spec.md:171 | SR | old | 11800 | 11799 | medium | Y |  |
| draft_b26pre.spec.md:171 | SR | old | 11879 | 11878 | medium | Y |  |
| draft_b26pre.spec.md:171 | SR | old | 11802 | 11801 | medium | Y |  |
| draft_b26pre.spec.md:186 | SD | old | 2686 | 2680 | medium | Y | def-ok(find_structural_symmetry_candidates) |
| draft_b26pre.spec.md:192 | SD | old | 2760 | 2754 | medium | Y |  |
| draft_b26pre.spec.md:197 | SD | old | 2100 | 2094 | medium | Y |  |
| draft_b26pre.spec.md:197 | SD | old | 2101 | 2095 | medium | Y |  |
| draft_b26pre.spec.md:197 | SD | old | 2176 | 2170 | medium | Y |  |
| draft_b26pre.spec.md:197 | SD | old | 2177 | 2171 | medium | Y |  |
| draft_b26pre.spec.md:197 | SD | old | 3985 | 3971 | medium | Y |  |
| draft_b26pre.spec.md:197 | SD | old | 3986 | 3972 | medium | Y |  |
| draft_b26pre.spec.md:268 | SR | old | 11825 | 11824 | medium | Y |  |
| draft_b26pre.spec.md:272 | SR | old | 11800 | 11799 | medium | Y |  |
| draft_b26pre.spec.md:272 | SR | old | 11879 | 11878 | medium | Y |  |
| draft_b26pre.spec.md:330 | SR | old | 9404 | 9403 | medium | Y |  |
| draft_b26pre.spec.md:330 | SR | old | 9406 | 9405 | medium | Y |  |
| draft_b26pre.spec.md:330 | SR | old | 11802 | 11801 | medium | Y |  |
| draft_b26pre.spec.md:331 | SR | old | 11828 | 11827 | medium | Y |  |
| draft_b26pre.spec.md:339 | SR | old | 11696 | 11695 | high | Y | snippet-ok |
| draft_b26pre.spec.md:340 | SR | old | 11698 | 11697 | high | Y | snippet-ok |
| draft_b26pre.spec.md:341 | SR | old | 11700 | 11699 | high | Y | snippet-ok |
| draft_b26pre.spec.md:342 | SR | old | 9404 | 9403 | high | Y | snippet-ok |
| draft_b26pre.spec.md:343 | SR | old | 9406 | 9405 | high | Y | snippet-ok |
| draft_b26pre.spec.md:344 | SR | old | 9404 | 9403 | high | Y | snippet-ok |
| draft_b26pre.spec.md:345 | SR | old | 9406 | 9405 | high | Y | snippet-ok |
| draft_b26pre.spec.md:346 | SR | old | 6573 | 6572 | high | Y | snippet-ok |
| draft_b26pre.spec.md:347 | SR | old | 11800 | 11799 | high | Y | snippet-ok |
| draft_b26pre.spec.md:348 | SR | old | 11801 | 11800 | high | Y | snippet-ok |
| draft_b26pre.spec.md:349 | SR | old | 11877 | 11876 | high | Y | snippet-ok |
| draft_b26pre.spec.md:350 | SR | old | 11879 | 11878 | high | Y | snippet-ok |
| draft_b26pre.spec.md:351 | SR | old | 11880 | 11879 | high | Y | snippet-ok |
| draft_b26pre.spec.md:352 | SR | old | 11881 | 11880 | high | Y | snippet-ok |
| draft_b26pre.spec.md:353 | SD | old | 4529 | 4515 | high | Y | snippet-ok |
| draft_b26pre.spec.md:354 | SD | old | 3282 | 3275 | high | Y | snippet-ok |
| draft_b26pre.spec.md:355 | SD | old | 6892 | 6878 | high | Y | snippet-ok |
| draft_b26pre.spec.md:356 | SD | old | 6894 | 6880 | high | Y | snippet-ok |
| draft_b26pre.spec.md:364 | SR | old | 11835 | 11834 | high | Y | snippet-ok |
| draft_b26pre.spec.md:365 | SR | old | 11836 | 11835 | high | Y | snippet-ok |
| draft_b26pre.spec.md:366 | SR | old | 11837 | 11836 | high | Y | snippet-ok |
| draft_b26pre.spec.md:367 | SR | old | 11802 | 11801 | high | Y | snippet-ok |
| draft_b26pre.spec.md:368 | SR | old | 11803 | 11802 | high | Y | snippet-ok |
| draft_b26pre.spec.md:369 | SR | old | 11828 | 11827 | high | Y | snippet-ok |
| draft_b26pre.spec.md:370 | SD | old | 2176 | 2170 | high | Y | snippet-ok |
| draft_b26pre.spec.md:371 | SD | old | 2177 | 2171 | high | Y | snippet-ok |
| draft_b26pre.spec.md:372 | SD | old | 2100 | 2094 | high | Y | snippet-ok |
| draft_b26pre.spec.md:373 | SD | old | 2101 | 2095 | high | Y | snippet-ok |
| draft_b26pre.spec.md:374 | SD | old | 3985 | 3971 | high | Y | snippet-ok |
| draft_b26pre.spec.md:375 | SD | old | 3986 | 3972 | high | Y | snippet-ok |
| draft_b26pre.spec.md:376 | SD | old | 4530 | 4516 | high | Y | snippet-ok |
| draft_b26pre.spec.md:377 | SD | old | 3285 | 3278 | high | Y | snippet-ok |
| draft_b26pre.spec.md:378 | SD | old | 3285 | 3278 | high | Y | snippet-ok |
| draft_b26pre.spec.md:379 | SD | old | 3286 | 3279 | high | Y | snippet-ok |
| draft_b26pre.spec.md:387 | SD | old | 2165 | 2159 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:388 | SD | old | 2169 | 2163 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:389 | SD | old | 2092 | 2086 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:391 | SD | old | 4291 | 4277 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:392 | SD | old | 4291 | 4277 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:393 | SD | old | 4295 | 4281 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:397 | SD | old | 4297 | 4283 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:398 | SD | old | 4299 | 4285 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:400 | SD | old | 4281 | 4267 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:402 | SD | old | 4350 | 4336 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:405 | SD | old | 6822 | 6808 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:406 | SD | old | 6822 | 6808 | high | Y | snippet-ok; section-rev(a796468)≡base |
| draft_b26pre.spec.md:409 | SR | old | 11800 | 11799 | medium | Y | def-outside(_backfill_interdig_ok); section-rev(a796468)≡base |
| draft_b26pre.spec.md:409 | SR | old | 11879 | 11878 | medium | Y | def-outside(_backfill_interdig_ok); section-rev(a796468)≡base |
| draft_b26pre.spec.md:413 | SR | old | 11784 | 11783 | medium | Y | section-rev(a796468)≡base |
| draft_b26pre.spec.md:413 | SR | old | 11786 | 11785 | medium | Y | section-rev(a796468)≡base |
| draft_b26pre.spec.md:414 | SR | old | 11802 | 11801 | medium | Y | def-outside(_finalize); section-rev(a796468)≡base |
| draft_b26pre.spec.md:427 | SR | old | 11800 | 11799 | medium | Y | section-rev(a796468)≡base |
| draft_b26pre.spec.md:427 | SR | old | 11879 | 11878 | medium | Y | section-rev(a796468)≡base |
| draft_b26pre.spec.md:430 | SR | old | 11802 | 11801 | medium | Y | section-rev(a796468)≡base |
| draft_b26pre.spec.md:491 | SR | old | 9363 | 9362 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 9367 | 9366 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 9400 | 9399 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 9406 | 9405 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 9408 | 9407 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 9412 | 9411 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 11582 | 11581 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 11769 | 11768 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 11770 | 11769 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 11784 | 11783 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:491 | SR | old | 11786 | 11785 | medium | Y | def-outside(resolve_stack_layout); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 2686 | 2680 | medium | Y | def-ok(find_structural_symmetry_candidates); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 2051 | 2045 | medium | Y | def-ok(_propose_gm_id_roles); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 2114 | 2108 | medium | Y | def-ok(_propose_L_roles); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 7532 | 7518 | medium | Y | def-ok(repair_matching_safety); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 7555 | 7541 | medium | Y | def-ok(repair_matching_safety); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 7557 | 7543 | medium | Y | def-ok(repair_matching_safety); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 6453 | 6439 | medium | Y | def-ok(StickResult); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 6461 | 6447 | medium | Y | def-ok(StickResult); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 6796 | 6782 | medium | Y | def-ok(AuditCheck); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:492 | SD | old | 6806 | 6792 | medium | Y | def-ok(AuditResult); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1504 | 1499 | medium | Y | def-ok(find_differential_pair_candidates); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1507 | 1502 | medium | Y | def-ok(find_differential_pair_candidates); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1509 | 1504 | medium | Y | def-ok(find_differential_pair_candidates); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1539 | 1534 | medium | Y | def-ok(find_differential_pair_candidates); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1540 | 1535 | medium | Y | def-ok(find_differential_pair_candidates); section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1567 | 1562 | high | Y | snippet-ok; section-rev(dd60db6)≡base |
| draft_b26_1.spec.md:77 | SD | p0 | 3559 | 3534 | medium | Y | def-ok(propose_theta_kcl_gap_fill); section-rev(cd64170)≡base |
| draft_b26_1.spec.md:77 | SD | p0 | 3561 | 3536 | medium | Y | def-ok(propose_theta_kcl_gap_fill); section-rev(cd64170)≡base |
| draft_b26_1.spec.md:77 | SD | p0 | 3719 | 3694 | medium | Y | def-ok(propose_theta_kcl_gap_fill); section-rev(cd64170)≡base |

## 다시 잴 것(remeasure -- 바뀐 덩어리 안)

| file:line | 엔진 | base | 옛 인용 | 새 인용 | 신뢰도 | 패치 | 근거 |
|---|---|---|---|---|---|---|---|
| draft_b26pre.spec.md:479 | SR | old | 6512 | - | remeasure |  | 바뀐 덩어리 안; section-rev(dd60db6)≡base |
| draft_b26_1.spec.md:28 | SD | p0 | 3042 | - | remeasure |  | 바뀐 덩어리 안 |

## 이미 새 번호(already-new -- 패치 밖. 다시 옮기면 이중 이동)

| file:line | 엔진 | base | 옛 인용 | 새 인용 | 신뢰도 | 패치 | 근거 |
|---|---|---|---|---|---|---|---|
| draft_b26_backfill_audit.spec.md:15 | SR | old | 11783 | 11782 | already-new |  | quote: new 같은 번호 줄과 맞고 base와 다름 |
| draft_b26_backfill_audit.spec.md:15 | SR | old | 11785 | 11784 | already-new |  | quote: new 같은 번호 줄과 맞고 base와 다름 |
| draft_b26_backfill_audit.spec.md:19 | SR | old | 11768 | 11767 | already-new |  | quote: new 같은 번호 줄과 맞고 base와 다름 |
| draft_b26_backfill_audit.spec.md:19 | SR | old | 11769 | 11768 | already-new |  | quote: new 같은 번호 줄과 맞고 base와 다름 |
| draft_b26_backfill_audit.spec.md:27 | SR | old | 11786 | 11785 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11786와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:59 | SR | old | 11802 | 11801 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11802와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:59 | SR | old | 11828 | 11827 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11828와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:59 | SR | old | 11836 | 11835 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11836와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:59 | SR | old | 11880 | 11879 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11880와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:65 | SR | old | 11769 | 11768 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:71 | SR | old | 11769 | 11768 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:99 | SR | old | 11801 | 11800 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11801와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:105 | SR | old | 11783 | 11782 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:105 | SR | old | 11785 | 11784 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:105 | SR | old | 11768 | 11767 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:105 | SR | old | 11769 | 11768 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:176 | SR | old | 6509 | 6509 | already-new |  | bare; 다른 초안의 묶인 인용 SR 6509와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:177 | SR | old | 11786 | 11785 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11786와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:177 | SR | old | 11769 | 11768 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:177 | SR | old | 11800 | 11799 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11800와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:177 | SR | old | 11802 | 11801 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11802와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:177 | SR | old | 11828 | 11827 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11828와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:177 | SR | old | 11836 | 11835 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11836와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:177 | SR | old | 11880 | 11879 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11880와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:178 | SR | old | 11769 | 11768 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:179 | SR | old | 11800 | 11799 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11800와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:179 | SR | old | 11879 | 11878 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11879와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:180 | SR | old | 11784 | 11783 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11784와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:180 | SR | old | 11786 | 11785 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11786와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:180 | SR | old | 11769 | 11768 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:180 | SR | old | 11770 | 11769 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11770와 같은 번호; section-rev(2183f2e)=new |
| draft_b26_backfill_audit.spec.md:180 | SR | old | 11769 | 11768 | already-new |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(2183f2e)=new |
| backfill_launch.sh:296 | SR | old | 11799 | - | already-new |  | literal: new 같은 번호 줄과 같고 base와 다름 |
| backfill_launch.sh:296 | SR | old | 11878 | - | already-new |  | literal: new 같은 번호 줄과 같고 base와 다름 |
| draft_b26_1.spec.md:16 | SR | b1 | 6513 | 6512 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 1014 | 1014 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 1570 | 1569 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 1612 | 1611 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 2090 | 2088 | already-new |  | def-outside(kcl_series_union); year-like; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 2166 | 2164 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 3130 | 3127 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 3235 | 3232 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 3967 | 3961 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 4146 | 4140 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 4282 | 4276 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 4298 | 4292 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 4345 | 4339 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:16 | SD | b1 | 4367 | 4361 | already-new |  | def-outside(kcl_series_union); section-rev(2183f2e)=new |
| draft_b26_1.spec.md:17 | SR | p0 | 2207 | 2207 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_1.spec.md:17 | SR | p0 | 4293 | 4293 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_1.spec.md:44 | SD | p0 | 3966 | 3941 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:44 | SD | p0 | 3970 | 3945 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:44 | SD | p0 | 3941 | 3916 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:44 | SD | p0 | 3945 | 3920 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:52 | SD | p0 | 3907 | 3882 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:52 | SD | p0 | 3908 | 3883 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:52 | SD | p0 | 2343 | 2337 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:52 | SD | p0 | 2344 | 2338 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:65 | SD | p0 | 1222 | 1217 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:65 | SD | p0 | 1233 | 1228 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:65 | SD | p0 | 1234 | 1229 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:65 | SD | p0 | 1270 | 1265 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:65 | SD | p0 | 1281 | 1276 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:65 | SD | p0 | 1282 | 1277 | already-new |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:66 | SD | p0 | 1355 | 1350 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_1.spec.md:66 | SD | p0 | 1357 | 1352 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_1.spec.md:66 | SD | p0 | 1557 | 1552 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_1.spec.md:66 | SD | p0 | 1558 | 1553 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_1.spec.md:66 | SD | p0 | 1737 | 1732 | already-new |  | section-rev(2183f2e)=new |
| draft_b26_1.spec.md:67 | SR | p0 | 4361 | 4361 | already-new |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:67 | SR | p0 | 4626 | 4626 | already-new |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:67 | SR | p0 | 4650 | 4650 | already-new |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:67 | SR | p0 | 4653 | 4653 | already-new |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(2183f2e)=new |
| draft_b26_1.spec.md:67 | SR | p0 | 4086 | 4086 | already-new |  | def-outside(_metric_battery_centering_deviation,_metric_rail_referenced_voltage,_metric_supply_current); section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 1014 | 1014 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 1570 | 1569 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 1612 | 1611 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 2090 | 2088 | already-new |  | assign; year-like; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 2166 | 2164 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 3130 | 3127 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 3235 | 3232 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 3967 | 3961 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 4146 | 4140 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 4282 | 4276 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 4298 | 4292 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 4345 | 4339 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:15 | SD | b1 | 4367 | 4361 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 1014 | 1014 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 1571 | 1570 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 1613 | 1612 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 2092 | 2090 | already-new |  | assign; year-like; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 2168 | 2166 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 3133 | 3130 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 3238 | 3235 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 3973 | 3967 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 4152 | 4146 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 4288 | 4282 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 4304 | 4298 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 4351 | 4345 | already-new |  | assign; section-rev(2183f2e)=new |
| b26_scripts/b26v4_head.py:16 | SD | b1 | 4373 | 4367 | already-new |  | assign; section-rev(2183f2e)=new |
| post35_kit/p35_heads.py:138 | SR | old | 11799 | - | already-new |  | literal: new 같은 번호 줄과 같고 base와 다름 |
| post35_kit/p35_heads.py:138 | SR | old | 11878 | - | already-new |  | literal: new 같은 번호 줄과 같고 base와 다름 |

## 모호(패치 밖) -- anchored·other-base·arrow·hyphen·unit·year-like·untied·bare·low

| file:line | 엔진 | base | 옛 인용 | 새 인용 | 신뢰도 | 패치 | 근거 |
|---|---|---|---|---|---|---|---|
| draft_b26pre.spec.md:15 | SD | old | 3286 | 3279 | ambiguous |  | untied; 같은 파일의 묶인 인용 SD 3286와 같은 번호 |
| draft_b26pre.spec.md:15 | SD | old | 4530 | 4516 | ambiguous |  | untied; 같은 파일의 묶인 인용 SD 4530와 같은 번호 |
| draft_b26pre.spec.md:65 | SR | old | 9363 | 9362 | anchored |  | anchored:a796468(commit, ≡ base) |
| draft_b26pre.spec.md:65 | SR | old | 9367 | 9366 | anchored |  | anchored:a796468(commit, ≡ base) |
| draft_b26pre.spec.md:69 | SD | old | 7532 | 7518 | ambiguous |  | bare; 같은 파일의 묶인 인용 SD 7532와 같은 번호 |
| draft_b26pre.spec.md:193 | SD | old | 2100 | 2094 | anchored |  | anchored:0f23786(commit, ≡ base) |
| draft_b26pre.spec.md:193 | SD | old | 2101 | 2095 | anchored |  | anchored:0f23786(commit, ≡ base) |
| draft_b26pre.spec.md:193 | SD | old | 2176 | 2170 | anchored |  | anchored:0f23786(commit, ≡ base) |
| draft_b26pre.spec.md:193 | SD | old | 2177 | 2171 | anchored |  | anchored:0f23786(commit, ≡ base) |
| draft_b26pre.spec.md:193 | SD | old | 3985 | 3971 | anchored |  | anchored:0f23786(commit, ≡ base) |
| draft_b26pre.spec.md:193 | SD | old | 3986 | 3972 | anchored |  | anchored:0f23786(commit, ≡ base) |
| draft_b26pre.spec.md:193 | SD | old | 2761 | 2755 | anchored |  | anchored:0f23786(commit, ≡ base) |
| draft_b26pre.spec.md:210 | SD | old | 1507 | 1502 | anchored |  | anchored:a796468(commit, ≡ base) |
| draft_b26pre.spec.md:210 | SD | old | 1509 | 1504 | anchored |  | anchored:a796468(commit, ≡ base) |
| draft_b26pre.spec.md:210 | SD | old | 1539 | 1534 | anchored |  | anchored:a796468(commit, ≡ base) |
| draft_b26pre.spec.md:210 | SD | old | 1540 | 1535 | anchored |  | anchored:a796468(commit, ≡ base) |
| draft_b26pre.spec.md:213 | SD | old | 1584 | 1579 | anchored |  | anchored:a796468(commit, ≡ base) |
| draft_b26pre.spec.md:213 | SD | old | 1596 | 1591 | anchored |  | anchored:a796468(commit, ≡ base) |
| draft_b26pre.spec.md:268 | SR | old | 11823 | 11822 | ambiguous |  | range-partner(11826: ambiguous) |
| draft_b26pre.spec.md:268 | SR | old | 11826 | 11825 | ambiguous |  | snippet: new 같은 번호 줄과 맞고 base와 다름(줄에 인용 여럿 -- 이미 옮겼거나 조각이 이웃 줄) |
| draft_b26pre.spec.md:329 | SR | old | 11800 | 11799 | ambiguous |  | line-mentions-base(b34) |
| draft_b26pre.spec.md:329 | SR | old | 11802 | 11801 | ambiguous |  | line-mentions-base(b34) |
| draft_b26pre.spec.md:329 | SR | old | 11879 | 11878 | ambiguous |  | line-mentions-base(b34) |
| draft_b26pre.spec.md:332 | SD | old | 2761 | 2755 | anchored |  | anchored:0f23786(commit, ≡ base) |
| draft_b26pre.spec.md:357 | SD | old | 1567 | 1562 | ambiguous |  | snippet-ok; new-value-present(SD 1562 @L357) |
| draft_b26pre.spec.md:357 | SD | old | 1562 | 1557 | ambiguous |  | other-base(b34); 앞 인용 SD 1567 -> 1562 |
| draft_b26pre.spec.md:358 | SD | old | 1567 | 1562 | ambiguous |  | snippet-ok; new-value-present(SD 1562 @L358) |
| draft_b26pre.spec.md:358 | SD | old | 1562 | 1557 | ambiguous |  | other-base(b34); 앞 인용 SD 1567 -> 1562 |
| draft_b26pre.spec.md:381 | SD | old | 2100 | 2094 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(a796468)≡base |
| draft_b26pre.spec.md:381 | SD | old | 2096 | 2090 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(a796468)≡base |
| draft_b26pre.spec.md:390 | SD | old | 4312 | 4298 | low |  | snippet-mismatch(base 줄: if y.source not in _RAIL_NETS:); section-rev(a796468)≡base |
| draft_b26pre.spec.md:394 | SD | old | 4359 | 4345 | low |  | snippet-mismatch(base 줄: if x.drain in _RAIL_NETS or x.drain in own_group_nets:); section-rev(a796468)≡base |
| draft_b26pre.spec.md:395 | SD | old | 4359 | 4345 | low |  | snippet-mismatch(base 줄: if x.drain in _RAIL_NETS or x.drain in own_group_nets:); section-rev(a796468)≡base |
| draft_b26pre.spec.md:396 | SD | old | 4381 | 4367 | low |  | snippet-mismatch(base 줄: if y.source in _RAIL_NETS:); section-rev(a796468)≡base |
| draft_b26pre.spec.md:399 | SD | old | 4160 | 4146 | low |  | snippet-mismatch(base 줄: if y is None or y.gate in _RAIL_NETS:); section-rev(a796468)≡base |
| draft_b26pre.spec.md:401 | SD | old | 4312 | 4298 | low |  | snippet-mismatch(base 줄: if y.source not in _RAIL_NETS:); section-rev(a796468)≡base |
| draft_b26pre.spec.md:403 | SD | old | 4359 | 4345 | low |  | snippet-mismatch(base 줄: if x.drain in _RAIL_NETS or x.drain in own_group_nets:); section-rev(a796468)≡base |
| draft_b26pre.spec.md:404 | SD | old | 4381 | 4367 | low |  | snippet-mismatch(base 줄: if y.source in _RAIL_NETS:); section-rev(a796468)≡base |
| draft_b26pre.spec.md:470 | SD | old | 1504 | 1499 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SD | old | 1567 | 1562 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SD | old | 2051 | 2045 | ambiguous |  | year-like; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:470 | SD | old | 2114 | 2108 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SD | old | 2686 | 2680 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SD | old | 6453 | 6439 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SD | old | 6796 | 6782 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SD | old | 7532 | 7518 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SR | old | 9363 | 9362 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SR | old | 9400 | 9399 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SR | old | 9408 | 9407 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:470 | SR | old | 11582 | 11581 | anchored |  | section-rev(dd60db6)≡base; anchored:dd60db6(commit, ≡ base) |
| draft_b26pre.spec.md:471 | SD | old | 1567 | 1562 | ambiguous |  | untied; 같은 파일의 묶인 인용 SD 1567와 같은 번호; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9363 | 9362 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9362 | 9361 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9400 | 9399 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9404 | 9403 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9406 | 9405 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9408 | 9407 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9399 | 9398 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9403 | 9402 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9405 | 9404 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 9407 | 9406 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11582 | 11581 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11581 | 11580 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11696 | 11695 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11700 | 11699 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11695 | 11694 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11699 | 11698 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 6573 | 6572 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 6572 | 6571 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11769 | 11768 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11768 | 11767 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11784 | 11783 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11783 | 11782 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11800 | 11799 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11801 | 11800 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11799 | 11798 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11800 | 11799 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11877 | 11876 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11879 | 11878 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11880 | 11879 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11881 | 11880 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11876 | 11875 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11878 | 11877 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11879 | 11878 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:479 | SR | old | 11880 | 11879 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 1504 | 1499 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 1567 | 1562 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 1584 | 1579 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 1596 | 1591 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 1499 | 1494 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 1562 | 1557 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 1579 | 1574 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 1591 | 1586 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 2051 | 2045 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 2114 | 2108 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 2686 | 2680 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 2045 | 2039 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 2108 | 2102 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 2680 | 2674 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 3282 | 3275 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 3275 | 3268 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 4529 | 4515 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 6453 | 6439 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 6796 | 6782 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 6892 | 6878 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 6894 | 6880 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 7532 | 7518 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 4515 | 4501 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 6439 | 6425 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 6782 | 6768 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 6878 | 6864 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 6880 | 6866 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:480 | SD | old | 7518 | 7504 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:487 | SR | old | 11799 | 11798 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:487 | SR | old | 11878 | 11877 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1562 | 1557 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1584 | 1579 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| draft_b26pre.spec.md:497 | SD | old | 1596 | 1591 | ambiguous |  | untied; 표지 줄의 유일 엔진 SD로 계산; section-rev(dd60db6)≡base |
| b26pre_launch.sh:202 | SR | old | 9363 | 9362 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 9363와 같은 번호; section-rev(dd60db6)≡base |
| b26pre_launch.sh:202 | SR | old | 11769 | 11768 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(dd60db6)≡base |
| draft_b26_backfill_audit.spec.md:186 | SR | old | 11784 | 11783 | ambiguous |  | untied; 다른 초안의 묶인 인용 SR 11784와 같은 번호; section-rev(dd60db6)≡base |
| draft_b26_backfill_audit.spec.md:186 | SR | old | 11802 | 11801 | ambiguous |  | untied; 다른 초안의 묶인 인용 SR 11802와 같은 번호; section-rev(dd60db6)≡base |
| draft_b26_backfill_audit.spec.md:186 | SR | old | 11877 | 11876 | ambiguous |  | untied; 다른 초안의 묶인 인용 SR 11877와 같은 번호; section-rev(dd60db6)≡base |
| draft_b26_backfill_audit.spec.md:186 | SR | old | 11800 | 11799 | ambiguous |  | untied; 다른 초안의 묶인 인용 SR 11800와 같은 번호; section-rev(dd60db6)≡base |
| draft_b26_backfill_audit.spec.md:186 | SR | old | 11879 | 11878 | ambiguous |  | untied; 다른 초안의 묶인 인용 SR 11879와 같은 번호; section-rev(dd60db6)≡base |
| draft_b26_backfill_audit.spec.md:193 | SR | old | 11769 | 11768 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(dd60db6)≡base |
| draft_b26_backfill_audit.spec.md:193 | SR | old | 11786 | 11785 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11786와 같은 번호; section-rev(dd60db6)≡base |
| b26_backfill_briefs.md:14 | SR | old | 6510 | - | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:14 | SR | old | 6512 | - | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:14 | SR | old | 6513 | 6512 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:14 | SR | old | 11799 | 11798 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:14 | SR | old | 11878 | 11877 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:19 | SR | old | 6510 | - | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:19 | SR | old | 6512 | - | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11757 | 11756 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11758 | 11757 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11768 | 11767 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11772 | 11771 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11783 | 11782 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11793 | 11792 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11797 | 11796 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11801 | 11800 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11876 | 11875 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:20 | SR | old | 11880 | 11879 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11711 | 11710 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11757 | 11756 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11758 | 11757 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11768 | 11767 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11769 | 11768 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11771 | 11770 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11772 | 11771 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11783 | 11782 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11785 | 11784 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11786 | 11785 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11793 | 11792 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11797 | 11796 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11799 | 11798 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11800 | 11799 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11801 | 11800 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11876 | 11875 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11878 | 11877 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:43 | SR | old | 11879 | 11878 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:75 | SR | old | 11877 | 11876 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11877와 같은 번호; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:77 | SR | old | 11799 | 11798 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:77 | SR | old | 11878 | 11877 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:84 | SR | old | 11800 | 11799 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11800와 같은 번호; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:84 | SR | old | 11801 | 11800 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11801와 같은 번호; section-rev(0f23786)≡base |
| b26_backfill_briefs.md:137 | SR | old | 11800 | 11799 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11800와 같은 번호; section-rev(dd60db6)≡base |
| b26_backfill_briefs.md:137 | SR | old | 11879 | 11878 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11879와 같은 번호; section-rev(dd60db6)≡base |
| b26_backfill_briefs.md:142 | SR | old | 11799 | 11798 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| b26_backfill_briefs.md:142 | SR | old | 11878 | 11877 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(dd60db6)≡base |
| b26_backfill_briefs.md:276 | SR | old | 11769 | 11768 | ambiguous |  | bare; 다른 초안의 묶인 인용 SR 11769와 같은 번호; section-rev(dd60db6)≡base |
| backfill_launch.sh:220 | SR | old | 11757 | 11756 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| backfill_launch.sh:220 | SR | old | 11880 | 11879 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| backfill_launch.sh:220 | SR | old | 11799 | 11798 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| backfill_launch.sh:220 | SR | old | 11878 | 11877 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| draft_b26_1.spec.md:71 | SR | p0 | 7282 | 7281 | anchored |  | def-ok(_hr_resolve_vertical_group); section-rev(cd64170)≡base; anchored:cd64170(commit, ≡ base),dd60db6(commit, ≡ base),2183f2e(commit, ≠ base) |
| draft_b26_1.spec.md:71 | SR | p0 | 8003 | 8002 | anchored |  | def-ok(_build_theta_evaluator); section-rev(cd64170)≡base; anchored:cd64170(commit, ≡ base),dd60db6(commit, ≡ base),2183f2e(commit, ≠ base) |
| draft_b26_1.spec.md:71 | SR | p0 | 8091 | 8090 | anchored |  | def-ok(_build_theta_evaluator); section-rev(cd64170)≡base; anchored:cd64170(commit, ≡ base),dd60db6(commit, ≡ base),2183f2e(commit, ≠ base) |
| draft_b26_1.spec.md:71 | SR | p0 | 6881 | 6880 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6886 | 6885 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6920 | 6919 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6931 | 6930 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6948 | 6947 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6510 | - | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6512 | - | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 7281 | 7280 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 8002 | 8001 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 8090 | 8089 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6880 | 6879 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6885 | 6884 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6919 | 6918 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6930 | 6929 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:71 | SR | p0 | 6947 | 6946 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:72 | SR | p0 | 8003 | 8002 | ambiguous |  | bare; 같은 파일의 묶인 인용 SR 8003와 같은 번호; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:72 | SR | p0 | 7282 | 7281 | ambiguous |  | bare; 같은 파일의 묶인 인용 SR 7282와 같은 번호; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:75 | SR | p0 | 8003 | 8002 | ambiguous |  | bare; 같은 파일의 묶인 인용 SR 8003와 같은 번호; section-rev(cd64170)≡base |
| draft_b26_1.spec.md:499 | SD | p0 | 1575 | 1570 | ambiguous |  | def-ok(find_differential_pair_candidates); section-rev(2d58fd8)≠base·new |
| draft_b26_1.spec.md:499 | SD | p0 | 1617 | 1612 | ambiguous |  | def-ok(_diff_pair_layer1_groups); section-rev(2d58fd8)≠base·new |
| draft_b26_1.spec.md:499 | SD | p0 | 2096 | 2090 | ambiguous |  | def-ok(_propose_gm_id_roles); section-rev(2d58fd8)≠base·new |
| draft_b26_1.spec.md:542 | SD | p0 | 3531 | 3506 | ambiguous |  | def-ok(propose_theta_kcl_gap_fill); section-rev(2d58fd8)≠base·new |
| draft_b26_1.spec.md:542 | SD | p0 | 3535 | 3510 | ambiguous |  | def-ok(propose_theta_kcl_gap_fill); section-rev(2d58fd8)≠base·new |
| draft_b26_1.spec.md:542 | SD | p0 | 3540 | 3515 | ambiguous |  | def-ok(propose_theta_kcl_gap_fill); section-rev(2d58fd8)≠base·new |
| b26_1_launch.sh:85 | SR | old | 6510 | - | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| b26_1_launch.sh:85 | SR | old | 6512 | - | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| post35_kit/p35_heads.py:16 | SR | old | 11800 | 11799 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| post35_kit/p35_heads.py:16 | SR | old | 11879 | 11878 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| post35_kit/p35_heads.py:16 | SR | old | 11799 | 11798 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| post35_kit/p35_heads.py:16 | SR | old | 11878 | 11877 | ambiguous |  | untied; 표지 줄의 유일 엔진 SR로 계산 |
| post35_kit/p35_heads.py:137 | SR | old | 11800 | 11799 | ambiguous |  | bare; 같은 파일의 묶인 인용 SR 11800와 같은 번호 |
| post35_kit/p35_heads.py:137 | SR | old | 11879 | 11878 | ambiguous |  | bare; 같은 파일의 묶인 인용 SR 11879와 같은 번호 |
| post35_kit/p35_heads.py:139 | SR | old | 11800 | 11799 | ambiguous |  | literal-verified(base); new-value-present(SR 11799 @L138) |
| post35_kit/p35_heads.py:139 | SR | old | 11879 | 11878 | ambiguous |  | literal-verified(base); new-value-present(SR 11878 @L138) |
