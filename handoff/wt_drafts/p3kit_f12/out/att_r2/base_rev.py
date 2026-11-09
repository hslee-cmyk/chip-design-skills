"""측정 전용 합성 probe(review_p3_f12_r1 S2 공격 A1b·A2·A10·A3 -- 모듈 객체 탈출 자리). 역할 산출물 아님."""
import sys
import sizing_recipe as sr


def helper(m):
    return m.diode_vds_window


def main():
    a = vars(sr)["allocate_stack_headroom"]
    b = helper(sr)
    alias = sr
    c = alias.diode_vds_window
    n = "size_transistor"
    d = getattr(sr, n)
    print(a, b, c, d, sr.size_transistor, file=sys.stderr)


if __name__ == "__main__":
    main()
