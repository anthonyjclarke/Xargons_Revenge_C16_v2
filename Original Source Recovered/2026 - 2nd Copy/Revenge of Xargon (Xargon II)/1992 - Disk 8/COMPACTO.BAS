1000 a=a+1:IF a=1 THEN LOAD "title-data",8,1
1010 POKE 56,64:CLR
1020 a=32768:REM start of data
1030 b=16384:REM save compacted data
1040 c=0    :REM counter
1050 :
1060 :
1070 REM start of loop
1080 :
1085 y=PEEK(32768+c*2)
1090 z=PEEK(32768+c*2+1)
1100 x=(y*16)+z
1110 :
1120 POKE b+c,x
1130 :
1140 c=c+1
1160 IF c<>320 THEN 1070
