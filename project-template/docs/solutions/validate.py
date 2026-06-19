#!/usr/bin/env python3
"""Validate docs/solutions/**/*.md frontmatter against schema.yaml.

RTL knowledge-asset validator (compound-docs 스타일). enum/필수필드/카테고리 정합/
날짜·태그 형식을 검사한다. CI나 커밋 훅에서 호출.

Usage:
    python validate.py            # docs/solutions 전체 검사
    python validate.py <file.md>  # 특정 파일만

Exit code 0 = PASS, 1 = 검증 실패, 2 = 실행 오류(스키마/의존성).
"""
from __future__ import annotations
import re
import sys
from datetime import date as _date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요. `pip install pyyaml` 또는 OSS CAD python.", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schema.yaml"

# frontmatter에 안 쓰는 서술 필드(본문에 둠) — required에서 제외
SCALAR_REQUIRED = ("module", "date")
# 폴더명(하이픈) ↔ problem_type(언더스코어) 매핑은 단순 치환으로 도출
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TAG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema 없음: {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(2)
    data = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    req = data.get("required", {}) or {}
    # enum 필드 = required 중 list 값을 가진 항목
    enums = {k: set(v) for k, v in req.items() if isinstance(v, list)}
    required_fields = list(req.keys())
    return {"enums": enums, "required_fields": required_fields}


def parse_frontmatter(text: str):
    m = FM_RE.match(text)
    if not m:
        return None, "frontmatter(--- ... ---) 없음"
    try:
        return yaml.safe_load(m.group(1)), None
    except yaml.YAMLError as e:
        return None, f"frontmatter YAML 파싱 실패: {e}"


def category_for(path: Path) -> str:
    # docs/solutions/<category>/file.md → <category>
    rel = path.resolve().relative_to(ROOT)
    return rel.parts[0] if len(rel.parts) > 1 else ""


def validate_file(path: Path, schema: dict) -> list[str]:
    errs: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm, err = parse_frontmatter(text)
    if err:
        return [err]
    if not isinstance(fm, dict):
        return ["frontmatter가 매핑이 아님"]

    enums = schema["enums"]
    # 1) 필수 필드
    for field in schema["required_fields"]:
        if field not in fm or fm[field] in (None, ""):
            errs.append(f"필수 필드 누락/빈값: {field}")
    # 2) enum 정합
    for field, allowed in enums.items():
        if field in fm and fm[field] not in (None, ""):
            if fm[field] not in allowed:
                errs.append(
                    f"{field}='{fm[field]}' 는 허용값 아님 "
                    f"({', '.join(sorted(allowed))})"
                )
    # 3) date 형식
    d = fm.get("date")
    if d is not None:
        ds = d.isoformat() if isinstance(d, _date) else str(d)
        if not DATE_RE.match(ds):
            errs.append(f"date 형식 오류(YYYY-MM-DD): {ds}")
    # 4) problem_type ↔ 폴더 정합
    cat = category_for(path)
    pt = fm.get("problem_type")
    if pt and cat:
        if cat.replace("-", "_") != str(pt):
            errs.append(f"problem_type='{pt}' 가 폴더 '{cat}/' 와 불일치")
    # 5) tags 형식
    tags = fm.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            errs.append("tags 는 배열이어야 함")
        else:
            for t in tags:
                if not TAG_RE.match(str(t)):
                    errs.append(f"tag '{t}' 는 lowercase-하이픈 형식 아님")
    return errs


def collect(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    files = []
    for p in sorted(target.rglob("*.md")):
        rel = p.resolve().relative_to(ROOT)
        if rel.parts[0] in ("patterns",) or p.name in ("README.md",):
            continue  # 카탈로그/패턴 문서는 frontmatter 스키마 대상 아님
        files.append(p)
    return files


def main() -> int:
    schema = load_schema()
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
    files = collect(target)
    if not files:
        print("검사 대상 .md 없음")
        return 0
    failed = 0
    for f in files:
        errs = validate_file(f, schema)
        rel = f.resolve().relative_to(ROOT)
        if errs:
            failed += 1
            print(f"FAIL  {rel}")
            for e in errs:
                print(f"      - {e}")
        else:
            print(f"PASS  {rel}")
    print(f"\n{len(files) - failed}/{len(files)} PASS"
          + (f", {failed} FAIL" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
