P2 SPICE(ngspice-46 ngspice_con -b, sky130 tt) -- current_reuse 파일럿 벤치 wt/_pilot_current_reuse/cr_a2_0.5e-6_0.45e-12_cl.cir 복사(제어부만 바꿈).
p2_h.cir/.log/p2_h_ac.txt: op 소자 값(gm·용량)과 A(Vop1)->G(Vg15) 전압비 h(f) = v(Vg15)/v(Vop1)(입력 차동 구동 AC). 저주파 1.589, 1 GHz 0.087, 100 GHz 0.228(수렴 중).
p2_pz_{conn,ginf,lowk}.cir/.log: .pz 시도 -- 'Pole-zero iteration limit reached'로 영점 목록 불완전 -> 결론에 쓰지 않음(측정 불능 기록).
