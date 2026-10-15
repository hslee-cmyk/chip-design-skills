"""gmid_engine -- 새 gm/ID 엔진(계획 N3 아키텍처). 하위 패키지 core(층 0) < lut < authoring < graph < sizing < metrics < search < layout < convergence < report < pipeline; 공개 API 는 각 하위 패키지 `__all__` 로만."""

__all__ = ()

from gmid_engine.core import pin_blas_threads

pin_blas_threads()      # [NFR-4] import 때 BLAS 스레드 1 고정·확인(못 하면 RuntimeError) -- 하위 패키지 import 는 이 파일을 먼저 실행한다
