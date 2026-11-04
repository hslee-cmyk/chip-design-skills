# -*- coding: utf-8 -*-
"""core/adapter_api.py -- 어댑터 계약(design §8.1). 코어는 이 계약만 안다: 어댑터 객체를 인자로 받고 어댑터 모듈을 import하지 않는다.

  name                       어댑터 이름(입력 simulator.adapter 가 고른다)
  capabilities() -> dict     {'op','ac','noise',...,'geometry_unit_application': [...], 'case_insensitive_names', 'model_families'}
  calibration() -> dict      {'default_tolerances','data_digits','simulator_version_probe','global_geometry_directive',...} 값마다 출처 칸
  fingerprint() -> mapping   {'name','code_sha256','exe_sha256','sim_version'}
  run(circuit, requests, descriptor, work_dir, timeout_s, cache_dir, compat) -> ResultBundle   벤치 하나를 순차 실행
  model_bundle(circuit, descriptor, cond) -> {경로: {'lf': sha256, 'raw': sha256}}             규칙 (i)(ii) 대조의 입력
"""
from __future__ import annotations

from typing import Protocol


class Adapter(Protocol):
    name: str

    def capabilities(self) -> dict: ...

    def calibration(self) -> dict: ...

    def fingerprint(self): ...

    def run(self, circuit, requests, descriptor, work_dir, timeout_s, cache_dir, compat): ...

    def model_bundle(self, circuit, descriptor, cond) -> dict: ...

