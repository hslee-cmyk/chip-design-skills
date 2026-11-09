"""c3_mixed.py에서 계약 3 변형 두 개를 만든다.
b: 실패 인벤토리 없음(rt_scale·항상 실패 test 제거) -> '인벤토리 없음 -> 생존 유지'를 ERROR 없이 관찰
c: 실패 인벤토리 def를 마지막에 -> 앞 def의 --out 기록이 남은 뒤 ERROR"""
src = open("C:/g17/probe/c3_mixed.py", encoding="utf-8").read()
old = ('ENG1 = ENG0 + ("\\n\\ndef rt_scale(x):\\n    return 3.0 * x\\n"\n'
       '               "\\n\\ndef rt_orphan(x):\\n    return x + 1\\n"\n'
       '               "\\n\\ndef rt_twice(x):\\n    return 2.0 * x\\n")')
assert old in src
b = src.replace('BASEDIR = "C:/g17/probe/c3"', 'BASEDIR = "C:/g17/probe/c3b"')
b = b.replace(old, 'ENG1 = ENG0 + ("\\n\\ndef rt_orphan(x):\\n    return x + 1\\n"\n'
                   '               "\\n\\ndef rt_twice(x):\\n    return 2.0 * x\\n")')
b = b.replace('w("skills/analog-gmid-design/assets/tests/test_rt_seven.py", T_SEVEN)\n', '')
assert "def rt_scale(x)" not in b and 'T_SEVEN)\n' not in b
b = b.replace('"""계약 3 측정', '"""계약 3 변형 b(실패 인벤토리 없음). 원본 설명: 계약 3 측정', 1)
open("C:/g17/probe/c3b_no_failing.py", "w", encoding="utf-8", newline="\n").write(b)
c = src.replace('BASEDIR = "C:/g17/probe/c3"', 'BASEDIR = "C:/g17/probe/c3c"')
c = c.replace(old, 'ENG1 = ENG0 + ("\\n\\ndef rt_orphan(x):\\n    return x + 1\\n"\n'
                   '               "\\n\\ndef rt_twice(x):\\n    return 2.0 * x\\n"\n'
                   '               "\\n\\ndef rt_scale(x):\\n    return 3.0 * x\\n")')
c = c.replace('"""계약 3 측정', '"""계약 3 변형 c(실패 인벤토리 def가 마지막). 원본 설명: 계약 3 측정', 1)
open("C:/g17/probe/c3c_failing_last.py", "w", encoding="utf-8", newline="\n").write(c)
print("ok")
