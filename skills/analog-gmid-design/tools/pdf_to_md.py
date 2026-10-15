"""topology 원문 PDF 보관 도구 (assets/*/sources/<폴더>/).

변환:  python tools/pdf_to_md.py convert <pdf> <출력폴더> "<제목>" "<웹 출처 또는 빈 값>"
  - source.pdf(원본 사본), paper.md(쪽 단위 텍스트 + 렌더 링크), pages/(150 dpi 쪽 렌더), images/(PDF 내장 비트맵)를 만든다.
  - paper.md 머리의 웹 출처·그림 위치·엔진 연결 줄은 변환 뒤 사람이 적는다.
생성:  python tools/pdf_to_md.py ensure [<sources 폴더> ...]   (기본: assets/library/sources, assets/heldout/sources)
  - pages/·images/ 는 git 에 넣지 않는다(.gitignore, 사용자 2026-10-14). 필요할 때 없으면 이 명령이 source.pdf 에서 다시 만든다.
  - paper.md 는 건드리지 않는다. 이미 있는 PNG 는 다시 쓰지 않는다.
"""
import sys, shutil, pathlib, hashlib, fitz

DPI = 150
LIG = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
SKILL = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_ROOTS = (SKILL / "assets" / "library" / "sources", SKILL / "assets" / "heldout" / "sources")


def clean(t):
    for a, b in LIG.items():
        t = t.replace(a, b)
    return t


def _page_png(i):
    return f"pages/p{i:02d}.png"


def _image_png(i, j):
    return f"images/p{i:02d}_{j}.png"


def _write_image(doc, xref, path):
    pix = fitz.Pixmap(doc, xref)
    if pix.n - pix.alpha >= 4:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    pix.save(path)


def render_assets(out, only_missing):
    """out/source.pdf 에서 pages/·images/ 를 만든다. 만든 파일 수를 돌려준다."""
    out = pathlib.Path(out)
    (out / "pages").mkdir(exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    doc = fitz.open(out / "source.pdf")
    made = 0
    for i, page in enumerate(doc, 1):
        target = out / _page_png(i)
        if not (only_missing and target.exists()):
            page.get_pixmap(dpi=DPI).save(target)
            made += 1
        for j, img in enumerate(page.get_images(full=True), 1):
            target = out / _image_png(i, j)
            if not (only_missing and target.exists()):
                _write_image(doc, img[0], target)
                made += 1
    return made


def convert(pdf, out, title, url):
    pdf, out = pathlib.Path(pdf), pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf, out / "source.pdf")
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    render_assets(out, only_missing=False)
    doc = fitz.open(out / "source.pdf")
    lines = [f"# {title}", "",
             f"- 원본 PDF: `{pdf}`", f"- 사본: `source.pdf` (sha256 `{sha}`)",
             f"- 웹 출처: {url or '(기록 없음)'}", f"- 쪽 수: {doc.page_count}",
             "- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.",
             "- `pages/`·`images/` 는 git 에 없다. 없으면 skill 폴더에서 `python tools/pdf_to_md.py ensure` 로 만든다.", ""]
    for i, page in enumerate(doc, 1):
        lines += ["---", "", f"## p.{i}", "", f"![p.{i}]({_page_png(i)})", ""]
        for j, _ in enumerate(page.get_images(full=True), 1):
            lines += [f"![p.{i} 내장 이미지 {j}]({_image_png(i, j)})", ""]
        text = clean(page.get_text("text")).strip()
        if text:
            lines += ["```text", text, "```", ""]
    (out / "paper.md").write_text("\n".join(lines), encoding="utf-8")
    print(out / "paper.md", doc.page_count)


def ensure(roots):
    for root in roots:
        for pdf in sorted(pathlib.Path(root).glob("*/source.pdf")):
            made = render_assets(pdf.parent, only_missing=True)
            print(pdf.parent.name, "만든 파일", made)


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "convert":
        convert(*args[:4])
    elif cmd == "ensure":
        ensure(args or DEFAULT_ROOTS)
    else:
        raise SystemExit("사용: pdf_to_md.py convert <pdf> <출력폴더> <제목> <웹 출처> | ensure [<sources 폴더> ...]")
