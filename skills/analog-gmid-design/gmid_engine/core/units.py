"""단위 표 -- metric 단위 어휘·영역 어휘·단위 정의 계수 (설계 요건 1.3 "단위 환산 계수는 `core/units.py` 한 곳", 3.1 표 `units.py`;
계획 DEC-53·DEC-67·DEC-68).

공개 정의 0(상수 표). 구조 규칙 D 의 숫자 리터럴 예외 파일이다.

* `METRIC_UNITS`: metric 정규 단위 = DEC-68 의 풀어 쓴 단위 접미사(`_db`, `_hz`, `_deg`, `_ohm`, `_mv`, `_amp`, `_w`)와 면적 `m2`
  (`mv` = 정합 오차 metric `mismatch_sigma_mv`·`mirror_ratio_error_mv` 의 접미사).
  레지스트리 항목의 단위는 이 안에 있어야 한다(표에 없는 단위는 거부 -- 옛 A12 규칙 계승).
* `DOMAINS`: 영역 어휘(DEC-67 의 DC·소신호·대신호 + MOD5 설계 3.4 의 레이아웃 기하 `geom`).
* `AMPLITUDE_DB_PER_DECADE`: 진폭비의 dB 정의 계수(20·log10|H|). dB 정의 자체라 유도할 근거가 없는 단위 계수다.
"""

METRIC_UNITS = ("db", "hz", "deg", "ohm", "mv", "amp", "w", "m2")

DOMAINS = ("dc", "ss", "ls", "geom")

AMPLITUDE_DB_PER_DECADE = 20.0
