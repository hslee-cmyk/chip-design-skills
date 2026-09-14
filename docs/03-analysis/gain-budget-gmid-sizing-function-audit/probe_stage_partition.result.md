# probe_stage_partition 결과

규칙: R1=gd엣지 1회당 stage+1(sd/gs 0), R2=R1+diode노드 게이트의 gd는 0(미러)+load/tail 분류, R3=대칭 net 대응으로 차동(DM, 자기대응 넷=가상접지)/공통(CM) 뷰에서 R2. stage index=입력에서 min 경로(0-1 BFS).

## current_reuse_telescopic_ota

- 소자 51개, 수동소자 12개, ideal_sources 1개, ports 선언 있음
- 입력 넷: ['Vim', 'Vip'] (ports 선언); p/n 짝=('Vip', 'Vim')
- 출력 넷: ['Vom', 'Vop'] (ports 선언); p/n 짝=('Vop', 'Vom')
- 교류접지 G1(레일): ['gnd', 'vdd']
- 교류접지 G2(gate-only 비구동, 입력·수동·이상원 단자 아님): []
- 교류접지 G3(이상 전압원 단자): []
- diode 노드(is_diode_connected drain): ['N11a11b', 'N11b', 'N14a14b', 'N14a_14b', 'N20a20b', 'N20b', 'N23a24b', 'N24b23a', 'N36b', 'Vbias1', 'Vbias2', 'Vbias3', 'Vbias4', 'Vcmfb', 'Voc_des', 'gnd']

### 대칭 net 대응 (find_structural_symmetry_candidates, mirror)
- 자기대응(차동모드 가상접지로 취급): ['N36b', 'N58_57', 'N64_63', 'Ncmfb_tail', 'Vbias1', 'Vbias2', 'Vbias3', 'Vbias4', 'Vcmfb', 'Voc', 'Voc_des', 'Vx', 'Vy']
- 수동소자로 확장한 대응[신규]: [('N_cc_rz1', 'N_cc_rz2', 'Cc1', 'Cc2')]
- 단일출력이라 대응을 제거한 것[신규 규칙]: []
- conflicts=[] unresolved=[] low_conf=[['M1a', 'M1b'], ['M4a', 'M4b']]

