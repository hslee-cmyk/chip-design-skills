# -*- coding: utf-8 -*-
"""adapters/ngspice/errors.py -- ngspice 로그 -> 오류 코드 (design §7.1, op·ac 몫).

대응은 **로그 문장 형태**(줄 머리의 심각도 표지 + 문구)로 한다. 시뮬레이터가 다시 찍는 회로 제목 줄(`Circuit: ...`)과 사용자 이름(넷·소자)이 든
부분은 대응에서 뺀다(옛 부분 문자열 정규식의 거짓 적중, S-18). 회복된 경고 규칙: 회복 시도 경고는 결과가 있으면 정보(warnings)로만 싣고,
결과가 없을 때만 그 경고가 가리키는 코드를 낸다. 시간 초과(`sim_timeout`)·시간 걸음 실패(`sim_timestep_too_small`)·pz 반복 한도는 OP-4 몫이다.
"""
from __future__ import annotations

import re

# (줄 머리 정규식, 코드, 회복 시도 경고인가). 앞에서부터 처음 맞는 행. 코드 None = 정보(오류 아님).
_ROWS = (
    (re.compile(r"^error:\s*could not find include file", re.I), "sim_model_not_found", False),
    (re.compile(r"^error:\s*fatal error in ngspice", re.I), "sim_failed_other", False),
    (re.compile(r"^error:\s*no such (?:device or model name|parameter)", re.I), "sim_failed_other", False),
    (re.compile(r"^warning:\s*singular matrix", re.I), "sim_singular_matrix", True),
    (re.compile(r"^warning:\s*(?:dynamic gmin stepping|true gmin stepping|source stepping) failed", re.I), "sim_convergence_failed", True),
)


def classify(log: str, *, result_present: bool):
    """(코드 | None, warnings). 구체 코드가 `sim_failed_other` 보다 우선한다. 결과가 있으면 회복 시도 경고는 코드가 아니라 warnings 다."""
    codes, warnings = [], []
    for raw in log.splitlines():
        ln = raw.strip()
        for pat, code, recovery in _ROWS:
            if pat.match(ln):
                if recovery and result_present:
                    warnings.append(ln)
                else:
                    codes.append((code, ln))
                break
    specific = [c for c, _ in codes if c != "sim_failed_other"]
    code = specific[0] if specific else (codes[0][0] if codes else None)
    return code, warnings


def excerpt(log: str, limit: int = 40) -> list:
    """오류 코드에 대응된 줄만 고른 발췌(옛 log_errors 의 거짓 적중 제거)."""
    out = []
    for raw in log.splitlines():
        ln = raw.strip()
        if any(pat.match(ln) for pat, _, _ in _ROWS):
            out.append(ln)
    return out[:limit]
