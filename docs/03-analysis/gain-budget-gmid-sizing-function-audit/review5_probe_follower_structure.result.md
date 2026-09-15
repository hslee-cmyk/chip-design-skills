# probe_follower_structure 결과

## current_reuse_telescopic_ota

- 소자 51, gate 전용 넷(교류접지 후보 SP1-1(2)): []
- drain=레일·source≠레일·gate=신호 후보(순수 follower 후보): 없음
- source 노드가 다른 소자 gate로 이어지고 drain·source 모두 비레일(비순수 CD/pass 후보): M11b(g=N11b s=N11a11b d=N11b), M9a(g=N11b s=Vg15 d=Vop1), M9b(g=N14a14b s=Vop1 d=Vg15), M14a(g=N14a14b s=N14a_14b d=N14a14b), M20b(g=N20b s=N20a20b d=N20b), M18a(g=N20b s=Vg25 d=Vom1), M18b(g=N24b23a s=Vom1 d=Vg25), M23a(g=N24b23a s=N23a24b d=N24b23a)
- equal_vgs 자명 평행 엣지 16건: M8~M6, M12~M5, M10~M5, M13~M6, M22~M6, M21~M5, M19~M5, M17~M6, M18_bg~M6, M60~M6, M61~M6, M66~M5, M68~M5, M36a~M7, M38~M5, M40~M39
- **비자명 VGS 사이클**: 소자 ['M4b', 'M4a', 'M1a', 'M1b'], 노드 ['Vim', 'Vip', 'Vx', 'Vy'], 레일 경유=False
- **비자명 VGS 사이클**: 소자 ['M9a', 'M15', 'M11a', 'M11b'], 노드 ['N11a11b', 'N11b', 'RAIL', 'Vg15'], 레일 경유=True
- **비자명 VGS 사이클**: 소자 ['M16', 'M14b', 'M14a', 'M9b'], 노드 ['N14a14b', 'N14a_14b', 'RAIL', 'Vop1'], 레일 경유=True
- **비자명 VGS 사이클**: 소자 ['M18a', 'M25', 'M20a', 'M20b'], 노드 ['N20a20b', 'N20b', 'RAIL', 'Vg25'], 레일 경유=True
- **비자명 VGS 사이클**: 소자 ['M26', 'M24b', 'M23a', 'M18b'], 노드 ['N23a24b', 'N24b23a', 'RAIL', 'Vom1'], 레일 경유=True
- (ports `_comment` 값이 dict가 아님: "2026-08-03(사용자 확인) -- 이 회로(opamp)의 최상위 4개 differential I/O 신호 역할 명시. netlist connectivity 자체는 안 바꾸고 순수 문서화 목적(예: 향후 report/testbench 생성 스크립트가 '어느 net이 입력/출력인지'를 topology.json에서 바로 읽을 수 있게)." -- 옛 스키마, 방향 분류 생략)
- 출력 포트 `Vop` drain/source 소자: M25[pmos, 단자=drain, 반대단자=vdd, gate=Vg25:signal]; M26[nmos, 단자=drain, 반대단자=gnd, gate=Vom1:signal]
- 출력 포트 `Vom` drain/source 소자: M15[pmos, 단자=drain, 반대단자=vdd, gate=Vg15:signal]; M16[nmos, 단자=drain, 반대단자=gnd, gate=Vop1:signal]

## folded_cascode

- 소자 13, gate 전용 넷(교류접지 후보 SP1-1(2)): ['bias3', 'vin_n', 'vin_p']
- drain=레일·source≠레일·gate=신호 후보(순수 follower 후보): 없음
- source 노드가 다른 소자 gate로 이어지고 drain·source 모두 비레일(비순수 CD/pass 후보): M7(g=Vg7 s=Vg9 d=Vg7)
- equal_vgs 자명 평행 엣지 4건: M3~MP, M4~MP, M10~M9, MN~M11
- 비자명 VGS 사이클: 없음

## nmcnr_amplifier

- 소자 15, gate 전용 넷(교류접지 후보 SP1-1(2)): ['VB1', 'VB2', 'VB3', 'VB4', 'VB5', 'Vin_n', 'Vin_p']
- drain=레일·source≠레일·gate=신호 후보(순수 follower 후보): 없음
- source 노드가 다른 소자 gate로 이어지고 drain·source 모두 비레일(비순수 CD/pass 후보): 없음
- equal_vgs 자명 평행 엣지 3건: M105~M104, M109~M108, M204~M203
- 비자명 VGS 사이클: 없음

## pushpull_follower_buffer

