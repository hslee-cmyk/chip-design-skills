### N6.25 card RB-1 -- 규칙 갈래 처리기 이음매 + 첫 처리기 S-OS2 일반형(사용자 결정 O-91 (1), DEC-102) -- **v6.35 대상 소멸**

**v6.35 -- 대상 소멸, 착수하지 않음**(사용자 결정 O-115 귀결 -- **원래 취지와 다름**: O-91 (1) '첫 처리기 = S-OS2 일반형'): 이 card의 대상(소유 블록 `icm_config`의 S-OS2 판정 자리, 첫 처리기 S-OS2 일반형 = 차동 DC 되먹임 결합·차동 모드만 닫음, 선언 없는 차동 출력 갈래)은 v6.35 N3.8 'ICMR 측정 구성'·'차동 출력 -- 정의 본문'이 IT-2c에서 servo 하나로 정의해 사라진다 -- S-OS2 멈춤 갈래·`icm_config_differential_output_structure`·`icm_config_differential_output_undeclared`·`icm_config_feedback_outputs_split`이 만들어지지 않으므로 등록표를 놓을 정지 자리가 없다(DEC-102 (6) 배치 규칙 '실제 소비 회로가 있는 소유 블록에만'). DEC-102 규칙은 그대로이고 다음 실제 소비 갈래가 생길 때 그 card가 첫 이음매를 깐다. 옛 본문(성격·범위·대표 소비자·미확인·순서·완료 조건)은 history H1 'v6.35'.

