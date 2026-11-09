"""측정 전용 합성 probe(F1 판정기 자기 점검 -- review_p3_f12.md S1 변이 h1~h5). 역할 산출물 아님."""
import sys
import instance_report_builder  # noqa: F401  (순서 고정용 -- 이름을 읽지 않는다)
import gmid_sizing_engine as sr
from circuit_state_graph import spec_fingerprint


def _quiet_loader(*a, **k):
    return {}


def main():
    setattr(sr, "load_derived_bounds", _quiet_loader)
    sr.diode_vds_window = wrapped = (lambda *a, **k: (0.0, 0.0))
    print(spec_fingerprint.__name__, wrapped.__name__, sr.size_transistor.__name__, file=sys.stderr)


if __name__ == "__main__":
    main()