- 소자 6, gate 전용 넷(교류접지 후보 SP1-1(2)): ['VNB1', 'VPB1']
- drain=레일·source≠레일·gate=신호 후보(순수 follower 후보): M3(pmos g=vin s=A d=vss), M4(nmos g=vin s=B d=vdd), M1(nmos g=A s=vout d=vdd), M2(pmos g=B s=vout d=vss)
- source 노드가 다른 소자 gate로 이어지고 drain·source 모두 비레일(비순수 CD/pass 후보): 없음
- equal_vgs 자명 평행 엣지 0건: 
- **비자명 VGS 사이클**: 소자 ['M2', 'M1', 'M3', 'M4'], 노드 ['A', 'B', 'vin', 'vout'], 레일 경유=False
- 출력 포트 `vout` drain/source 소자: M1[nmos, 단자=source, 반대단자=vdd, gate=A:signal]; M2[pmos, 단자=source, 반대단자=vss, gate=B:signal]

## sf_pushpull_output_opamp

- 소자 22, gate 전용 넷(교류접지 후보 SP1-1(2)): []
- drain=레일·source≠레일·gate=신호 후보(순수 follower 후보): M18(pmos g=Y s=N17 d=vss), M19(nmos g=Y s=N20 d=vdd), M22(nmos g=N17 s=vout d=vdd), M21(pmos g=N20 s=vout d=vss)
- source 노드가 다른 소자 gate로 이어지고 drain·source 모두 비레일(비순수 CD/pass 후보): 없음
- equal_vgs 자명 평행 엣지 6건: M4~M3, M11~M8, M9~M6, M16~M14, M17~M6, M20~M14
- **비자명 VGS 사이클**: 소자 ['M21', 'M22', 'M18', 'M19'], 노드 ['N17', 'N20', 'Y', 'vout'], 레일 경유=False
- 출력 포트 `vout` drain/source 소자: M22[nmos, 단자=source, 반대단자=vdd, gate=N17:signal]; M21[pmos, 단자=source, 반대단자=vss, gate=N20:signal]

## two_stage_ota

- 소자 7, gate 전용 넷(교류접지 후보 SP1-1(2)): ['bias']
- drain=레일·source≠레일·gate=신호 후보(순수 follower 후보): 없음
- source 노드가 다른 소자 gate로 이어지고 drain·source 모두 비레일(비순수 CD/pass 후보): 없음
- equal_vgs 자명 평행 엣지 2건: M4~M3, M7~M5
- 비자명 VGS 사이클: 없음
- (ports `_comment` 값이 dict가 아님: "2026-09-10 -- 입력환산 오프셋 metric(input_referred_offset)이 '게이트가 **신호 입력**에 물린 매칭 쌍'만 세려면 어느 net이 입력인지 선언이 필요하다(파일럿 실측: offset 쌍 3개 중 하나는 CMFB 오차증폭기라 그 구분이 실제로 결과를 바꾼다). net 이름 자체가 vin_p/vin_n이고 이 회로의 유일한 differential 입력쌍 M1/M2의 게이트다 -- connectivity는 안 건드리고 역할만 적는다. current_reuse_telescopic_ota의 ports 선언과 같은 형식. ⚠️ 출력 net은 아직 안 적었다 -- 지금 쓰는 곳이 없어서다(필요해지면 추가)." -- 옛 스키마, 방향 분류 생략)

## two_stage_ota_sf

- 소자 9, gate 전용 넷(교류접지 후보 SP1-1(2)): ['bias']
- drain=레일·source≠레일·gate=신호 후보(순수 follower 후보): M8(nmos g=OUT s=vout d=vdd)
- source 노드가 다른 소자 gate로 이어지고 drain·source 모두 비레일(비순수 CD/pass 후보): 없음
- equal_vgs 자명 평행 엣지 3건: M4~M3, M7~M5, M9~M5
- 비자명 VGS 사이클: 없음
- 출력 포트 `vout` drain/source 소자: M8[nmos, 단자=source, 반대단자=vdd, gate=OUT:signal]; M9[nmos, 단자=drain, 반대단자=gnd, gate=bias:bias(gate 전용 넷)]

## LUT npz(ac_sweep_checkpoints 제외)

- `skills\analog-gmid-design\assets\sky130_nfet_pfet_lut_sample.npz`: corner(), temp_c(), L[1.5e-07..4e-06, n=12], VGS[0..1.8, n=49], VDS[0..1.8, n=49], VS[0..0.8, n=5], ID_n(12, 49, 49, 5), GM_n(12, 49, 49, 5), GDS_n(12, 49, 49, 5), CGG_n(12, 49, 49, 5), CGD_n(12, 49, 49, 5), SID_1F_n(12, 49, 49, 5), ID_p(12, 49, 49, 5), GM_p(12, 49, 49, 5), GDS_p(12, 49, 49, 5), CGG_p(12, 49, 49, 5), CGD_p(12, 49, 49, 5), SID_1F_p(12, 49, 49, 5)
