"""gmid_engine test 경로 설정 -- editable 설치 없이 skills/analog-gmid-design 을 sys.path 앞에 둬 `import gmid_engine` 이 되게 한다."""
import os
import sys

# tests -> gmid_engine -> analog-gmid-design(패키지 부모)
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _SKILL_DIR not in sys.path:
    sys.path.insert(0, _SKILL_DIR)
