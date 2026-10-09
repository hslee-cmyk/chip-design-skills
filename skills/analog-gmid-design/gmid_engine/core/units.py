"""단위 표 -- metric 단위 어휘·영역 어휘·단위 정의 계수 (설계 요건 1.3 "단위 환산 계수는 `core/units.py` 한 곳", 3.1 표 `units.py`;
계획 DEC-53·DEC-67·DEC-68).

공개 정의 0(상수 표). 구조 규칙 D 의 숫자 리터럴 예외 파일이다.

* `METRIC_UNITS`: metric 정규 단위 = DEC-68 의 풀어 쓴 단위 접미사(`_db`, `_hz`, `_deg`, `_ohm`, `_mv`, `_amp`, `_w`)와 면적 `m2`
  (`mv` = 입력 환산 offset metric `offset_in_sigma_mv`·`offset_sys_mv` 의 접미사).
  [U5, 설계 40 §3.8-8·41 §7.1] `pct`(`mirror_ratio_sigma_pct`)·`ratio`(무차원 비 `offset_excess`·`noise_excess_th`)·`v`(`swing_out_v`·
  `icmr_v`·`icm_margin_v`·`noise_out_int_vrms`)·`v2_per_hz`(`noise_th_in_v2hz` 전력 밀도)를 더했다. `hz` 는 `noise_fc_in_hz` 와 공유.
  레지스트리 항목의 단위는 이 안에 있어야 한다(표에 없는 단위는 거부 -- 옛 A12 규칙 계승).
* `DOMAINS`: 영역 어휘(DEC-67 의 DC·소신호·대신호 + MOD5 설계 3.4 의 레이아웃 기하 `geom`).
* `AMPLITUDE_DB_PER_DECADE`: 진폭비의 dB 정의 계수(20·log10|H|). dB 정의 자체라 유도할 근거가 없는 단위 계수다.
* `MILLI`: SI 접두사 m(mv -> V 환산, [U13] `iv_matching_l` 이 `offset_in_sigma_mv` 값을 V 로 옮긴다). 단위 환산 계수는 이 파일 한 곳에 둔다.
"""

METRIC_UNITS = ("db", "hz", "deg", "ohm", "mv", "amp", "w", "m2", "pct", "ratio", "v", "v2_per_hz")

DOMAINS = ("dc", "ss", "ls", "geom")

AMPLITUDE_DB_PER_DECADE = 20.0

MILLI = 0.001
MV_PER_V = 1000.0
PCT_PER_UNIT = 100.0
# [U7] 단위 환산 계수 둘: 전압(V) -> 정규 단위 `mv`, 무차원 비 -> 정규 단위 `pct`. 정의에 의한 환산이라 유도할 근거가 없다.
