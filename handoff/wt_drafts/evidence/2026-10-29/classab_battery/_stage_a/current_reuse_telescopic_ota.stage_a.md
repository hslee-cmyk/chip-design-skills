# 단계 A 보고서: current_reuse_telescopic_ota

- 상태: ok (exit 0)
- N_S(계수 예산): 13829760
- declared 대조: not_performed: current_reuse_telescopic_ota.structure.json has no stage_members facts

## 적용한 ratified 사실
- ac_ground_exception Vbias2

## 결합 변수 y (GB3, 소비자: U15 층 0 조립)
- 종류별 수: {'K1': 4, 'K2': 2, 'K4': 5, 'K7': 21}
- 바이어스 기둥: [34, 35, 36, 37, 38, 39, 40]
- 기둥↔블록 매핑표 행: 454, 기둥 이웃으로 귀속된 소자: ['M36b', 'M57', 'M61', 'M64', 'M68']
- K1 ['M10', 'M12', 'M19', 'M21', 'M38', 'M5', 'M66', 'M68'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['loop:M37a:Voc', ['bias:34']], ['loop:M37a:Voc', ['bias:36']], ['loop:M37a:Voc', ['bias:39']], ['transfer:0', ['Vom1', 'Vop1']], ['transfer:0', ['bias:34']], ['transfer:0', ['bias:36']], ['transfer:0', ['bias:39']]] (geom, class_owner_value)
- K1 ['M13', 'M17', 'M18_bg', 'M22', 'M6', 'M60', 'M61', 'M8'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['loop:M37a:Voc', ['bias:35']], ['loop:M37a:Voc', ['bias:37']], ['loop:M37a:Voc', ['bias:38']], ['loop:M37a:Voc', ['bias:39']], ['transfer:0', ['Vom1', 'Vop1']], ['transfer:0', ['bias:35']], ['transfer:0', ['bias:37']], ['transfer:0', ['bias:38']], ['transfer:0', ['bias:39']]] (geom, class_owner_value)
- K1 ['M18_bg', 'M6'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['loop:M37a:Voc', ['bias:38']], ['transfer:0', ['Vom1', 'Vop1']], ['transfer:0', ['bias:38']]] (dc, class_owner_value)
- K1 ['M38', 'M5', 'M66'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['loop:M37a:Voc', ['bias:39']], ['transfer:0', ['Vom1', 'Vop1']], ['transfer:0', ['bias:39']]] (dc, class_owner_value)
- K2 ['M10', 'M12', 'M19', 'M21', 'M38', 'M5', 'M66', 'M68'] 넷 ['Vbias4', 'gnd'] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['loop:M37a:Voc', ['bias:34']], ['loop:M37a:Voc', ['bias:36']], ['loop:M37a:Voc', ['bias:39']], ['transfer:0', ['Vom1', 'Vop1']], ['transfer:0', ['bias:34']], ['transfer:0', ['bias:36']], ['transfer:0', ['bias:39']]] (dc, common_vgs_candidates)
- K2 ['M13', 'M17', 'M18_bg', 'M22', 'M6', 'M60', 'M61', 'M8'] 넷 ['Vbias1', 'vdd'] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['loop:M37a:Voc', ['bias:35']], ['loop:M37a:Voc', ['bias:37']], ['loop:M37a:Voc', ['bias:38']], ['loop:M37a:Voc', ['bias:39']], ['transfer:0', ['Vom1', 'Vop1']], ['transfer:0', ['bias:35']], ['transfer:0', ['bias:37']], ['transfer:0', ['bias:38']], ['transfer:0', ['bias:39']]] (dc, common_vgs_candidates)
- K4 ['M15'] 넷 ['Vom', 'vdd'] 블록 [['loop:M37a:Voc', ['Vom']], ['loop:M37a:Voc', ['Vop']], ['transfer:0', ['Vom']], ['transfer:0', ['Vop']]] (dc, shared_node_kvl_kcl)
- K4 ['M16'] 넷 ['Vom', 'gnd'] 블록 [['loop:M37a:Voc', ['Vom']], ['loop:M37a:Voc', ['Vop']], ['transfer:0', ['Vom']], ['transfer:0', ['Vop']]] (dc, shared_node_kvl_kcl)
- K4 ['M25'] 넷 ['Vop', 'vdd'] 블록 [['loop:M37a:Voc', ['Vom']], ['loop:M37a:Voc', ['Vop']], ['transfer:0', ['Vom']], ['transfer:0', ['Vop']]] (dc, shared_node_kvl_kcl)
- K4 ['M26'] 넷 ['Vop', 'gnd'] 블록 [['loop:M37a:Voc', ['Vom']], ['loop:M37a:Voc', ['Vop']], ['transfer:0', ['Vom']], ['transfer:0', ['Vop']]] (dc, shared_node_kvl_kcl)
- K4 ['R1', 'R2'] 넷 ['Vom', 'Vop'] 블록 [['loop:M37a:Voc', ['Vom']], ['loop:M37a:Voc', ['Vop']], ['transfer:0', ['Vom']], ['transfer:0', ['Vop']]] (dc, shared_node_kvl_kcl)
- K7 ['M10'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M15'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom']], ['transfer:0', ['Vom']]] (dc, view_shared_split)
- K7 ['M16'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom']], ['transfer:0', ['Vom']]] (dc, view_shared_split)
- K7 ['M17'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M18a'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M18b'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M19'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M1a'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M1b'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M25'] 넷 [] 블록 [['loop:M37a:Voc', ['Vop']], ['transfer:0', ['Vop']]] (dc, view_shared_split)
- K7 ['M26'] 넷 [] 블록 [['loop:M37a:Voc', ['Vop']], ['transfer:0', ['Vop']]] (dc, view_shared_split)
- K7 ['M2a'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M2b'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M3a'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M3b'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M58'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M6'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M7'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M8'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M9a'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)
- K7 ['M9b'] 넷 [] 블록 [['loop:M37a:Voc', ['Vom1', 'Vop1']], ['transfer:0', ['Vom1', 'Vop1']]] (dc, view_shared_split)

## 뷰 transfer:0 (transfer)
- 블록: gain['Vom']@s2, gain['Vom1', 'Vop1']@s1, gain['Vop']@s2
- 루프: 10, 끊는 점: [['M37a', 'Voc']], 극성: 0
- 루프 역할: loop:M37a:Voc=loop_view

## 뷰 loop:M37a:Voc (loop)
- 블록: gain['Vom']@s2, gain['Vop']@s2, gain['Vom1', 'Vop1']@s1
- 루프: 10, 끊는 점: [['M37a', 'Voc']], 극성: -1

