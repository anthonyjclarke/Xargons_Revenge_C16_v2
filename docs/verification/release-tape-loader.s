; Disassembly of $0C00-$0C5F from the decompressed xargons_revenge.prg (running version).
; Evidence only: not source, and not used in either game version.
; da65 V2.18 - N/A
; Page:       1


        .setcpu "6502"

L1800           := $1800
LFF90           := $FF90
LFFBA           := $FFBA
LFFBD           := $FFBD
LFFD5           := $FFD5
        lda     #$00
        sta     $FF15
        sta     $FF19
        jsr     LFF90
L0C0B:  lda     #$01
        tax
        ldy     #$FF
        jsr     LFFBA
        lda     #$02
        ldx     #$52
        ldy     #$0C
        jsr     LFFBD
        lda     #$00
        jsr     LFFD5
        inc     L0C53
        lda     L0C53
        cmp     #$35
        bne     L0C0B
        sei
        sta     $FF3F
        ldy     #$03
L0C31:  ldx     #$00
L0C33:  .byte   $BD
L0C34:  .byte   $04
        php
        .byte   $9D
        brk
L0C38:  php
        inx
        bne     L0C33
        inc     L0C34
        inc     L0C38
        dey
        bpl     L0C31
        jmp     L1800

        brk
        brk
        brk
        brk
        brk
        brk
        brk
        brk
        brk
        brk
        .byte   $50
L0C53:  and     $00,x
        brk
        brk
        brk
        brk
        brk
        brk
        brk
        brk
        brk
        brk
        brk
