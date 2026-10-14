"""PDF -> Markdown 변환(토폴로지 원문 보관용). 사용: python pdf_to_md.py <pdf> <출력폴더> "<제목>" "<출처 URL 또는 빈 값>"
- 원본 PDF를 source.pdf 로 복사, 쪽마다 텍스트(리거처 정리)와 쪽 렌더 PNG(150 dpi), 내장 이미지를 저장."""
import sys, shutil, pathlib, hashlib, fitz

LIG = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl"}


def clean(t):
    for a, b in LIG.items():
        t = t.replace(a, b)
    return t


def main(pdf, out, title, url):
    pdf, out = pathlib.Path(pdf), pathlib.Path(out)
    (out / "pages").mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    shutil.copy2(pdf, out / "source.pdf")
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    doc = fitz.open(pdf)
    lines = [f"# {title}", "",
             f"- 원본 PDF: `{pdf}`", f"- 사본: `source.pdf` (sha256 `{sha}`)",
             f"- 웹 출처: {url or '(기록 없음)'}", f"- 쪽 수: {doc.page_count}",
             "- 변환: PyMuPDF 텍스트 추출(쪽 단위). 수식·표·그림은 텍스트가 깨질 수 있으니 같은 쪽의 렌더 PNG(`pages/`)로 확인할 것.", ""]
    for i, page in enumerate(doc, 1):
        png = f"pages/p{i:02d}.png"
        page.get_pixmap(dpi=150).save(out / png)
        lines += ["---", "", f"## p.{i}", "", f"![p.{i}]({png})", ""]
        for j, img in enumerate(page.get_images(full=True), 1):
            pix = fitz.Pixmap(doc, img[0])
            if pix.n - pix.alpha >= 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            name = f"images/p{i:02d}_{j}.png"
            pix.save(out / name)
            lines += [f"![p.{i} 내장 이미지 {j}]({name})", ""]
        text = clean(page.get_text("text")).strip()
        if text:
            lines += ["```text", text, "```", ""]
    (out / "paper.md").write_text("\n".join(lines), encoding="utf-8")
    print(out / "paper.md", doc.page_count)


if __name__ == "__main__":
    main(*sys.argv[1:5])
