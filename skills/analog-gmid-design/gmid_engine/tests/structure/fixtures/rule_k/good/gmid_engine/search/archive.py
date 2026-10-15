"""쓰기만 한다: read_snapshot 같은 읽기 API 는 없다(문자열 안 언급은 참조가 아니다)."""


class S3Archive:
    def __init__(self, root):
        self.dir = root

    def write_snapshot(self, ref, body):
        self.snapshot_dir = self.dir / "snapshots"
        return "front_query", ref, body
