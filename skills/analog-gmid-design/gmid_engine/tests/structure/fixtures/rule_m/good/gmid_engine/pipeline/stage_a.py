"""엔진 쪽 진입은 두 객체를 받기만 한다(만들지 않는다). docstring 안 open_run 언급은 참조가 아니다."""


class StageAResult:
    def __init__(self, donors, counters):
        self.donors = donors
        self.counters = counters


def run_stage_a(topology_path, spec_path, lut, *, output_dir, donors, counters):
    return StageAResult(donors=donors, counters=counters)
