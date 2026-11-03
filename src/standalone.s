; Pardy 3 FLI waterfall - standalone unpacked PRG (64tass)
; Code/graphics: Flimbo/Xentrix, music: Chris/Xentrix, 1990.
;
; Wraps the depacked RAM image from recovered/unpacked-analysis-ram.bin
; with a BASIC stub that reproduces the depacker's hand-off
; ($01=$37, CLI, JMP $3620). The effect code itself is not yet
; reassembled from source; it is included byte-for-byte from the dump.

DUMP = "../recovered/unpacked-analysis-ram.bin"

        * = $0801
        .word basend, 1990
        .byte $9e
        .text "2061"
        .byte 0
basend  .word 0

        * = $080d
        sei
        lda #$37
        sta $01
        cli
        jmp $3620               ; post-depack entry (resets counters, runs intro)

        * = $0d00               ; music ($1000), effect ($2000), tables, intro ($3200-$35ff), $4000 page
        .binary DUMP, $0d00, $4500 - $0d00

        * = $9000               ; NMI/RESTORE exit handler
        .binary DUMP, $9000, $0100
