표 1

| 묶음 | 변이(head def·연산자·경로) | base 줄(a796468) | 문장(head) | 정의 | 시제품 판정 |
|---|---|---|---|---|---|
| E6-b | `_fixup_euler_blocked_rows` `stmt_delete` `body[5].body[13]` | SR 11696 | `split = find_min_crossover_layout_with_branch_composite(row_transistor` | N2b/N2w/N2d | 죽음 (test_b26pre_euler_fixup_group_split) |
| E6-b | `_fixup_euler_blocked_rows` `stmt_delete` `body[5].body[14]` | SR 11698 | `by_name = {t.name: t for t in row_transistors}` | N2b/N2w/N2d | 죽음 (test_b26pre_euler_fixup_group_split) |
| E6-b | `_fixup_euler_blocked_rows` `stmt_delete` `body[5].body[16]` | SR 11700 | `for seg_idx, seg in enumerate(split['segments']):` | N2w | 죽음 (test_b26pre_euler_fixup_group_split) |
| E6-a | `optimize_full_circuit_budget._evaluate_row_split` `stmt_delete` `body[5].body[3].orelse[0]` | SR 9404 | `repaired_rows, repaired_audit = repair_matching_safety(rows, matching_` | N2b/N2w/N2d | 죽음 (test_b26pre_ofcb_lutless_repair) |
| E6-a | `optimize_full_circuit_budget._evaluate_row_split` `stmt_delete` `body[5].body[3].orelse[1]` | SR 9406 | `pr = dict(pr, repaired_rows=repaired_rows, repaired_audit=repaired_aud` | N2b/N2w/N2d | 죽음 (test_b26pre_ofcb_lutless_repair) |
| E6-a | `optimize_full_circuit_budget` `stmt_delete` `body[12].body[3].body[5].body[3].orelse[0]` | SR 9404 | `repaired_rows, repaired_audit = repair_matching_safety(rows, matching_` | N2b/N2w/N2d | 죽음 (test_b26pre_ofcb_lutless_repair) |
| E6-a | `optimize_full_circuit_budget` `stmt_delete` `body[12].body[3].body[5].body[3].orelse[1]` | SR 9406 | `pr = dict(pr, repaired_rows=repaired_rows, repaired_audit=repaired_aud` | N2b/N2w/N2d | 죽음 (test_b26pre_ofcb_lutless_repair) |
| E7 | `resolve_stack_layout` `stmt_delete` `body[5]` | SR 6573 | `if refined is not None and refined.get('vertical_stack_id_candidates')` | N2b/N2w/N2d | 죽음 (test_b26pre_resolve_stack_candidates) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[10]` | SR 11835 | `if a not in all_devs or b not in all_devs:` | N2d만 | 죽음 (test_b26pre_growth_pair_not_found) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[10].body[0]` | SR 11836 | `current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)` | N2d만 | 죽음 (test_b26pre_growth_pair_not_found) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[10].body[1]` | SR 11837 | `return {'rows': current_rows, 'audit': result, 'ctx': cur_ctx, 'growth` | N2d만 | 죽음 (test_b26pre_growth_pair_not_found) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[1]` | SR 11800 | `_backfill_interdig_ok(result)` | N2b/N2w/N2d | 생존 |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[2]` | SR 11801 | `if result.ok:` | N2w | 죽음 (test_b26pre_growth_already_ok) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[2].body[0]` | SR 11802 | `current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)` | N2d만 | 생존 |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[2].body[1]` | SR 11803 | `return {'rows': current_rows, 'audit': result, 'ctx': cur_ctx, 'growth` | N2d만 | 죽음 (test_b26pre_growth_already_ok) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[10].body[7].body[1]` | SR 11828 | `current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)` | N2d만 | 죽음 (test_b26pre_growth_only_3b_left) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[11]` | SR 11877 | `current_rows, result = repair_matching_safety(current_rows, matching_p` | N2b/N2w/N2d | 죽음 (test_b26pre_growth_zero_rounds) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[12]` | SR 11879 | `_backfill_interdig_ok(result)` | N2b/N2w/N2d | 생존 |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[13]` | SR 11880 | `current_rows, cur_ctx, result = _finalize(current_rows, cur_ctx)` | N2w | 죽음 (test_b26pre_growth_zero_rounds_euler) |
| E6-c | `run_matching_safety_with_finger_growth` `stmt_delete` `body[14]` | SR 11881 | `return {'rows': current_rows, 'audit': result, 'ctx': cur_ctx, 'growth` | N2w | 죽음 (test_b26pre_growth_zero_rounds, test_b26pre_growth_zero_rounds_euler) |
| E7-seed | `_propose_L_roles` `stmt_delete` `body[7].body[2]` | SD 2176 | `seeds[ga] = gb` | N2d만 | 생존 |
| E7-seed | `_propose_L_roles` `stmt_delete` `body[7].body[3]` | SD 2177 | `seeds[gb] = ga` | N2d만 | 생존 |
| E7-seed | `_propose_gm_id_roles` `stmt_delete` `body[6].body[2]` | SD 2100 | `seeds[ga] = gb` | N2d만 | 생존 |
| E7-seed | `_propose_gm_id_roles` `stmt_delete` `body[6].body[3]` | SD 2101 | `seeds[gb] = ga` | N2d만 | 생존 |
| E7-seed | `propose_device_roles_gap_fill` `stmt_delete` `body[13].body[2]` | SD 3985 | `seed_net_pairs[ga] = gb` | N2d만 | 생존 |
| E7-seed | `propose_device_roles_gap_fill` `stmt_delete` `body[13].body[3]` | SD 3986 | `seed_net_pairs[gb] = ga` | N2d만 | 생존 |
| E7 | `propose_device_roles_gap_fill` `stmt_delete` `body[49]` | SD 4529 | `if disp.case_collisions:` | N2w | 죽음 (test_b26pre_case_collisions) |
| E7 | `propose_device_roles_gap_fill` `stmt_delete` `body[49].body[0]` | SD 4530 | `review_needed.append({'case_collisions': disp.case_collisions})` | N2d만 | 죽음 (test_b26pre_case_collisions) |
| E7 | `propose_vertical_stack_id_gap_fill` `cmp_flip` `body[2].body[1].test.ops[0]` | SD 3285 | `if relations is not None:` | N2d만 | 죽음 (test_b26pre_vsid_gap_fill_ports) |
| E7 | `propose_vertical_stack_id_gap_fill` `stmt_delete` `body[2]` | SD 3282 | `if inputs or outputs or feedbacks or biases or clocks:` | N2b/N2w/N2d | 죽음 (test_b26pre_vsid_gap_fill_ports) |
| E7 | `propose_vertical_stack_id_gap_fill` `stmt_delete` `body[2].body[1]` | SD 3285 | `if relations is not None:` | N2d만 | 죽음 (test_b26pre_vsid_gap_fill_ports) |
| E7 | `propose_vertical_stack_id_gap_fill` `stmt_delete` `body[2].body[1].body[0]` | SD 3286 | `edges.extend((rel['devices'] for rel in relations['differential']))` | N2d만 | 죽음 (test_b26pre_vsid_gap_fill_ports) |
| E7 | `run_full_circuit_audit` `stmt_delete` `body[16]` | SD 6892 | `for (kind, net), group in mc['current_mirror'].items():` | N2w | 죽음 (test_b26pre_full_audit_mirror_undisposed) |
| E7 | `run_full_circuit_audit` `stmt_delete` `body[17]` | SD 6894 | `for (kind, net), group in mc['diff_pair'].items():` | N2w | 죽음 (test_b26pre_full_audit_diffpair_undisposed) |

표 2

| 묶음 | 변이(head def·연산자·경로) | base 줄(a796468) | 문장(head) | 정의 | 시제품 판정 |
|---|---|---|---|---|---|
| E4 | `_propose_L_roles` `stmt_delete` `body[2]` | SD 2165 | `if gm_id_roles is None:` | N2b/N2w/N2d | 생존 |
| E4 | `_propose_L_roles` `stmt_delete` `body[4]` | SD 2169 | `if candidates is None:` | N2b/N2w/N2d | 생존 |
| E4 | `_propose_gm_id_roles` `stmt_delete` `body[2]` | SD 2092 | `if candidates is None:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[40].body[12].test.ops[0]` | SD 4312 | `if y.source not in rails.nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[40].body[5].value.generators[0].ifs[0].values[0].ops[0]` | SD 4291 | `own_group_nets = {n for m in transistors if m.name != x.name and (devi` | N2w | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[40].body[5].value.generators[0].ifs[0].values[1].ops[0]` | SD 4291 | `own_group_nets = {n for m in transistors if m.name != x.name and (devi` | N2w | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[40].body[6].value.generators[0].ifs[0].values[1].ops[0]` | SD 4295 | `open_terminals = [n for n in (x.source, x.drain) if n not in rails.net` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[43].body[4].test.values[0].ops[0]` | SD 4359 | `if x.drain in rails.nets or x.drain in own_group_nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[43].body[4].test.values[1].ops[0]` | SD 4359 | `if x.drain in rails.nets or x.drain in own_group_nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `cmp_flip` `body[43].body[9].test.ops[0]` | SD 4381 | `if y.source in rails.nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `const+` `body[40].body[7].test.comparators[0]` | SD 4297 | `if len(open_terminals) != 1:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `const-` `body[40].body[8].value.slice` | SD 4299 | `open_net = open_terminals[0]` | N2w | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[36].body[1]` | SD 4160 | `if y is None or y.gate in rails.nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[40]` | SD 4281 | `for x in transistors:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[40].body[12]` | SD 4312 | `if y.source not in rails.nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[43]` | SD 4350 | `for x in transistors:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[43].body[4]` | SD 4359 | `if x.drain in rails.nets or x.drain in own_group_nets:` | N2b/N2w/N2d | 생존 |
| E1 | `propose_device_roles_gap_fill` `stmt_delete` `body[43].body[9]` | SD 4381 | `if y.source in rails.nets:` | N2b/N2w/N2d | 생존 |
| E3 | `run_full_circuit_audit` `const+` `args.defaults[1]` | SD 6822 | `def run_full_circuit_audit(devices: dict, expected_counts: dict, dispo` | N2b/N2w/N2d | 생존 |
| E3 | `run_full_circuit_audit` `const-` `args.defaults[1]` | SD 6822 | `def run_full_circuit_audit(devices: dict, expected_counts: dict, dispo` | N2b/N2w/N2d | 생존 |
