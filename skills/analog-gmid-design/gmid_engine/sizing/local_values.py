"""국소 봉인 결과 값 형식 -- 데이터 선언 모듈 (설계 41 §5.3 `LocalSeal`, 40 §3.7).

* `SnapshotFragment`: 덮는 소자·넷의 봉인 점 값. `devices` = ((MOS, DeviceOp), ...) 이름순, `nodes` = ((넷, V), ...) 이름순(레일 제외).
* `LocalSeal`: `size_and_seal_local` 결과. `ok` = 덮는 범위에 위반이 없고 커널이 끝까지 돌았다, `failures` = FailureRecord tuple(항목 순),
  `snapshot_fragment`(실패하면 빈 조각), `gain_db`(블록 국소 gain 모델 `metrics.block_local_gain` 이 병합되기 전에는 None), `power_w`·`area_m2`
  (실패하면 None).
"""
import dataclasses


@dataclasses.dataclass(frozen=True)
class SnapshotFragment:
    """덮는 소자·넷의 봉인 점 값. `devices` = ((MOS, DeviceOp), ...) 이름순, `nodes` = ((넷, V), ...) 이름순(레일 제외)."""

    devices: tuple = ()
    nodes: tuple = ()


@dataclasses.dataclass(frozen=True)
class LocalSeal:
    """국소 봉인 결과. `ok` = 덮는 범위에 위반이 없고 커널이 끝까지 돌았다. 나머지는 모듈 설명."""

    ok: bool
    failures: tuple
    snapshot_fragment: SnapshotFragment
    gain_db: object = None
    power_w: object = None
    area_m2: object = None
