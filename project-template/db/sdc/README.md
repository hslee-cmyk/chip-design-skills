# db/sdc/ — 제약 파일

- `.sdc` : 타이밍 제약 (`<TOP_MODULE>_ice.sdc`)
- `.pcf`(iCEcube2)/`.pdc`(Radiant)/`.lpf`(Diamond) : 핀·I/O 제약 (`<TOP_MODULE>_<pkg>_io.pcf`)

`config.sh`의 `PCF`/`SDC` 변수와 파일명을 일치시킬 것.
