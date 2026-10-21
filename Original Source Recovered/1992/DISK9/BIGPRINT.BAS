10 a$="xargon's"
20 xx=0:yy=0:GOSUB 2000
30 a$="revenge"
40 xx=0:yy=9:GOSUB 2000
50 WAIT198,1:STOP
1000 REM print (a) at (x),(y)
1010 da=14336+a*8
1020 sc=1024+x+y*40
1030 FOR y=0 TO 7
1050 d=PEEK(da+y)
1060 FOR x=7 TO 0 STEP -1
1070 d1=(d/2):d=(d/2)AND255
1071 IF d1<>d THEN POKE sc+x,160
1090 NEXT x
1091 sc=sc+40
1092 NEXT y
1100 RETURN
2000 FOR b=1 TO LEN(a$)
2010 a=ASC(MID$(a$,b,1))AND 63
2020 x=xx
2030 y=yy
2040 GOSUB 1000
2041 xx=xx+8
2050 NEXT b
2060 RETURN
