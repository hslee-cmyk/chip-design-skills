# -*- coding: utf-8 -*-
"""design 20 §11-1(231행) 정정 -- 계획 정정 A2(8356c1e, v5.20) 반영.

DF-19·DF-26 교체가 "MG1 레일 이름 변경과 같은 자리"라는 문장을, A2 뒤 계획 DF-19 `수정 Phase` 칸
(넷 몫 = B26-1~B26-4, Phase 3 착수 전 가능 / 전압 몫 = MG1) 인용으로 바꾼다.

사용: python -B patch_design20_231.py [--root <저장소 루트>]   (기본 = 메인 체크아웃)
- 바이너리로 읽고 쓰며 줄 끝(LF/CRLF)·나머지 바이트는 그대로 둔다.
- 옛 문장이 정확히 1번 있어야 바꾼다. 새 문장이 이미 있고 옛 문장이 없으면 '이미 적용'으로 끝낸다(멱등).
"""
import argparse
import os
import sys

REL = "docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md"

OLD = ("→ 새 DF 없이 DF-19·DF-26 교체(담당 Phase 4, MG1 레일 이름 변경과 같은 자리)에서 다룬다.")

NEW = ("→ 새 DF 없이 DF-19·DF-26 교체(`수정 Phase` 4)에서 다룬다. 이 교체는 MG1과 한 자리가 아니다 -- "
       "2026-10-01 계획 정정 A2(v5.20, 승인 기록 `20260930-b26-before-phase3`) 뒤 계획 DF-19 `수정 Phase` 칸: "
       "\"넷 몫(`supply_nets`)은 B26-1~B26-4로 나누고 Phase 3 착수 전에 해도 된다 -- DF-26과 같은 변경 단위. "
       "전압 몫(`supplies_v`, 스칼라 `vdd` 리터럴)은 MG1과 같은 변경 단위\". 위 레일 집합 세 곳과 "
       "`_metric_supply_current`의 `'vdd'` 넷 선택은 넷 몫(B26-1~B26-4)이고, 스칼라 `vdd` 전압 리터럴만 MG1 몫이다"
       "(처음 기록 'MG1 레일 이름 변경과 같은 자리'는 A2 전 계획 기준이었다).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills")
    ns = ap.parse_args()
    path = os.path.join(ns.root, *REL.split("/"))
    with open(path, "rb") as f:
        data = f.read()
    old_b, new_b = OLD.encode("utf-8"), NEW.encode("utf-8")
    n_old, n_new = data.count(old_b), data.count(new_b)
    if n_old == 0 and n_new == 1:
        print("이미 적용: " + REL)
        return 0
    if n_old != 1 or n_new != 0:
        print("중단: 옛 문장 %d회, 새 문장 %d회(기대 1·0) -- %s" % (n_old, n_new, REL))
        return 1
    out = data.replace(old_b, new_b, 1)
    assert out.count(b"\r\n") == data.count(b"\r\n"), "CRLF 수가 바뀌었다"
    assert out.count(b"\n") == data.count(b"\n"), "줄 수가 바뀌었다"
    with open(path, "wb") as f:
        f.write(out)
    print("적용: " + REL + " (1곳, 줄 수 불변)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
