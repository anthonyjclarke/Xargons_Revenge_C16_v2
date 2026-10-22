1000 REM auto booter
1010 REM
1020 REM (c) micro projects 1985
1030 REM
1040 a$="l "+CHR$(34)+"mega*"+CHR$(34)+" 08"+CHR$(13)
1050 a$=a$+"g 3c00"+CHR$(13)+CHR$(13)+"obj"+CHR$(13)
1060 a$=a$+"l "+CHR$(34)+"frak!"+CHR$(34)+" 08"+CHR$(13)
1070 a$=a$+"l "+CHR$(34)+"landscape-2"+CHR$(34)+" 08"+CHR$(13)
1080 a$=a$+"l "+CHR$(34)+"loader"+CHR$(34)+" 08"+CHR$(13)
1090 a$=a$+"g 033c"
1100 KEY 1,a$
1110 MONITOR
