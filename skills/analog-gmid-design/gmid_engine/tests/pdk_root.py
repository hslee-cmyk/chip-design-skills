"""test 용: PDK 위치 해석 -- PDK 상위 폴더 환경 변수 `GMID_PDK_ROOT`(없으면 `C:/pdk`) 하나에서 모든 PDK 경로를 도출한다.

엔진(`read_pdk_decl`·`resolve_lut_location`)과 같은 변수·같은 규칙(비어 있지 않은 환경 변수 우선, 없으면 default)을 독립 구현한 것이다 -- 엔진 함수를
부르지 않는다(oracle 독립). 라이브러리 폴더(`sky130_fd_pr`)·tech LEF 같은 하위 경로는 이 루트 아래에서 정한다(따로 받는 변수는 없다).
"""
import os

ENV = "GMID_PDK_ROOT"
DEFAULT_ROOT = "C:/pdk"


def effective_pdk_root(declared=None):
    """`declared` = 선언의 `pdk_root`(문자열 또는 `{"env", "default"}`), 생략하면 `GMID_PDK_ROOT` 또는 기본 루트."""
    if declared is None:
        declared = {"env": ENV, "default": DEFAULT_ROOT}
    if isinstance(declared, dict):
        return os.environ.get(declared.get("env") or "") or declared["default"]
    return declared


def pdk_roots(declared):
    """결과 값에 들어 있으면 안 되는 루트 표기들(선언의 default 와 이 기계의 실제 루트)."""
    default = declared["default"] if isinstance(declared, dict) else declared
    return (default, effective_pdk_root(declared))


def pdk_path(*parts):
    return "/".join((effective_pdk_root(),) + parts)


def fd_pr_dir():
    return pdk_path("sky130_fd_pr")


def tlef_path():
    return pdk_path("sky130_fd_sc_hd", "tech", "sky130_fd_sc_hd.tlef")
