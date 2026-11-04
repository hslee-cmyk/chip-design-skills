# 복제본 사본 test 의 log_of 만 고친다(로그를 실행 폴더 기준으로 읽음). 다른 단언 변경 없음. 원인 확인용.
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
s = s.replace('return Path(p).read_text(encoding="utf-8", errors="replace")', 'return Path(_LAST["w"], p).read_text(encoding="utf-8", errors="replace")', 1)
s = s.replace("def log_of(res):", '_LAST = {}\n\n\ndef log_of(res):', 1)
s = s.replace('    res = ad.run(ckt, req, descriptor, str(tmp_path / "work"), None, None, compat)', '    _LAST["w"] = str(tmp_path / "work")\n    res = ad.run(ckt, req, descriptor, str(tmp_path / "work"), None, None, compat)', 1)
s = s.replace('    res = ad.run(ckt, req, descriptor, str(tmp_path / "work"), None, None, None)', '    _LAST["w"] = str(tmp_path / "work")\n    res = ad.run(ckt, req, descriptor, str(tmp_path / "work"), None, None, None)', 1)
open(p, "w", encoding="utf-8").write(s)
