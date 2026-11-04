# -*- coding: utf-8 -*-
"""adapters/ngspice/run.py -- ngspice 배치 실행·모델 묶음 수집·실행 캐시 저장소 (design §8.2·§9, card 20261104-op23).

프로세스를 부르는 곳은 이 파일뿐이다(`subprocess`). 실행은 순차 하나다(P NFR-P7). 캐시 키 정의는 코어 `core.cache.cache_key`(D §9)이고
이 파일은 그 키로 슬롯 폴더를 읽고 쓴다: 키 = sha256(어댑터 지문 ∥ 방언 텍스트 ∥ 모델 묶음 LF 정렬 목록 ∥ 실행 인자 ∥ spiceinit sha). 시간 초과 실행은
슬롯을 만들지 않는다. 판정은 캐시 상태를 읽지 않는다.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess

from core.results import OracleError, lf_sha256, raw_sha256

_INC = re.compile(r"""^\s*\.(?:include|inc|lib)\s+["']?([^"'\s]+)["']?""", re.I)
ARGS = ("-b",)


def model_files(path, seen):
    """path 가 .include/.lib/.inc 로 읽는 파일을 재귀로 모은다(상대 경로는 그 파일 폴더 기준). 못 찾으면 그 경로를 돌려준다(없으면 None)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for ln in lines:
        m = _INC.match(ln)
        if not m:
            continue
        q = m.group(1)
        q = q if os.path.isabs(q) else os.path.join(os.path.dirname(os.path.abspath(path)), q)
        q = os.path.abspath(q)
        if q in seen:
            continue
        if not os.path.exists(q):
            return q
        seen.add(q)
        miss = model_files(q, seen)
        if miss:
            return miss
    return None


def collect_bundle(roots):
    """루트 파일 목록 -> {경로: {lf, raw}} (include 재귀). 파일을 못 읽으면 sim_model_not_found."""
    seen = []
    allp = set()
    for r in roots:
        r = os.path.abspath(r)
        if not os.path.exists(r):
            raise OracleError("sim_model_not_found", {"path": r}, "8")
        if r not in allp:
            allp.add(r)
            seen.append(r)
        sub = set()
        miss = model_files(r, sub)
        if miss:
            raise OracleError("sim_model_not_found", {"path": miss, "included_from": r}, "8")
        for q in sorted(sub):
            if q not in allp:
                allp.add(q)
                seen.append(q)
    out = {}
    for p in seen:
        with open(p, "rb") as f:
            b = f.read()
        out[p.replace("\\", "/")] = {"lf": lf_sha256(b), "raw": raw_sha256(b)}
    return out


def execute(exe, text, work_dir, data_files, timeout_s, cache_dir, key):
    """text 를 work_dir/bench.cir 로 쓰고 `exe -b bench.cir` 를 돌린다. 반환 (rc | None, 로그 글, 캐시 상태, 시간 초과 여부).
    캐시 상태 None(캐시 폴더 없음) | 'hit' | 'miss'. data_files = 넷리스트가 work_dir 에 쓰는 데이터 파일 이름(캐시에 함께 저장·복원)."""
    os.makedirs(work_dir, exist_ok=True)
    cir, log_path = os.path.join(work_dir, "bench.cir"), os.path.join(work_dir, "bench.log")
    for n in data_files:
        p = os.path.join(work_dir, n)
        if os.path.exists(p):
            os.remove(p)
    with open(cir, "wb") as f:
        f.write(text.encode("utf-8"))
    state = None if not cache_dir else "miss"
    slot = os.path.join(cache_dir, key) if cache_dir else None
    if slot and os.path.exists(os.path.join(slot, "done")):
        for n in data_files:
            src = os.path.join(slot, n)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(work_dir, n))
        shutil.copyfile(os.path.join(slot, "bench.log"), log_path)
        with open(os.path.join(slot, "rc"), encoding="utf-8") as f:
            rc = int(f.read().strip())
        with open(log_path, encoding="utf-8", errors="replace") as f:
            return rc, f.read(), "hit", False
    try:
        with open(log_path, "w", encoding="utf-8", errors="replace") as fo:
            r = subprocess.run([exe, *ARGS, "bench.cir"], cwd=work_dir, stdout=fo, stderr=subprocess.STDOUT, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            return None, f.read(), state, True              # 시간 초과 실행은 슬롯을 만들지 않는다
    if slot:
        os.makedirs(slot, exist_ok=True)
        for n in data_files:
            if os.path.exists(os.path.join(work_dir, n)):
                shutil.copyfile(os.path.join(work_dir, n), os.path.join(slot, n))
        shutil.copyfile(log_path, os.path.join(slot, "bench.log"))
        with open(os.path.join(slot, "rc"), "w", encoding="utf-8") as f:
            f.write(str(r.returncode))
        with open(os.path.join(slot, "done"), "w", encoding="utf-8") as f:
            f.write(key)
    with open(log_path, encoding="utf-8", errors="replace") as f:
        return r.returncode, f.read(), state, False
