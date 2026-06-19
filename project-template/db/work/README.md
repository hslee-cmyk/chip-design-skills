# db/work/ — 빌드 출력 (대부분 gitignore)

iCEcube2/yosys 빌드 산출물이 `db/work/<BASE_NAME>/` 아래 생성된다. 빌드 시 자동 생성되므로 비워둬도 된다.

권장 .gitignore:
```
db/work/**/work/
db/work/**/*.log*
db/work/<BASE_NAME>/*.xcf
db/work/yosys_build/
```
