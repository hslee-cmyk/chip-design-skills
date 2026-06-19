# db/design/ — 칩 공유 RTL (git submodule)

칩 공유 RTL이 **submodule로 마운트**되는 지점이다 (`.gitmodules`에 `db/design` 등록).

```bash
git submodule update --init        # 최초 체크아웃
git submodule update --remote      # 최신 반영
```
- 이 안의 RTL은 **read-only로 취급** — formal/lint scratch는 `<project>/formal/`에서(guard hook 강제).
- 수정이 필요하면 submodule 저장소에서 commit 후 상위에서 포인터 갱신.
