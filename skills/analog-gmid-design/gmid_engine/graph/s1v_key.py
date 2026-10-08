"""S1v 규칙 코드 지문 (설계 40 §3.2 '`rule_hash`', 계획 N3.3 S0 '유도 규칙 코드 해시').

진입점: `structure_rule_fp() -> str`  (`s1v_rule_fp() -> str` 은 그 부분 계산이고 같은 파일에 둔다 -- `structure_rule_fp` 가 부른다).

* `s1v_rule_fp()`: `S1V_RULE_FILES`(S1v 필드 값을 정하는 graph 파일) 각각의 (basename, LF 정규화 파일 바이트 sha256)을 이름순으로 묶은 `fp_of`. 파일이 바뀌면 지문이 바뀐다 --
  `build_s1v` 의 재사용 키가 쓴다.
* `structure_rule_fp()`: `s1v_rule_fp()` + `STRUCTURE_RULE_EXTRA_FILES`(사실이 대조하거나 덮어쓰는 S1 쪽 소비 파일 -- 복합 diode·DC 역할·gs 묶음·matching 그룹)의 같은 방식 지문.
  `structure.json` 의 `rule_hash` 가 이 값이다. S1 쪽 소비 파일이 바뀌어도 사실이 stale(review_needed)로 돌아간다 -- as-built 가 S1v 파일만 보던 틈을 닫는다(40 §3.2-3).
"""
import hashlib
from pathlib import Path

from gmid_engine.core import fp_of

from .s1v_values import S1V_RULE_FILES, STRUCTURE_RULE_EXTRA_FILES


def _files_fp(names):
    here = Path(__file__).resolve().parent
    return fp_of(tuple((name, hashlib.sha256((here / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest())
                       for name in sorted(names)))


def s1v_rule_fp():
    return _files_fp(S1V_RULE_FILES)


def structure_rule_fp():
    return fp_of((s1v_rule_fp(), _files_fp(STRUCTURE_RULE_EXTRA_FILES)))