### 뷰 full: 입력=['Vim', 'Vip'], 출력=['Vom', 'Vop']
- MOS 엣지 79 (gd 35, sd 22, gs 22), 수동 방향엣지 16
- diode/수동 자기루프: [('M11a', 'N11a11b'), ('M11b', 'N11b'), ('M14a', 'N14a14b'), ('M14b', 'N14a_14b'), ('M18_bg', 'Vbias1'), ('M20a', 'N20a20b'), ('M20b', 'N20b'), ('M23a', 'N24b23a'), ('M24b', 'N23a24b'), ('M36a', 'Vcmfb'), ('M36b', 'N36b'), ('M39', 'Voc_des'), ('M57', 'Vbias2'), ('M64', 'Vbias3'), ('M66', 'Vbias4')]
- 접지 shunt 수동소자: [('CL1', 'Vop', 'gnd'), ('CL2', 'Vom', 'gnd'), ('Cs1', 'Vip', 'gnd'), ('Cs2', 'Vim', 'gnd')]
- SCC(MOS만, >1노드): [['Vg15', 'Vop1'], ['N11a11b', 'N11b'], ['N14a14b', 'N14a_14b'], ['Vg25', 'Vom1'], ['N20a20b', 'N20b'], ['N23a24b', 'N24b23a'], ['N58_57', 'Vbias2', 'Vx'], ['N64_63', 'Vbias3', 'Vy']]
- SCC(MOS+수동, >1노드): [['N1a2a', 'N1b2b', 'N3a4a', 'N3b4b', 'N58_57', 'N64_63', 'N_cc_rz1', 'N_cc_rz2', 'Ncmfb_tail', 'Vbias2', 'Vbias3', 'Vcmfb', 'Vg15', 'Vg25', 'Vim', 'Vip', 'Voc', 'Vom', 'Vom1', 'Vop', 'Vop1', 'Vx', 'Vy'], ['N11a11b', 'N11b'], ['N14a14b', 'N14a_14b'], ['N20a20b', 'N20b'], ['N23a24b', 'N24b23a']]
- BFS 레벨(R1 min index 기준; 괄호: R1 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: N1a2a(max=1,R2=0,R1ng=1,R2ng=1), N1b2b(max=1,R2=0,R1ng=1,R2ng=1), N3a4a(max=1,R2=0,R1ng=1,R2ng=1), N3b4b(max=1,R2=0,R1ng=1,R2ng=1), N58_57(max=0,R2=0,R1ng=None,R2ng=None), N64_63(max=0,R2=0,R1ng=None,R2ng=None), Vbias2(max=0,R2=0,R1ng=None,R2ng=None), Vbias3(max=0,R2=0,R1ng=None,R2ng=None), Vg15(max=1,R2=0,R1ng=1,R2ng=1), Vg25(max=1,R2=0,R1ng=1,R2ng=1), Vim(max=0,R2=0,R1ng=0,R2ng=0), Vip(max=0,R2=0,R1ng=0,R2ng=0), Vom1(max=1,R2=0,R1ng=1,R2ng=1), Vop1(max=1,R2=0,R1ng=1,R2ng=1), Vx(max=0,R2=0,R1ng=None,R2ng=None), Vy(max=0,R2=0,R1ng=None,R2ng=None)
  - idx 1: Vom(max=2,R2=1,R1ng=2,R2ng=2), Vop(max=2,R2=1,R1ng=2,R2ng=2)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R1: [['N58_57', 'Vbias2', 'Vx'], ['N64_63', 'Vbias3', 'Vy']] / R2: [] / R1ng: [] / R2ng: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M9a(sd) Vg15->Vop1 사이클=['Vop1', 'Vg15'] 부호=+1
  - M18a(sd) Vg25->Vom1 사이클=['Vom1', 'Vg25'] 부호=+1
  - M57(gs) Vbias2->N58_57 사이클=['N58_57', 'Vbias2'] 부호=+1
  - M58(gd) Vbias2->N58_57 사이클=['N58_57', 'Vbias2'] 부호=-1
  - M58(gs) Vbias2->Vx 사이클=['Vx', 'N58_57', 'Vbias2'] 부호=+1
  - M63(gd) Vbias3->N64_63 사이클=['N64_63', 'Vbias3'] 부호=-1
  - M64(gs) Vbias3->N64_63 사이클=['N64_63', 'Vbias3'] 부호=+1
  - M63(gs) Vbias3->Vy 사이클=['Vy', 'N64_63', 'Vbias3'] 부호=+1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - R1 Vom->Voc: MOS만 [-1, 1] / 수동경유 [-1, 1] || gs제외: MOS만 [-1, 1] / 수동경유 [-1, 1]
  - R1 Voc->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - R2 Voc->Vop: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - R2 Vop->Voc: MOS만 [-1, 1] / 수동경유 [-1, 1] || gs제외: MOS만 [-1, 1] / 수동경유 [-1, 1]
  - Cc1 Vom->N_cc_rz1: MOS만 [] / 수동경유 [-1] || gs제외: MOS만 [] / 수동경유 [-1]
  - Cc1 N_cc_rz1->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz1 N_cc_rz1->Vop1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz1 Vop1->N_cc_rz1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cc2 Vop->N_cc_rz2: MOS만 [] / 수동경유 [-1] || gs제외: MOS만 [] / 수동경유 [-1]
  - Cc2 N_cc_rz2->Vop: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz2 N_cc_rz2->Vom1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz2 Vom1->N_cc_rz2: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cf1 Vom->Vip: MOS만 [-1, 1] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cf2 Vop->Vim: MOS만 [-1, 1] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
- R1 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M18a', 'M18b', 'M9a', 'M9b']; diode_load@idx0=['M57', 'M64']; gd_nonadvancing@idx0=['M1a', 'M1b', 'M2a', 'M2b', 'M3a', 'M3b', 'M4a', 'M4b', 'M58', 'M63']; load@idx0=['M10', 'M17', 'M19', 'M5', 'M6', 'M61', 'M68', 'M7', 'M8']
  - stage 1: 출력노드=['Vom', 'Vop'] | input=['M15', 'M16', 'M25', 'M26']
  - 신호그래프 밖: ['M11a', 'M11b', 'M12', 'M13', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M21', 'M22', 'M23a', 'M24b', 'M36a', 'M36b', 'M37a', 'M37b', 'M38', 'M39', 'M40', 'M60', 'M66']
- R2 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M18a', 'M18b', 'M9a', 'M9b']; diode_load@idx0=['M57', 'M64']; gd_nonadvancing@idx0=['M1a', 'M1b', 'M4a', 'M4b']; load@idx0=['M10', 'M17', 'M19', 'M5', 'M6', 'M61', 'M68', 'M7', 'M8']; mirror_out@idx0=['M2a', 'M2b', 'M3a', 'M3b', 'M58', 'M63']
  - stage 1: 출력노드=['Vom', 'Vop'] | input=['M15', 'M16', 'M25', 'M26']
  - 신호그래프 밖: ['M11a', 'M11b', 'M12', 'M13', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M21', 'M22', 'M23a', 'M24b', 'M36a', 'M36b', 'M37a', 'M37b', 'M38', 'M39', 'M40', 'M60', 'M66']
- R1ng stage 목록:
  - stage 1: 출력노드=['Vg15', 'Vg25', 'Vom1', 'Vop1'] | cascode=['M18a', 'M18b', 'M2a', 'M2b', 'M3a', 'M3b', 'M9a', 'M9b']; input=['M1a', 'M1b', 'M4a', 'M4b']; load=['M10', 'M17', 'M19', 'M8']; tail=['M5', 'M6', 'M7']
  - stage 2: 출력노드=['Vom', 'Vop'] | input=['M15', 'M16', 'M25', 'M26']
  - 신호그래프 밖: ['M11a', 'M11b', 'M12', 'M13', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M21', 'M22', 'M23a', 'M24b', 'M36a', 'M36b', 'M37a', 'M37b', 'M38', 'M39', 'M40', 'M57', 'M58', 'M60', 'M61', 'M63', 'M64', 'M66', 'M68']
- R2ng stage 목록:
  - stage 1: 출력노드=['Vg15', 'Vg25', 'Vom1', 'Vop1'] | cascode=['M18a', 'M18b', 'M2a', 'M2b', 'M3a', 'M3b', 'M9a', 'M9b']; input=['M1a', 'M1b', 'M4a', 'M4b']; load=['M10', 'M17', 'M19', 'M8']; tail=['M5', 'M6', 'M7']
  - stage 2: 출력노드=['Vom', 'Vop'] | input=['M15', 'M16', 'M25', 'M26']
  - 신호그래프 밖: ['M11a', 'M11b', 'M12', 'M13', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M21', 'M22', 'M23a', 'M24b', 'M36a', 'M36b', 'M37a', 'M37b', 'M38', 'M39', 'M40', 'M57', 'M58', 'M60', 'M61', 'M63', 'M64', 'M66', 'M68']

### 뷰 R3-DM: 입력=['Vim'], 출력=['Vom']
- MOS 엣지 32 (gd 12, sd 12, gs 8), 수동 방향엣지 12
- diode/수동 자기루프: [('M11a', 'N11a11b'), ('M11b', 'N11b'), ('M14a', 'N14a14b'), ('M14b', 'N14a_14b'), ('M20a', 'N20a20b'), ('M20b', 'N20b'), ('M23a', 'N24b23a'), ('M24b', 'N23a24b')]
- 접지 shunt 수동소자: [('R1', 'Vom', 'Voc'), ('R2', 'Voc', 'Vop'), ('CL1', 'Vop', 'gnd'), ('CL2', 'Vom', 'gnd'), ('Cs1', 'Vip', 'gnd'), ('Cs2', 'Vim', 'gnd')]
- SCC(MOS만, >1노드): [['Vg15', 'Vom1'], ['N11a11b', 'N11b'], ['N14a14b', 'N14a_14b']]
- SCC(MOS+수동, >1노드): [['N1a2a', 'N3a4a', 'N_cc_rz1', 'Vg15', 'Vim', 'Vom', 'Vom1'], ['N11a11b', 'N11b'], ['N14a14b', 'N14a_14b']]
- BFS 레벨(R1 min index 기준; 괄호: R1 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: Vim(max=0,R2=0)
  - idx 1: N1a2a(max=1,R2=1), N3a4a(max=1,R2=1), Vg15(max=1,R2=1), Vom1(max=1,R2=1)
  - idx 2: Vom(max=2,R2=2)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R1: [] / R2: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M18a(sd) Vg15->Vom1 사이클=['Vom1', 'Vg15'] 부호=+1
  - M9a(sd) Vg15->Vom1 사이클=['Vom1', 'Vg15'] 부호=+1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - Cc1 Vom->N_cc_rz1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cc1 N_cc_rz1->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz1 N_cc_rz1->Vom1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz1 Vom1->N_cc_rz1: MOS만 [] / 수동경유 [1] || gs제외: MOS만 [] / 수동경유 [1]
  - Cc2 Vom->N_cc_rz1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cc2 N_cc_rz1->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz2 N_cc_rz1->Vom1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz2 Vom1->N_cc_rz1: MOS만 [] / 수동경유 [1] || gs제외: MOS만 [] / 수동경유 [1]
  - Cf1 Vom->Vim: MOS만 [-1] / 수동경유 [-1, 1] || gs제외: MOS만 [-1] / 수동경유 [-1, 1]
  - Cf1 Vim->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cf2 Vom->Vim: MOS만 [-1] / 수동경유 [-1, 1] || gs제외: MOS만 [-1] / 수동경유 [-1, 1]
  - Cf2 Vim->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
- R1 stage 목록:
  - stage 1: 출력노드=['Vg15', 'Vom1'] | cascode=['M18a', 'M18b', 'M2a', 'M2b', 'M3a', 'M3b', 'M9a', 'M9b']; input=['M1a', 'M1b', 'M4a', 'M4b']; load=['M10', 'M17', 'M19', 'M8']; tail=['M5', 'M6', 'M7']
  - stage 2: 출력노드=['Vom'] | input=['M15', 'M16', 'M25', 'M26']
  - 신호그래프 밖: ['M11a', 'M11b', 'M12', 'M13', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M21', 'M22', 'M23a', 'M24b', 'M36a', 'M36b', 'M37a', 'M37b', 'M38', 'M39', 'M40', 'M57', 'M58', 'M60', 'M61', 'M63', 'M64', 'M66', 'M68']
- R2 stage 목록:
  - stage 1: 출력노드=['Vg15', 'Vom1'] | cascode=['M18a', 'M18b', 'M2a', 'M2b', 'M3a', 'M3b', 'M9a', 'M9b']; input=['M1a', 'M1b', 'M4a', 'M4b']; load=['M10', 'M17', 'M19', 'M8']; tail=['M5', 'M6', 'M7']
  - stage 2: 출력노드=['Vom'] | input=['M15', 'M16', 'M25', 'M26']
  - 신호그래프 밖: ['M11a', 'M11b', 'M12', 'M13', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M21', 'M22', 'M23a', 'M24b', 'M36a', 'M36b', 'M37a', 'M37b', 'M38', 'M39', 'M40', 'M57', 'M58', 'M60', 'M61', 'M63', 'M64', 'M66', 'M68']

### 뷰 R3-CM: 입력=['Vim'], 출력=['Vom']
- MOS 엣지 79 (gd 35, sd 22, gs 22), 수동 방향엣지 16
- diode/수동 자기루프: [('M11a', 'N11a11b'), ('M11b', 'N11b'), ('M14a', 'N14a14b'), ('M14b', 'N14a_14b'), ('M18_bg', 'Vbias1'), ('M20a', 'N20a20b'), ('M20b', 'N20b'), ('M23a', 'N24b23a'), ('M24b', 'N23a24b'), ('M36a', 'Vcmfb'), ('M36b', 'N36b'), ('M39', 'Voc_des'), ('M57', 'Vbias2'), ('M64', 'Vbias3'), ('M66', 'Vbias4')]
- 접지 shunt 수동소자: [('CL1', 'Vop', 'gnd'), ('CL2', 'Vom', 'gnd'), ('Cs1', 'Vip', 'gnd'), ('Cs2', 'Vim', 'gnd')]
- SCC(MOS만, >1노드): [['Vg15', 'Vom1'], ['N11a11b', 'N11b'], ['N14a14b', 'N14a_14b'], ['N58_57', 'Vbias2', 'Vx'], ['N64_63', 'Vbias3', 'Vy']]
- SCC(MOS+수동, >1노드): [['N1a2a', 'N3a4a', 'N58_57', 'N64_63', 'N_cc_rz1', 'Ncmfb_tail', 'Vbias2', 'Vbias3', 'Vcmfb', 'Vg15', 'Vim', 'Voc', 'Vom', 'Vom1', 'Vx', 'Vy'], ['N11a11b', 'N11b'], ['N14a14b', 'N14a_14b']]
- BFS 레벨(R2 min index 기준; 괄호: R2 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: N1a2a(max=1,R2ng=1), N3a4a(max=1,R2ng=1), N58_57(max=0,R2ng=None), N64_63(max=0,R2ng=None), Vbias2(max=0,R2ng=None), Vbias3(max=0,R2ng=None), Vg15(max=1,R2ng=1), Vim(max=0,R2ng=0), Vom1(max=1,R2ng=1), Vx(max=0,R2ng=None), Vy(max=0,R2ng=None)
  - idx 1: Vom(max=2,R2ng=2)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R2: [] / R2ng: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M18a(sd) Vg15->Vom1 사이클=['Vom1', 'Vg15'] 부호=+1
  - M9a(sd) Vg15->Vom1 사이클=['Vom1', 'Vg15'] 부호=+1
  - M57(gs) Vbias2->N58_57 사이클=['N58_57', 'Vbias2'] 부호=+1
  - M58(gd) Vbias2->N58_57 사이클=['N58_57', 'Vbias2'] 부호=-1
  - M58(gs) Vbias2->Vx 사이클=['Vx', 'N58_57', 'Vbias2'] 부호=+1
  - M63(gd) Vbias3->N64_63 사이클=['N64_63', 'Vbias3'] 부호=-1
  - M64(gs) Vbias3->N64_63 사이클=['N64_63', 'Vbias3'] 부호=+1
  - M63(gs) Vbias3->Vy 사이클=['Vy', 'N64_63', 'Vbias3'] 부호=+1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - R1 Vom->Voc: MOS만 [-1, 1] / 수동경유 [-1, 1] || gs제외: MOS만 [-1, 1] / 수동경유 [-1, 1]
  - R1 Voc->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - R2 Voc->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - R2 Vom->Voc: MOS만 [-1, 1] / 수동경유 [-1, 1] || gs제외: MOS만 [-1, 1] / 수동경유 [-1, 1]
  - Cc1 Vom->N_cc_rz1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cc1 N_cc_rz1->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz1 N_cc_rz1->Vom1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz1 Vom1->N_cc_rz1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cc2 Vom->N_cc_rz1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cc2 N_cc_rz1->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz2 N_cc_rz1->Vom1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Rz2 Vom1->N_cc_rz1: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cf1 Vom->Vim: MOS만 [-1, 1] / 수동경유 [-1, 1] || gs제외: MOS만 [1] / 수동경유 [-1, 1]
  - Cf1 Vim->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
  - Cf2 Vom->Vim: MOS만 [-1, 1] / 수동경유 [-1, 1] || gs제외: MOS만 [1] / 수동경유 [-1, 1]
  - Cf2 Vim->Vom: MOS만 [] / 수동경유 [-1, 1] || gs제외: MOS만 [] / 수동경유 [-1, 1]
- R2 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M18a', 'M18b', 'M9a', 'M9b']; diode_load@idx0=['M57', 'M64']; gd_nonadvancing@idx0=['M1a', 'M1b', 'M4a', 'M4b']; load@idx0=['M10', 'M17', 'M19', 'M5', 'M6', 'M61', 'M68', 'M7', 'M8']; mirror_out@idx0=['M2a', 'M2b', 'M3a', 'M3b', 'M58', 'M63']
  - stage 1: 출력노드=['Vom'] | input=['M15', 'M16', 'M25', 'M26']
  - 신호그래프 밖: ['M11a', 'M11b', 'M12', 'M13', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M21', 'M22', 'M23a', 'M24b', 'M36a', 'M36b', 'M37a', 'M37b', 'M38', 'M39', 'M40', 'M60', 'M66']
- R2ng stage 목록:
  - stage 1: 출력노드=['Vg15', 'Vom1'] | cascode=['M18a', 'M18b', 'M2a', 'M2b', 'M3a', 'M3b', 'M9a', 'M9b']; input=['M1a', 'M1b', 'M4a', 'M4b']; load=['M10', 'M17', 'M19', 'M8']; tail=['M5', 'M6', 'M7']
  - stage 2: 출력노드=['Vom'] | input=['M15', 'M16', 'M25', 'M26']
  - 신호그래프 밖: ['M11a', 'M11b', 'M12', 'M13', 'M14a', 'M14b', 'M18_bg', 'M20a', 'M20b', 'M21', 'M22', 'M23a', 'M24b', 'M36a', 'M36b', 'M37a', 'M37b', 'M38', 'M39', 'M40', 'M57', 'M58', 'M60', 'M61', 'M63', 'M64', 'M66', 'M68']

### 선언 stage 대조 (소자 단위, 규칙 stage == 선언 stage)
| 선언 | 규칙/뷰 | 일치/전체 | 불일치(소자: 선언→규칙[역할]) |
|---|---|---|---|
| compensation.stage_devices+shared_gm_id_groups | R1 | 0/8 | M1a:1→0[gd_nonadvancing@idx0], M1b:1→0[gd_nonadvancing@idx0], M4a:1→0[gd_nonadvancing@idx0], M4b:1→0[gd_nonadvancing@idx0], M15:2→1[input], M25:2→1[input], M16:2→1[input], M26:2→1[input] |
| compensation.stage_devices+shared_gm_id_groups | R2 | 0/8 | M1a:1→0[gd_nonadvancing@idx0], M1b:1→0[gd_nonadvancing@idx0], M4a:1→0[gd_nonadvancing@idx0], M4b:1→0[gd_nonadvancing@idx0], M15:2→1[input], M25:2→1[input], M16:2→1[input], M26:2→1[input] |
| compensation.stage_devices+shared_gm_id_groups | R1ng | 8/8 | - |
| compensation.stage_devices+shared_gm_id_groups | R2ng | 8/8 | - |
| compensation.stage_devices+shared_gm_id_groups | R3(DM/R1) | 8/8 | - |
| compensation.stage_devices+shared_gm_id_groups | R3(DM/R2) | 8/8 | - |
| compensation.stage_devices+shared_gm_id_groups | R3(CM/R2) | 0/8 | M1a:1→0[gd_nonadvancing@idx0], M1b:1→0[gd_nonadvancing@idx0], M4a:1→0[gd_nonadvancing@idx0], M4b:1→0[gd_nonadvancing@idx0], M15:2→1[input], M25:2→1[input], M16:2→1[input], M26:2→1[input] |
| compensation.stage_devices+shared_gm_id_groups | R3(CM/R2ng) | 8/8 | - |
| metrics.gain_db.stages(gain_stages_sum) | R1 | 0/6 | M1a:1→0[gd_nonadvancing@idx0], M4a:1→0[gd_nonadvancing@idx0], M2a:1→0[gd_nonadvancing@idx0], M3a:1→0[gd_nonadvancing@idx0], M15:2→1[input], M16:2→1[input] |
| metrics.gain_db.stages(gain_stages_sum) | R2 | 0/6 | M1a:1→0[gd_nonadvancing@idx0], M4a:1→0[gd_nonadvancing@idx0], M2a:1→0[mirror_out@idx0], M3a:1→0[mirror_out@idx0], M15:2→1[input], M16:2→1[input] |
| metrics.gain_db.stages(gain_stages_sum) | R1ng | 6/6 | - |
| metrics.gain_db.stages(gain_stages_sum) | R2ng | 6/6 | - |
| metrics.gain_db.stages(gain_stages_sum) | R3(DM/R1) | 6/6 | - |
| metrics.gain_db.stages(gain_stages_sum) | R3(DM/R2) | 6/6 | - |
| metrics.gain_db.stages(gain_stages_sum) | R3(CM/R2) | 0/6 | M1a:1→0[gd_nonadvancing@idx0], M4a:1→0[gd_nonadvancing@idx0], M2a:1→0[mirror_out@idx0], M3a:1→0[mirror_out@idx0], M15:2→1[input], M16:2→1[input] |
| metrics.gain_db.stages(gain_stages_sum) | R3(CM/R2ng) | 6/6 | - |

### stage 출력노드 gds 기여자 (R3-DM/R2 stage index, 원 넷 기준: 선언 stage-k 소자의 drain 넷 중 DM idx==k 이고 같은 stage 신호소자의 source가 아닌(=캐스코드 사슬 꼭대기) 넷; diode 노드는 따로 표시)
- [metrics.gain_db.stages(gain_stages_sum)] stage 1 노드 Vom1
  - drain 접속(gds/ro 사슬): ['M18a<-[M17 | M18b<-[M19 | M2a<-[M1a]@N1a2a | M3a<-[M4a]@N3a4a]@Vom1]@Vg25', 'M19', 'M2a<-[M1a]@N1a2a', 'M3a<-[M4a]@N3a4a']
  - source 접속(소스 들여다본 1/gm 부하): ['M18b']
  - 수동소자: ['Rz2']
  - 선언 stage 목록 **누락**: drain접속 ['M18a', 'M19'], source접속 ['M18b'], 사슬 하위 ['M17', 'M18b']
- [metrics.gain_db.stages(gain_stages_sum)] stage 2 노드 Vom
  - drain 접속(gds/ro 사슬): ['M15', 'M16']
  - source 접속(소스 들여다본 1/gm 부하): []
  - 수동소자: ['CL2', 'Cc1', 'Cf1', 'R1']
  - 선언 stage 목록 **누락**: drain접속 [], source접속 [], 사슬 하위 []

### 기존 함수 교차확인
- find_differential_pair_candidates: [(('M1a', 'M1b'), 'Vx'), (('M37a', 'M37b'), 'Ncmfb_tail'), (('M4a', 'M4b'), 'Vy')]
- tail: R3-DM/R2 규칙=['M5', 'M6', 'M7'] / gain_stage_tails(선언 기반)={'M5': {'stage_index': 0, 'is_input_stage': True}, 'M6': {'stage_index': 0, 'is_input_stage': True}, 'M7': {'stage_index': 0, 'is_input_stage': True}} / diffpair shared_source를 drain으로 갖는 소자=['M38', 'M5', 'M6', 'M7']
- true_current_mirror_groups: [['M10', 'M12', 'M19', 'M21', 'M38', 'M5', 'M66', 'M68'], ['M13', 'M17', 'M18_bg', 'M22', 'M6', 'M60', 'M61', 'M8'], ['M36a', 'M7']]
- trace_vdd_to_gnd_branches: branch 30개
- signal_path_nodes(excite=입력, sense=출력; 접지 절단·gs엣지 없음) = ['N1a2a', 'N1b2b', 'N3a4a', 'N3b4b', 'Vg15', 'Vg25', 'Vom1', 'Vop1']
  - 이 probe full/R1 도달노드에만 있음: ['N58_57', 'N64_63', 'Vbias2', 'Vbias3', 'Vx', 'Vy'] / signal_path_nodes에만 있음: []

## folded_cascode

- 소자 13개, 수동소자 0개, ideal_sources 1개, ports 선언 없음
- 입력 넷: ['vin_n', 'vin_p'] (제안: gate-only 비구동 넷 중 이름에 'in'); p/n 짝=('vin_p', 'vin_n')
- 출력 넷: ['out'] (제안: drain 전용·게이트 미구동 넷(sink)); p/n 짝=None
- 교류접지 G1(레일): ['gnd', 'vdd']
- 교류접지 G2(gate-only 비구동, 입력·수동·이상원 단자 아님): ['bias3']
- 교류접지 G3(이상 전압원 단자): []
- diode 노드(is_diode_connected drain): ['Vg7', 'Vg9', 'vb1', 'vb2']

### 대칭 net 대응 (find_structural_symmetry_candidates, mirror)
- 자기대응(차동모드 가상접지로 취급): ['bias3', 'tail', 'vb1', 'vb2']
- 수동소자로 확장한 대응[신규]: []
- 단일출력이라 대응을 제거한 것[신규 규칙]: [('out', 'Vg7')]
- conflicts=[] unresolved=['M10', 'M7', 'M8', 'M9'] low_conf=[['M1', 'M2'], ['M5', 'M6']]

### 뷰 full: 입력=['vin_n', 'vin_p'], 출력=['out']
- MOS 엣지 17 (gd 7, sd 6, gs 4), 수동 방향엣지 0
- diode/수동 자기루프: [('M7', 'Vg7'), ('M9', 'Vg9'), ('MN', 'vb2'), ('MP', 'vb1')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): [['Vg7', 'Vg9']]
- SCC(MOS+수동, >1노드): [['Vg7', 'Vg9']]
- BFS 레벨(R1 min index 기준; 괄호: R1 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: Vg10(max=2,R2=0,R1ng=None,R2ng=None), Vg7(max=1,R2=0,R1ng=1,R2ng=1), Vg9(max=1,R2=0,R1ng=None,R2ng=None), X(max=1,R2=0,R1ng=1,R2ng=1), Y(max=1,R2=0,R1ng=1,R2ng=1), out(max=2,R2=0,R1ng=1,R2ng=1), tail(max=0,R2=0,R1ng=None,R2ng=None), vin_n(max=0,R2=0,R1ng=0,R2ng=0), vin_p(max=0,R2=0,R1ng=0,R2ng=0)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R1: [] / R2: [] / R1ng: [] / R2ng: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M7(sd) Vg9->Vg7 사이클=['Vg7', 'Vg9'] 부호=+1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R1 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M5', 'M6']; diode_load@idx0=['M7', 'M9']; gd_nonadvancing@idx0=['M1', 'M10', 'M2', 'M8']; load@idx0=['M11', 'M3', 'M4']
  - 신호그래프 밖: ['MN', 'MP']
- R2 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M5', 'M6']; diode_load@idx0=['M7', 'M9']; gd_nonadvancing@idx0=['M1', 'M2']; load@idx0=['M11', 'M3', 'M4']; mirror_out@idx0=['M10', 'M8']
  - 신호그래프 밖: ['MN', 'MP']
- R1ng stage 목록:
  - stage 1: 출력노드=['out'] | cascode=['M5', 'M6']; diode_load=['M7']; gd_nonadvancing=['M8']; input=['M1', 'M2']; load=['M3', 'M4']; tail=['M11']
  - 신호그래프 밖: ['M10', 'M9', 'MN', 'MP']
- R2ng stage 목록:
  - stage 1: 출력노드=['out'] | cascode=['M5', 'M6']; diode_load=['M7']; input=['M1', 'M2']; load=['M3', 'M4']; mirror_out=['M8']; tail=['M11']
  - 신호그래프 밖: ['M10', 'M9', 'MN', 'MP']

### 뷰 R3-DM: 입력=['vin_n'], 출력=['out']
- MOS 엣지 10 (gd 4, sd 4, gs 2), 수동 방향엣지 0
- diode/수동 자기루프: [('M7', 'Vg7'), ('M9', 'Vg9')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): [['Vg7', 'Vg9']]
- SCC(MOS+수동, >1노드): [['Vg7', 'Vg9']]
- BFS 레벨(R1 min index 기준; 괄호: R1 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: vin_n(max=0,R2=0)
  - idx 1: Vg10(max=2,R2=1), Vg7(max=1,R2=1), Vg9(max=1,R2=1), X(max=1,R2=1), out(max=2,R2=1)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R1: [] / R2: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M7(sd) Vg9->Vg7 사이클=['Vg7', 'Vg9'] 부호=+1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R1 stage 목록:
  - stage 1: 출력노드=['out'] | cascode=['M5', 'M6']; diode_load=['M7', 'M9']; gd_nonadvancing=['M10', 'M8']; input=['M1', 'M2']; load=['M3', 'M4']; tail=['M11']
  - 신호그래프 밖: ['MN', 'MP']
- R2 stage 목록:
  - stage 1: 출력노드=['out'] | cascode=['M5', 'M6']; diode_load=['M7', 'M9']; input=['M1', 'M2']; load=['M3', 'M4']; mirror_out=['M10', 'M8']; tail=['M11']
  - 신호그래프 밖: ['MN', 'MP']

### 뷰 R3-CM: 입력=['vin_n'], 출력=['out']
- MOS 엣지 17 (gd 7, sd 6, gs 4), 수동 방향엣지 0
- diode/수동 자기루프: [('M7', 'Vg7'), ('M9', 'Vg9'), ('MN', 'vb2'), ('MP', 'vb1')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): [['Vg7', 'Vg9']]
- SCC(MOS+수동, >1노드): [['Vg7', 'Vg9']]
- BFS 레벨(R2 min index 기준; 괄호: R2 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: Vg10(max=1,R2ng=None), Vg7(max=1,R2ng=1), Vg9(max=1,R2ng=None), X(max=1,R2ng=1), out(max=1,R2ng=1), tail(max=0,R2ng=None), vin_n(max=0,R2ng=0)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R2: [] / R2ng: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M7(sd) Vg9->Vg7 사이클=['Vg7', 'Vg9'] 부호=+1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R2 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M5', 'M6']; diode_load@idx0=['M7', 'M9']; gd_nonadvancing@idx0=['M1', 'M2']; load@idx0=['M11', 'M3', 'M4']; mirror_out@idx0=['M10', 'M8']
  - 신호그래프 밖: ['MN', 'MP']
- R2ng stage 목록:
  - stage 1: 출력노드=['out'] | cascode=['M5', 'M6']; diode_load=['M7']; input=['M1', 'M2']; load=['M3', 'M4']; mirror_out=['M8']; tail=['M11']
  - 신호그래프 밖: ['M10', 'M9', 'MN', 'MP']

### 선언 stage 대조 (소자 단위, 규칙 stage == 선언 stage)
| 선언 | 규칙/뷰 | 일치/전체 | 불일치(소자: 선언→규칙[역할]) |
|---|---|---|---|
| metrics.gain_db(folded_cascode_gain_db) 역할필드 | R1 | 0/5 | M1:1→0[gd_nonadvancing@idx0], M3:1→0[load@idx0], M6:1→0[cascode@idx0], M8:1→0[gd_nonadvancing@idx0], M10:1→0[gd_nonadvancing@idx0] |
| metrics.gain_db(folded_cascode_gain_db) 역할필드 | R2 | 0/5 | M1:1→0[gd_nonadvancing@idx0], M3:1→0[load@idx0], M6:1→0[cascode@idx0], M8:1→0[mirror_out@idx0], M10:1→0[mirror_out@idx0] |
| metrics.gain_db(folded_cascode_gain_db) 역할필드 | R1ng | 4/5 | M10:1→None[not_in_signal] |
| metrics.gain_db(folded_cascode_gain_db) 역할필드 | R2ng | 4/5 | M10:1→None[not_in_signal] |
| metrics.gain_db(folded_cascode_gain_db) 역할필드 | R3(DM/R1) | 5/5 | - |
| metrics.gain_db(folded_cascode_gain_db) 역할필드 | R3(DM/R2) | 5/5 | - |
| metrics.gain_db(folded_cascode_gain_db) 역할필드 | R3(CM/R2) | 0/5 | M1:1→0[gd_nonadvancing@idx0], M3:1→0[load@idx0], M6:1→0[cascode@idx0], M8:1→0[mirror_out@idx0], M10:1→0[mirror_out@idx0] |
| metrics.gain_db(folded_cascode_gain_db) 역할필드 | R3(CM/R2ng) | 4/5 | M10:1→None[not_in_signal] |
| metrics.gain_db(folded_cascode_gain_db) 역할필드 역할필드 vs R3-DM/R2 역할 | | | M1:gm1_device→input, M3:fold_leg_b→load, M6:cascode_p→cascode, M8:cascode_n→mirror_out, M10:mirror_n→mirror_out |

### stage 출력노드 gds 기여자 (R3-DM/R2 stage index, 원 넷 기준: 선언 stage-k 소자의 drain 넷 중 DM idx==k 이고 같은 stage 신호소자의 source가 아닌(=캐스코드 사슬 꼭대기) 넷; diode 노드는 따로 표시)
- [metrics.gain_db(folded_cascode_gain_db) 역할필드] stage 1 노드 out
  - drain 접속(gds/ro 사슬): ['M6<-[M1 | M3]@X', 'M8<-[M10]@Vg10']
  - source 접속(소스 들여다본 1/gm 부하): []
  - 수동소자: []
  - 선언 stage 목록 **누락**: drain접속 [], source접속 [], 사슬 하위 []

### 기존 함수 교차확인
- find_differential_pair_candidates: [(('M1', 'M2'), 'tail')]
- tail: R3-DM/R2 규칙=['M11'] / gain_stage_tails(선언 기반)={} / diffpair shared_source를 drain으로 갖는 소자=['M11']
- true_current_mirror_groups: [['M10', 'M9'], ['M11', 'MN'], ['M3', 'M4', 'MP']]
- trace_vdd_to_gnd_branches: branch 3개
- signal_path_nodes(excite=입력, sense=출력; 접지 절단·gs엣지 없음) = ['Vg7', 'X', 'Y']
  - 이 probe full/R1 도달노드에만 있음: ['Vg10', 'Vg9', 'tail'] / signal_path_nodes에만 있음: []

## two_stage_ota

- 소자 7개, 수동소자 0개, ideal_sources 0개, ports 선언 있음
- 입력 넷: ['vin_n', 'vin_p'] (ports 선언); p/n 짝=('vin_p', 'vin_n')
- 출력 넷: ['OUT'] (제안: gain metric sense_p/n); p/n 짝=None
- 교류접지 G1(레일): ['gnd', 'vdd']
- 교류접지 G2(gate-only 비구동, 입력·수동·이상원 단자 아님): ['bias']
- 교류접지 G3(이상 전압원 단자): []
- diode 노드(is_diode_connected drain): ['D3']
- 대조: gain metric excite=0(선언 교류접지) ['bias', 'vdd'] / 규칙 G에 없는 것 []

### 대칭 net 대응 (find_structural_symmetry_candidates, mirror)
- 자기대응(차동모드 가상접지로 취급): ['CS', 'bias']
- 수동소자로 확장한 대응[신규]: []
- 단일출력이라 대응을 제거한 것[신규 규칙]: [('OUT', 'OUT')]
- conflicts=[] unresolved=['M3', 'M4', 'M6'] low_conf=[['M1', 'M2']]

### 뷰 full: 입력=['vin_n', 'vin_p'], 출력=['OUT']
- MOS 엣지 8 (gd 4, sd 2, gs 2), 수동 방향엣지 0
- diode/수동 자기루프: [('M3', 'D3')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): []
- SCC(MOS+수동, >1노드): []
- BFS 레벨(R1 min index 기준; 괄호: R1 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: CS(max=0,R2=0,R1ng=None,R2ng=None), D3(max=1,R2=0,R1ng=1,R2ng=1), O1(max=2,R2=0,R1ng=1,R2ng=1), vin_n(max=0,R2=0,R1ng=0,R2ng=0), vin_p(max=0,R2=0,R1ng=0,R2ng=0)
  - idx 1: OUT(max=3,R2=1,R1ng=2,R2ng=2)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R1: [] / R2: [] / R1ng: [] / R2ng: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R1 stage 목록:
  - stage 0: 출력노드=[] | diode_load@idx0=['M3']; gd_nonadvancing@idx0=['M1', 'M2', 'M4']; load@idx0=['M5']
  - stage 1: 출력노드=['OUT'] | input=['M6']; load=['M7']
  - 신호그래프 밖: []
- R2 stage 목록:
  - stage 0: 출력노드=[] | diode_load@idx0=['M3']; gd_nonadvancing@idx0=['M1', 'M2']; load@idx0=['M5']; mirror_out@idx0=['M4']
  - stage 1: 출력노드=['OUT'] | input=['M6']; load=['M7']
  - 신호그래프 밖: []
- R1ng stage 목록:
  - stage 1: 출력노드=['O1'] | diode_load=['M3']; gd_nonadvancing=['M4']; input=['M1', 'M2']; tail=['M5']
  - stage 2: 출력노드=['OUT'] | input=['M6']; load=['M7']
  - 신호그래프 밖: []
- R2ng stage 목록:
  - stage 1: 출력노드=['O1'] | diode_load=['M3']; input=['M1', 'M2']; mirror_out=['M4']; tail=['M5']
  - stage 2: 출력노드=['OUT'] | input=['M6']; load=['M7']
  - 신호그래프 밖: []

### 뷰 R3-DM: 입력=['vin_n'], 출력=['OUT']
- MOS 엣지 4 (gd 4, sd 0, gs 0), 수동 방향엣지 0
- diode/수동 자기루프: [('M3', 'D3')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): []
- SCC(MOS+수동, >1노드): []
- BFS 레벨(R1 min index 기준; 괄호: R1 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: vin_n(max=0,R2=0)
  - idx 1: D3(max=1,R2=1)
  - idx 2: OUT(max=2,R2=2)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R1: [['D3']] / R2: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M4(gd) D3->D3 사이클=['D3'] 부호=+1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R1 stage 목록:
  - stage 1: 출력노드=['D3'] | diode_load=['M3']; gd_nonadvancing=['M4']; input=['M1', 'M2']; tail=['M5']
  - stage 2: 출력노드=['OUT'] | input=['M6']; load=['M7']
  - 신호그래프 밖: []
- R2 stage 목록:
  - stage 1: 출력노드=[] | diode_load=['M3']; input=['M1', 'M2']; mirror_out=['M4']; tail=['M5']
  - stage 2: 출력노드=['OUT'] | input=['M6']; load=['M7']
  - 신호그래프 밖: []

### 뷰 R3-CM: 입력=['vin_n'], 출력=['OUT']
- MOS 엣지 8 (gd 4, sd 2, gs 2), 수동 방향엣지 0
- diode/수동 자기루프: [('M3', 'D3')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): []
- SCC(MOS+수동, >1노드): []
- BFS 레벨(R2 min index 기준; 괄호: R2 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: CS(max=0,R2ng=None), D3(max=1,R2ng=1), vin_n(max=0,R2ng=0)
  - idx 1: OUT(max=2,R2ng=2)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R2: [] / R2ng: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M4(gd) D3->D3 사이클=['D3'] 부호=-1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R2 stage 목록:
  - stage 0: 출력노드=[] | diode_load@idx0=['M3']; gd_nonadvancing@idx0=['M1', 'M2']; load@idx0=['M5']; mirror_out@idx0=['M4']
  - stage 1: 출력노드=['OUT'] | input=['M6']; load=['M7']
  - 신호그래프 밖: []
- R2ng stage 목록:
  - stage 1: 출력노드=[] | diode_load=['M3']; input=['M1', 'M2']; mirror_out=['M4']; tail=['M5']
  - stage 2: 출력노드=['OUT'] | input=['M6']; load=['M7']
  - 신호그래프 밖: []

### 선언 stage 대조 (소자 단위, 규칙 stage == 선언 stage)
| 선언 | 규칙/뷰 | 일치/전체 | 불일치(소자: 선언→규칙[역할]) |
|---|---|---|---|
| compensation.stage_devices | R1 | 0/3 | M1:1→0[gd_nonadvancing@idx0], M2:1→0[gd_nonadvancing@idx0], M6:2→1[input] |
| compensation.stage_devices | R2 | 0/3 | M1:1→0[gd_nonadvancing@idx0], M2:1→0[gd_nonadvancing@idx0], M6:2→1[input] |
| compensation.stage_devices | R1ng | 3/3 | - |
| compensation.stage_devices | R2ng | 3/3 | - |
| compensation.stage_devices | R3(DM/R1) | 3/3 | - |
| compensation.stage_devices | R3(DM/R2) | 3/3 | - |
| compensation.stage_devices | R3(CM/R2) | 0/3 | M1:1→0[gd_nonadvancing@idx0], M2:1→0[gd_nonadvancing@idx0], M6:2→1[input] |
| compensation.stage_devices | R3(CM/R2ng) | 3/3 | - |

### stage 출력노드 gds 기여자 (R3-DM/R2 stage index, 원 넷 기준: 선언 stage-k 소자의 drain 넷 중 DM idx==k 이고 같은 stage 신호소자의 source가 아닌(=캐스코드 사슬 꼭대기) 넷; diode 노드는 따로 표시)
- (gain metric에 소자 목록이 없음 -> compensation.stage_devices로 대조)
- [compensation.stage_devices] stage 1 노드 D3: **diode 노드**(저임피던스, 이득 출력노드 아님) -- drain 접속 ['M1', 'M3']
- [compensation.stage_devices] stage 1 노드 O1
  - drain 접속(gds/ro 사슬): ['M2', 'M4']
  - source 접속(소스 들여다본 1/gm 부하): []
  - 수동소자: []
  - 선언 stage 목록 **누락**: drain접속 ['M4'], source접속 [], 사슬 하위 []
- [compensation.stage_devices] stage 2 노드 OUT
  - drain 접속(gds/ro 사슬): ['M6', 'M7']
  - source 접속(소스 들여다본 1/gm 부하): []
  - 수동소자: []
  - 선언 stage 목록 **누락**: drain접속 ['M7'], source접속 [], 사슬 하위 []

### 기존 함수 교차확인
- find_differential_pair_candidates: [(('M1', 'M2'), 'CS')]
- tail: R3-DM/R2 규칙=['M5'] / gain_stage_tails(선언 기반)={} / diffpair shared_source를 drain으로 갖는 소자=['M5']
- true_current_mirror_groups: [['M3', 'M4'], ['M5', 'M7']]
- trace_vdd_to_gnd_branches: branch 3개
- signal_path_nodes(excite=입력, sense=출력; 접지 절단·gs엣지 없음) = ['D3', 'O1']
  - 이 probe full/R1 도달노드에만 있음: ['CS'] / signal_path_nodes에만 있음: []

## nmcnr_amplifier

- 소자 15개, 수동소자 0개, ideal_sources 0개, ports 선언 없음
- 입력 넷: ['Vin_n', 'Vin_p'] (제안: gate-only 비구동 넷 중 이름에 'in'); p/n 짝=('Vin_p', 'Vin_n')
- 출력 넷: ['Vout'] (제안: drain 전용·게이트 미구동 넷(sink)); p/n 짝=None
- 교류접지 G1(레일): ['vdd', 'vss']
- 교류접지 G2(gate-only 비구동, 입력·수동·이상원 단자 아님): ['VB1', 'VB2', 'VB3', 'VB4', 'VB5']
- 교류접지 G3(이상 전압원 단자): []
- diode 노드(is_diode_connected drain): ['NodeC', 'NodeM1']

### 대칭 net 대응 (find_structural_symmetry_candidates, mirror)
- 자기대응(차동모드 가상접지로 취급): ['NodeTail', 'VB1', 'VB2', 'VB3']
- 수동소자로 확장한 대응[신규]: []
- 단일출력이라 대응을 제거한 것[신규 규칙]: []
- conflicts=[] unresolved=['M108', 'M109', 'M201', 'M202', 'M203', 'M204', 'M301', 'M302'] low_conf=[['M102', 'M103'], ['M106', 'M107']]

### 뷰 full: 입력=['Vin_n', 'Vin_p'], 출력=['Vout']
- MOS 엣지 12 (gd 6, sd 4, gs 2), 수동 방향엣지 0
- diode/수동 자기루프: [('M108', 'NodeM1'), ('M203', 'NodeC')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): []
- SCC(MOS+수동, >1노드): []
- BFS 레벨(R1 min index 기준; 괄호: R1 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: NodeF1(max=1,R2=0,R1ng=1,R2ng=1), NodeF2(max=1,R2=0,R1ng=1,R2ng=1), NodeM1(max=1,R2=0,R1ng=1,R2ng=1), NodeM2(max=2,R2=0,R1ng=1,R2ng=1), NodeTail(max=0,R2=0,R1ng=None,R2ng=None), Vin_n(max=0,R2=0,R1ng=0,R2ng=0), Vin_p(max=0,R2=0,R1ng=0,R2ng=0)
  - idx 1: NodeC(max=3,R2=1,R1ng=2,R2ng=2)
  - idx 2: NodeS2(max=4,R2=1,R1ng=3,R2ng=2)
  - idx 3: Vout(max=5,R2=2,R1ng=4,R2ng=3)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R1: [] / R2: [] / R1ng: [] / R2ng: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R1 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M106', 'M107']; diode_load@idx0=['M108']; gd_nonadvancing@idx0=['M102', 'M103', 'M109']; load@idx0=['M101', 'M104', 'M105']
  - stage 1: 출력노드=['NodeC'] | diode_load=['M203']; input=['M201']
  - stage 2: 출력노드=['NodeS2'] | input=['M204']; load=['M202']
  - stage 3: 출력노드=['Vout'] | input=['M301']; load=['M302']
  - 신호그래프 밖: []
- R2 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M106', 'M107']; diode_load@idx0=['M108']; gd_nonadvancing@idx0=['M102', 'M103']; load@idx0=['M101', 'M104', 'M105']; mirror_out@idx0=['M109']
  - stage 1: 출력노드=['NodeS2'] | diode_load=['M203']; input=['M201']; load=['M202']; mirror_out=['M204']
  - stage 2: 출력노드=['Vout'] | input=['M301']; load=['M302']
  - 신호그래프 밖: []
- R1ng stage 목록:
  - stage 1: 출력노드=['NodeM2'] | cascode=['M106', 'M107']; diode_load=['M108']; gd_nonadvancing=['M109']; input=['M102', 'M103']; load=['M104', 'M105']; tail=['M101']
  - stage 2: 출력노드=['NodeC'] | diode_load=['M203']; input=['M201']
  - stage 3: 출력노드=['NodeS2'] | input=['M204']; load=['M202']
  - stage 4: 출력노드=['Vout'] | input=['M301']; load=['M302']
  - 신호그래프 밖: []
- R2ng stage 목록:
  - stage 1: 출력노드=['NodeM2'] | cascode=['M106', 'M107']; diode_load=['M108']; input=['M102', 'M103']; load=['M104', 'M105']; mirror_out=['M109']; tail=['M101']
  - stage 2: 출력노드=['NodeS2'] | diode_load=['M203']; input=['M201']; load=['M202']; mirror_out=['M204']
  - stage 3: 출력노드=['Vout'] | input=['M301']; load=['M302']
  - 신호그래프 밖: []

### 뷰 R3-DM: 입력=['Vin_n'], 출력=['Vout']
- MOS 엣지 8 (gd 6, sd 2, gs 0), 수동 방향엣지 0
- diode/수동 자기루프: [('M108', 'NodeM1'), ('M203', 'NodeC')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): []
- SCC(MOS+수동, >1노드): []
- BFS 레벨(R1 min index 기준; 괄호: R1 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: Vin_n(max=0,R2=0)
  - idx 1: NodeF1(max=1,R2=1), NodeM1(max=1,R2=1)
  - idx 2: NodeC(max=2,R2=2)
  - idx 3: NodeS2(max=3,R2=2)
  - idx 4: Vout(max=4,R2=3)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R1: [['NodeM1']] / R2: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M109(gd) NodeM1->NodeM1 사이클=['NodeM1'] 부호=+1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R1 stage 목록:
  - stage 1: 출력노드=['NodeM1'] | cascode=['M106', 'M107']; diode_load=['M108']; gd_nonadvancing=['M109']; input=['M102', 'M103']; load=['M104', 'M105']; tail=['M101']
  - stage 2: 출력노드=['NodeC'] | diode_load=['M203']; input=['M201']
  - stage 3: 출력노드=['NodeS2'] | input=['M204']; load=['M202']
  - stage 4: 출력노드=['Vout'] | input=['M301']; load=['M302']
  - 신호그래프 밖: []
- R2 stage 목록:
  - stage 1: 출력노드=[] | cascode=['M106', 'M107']; diode_load=['M108']; input=['M102', 'M103']; load=['M104', 'M105']; mirror_out=['M109']; tail=['M101']
  - stage 2: 출력노드=['NodeS2'] | diode_load=['M203']; input=['M201']; load=['M202']; mirror_out=['M204']
  - stage 3: 출력노드=['Vout'] | input=['M301']; load=['M302']
  - 신호그래프 밖: []

### 뷰 R3-CM: 입력=['Vin_n'], 출력=['Vout']
- MOS 엣지 12 (gd 6, sd 4, gs 2), 수동 방향엣지 0
- diode/수동 자기루프: [('M108', 'NodeM1'), ('M203', 'NodeC')]
- 접지 shunt 수동소자: []
- SCC(MOS만, >1노드): []
- SCC(MOS+수동, >1노드): []
- BFS 레벨(R2 min index 기준; 괄호: R2 max(응축 DAG 최장경로), 다른 규칙 min):
  - idx 0: NodeF1(max=1,R2ng=1), NodeM1(max=1,R2ng=1), NodeTail(max=0,R2ng=None), Vin_n(max=0,R2ng=0)
  - idx 1: NodeC(max=2,R2ng=2), NodeS2(max=2,R2ng=2)
  - idx 2: Vout(max=3,R2ng=3)
- 양(+) 가중 사이클 SCC(gd 포함 -> 최장경로 불확정): R2: [] / R2ng: []
- MOS만의 루프(DFS back edge, 부호곱 -1=반전 +1=비반전):
  - M109(gd) NodeM1->NodeM1 사이클=['NodeM1'] 부호=-1
- 수동소자가 닫는 루프(수동 u->v + 복귀경로 v=>u 부호집합; -1=부궤환 후보, 저주파 부호; [MOS만 복귀]/[다른 수동 경유 복귀], 괄호 뒤=gs 엣지 제외 시):
  - (수동 엣지 없음)
- R2 stage 목록:
  - stage 0: 출력노드=[] | cascode@idx0=['M106', 'M107']; diode_load@idx0=['M108']; gd_nonadvancing@idx0=['M102', 'M103']; load@idx0=['M101', 'M104', 'M105']; mirror_out@idx0=['M109']
  - stage 1: 출력노드=['NodeS2'] | diode_load=['M203']; input=['M201']; load=['M202']; mirror_out=['M204']
  - stage 2: 출력노드=['Vout'] | input=['M301']; load=['M302']
  - 신호그래프 밖: []
- R2ng stage 목록:
  - stage 1: 출력노드=[] | cascode=['M106', 'M107']; diode_load=['M108']; input=['M102', 'M103']; load=['M104', 'M105']; mirror_out=['M109']; tail=['M101']
  - stage 2: 출력노드=['NodeS2'] | diode_load=['M203']; input=['M201']; load=['M202']; mirror_out=['M204']
  - stage 3: 출력노드=['Vout'] | input=['M301']; load=['M302']
  - 신호그래프 밖: []

### 선언 stage 대조 (소자 단위, 규칙 stage == 선언 stage)
| 선언 | 규칙/뷰 | 일치/전체 | 불일치(소자: 선언→규칙[역할]) |
|---|---|---|---|
| compensation.stage_devices | R1 | 1/4 | M102:1→0[gd_nonadvancing@idx0], M103:1→0[gd_nonadvancing@idx0], M201:2→1[input] |
| compensation.stage_devices | R2 | 0/4 | M102:1→0[gd_nonadvancing@idx0], M103:1→0[gd_nonadvancing@idx0], M201:2→1[input], M301:3→2[input] |
| compensation.stage_devices | R1ng | 3/4 | M301:3→4[input] |
| compensation.stage_devices | R2ng | 4/4 | - |
| compensation.stage_devices | R3(DM/R1) | 3/4 | M301:3→4[input] |
| compensation.stage_devices | R3(DM/R2) | 4/4 | - |
| compensation.stage_devices | R3(CM/R2) | 0/4 | M102:1→0[gd_nonadvancing@idx0], M103:1→0[gd_nonadvancing@idx0], M201:2→1[input], M301:3→2[input] |
| compensation.stage_devices | R3(CM/R2ng) | 4/4 | - |
| metrics.gain_db(nmcnr_gain_db) 역할필드 | R1 | 4/10 | M102:1→0[gd_nonadvancing@idx0], M201:2→1[input], M107:1→0[cascode@idx0], M103:1→0[gd_nonadvancing@idx0], M105:1→0[load@idx0], M109:1→0[gd_nonadvancing@idx0] |
| metrics.gain_db(nmcnr_gain_db) 역할필드 | R2 | 0/10 | M102:1→0[gd_nonadvancing@idx0], M201:2→1[input], M301:3→2[input], M107:1→0[cascode@idx0], M103:1→0[gd_nonadvancing@idx0], M105:1→0[load@idx0], M109:1→0[mirror_out@idx0], M202:2→1[load], M204:2→1[mirror_out], M302:3→2[load] |
| metrics.gain_db(nmcnr_gain_db) 역할필드 | R1ng | 6/10 | M301:3→4[input], M202:2→3[load], M204:2→3[input], M302:3→4[load] |
| metrics.gain_db(nmcnr_gain_db) 역할필드 | R2ng | 10/10 | - |
| metrics.gain_db(nmcnr_gain_db) 역할필드 | R3(DM/R1) | 6/10 | M301:3→4[input], M202:2→3[load], M204:2→3[input], M302:3→4[load] |
| metrics.gain_db(nmcnr_gain_db) 역할필드 | R3(DM/R2) | 10/10 | - |
| metrics.gain_db(nmcnr_gain_db) 역할필드 | R3(CM/R2) | 0/10 | M102:1→0[gd_nonadvancing@idx0], M201:2→1[input], M301:3→2[input], M107:1→0[cascode@idx0], M103:1→0[gd_nonadvancing@idx0], M105:1→0[load@idx0], M109:1→0[mirror_out@idx0], M202:2→1[load], M204:2→1[mirror_out], M302:3→2[load] |
| metrics.gain_db(nmcnr_gain_db) 역할필드 | R3(CM/R2ng) | 10/10 | - |
| metrics.gain_db(nmcnr_gain_db) 역할필드 역할필드 vs R3-DM/R2 역할 | | | M102:gm1_device→input, M201:gm2_device→input, M301:gm3_device→input, M107:stage1_cascode_n→cascode, M103:stage1_fold_leg_a→input, M105:stage1_fold_leg_b→load, M109:stage1_mirror_p→mirror_out, M202:stage2_devices→load, M204:stage2_devices→mirror_out, M302:stage3_devices→load |

### stage 출력노드 gds 기여자 (R3-DM/R2 stage index, 원 넷 기준: 선언 stage-k 소자의 drain 넷 중 DM idx==k 이고 같은 stage 신호소자의 source가 아닌(=캐스코드 사슬 꼭대기) 넷; diode 노드는 따로 표시)
- [metrics.gain_db(nmcnr_gain_db) 역할필드] stage 1 노드 NodeF1
  - drain 접속(gds/ro 사슬): ['M102', 'M104']
  - source 접속(소스 들여다본 1/gm 부하): ['M106']
  - 수동소자: []
  - 선언 stage 목록 **누락**: drain접속 ['M104'], source접속 ['M106'], 사슬 하위 []
- [metrics.gain_db(nmcnr_gain_db) 역할필드] stage 1 노드 NodeM2
  - drain 접속(gds/ro 사슬): ['M107<-[M103 | M105]@NodeF2', 'M109']
  - source 접속(소스 들여다본 1/gm 부하): []
  - 수동소자: []
  - 선언 stage 목록 **누락**: drain접속 [], source접속 [], 사슬 하위 []
- [metrics.gain_db(nmcnr_gain_db) 역할필드] stage 2 노드 NodeC: **diode 노드**(저임피던스, 이득 출력노드 아님) -- drain 접속 ['M201', 'M203']
- [metrics.gain_db(nmcnr_gain_db) 역할필드] stage 2 노드 NodeS2
  - drain 접속(gds/ro 사슬): ['M202', 'M204']
  - source 접속(소스 들여다본 1/gm 부하): []
  - 수동소자: []
  - 선언 stage 목록 **누락**: drain접속 [], source접속 [], 사슬 하위 []
- [metrics.gain_db(nmcnr_gain_db) 역할필드] stage 3 노드 Vout
  - drain 접속(gds/ro 사슬): ['M301', 'M302']
  - source 접속(소스 들여다본 1/gm 부하): []
  - 수동소자: []
  - 선언 stage 목록 **누락**: drain접속 [], source접속 [], 사슬 하위 []

### 기존 함수 교차확인
- find_differential_pair_candidates: [(('M102', 'M103'), 'NodeTail')]
- tail: R3-DM/R2 규칙=['M101'] / gain_stage_tails(선언 기반)={} / diffpair shared_source를 drain으로 갖는 소자=['M101']
- true_current_mirror_groups: [['M104', 'M105'], ['M108', 'M109'], ['M203', 'M204']]
- trace_vdd_to_gnd_branches: branch 7개
- signal_path_nodes(excite=입력, sense=출력; 접지 절단·gs엣지 없음) = ['NodeC', 'NodeF1', 'NodeF2', 'NodeM1', 'NodeM2', 'NodeS2']
  - 이 probe full/R1 도달노드에만 있음: ['NodeTail'] / signal_path_nodes에만 있음: []

## 요약

| 회로 | 선언 | 규칙 | 일치 |
|---|---|---|---|
| current_reuse_telescopic_ota | compensation.stage_devices+shared_gm_id_groups | R1 | 0/8 |
| current_reuse_telescopic_ota | compensation.stage_devices+shared_gm_id_groups | R2 | 0/8 |
| current_reuse_telescopic_ota | compensation.stage_devices+shared_gm_id_groups | R1ng | 8/8 |
| current_reuse_telescopic_ota | compensation.stage_devices+shared_gm_id_groups | R2ng | 8/8 |
| current_reuse_telescopic_ota | compensation.stage_devices+shared_gm_id_groups | R3(DM/R1) | 8/8 |
| current_reuse_telescopic_ota | compensation.stage_devices+shared_gm_id_groups | R3(DM/R2) | 8/8 |
| current_reuse_telescopic_ota | compensation.stage_devices+shared_gm_id_groups | R3(CM/R2) | 0/8 |
| current_reuse_telescopic_ota | compensation.stage_devices+shared_gm_id_groups | R3(CM/R2ng) | 8/8 |
| current_reuse_telescopic_ota | metrics.gain_db.stages(gain_stages_sum) | R1 | 0/6 |
| current_reuse_telescopic_ota | metrics.gain_db.stages(gain_stages_sum) | R2 | 0/6 |
| current_reuse_telescopic_ota | metrics.gain_db.stages(gain_stages_sum) | R1ng | 6/6 |
| current_reuse_telescopic_ota | metrics.gain_db.stages(gain_stages_sum) | R2ng | 6/6 |
| current_reuse_telescopic_ota | metrics.gain_db.stages(gain_stages_sum) | R3(DM/R1) | 6/6 |
| current_reuse_telescopic_ota | metrics.gain_db.stages(gain_stages_sum) | R3(DM/R2) | 6/6 |
| current_reuse_telescopic_ota | metrics.gain_db.stages(gain_stages_sum) | R3(CM/R2) | 0/6 |
| current_reuse_telescopic_ota | metrics.gain_db.stages(gain_stages_sum) | R3(CM/R2ng) | 6/6 |
| folded_cascode | metrics.gain_db(folded_cascode_gain_db) 역할필드 | R1 | 0/5 |
| folded_cascode | metrics.gain_db(folded_cascode_gain_db) 역할필드 | R2 | 0/5 |
| folded_cascode | metrics.gain_db(folded_cascode_gain_db) 역할필드 | R1ng | 4/5 |
| folded_cascode | metrics.gain_db(folded_cascode_gain_db) 역할필드 | R2ng | 4/5 |
| folded_cascode | metrics.gain_db(folded_cascode_gain_db) 역할필드 | R3(DM/R1) | 5/5 |
| folded_cascode | metrics.gain_db(folded_cascode_gain_db) 역할필드 | R3(DM/R2) | 5/5 |
| folded_cascode | metrics.gain_db(folded_cascode_gain_db) 역할필드 | R3(CM/R2) | 0/5 |
| folded_cascode | metrics.gain_db(folded_cascode_gain_db) 역할필드 | R3(CM/R2ng) | 4/5 |
| two_stage_ota | compensation.stage_devices | R1 | 0/3 |
| two_stage_ota | compensation.stage_devices | R2 | 0/3 |
| two_stage_ota | compensation.stage_devices | R1ng | 3/3 |
| two_stage_ota | compensation.stage_devices | R2ng | 3/3 |
| two_stage_ota | compensation.stage_devices | R3(DM/R1) | 3/3 |
| two_stage_ota | compensation.stage_devices | R3(DM/R2) | 3/3 |
| two_stage_ota | compensation.stage_devices | R3(CM/R2) | 0/3 |
| two_stage_ota | compensation.stage_devices | R3(CM/R2ng) | 3/3 |
| nmcnr_amplifier | compensation.stage_devices | R1 | 1/4 |
| nmcnr_amplifier | compensation.stage_devices | R2 | 0/4 |
| nmcnr_amplifier | compensation.stage_devices | R1ng | 3/4 |
| nmcnr_amplifier | compensation.stage_devices | R2ng | 4/4 |
| nmcnr_amplifier | compensation.stage_devices | R3(DM/R1) | 3/4 |
| nmcnr_amplifier | compensation.stage_devices | R3(DM/R2) | 4/4 |
| nmcnr_amplifier | compensation.stage_devices | R3(CM/R2) | 0/4 |
| nmcnr_amplifier | compensation.stage_devices | R3(CM/R2ng) | 4/4 |
| nmcnr_amplifier | metrics.gain_db(nmcnr_gain_db) 역할필드 | R1 | 4/10 |
| nmcnr_amplifier | metrics.gain_db(nmcnr_gain_db) 역할필드 | R2 | 0/10 |
| nmcnr_amplifier | metrics.gain_db(nmcnr_gain_db) 역할필드 | R1ng | 6/10 |
| nmcnr_amplifier | metrics.gain_db(nmcnr_gain_db) 역할필드 | R2ng | 10/10 |
| nmcnr_amplifier | metrics.gain_db(nmcnr_gain_db) 역할필드 | R3(DM/R1) | 6/10 |
| nmcnr_amplifier | metrics.gain_db(nmcnr_gain_db) 역할필드 | R3(DM/R2) | 10/10 |
| nmcnr_amplifier | metrics.gain_db(nmcnr_gain_db) 역할필드 | R3(CM/R2) | 0/10 |
| nmcnr_amplifier | metrics.gain_db(nmcnr_gain_db) 역할필드 | R3(CM/R2ng) | 10/10 |
- current_reuse_telescopic_ota: gain 선언 누락 출력노드 접속 소자 3개 ['M18a', 'M18b', 'M19']
- folded_cascode: gain 선언 누락 출력노드 접속 소자 0개 []
- two_stage_ota: gain 선언 누락 출력노드 접속 소자 0개 []
- nmcnr_amplifier: gain 선언 누락 출력노드 접속 소자 2개 ['M104', 'M106']
