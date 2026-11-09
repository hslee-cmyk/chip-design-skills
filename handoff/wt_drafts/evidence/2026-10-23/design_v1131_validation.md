# design v1.13.1 정오 검증 (2026-10-23)

- 대상: `wt/design-v1131` `d728c778`(base master `0dd40d4a`)
- 엔진 대조: `wt/integ-it12` `ee9bcf5b`
- 읽기 전용, git은 `git -C`만 썼다.

## 결과: 새 G·S 없음, 점수 97 / 100

## 1. 사실 대조 (`ee9bcf5b`)
| 항목 | 엔진 사실 | 판정 |
|---|---|---|
| Q-2 detail 키 `"elements"`(40:1884) | `ss_metrics.py:403`·`metrics_aux.py:165`가 `(("elements", ss.missing),)`이다 | 맞음. 41:739·812와 키가 같다 |
| Q-3 `sizing.__all__` 여덟 이름(40:2092) | 41:760·797과 40:1881의 목록(`Circuit`, `saturation_window`, `INPUT_STATUS_*` 셋, writer 상수 셋)과 같다 | 맞음 |
| Q-4 문자열 `"ss_circuit"` 2건(41:739) | `git grep`으로 `metrics/__init__.py:337`(함수 export)과 `_module_map.py:773`(진입점) 두 곳만 나온다 | 맞음. '쓰는 곳 하나 = WRITES·권한표로 잼'은 L10 (c)의 'writer 1곳'과 모순되지 않는다 |
| Q-5 `spec_elements.py:118` | `:118` = `def _feedback(raw, passive_names, topology):`, `:116`은 빈 줄이다 | 유지가 맞음(41:731·748 그대로) |

## 2. 다른 줄과의 모순 grep
- 40·41에서 `("devices"`로 남은 detail 키: 0건.
- `"ss_circuit"`을 '0건'이라고 적은 다른 자리: 0건. 41:17·739만 2건으로 적는다.
- `__all__` 목록이 나오는 자리(40:1881·2092, 41:760·797·834): 모두 여덟 이름이거나 같은 범위를 가리킨다. 모순 없음.

## 3. 범위
- numstat: 40 = 4/4, 41 = 3/3. 바뀐 줄은 version·Status와 위 네 자리뿐이고, 줄 수는 그대로다. 범위 밖 변경은 없다.

## 미확인
- 없음.
