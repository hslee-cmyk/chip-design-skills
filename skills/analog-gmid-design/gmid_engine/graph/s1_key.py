"""S1 지문 (설계 design_mod3_s1_graph 5.1, S0 지문의 S1 부분 P 363~364, NFR-2 '키 = 그 계산이 실제로 읽는 상태의 지문').

진입점: `s1_key(doc, supplies) -> S1Key`.

* `topology_fp` = `doc.connectivity_fp`(정규화한 연결 투영 -- `_` 주석·태그 키·원소 순서와 무관, 파일 sha256 은 넣지 않음).
* `rule_fp` = `S1_RULE_FILES`(S1 필드 값을 정하는 graph 파일) 각각의 (basename, 파일 바이트 sha256) 를 이름순으로 묶은
  `fp_of`. writer 코드가 바뀌면 키가 바뀐다.
* `supplies_v_fp` = `fp_of(supplies)`(`supplies_declaration` 이 정규화한 tuple), None 이면 `NO_SUPPLIES_FP`.
"""
import hashlib
from pathlib import Path

from gmid_engine.core import fp_of

from .s1_values import NO_SUPPLIES_FP, S1_RULE_FILES, S1Key


def s1_key(doc, supplies):
    here = Path(__file__).resolve().parent
    rule_fp = fp_of(tuple((name, hashlib.sha256(_lf_bytes(here / name)).hexdigest())
                          for name in sorted(S1_RULE_FILES)))
    supplies_fp = NO_SUPPLIES_FP if supplies is None else fp_of(supplies)
    return S1Key(doc.connectivity_fp, rule_fp, supplies_fp)


def _lf_bytes(path):
    # 줄 끝을 LF 로 맞춘 바이트 -- checkout 의 CRLF 변환(core.autocrlf)이 지문을 바꾸지 않게 한다.
    return path.read_bytes().replace(b"\r\n", b"\n")
