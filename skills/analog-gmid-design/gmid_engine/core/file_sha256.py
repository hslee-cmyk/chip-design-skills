"""파일 내용 sha256 -- 줄바꿈 LF 환산값 (WB-1 범위 0, 선언 파일의 기계 독립 지문).

진입점: `file_sha256`.

값 = sha256(파일 바이트의 CRLF -> LF). 같은 선언을 CRLF 기계와 LF 기계에서 읽어도 같은 값이다. 파일 없음 = `FileNotFoundError`.
"""
import hashlib


def file_sha256(path):
    """`path` 파일의 LF 환산 sha256(64자 hex). 파일이 없으면 `FileNotFoundError`."""
    with open(path, "rb") as fh:
        data = fh.read()
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
