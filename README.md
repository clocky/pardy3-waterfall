# Pardy 3: Flimbo's FLI waterfall found

The packed disk file `11.CHRIS..FLIMBO` contains a credit screen at recovered RAM $3200 explicitly identifying a 40x24 FLI waterfall coded by Flimbo of Xentrix, with music by Chris/Xentrix and graphics by Flimbo/Xentrix. See the included verbatim decoded credits.

The display code independently supports that identification: initialization at $2000 installs the raster IRQ at $2033. The loop at $2055-$20B9 changes $D018 from a table at $2B00 and repeatedly increments $D011, with NOP/BIT timing padding. This is the characteristic FLI mechanism. Animation updates screen memory and the screen-pointer table. The entry after decompression is $3620. The intro waits for SPACE; its text says RESTORE exits the effect.

## Recovery and limits

Downloaded from https://csdb.dk/getinternalfile.php/19472/Xentrix%20-%20Pardey%20demo%203.D64 (release: https://csdb.dk/release/?id=30608).

Parsed the D64 directory and followed each file's sector chain. The target is stored with load address $2800 but contains a packed program designed to execute after relocation to $0801. For analysis, its payload was placed at $0801 and the depacker executed from $080D using py65's 6502 interpreter. Execution stopped before CLI at $044A, immediately before JMP $3620. The included 64 KiB dump includes decompressed data and leftover packed bytes; it is an analysis snapshot, NOT a VICE snapshot or standalone runnable PRG.

The addressed disassembly in `recovered/` covers the display routine and intro code. The full source now lives in `src/` (see below). The effect's identity and authorship are explicit in the binary. Update (2026-11-03): both the original packed part and a standalone build (`make`, then `make run`) play the waterfall in VICE x64sc (PAL). Their screenshots are byte-identical. It has not been tested on real hardware. REA's advertised binary formats do not cover D64/6510; this recovery used a format-specific disk parser and 6502 interpreter instead.

## Building

The part has been re-sourced in Turbo Macro Pro / [TMPx](https://turbo.style64.org/) syntax in `src/`. It reassembles byte-identically to the depacked original with both TMPx and 64tass (`-T` Turbo Assembler mode):

```sh
brew install vice tass64   # emulator + native assembler
make tools                 # optional: fetch TMPx (x86_64; needs Rosetta on Apple Silicon)
make verify                # byte-identical check against the depacked image
make run                   # SPACE at the intro starts the waterfall
```

VS Code: open the folder, run `make vscode` once to install the bundled TMPx syntax highlighting, then use the Build/Verify/Run tasks.

## Next recovery steps

- Name the remaining auto-generated labels, and identify the data tables at `$0D00`, `$2800` and `$4000`.
- Disassemble the music player.
- RESTORE: the handler at `$9000` restores the demo's BASIC menu from RAM under ROM. In the standalone build there is no menu there.

The D64 is not committed to this repository. Download it from the CSDb link above and save it as `original/pardy3.d64`. Original D64 SHA-256: `cdd2305f2bfca195d565855c5840f429409c07a76bd7c7d294b990133ac40aa8`
