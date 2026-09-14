# common drain·source 출력 경로 실측 (2026-09-14)

방법: 4개 topology.json 넷리스트에서 (1) drain이 레일(vdd/gnd/vss)이고 source·gate가 비레일인 순수 follower, (2) gate가 다른 소자 drain으로 구동되고 source가 비레일인 소자(신호가 source·drain 단자로 넘어갈 수 있는 소자)를 나열. 교류접지·DM 뷰 해석은 하지 않은 connectivity 목록이다.

## current_reuse_telescopic_ota (소자 51)
- (1) 순수 follower: 없음
- (2) 신호 구동 게이트 + 비레일 source:
  - M2a pmos g=Vbias2 d=Vom1 s=N1a2a (gate 구동: ['M57', 'M68'])
  - M2b pmos g=Vbias2 d=Vop1 s=N1b2b (gate 구동: ['M57', 'M68'])
  - M3a nmos g=Vbias3 d=Vom1 s=N3a4a (gate 구동: ['M61', 'M64'])
  - M3b nmos g=Vbias3 d=Vop1 s=N3b4b (gate 구동: ['M61', 'M64'])
  - M9a pmos g=N11b d=Vop1 s=Vg15 (gate 구동: ['M11b', 'M12'])
  - M9b nmos g=N14a14b d=Vg15 s=Vop1 (gate 구동: ['M13', 'M14a'])
  - M18a pmos g=N20b d=Vom1 s=Vg25 (gate 구동: ['M20b', 'M21'])
  - M18b nmos g=N24b23a d=Vg25 s=Vom1 (gate 구동: ['M22', 'M23a'])
  - M63 nmos g=Vbias3 d=N64_63 s=Vy (gate 구동: ['M61', 'M64'])
  - M58 pmos g=Vbias2 d=N58_57 s=Vx (gate 구동: ['M57', 'M68'])
  - M37b nmos g=Voc_des d=N36b s=Ncmfb_tail (gate 구동: ['M39'])

## folded_cascode (소자 13)
- (1) 순수 follower: 없음
- (2) 신호 구동 게이트 + 비레일 source:
  - M8 nmos g=Vg7 d=out s=Vg10 (gate 구동: ['M5', 'M7'])

## two_stage_ota (소자 7)
- (1) 순수 follower: 없음
- (2) 신호 구동 게이트 + 비레일 source:

## nmcnr_amplifier (소자 15)
- (1) 순수 follower: 없음
- (2) 신호 구동 게이트 + 비레일 source:

해석(계획 v5.1 N3.2): (2) 중 게이트가 바이어스 넷(Vbias2/Vbias3 등, 레플리카 drain이 구동)인 M2a/M2b/M3a/M3b/M58/M63/M37b는 CG(캐스코드) 또는 바이어스 경로다. 신호가 source·drain으로 넘어가는 pass 구성 후보는 파일럿 floating battery M9a/M9b(Vop1↔Vg15), M18a/M18b(Vom1↔Vg25)이고, folded M8(gate Vg7, source Vg10)은 CD 또는 CG 판정이 필요하다(J3, J10).
