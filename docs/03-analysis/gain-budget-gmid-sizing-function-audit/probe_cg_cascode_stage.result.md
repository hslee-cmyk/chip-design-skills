# CG(캐스코드)를 stage로 나눌지 -- 4개 회로 connectivity 실측 (2026-09-14)
방법: 입력 넷에서 신호 넷을 BFS(gate->drain/source, source->drain, drain->source 전달, 레일 제외). CG = 게이트가 신호 넷이 아니고(바이어스) source·drain이 신호 넷인 소자. source 구동 = 그 넷에 다른 소자 drain이 붙음(전류 구동) / 입력 포트(전압 구동). 선언 stage = topology.json 안에서 stage를 뜻하는 필드(stage_devices, gain_stages_sum.stages 등)에 소자가 함께 나오는 목록.

## current_reuse_telescopic_ota  입력 넷=['Vip', 'Vim'] (ports 선언 있음)
- 선언 .compensation.stage_devices: [["M1a", "M1b"], ["M4a", "M4b"], ["M15", "M25"], ["M16", "M26"]]
- 선언 .sizing_roles.metrics.gain_db.stages: [["M1a", "M4a", "M2a", "M3a"], ["M15", "M16"]]
- 선언 .sizing_roles.metrics.noise_v_rthz.stages: [["M1a", "M4a"]]
- CG M9a pmos g=N11b s=Vg15<-['M8', 'M9b'] d=Vop1: 전류 구동(캐스코드); 선언 stage 목록 등장=[]
- CG M9b nmos g=N14a14b s=Vop1<-['M10', 'M2b', 'M3b', 'M9a'] d=Vg15: 전류 구동(캐스코드); 선언 stage 목록 등장=[]
- CG M18a pmos g=N20b s=Vg25<-['M17', 'M18b'] d=Vom1: 전류 구동(캐스코드); 선언 stage 목록 등장=[]
- CG M18b nmos g=N24b23a s=Vom1<-['M18a', 'M19', 'M2a', 'M3a'] d=Vg25: 전류 구동(캐스코드); 선언 stage 목록 등장=[]

## folded_cascode  입력 넷=['vin_n', 'vin_p'] (ports 선언 없음 -> 이름으로 추정)
- CG M5 pmos g=bias3 s=Y<-['M2', 'M4'] d=Vg7: 전류 구동(캐스코드); 선언 stage 목록 등장=[]
- CG M6 pmos g=bias3 s=X<-['M1', 'M3'] d=out: 전류 구동(캐스코드); 선언 stage 목록 등장=[]

## two_stage_ota  입력 넷=['vin_p', 'vin_n'] (ports 선언 있음)
- 선언 .compensation.stage_devices: [["M1", "M2"], ["M6"]]

## nmcnr_amplifier  입력 넷=['Vin_n', 'Vin_p'] (ports 선언 없음 -> 이름으로 추정)
- 선언 .compensation.stage_devices: [["M102", "M103"], ["M201"], ["M301"]]
- CG M106 nmos g=VB3 s=NodeF1<-['M102', 'M104'] d=NodeM1: 전류 구동(캐스코드); 선언 stage 목록 등장=[]
- CG M107 nmos g=VB3 s=NodeF2<-['M103', 'M105'] d=NodeM2: 전류 구동(캐스코드); 선언 stage 목록 등장=[]
