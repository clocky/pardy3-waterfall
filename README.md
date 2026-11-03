# Pardy 3: Flimbo's FLI waterfall found

The packed disk file `11.CHRIS..FLIMBO` contains a credit screen at recovered RAM $3200 explicitly identifying a 40x24 FLI waterfall coded by Flimbo of Xentrix, with music by Chris/Xentrix and graphics by Flimbo/Xentrix. See the included verbatim decoded credits.

The display code independently supports that identification: initialization at $2000 installs the raster IRQ at $2033. The loop at $2055-$20B9 changes $D018 from a table at $2B00 and repeatedly increments $D011, with NOP/BIT timing padding. This is the characteristic FLI mechanism. Animation updates screen memory and the screen-pointer table. The entry after decompression is $3620. The intro waits for SPACE; its text says RESTORE exits the effect.

## Recovery and limits

Downloaded from https://csdb.dk/getinternalfile.php/19472/Xentrix%20-%20Pardey%20demo%203.D64 (release: https://csdb.dk/release/?id=30608).

Parsed the D64 directory and followed each file's sector chain. The target is stored with load address $2800 but contains a packed program designed to execute after relocation to $0801. For analysis, its payload was placed at $0801 and the depacker executed from $080D using py65's 6502 interpreter. Execution stopped before CLI at $044A, immediately before JMP $3620. The included 64 KiB dump includes decompressed data and leftover packed bytes; it is an analysis snapshot, NOT a VICE snapshot or standalone runnable PRG.

The addressed disassembly covers the display routine and intro code. It is not yet a complete reassemblable source recovery. The effect's identity and authorship are explicit in the binary. No live visual playback or cycle-accurate timing verification has been completed. REA's advertised binary formats do not cover D64/6510; this recovery used a format-specific disk parser and 6502 interpreter instead.

## Next recovery step

Run the original D64 in a PAL C64 emulator, reach this part, press SPACE, and capture the waterfall. Preserve its loader/KERNAL assumptions when building a standalone version. Keep instruction placement and timing unchanged until an unchanged build is verified.

Original D64 SHA-256: `cdd2305f2bfca195d565855c5840f429409c07a76bd7c7d294b990133ac40aa8`
