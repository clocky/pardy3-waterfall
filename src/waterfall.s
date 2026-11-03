; pardy 3 (xentrix, 1990)
; 40x24 fli "waterfall"
; code+gfx flimbo/xentrix
; music chris/xentrix
;
; turbo macro pro / tmpx source.
; build: make  (tmpx, or 64tass -C -T -a)

; basic stub: 1990 sys2061

         *= $0801
         .word basend,1990
         .byte $9e
         .text "2061"
         .byte 0
basend   .word 0

; same hand-off as the depacker

start    sei
         lda #$37
         sta $01
         cli
         jmp entry

         .include "tables.s"
         .include "music.s"
         .include "effect.s"
         .include "intro.s"
         .include "vicbank.s"
         .include "restore.s"
