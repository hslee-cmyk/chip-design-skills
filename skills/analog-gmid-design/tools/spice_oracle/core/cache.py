# -*- coding: utf-8 -*-
"""core/cache.py -- 실행 캐시 키 원칙 (design §9, card 20261104-op23 C-3.9).

키 = sha256(어댑터 지문 ∥ 방언 텍스트 ∥ 모델 묶음 LF sha256 정렬 목록 ∥ 실행 인자 ∥ spiceinit sha256(없으면 빈 값)).
같은 키는 결과를 재사용하고, 키에 없는 입력이 결과를 바꾸면 결함이다. 시간 초과 실행은 저장하지 않는다(어댑터 몫).
결과 저장·복원은 어댑터가 하고(방언 파일을 다루므로), 이 모듈은 키 정의 하나만 갖는다. 판정은 캐시 상태를 읽지 않는다.
"""
from __future__ import annotations

from core.descriptor import canonical_sha256


def cache_key(adapter_fp: str, text: str, bundle_lf, args, spiceinit_sha: str) -> str:
    return canonical_sha256({"adapter_fp": adapter_fp, "text": text, "bundle": sorted(bundle_lf), "args": list(args),
                             "spiceinit_sha256": spiceinit_sha or ""})
