"""S1v 규칙 코드 지문 (설계 40 §3.2 '`rule_hash`', 계획 N3.3 S0 '유도 규칙 코드 해시').

진입점: `s1v_rule_fp() -> str`.

`S1V_RULE_FILES`(S1v 필드 값을 정하는 graph 파일) 각각의 (basename, LF 정규화 파일 바이트 sha256)을 이름순으로 묶은 `fp_of`. 파일이 바뀌면 지문이 바뀐다 --
`build_s1v` 의 재사용 키와 `structure.json` 의 `rule_hash` 가 이 값을 쓴다.
"""
import hashlib
from pathlib import Path

from gmid_engine.core import fp_of

from .s1v_values import S1V_RULE_FILES


def s1v_rule_fp():
    here = Path(__file__).resolve().parent
    return fp_of(tuple((name, hashlib.sha256((here / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest())
                       for name in sorted(S1V_RULE_FILES)))
