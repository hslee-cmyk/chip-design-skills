#!/usr/bin/env bash
# card IT-1 + IT-2 재동결 실측 -- 읽기 전용(저장소 파일을 바꾸지 않는다; merge-tree는 tree 객체만 쓴다).
# 실행: bash measure_it_scope.sh > scope_grep.txt
export MSYS_NO_PATHCONV=1
R=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
E=skills/analog-gmid-design/gmid_engine
I=integ/it12
M=master
g() { git -C "$R" grep -nE "$1" "$I" -- "$E" ":!$E/tests" | sed "s#$I:$E/##" | cut -c1-150; }
t() { git -C "$R" grep -cE "$1" "$I" -- "$E/tests" | sed "s#$I:$E/tests/##"; }
d() { git -C "$R" grep -cE "$1" "$M" -- docs/01-plan docs/02-design | sed "s#$M:##" | grep -v history; }

echo "# base"
git -C "$R" rev-parse --short "$M"; git -C "$R" rev-parse --short "$I"
echo "merge-base: $(git -C "$R" merge-base "$M" "$I" | cut -c1-8)"
echo "commits only on master: $(git -C "$R" rev-list --count "$I..$M")"
echo "commits only on integ:  $(git -C "$R" rev-list --count "$M..$I")"
echo "## merge-tree master integ/it12 (첫 줄 = tree, 충돌이 있으면 뒤에 경로·CONFLICT 줄)"
git -C "$R" merge-tree --write-tree --name-only "$M" "$I"
echo "exit=$?"
echo "## 양쪽이 고친 파일(merge-base 기준)"
comm -12 <(git -C "$R" diff --name-only "$I...$M" | sort) <(git -C "$R" diff --name-only "$M...$I" | sort)
echo "## master 쪽 엔진 변경"
git -C "$R" diff --stat=100 "$I...$M" -- "$E" | cut -c1-110
echo "## integ 쪽 규모"
git -C "$R" diff --stat=1 "$M...$I" | tail -1
git -C "$R" diff --stat=1 "$M...$I" -- "$E" | tail -1
echo "## .ai/verification 크기 (파일 수, MiB)"
for b in "$M" "$I"; do git -C "$R" ls-tree -r -l "$b" .ai/verification | awk -v b="$b" '{s+=$4; n++} END {print b, n, s/1048576}'; done

for q in \
 'input_port_multiple_roots|BRANCH_INPUT_MULTIPLE_ROOTS' \
 'gvgs_self_edge|BRANCH_GVGS_SELF_EDGE' \
 'net_model\(' \
 'dc_output_structure|_output_structure|OUTPUT_HIGH_IMPEDANCE|OUTPUT_KVL' \
 'INPUT_STATUS_F_COMPONENT_UNDECLARED|f_component_undeclared' \
 'writer_head|declared_inputs|def input_windows|def input_roots' \
 'def region_rows|tol_vdsat_table\(|vds - sat - tol|sat - vds - tol' \
 'def saturation_window|roots' \
 '_refine_ends|_interior_solution|_dyadic_ys|INPUT_STATUS_UNSETTLED' \
 'dc_seal_conduction|dc_off_current|dc_conduction_floor' \
 'SEAL_ITEM_BLOCKS|derive_child|attach_partial\(' \
 'ls_swing\(|_ss_of|SsCircuit\(|ss_circuit\(' \
 'conductance_matrix\(|nodal_factor\(' \
 'collect_views|_default\(model' \
 'linear_devices'; do
  echo; echo "### 엔진: $q"; g "$q"
done

echo; echo "===== 옛 test (파일:건수) ====="
for q in \
 'input_port_multiple_roots|BRANCH_INPUT_MULTIPLE_ROOTS' \
 'gvgs_self_edge|BRANCH_GVGS_SELF_EDGE' \
 'dc_output_structure|OUTPUT_HIGH_IMPEDANCE|OUTPUT_KVL|kvl_fixed|high_impedance' \
 'f_component_undeclared|INPUT_STATUS_F_COMPONENT' \
 'saturation_window' \
 'region_rows|_ROW_SAT|_ROW_TRIODE|_Circuit' \
 'tol_vdsat_table|tol_VDsat' \
 'SS_WRITES|DC_TABLE|SS_TABLE' \
 'S1V_WRITES|net_model' \
 'ls_swing\(' \
 '"ls"|, "ls",' \
 'dc_seal_conduction|dc_off_current|dc_conduction_floor' \
 'partial|attach_partial'; do
  echo; echo "### test: $q"; t "$q"
done

echo; echo "===== 새 이름 충돌 (엔진 + test, integ/it12) ====="
for n in input_point REL_INPUT_POINT input_cm_undefined BRANCH_INPUT_CM_UNDEFINED gate_source_same writers_in_scope icm_config ICM_CONFIG_WRITER ss_nodal SS_NODAL_WRITER ss_circuit_field SS_CIRCUIT_WRITER kvl_sensitivity IcmConfig IcmPort IcmWindow NodalSystem icm_window_metrics _helpers_dc_solve diode_nodes composite_mos composite_bundles composite_internal icm_capacitive_only_node default_port g_bound test_it1_ test_it2c_ test_it2d_ test_it2e_; do
  c=$(git -C "$R" grep -lw "$n" "$I" -- "$E" | wc -l); echo "$n: $c 파일"
done
echo "## test glob 패턴"
git -C "$R" grep -n 'glob(' "$I" -- "$E/tests" | sed "s#$I:$E/tests/##" | grep -vE 'topology|sizing_spec|LIBRARY|library' | cut -c1-130
echo "## structure.json rule_hash"
git -C "$R" grep -n 'rule_hash' "$I" -- skills/analog-gmid-design/assets | sed "s#$I:skills/analog-gmid-design/assets/##" | cut -c1-120
echo "## S1V_RULE_FILES·S1_RULE_FILES에 이 card가 고칠 파일이 드는가"
git -C "$R" show "$I:$E/graph/s1v_values.py" | sed -n 14,21p | cut -c1-200
git -C "$R" grep -n -A6 'S1_RULE_FILES *=' "$I" -- "$E/graph/s1_values.py" | cut -c1-200

echo; echo "===== 계획·design 소비자(master, history 제외, 파일:건수) ====="
for q in 'input_port_multiple_roots' 'gvgs_self_edge' 'dc_output_structure' '_conduction_rows' 'dc_window_def' 'f_component_undeclared' 'writer_head'; do
  echo "### 문서: $q"; d "$q"
done
echo "## 쓰이지 않은 GL-1 card 흔적(tools·specs)"
git -C "$R" ls-tree --name-only "$M" tools/ | tr '\n' ' '; echo
git -C "$R" grep -l 'scan_shared_calls' "$M" -- tools | head -3
git -C "$R" ls-tree --name-only "$M" docs/02-design/specs/ | grep -iE 'gl1|gl-1'
echo "END"
