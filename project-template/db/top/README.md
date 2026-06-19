# db/top/ — FPGA 전용 Top Wrapper

FPGA 전용 top 모듈(`<TOP_MODULE>.v`). 칩 코어(`db/design`)를 인스턴스화하고 하드 IP(오실레이터·I/O 버퍼)를 연결.
Top I/O는 single-bit 이름 규칙 준수(iCEcube2). `config.sh`의 `TOP_MODULE`과 일치.
