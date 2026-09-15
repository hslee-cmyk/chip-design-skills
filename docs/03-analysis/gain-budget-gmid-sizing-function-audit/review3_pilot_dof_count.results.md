
# run 2026-09-15 15:39:39
- 소자 51
- true_current_mirror_groups: 3개 [['M10', 'M12', 'M19', 'M21', 'M38', 'M5', 'M66', 'M68'], ['M13', 'M17', 'M18_bg', 'M22', 'M6', 'M60', 'M61', 'M8'], ['M36a', 'M7']]
- l_sharing_classes: 15개
  - M68: ['M10', 'M12', 'M19', 'M21', 'M38', 'M5', 'M66', 'M68']
  - M8: ['M13', 'M17', 'M18_bg', 'M22', 'M36a', 'M36b', 'M6', 'M60', 'M61', 'M7', 'M8']
  - M2a: ['M2a', 'M2b']
  - M3a: ['M3a', 'M3b']
  - M1b: ['M1a', 'M1b']
  - M4b: ['M4a', 'M4b']
  - M20a: ['M11a', 'M20a']
  - M20b: ['M11b', 'M20b']
  - M23a: ['M14a', 'M23a']
  - M24b: ['M14b', 'M24b']
  - M25: ['M15', 'M25']
  - M26: ['M16', 'M26']
  - M18a: ['M18a', 'M9a']
  - M18b: ['M18b', 'M9b']
  - M37b: ['M37a', 'M37b']
  - owner[M68] = M5 (최초 input 단의 tail), owners_all=['M5']
  - owner[M8] = M6 (최초 input 단의 tail), owners_all=['M6', 'M7']
  - owner[M2a] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M3a] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M1b] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M4b] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M20a] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M20b] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M23a] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M24b] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M25] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M26] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M18a] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M18b] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]
  - owner[M37b] = None (이 류에 gain stage tail이 없다 -- L_role 폴백), owners_all=[]

## L 결정변수 수
- P (DEC-04, 등식 관계만 묶음): 동치류 15 + 단독 6 = **21**
- Q1 = 1, Q2 = 2 (['nmos', 'pmos'])
- 블록 선언 5개: stage1_diffpair(11), classab_vom(12), classab_vop(12), biasgen(9), cmfb(7)
  - 블록 미배정 소자 []
- Q3 명목 5, L 동치류가 블록을 가로질러 병합된 뒤 실효 **1**: [['stage1_diffpair', 'classab_vom', 'classab_vop', 'biasgen', 'cmfb']]
- Q3' (블록 x kind) 실효 2

## gm_id 결정변수 (미러+same_as+matching_pairs+gm_id_match_vgs_of(15건) union)
- 동치류 21 (소자 51), diode 16: ['M11a', 'M11b', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M23a', 'M24b', 'M36a', 'M36b', 'M39', 'M40', 'M57', 'M64', 'M66']

## 노드 35: 레일 2, 포트 ['Vim', 'Vip', 'Vom', 'Vop'], diode 노드(W1) 16, gate-only ['Vim', 'Vip', 'Voc']
- W2/W3/W4 후보(나머지, 상한) 13: ['N1a2a', 'N1b2b', 'N3a4a', 'N3b4b', 'N58_57', 'N64_63', 'Ncmfb_tail', 'Vg15', 'Vg25', 'Vom1', 'Vop1', 'Vx', 'Vy']

## L 조합 수 (log10)
- LUT 앵커 12: P 22.7 | Q1 1.08 | Q2 2.16 | Q3 1.08 | Q3' 2.16
- theta bounds 0.15~1.0um 앵커 9: P 20.0 | Q1 0.95 | Q2 1.91 | Q3 0.95 | Q3' 1.91
- knee 후보 3: P 10.0 | Q1 0.48 | Q2 0.95 | Q3 0.48 | Q3' 0.95

## 신호 경로 소자의 L 류
- M1a (pmos, 블록 stage1_diffpair): L류 M1b
- M1b (pmos, 블록 stage1_diffpair): L류 M1b
- M2a (pmos, 블록 stage1_diffpair): L류 M2a
- M2b (pmos, 블록 stage1_diffpair): L류 M2a
- M3a (nmos, 블록 stage1_diffpair): L류 M3a
- M3b (nmos, 블록 stage1_diffpair): L류 M3a
- M4a (nmos, 블록 stage1_diffpair): L류 M4b
- M4b (nmos, 블록 stage1_diffpair): L류 M4b
- M15 (pmos, 블록 classab_vom): L류 M25
- M25 (pmos, 블록 classab_vop): L류 M25
- M16 (nmos, 블록 classab_vom): L류 M26
- M26 (nmos, 블록 classab_vop): L류 M26
- M9a (pmos, 블록 classab_vom): L류 M18a
- M9b (nmos, 블록 classab_vom): L류 M18b
- M18a (pmos, 블록 classab_vop): L류 M18a
- M18b (nmos, 블록 classab_vop): L류 M18b
- M5 (nmos, 블록 stage1_diffpair): L류 M68
- M6 (pmos, 블록 stage1_diffpair): L류 M8
- M7 (pmos, 블록 stage1_diffpair): L류 M8
