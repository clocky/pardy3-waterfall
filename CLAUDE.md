# CLAUDE.md

Recovery and preservation of a Commodore 64 demo part: the 40x24 FLI "waterfall" from **Pardy 3** (Xentrix, 1990). Code and graphics by Flimbo/Xentrix, music by Chris/Xentrix. The repo owner is Flimbo, the original author, so they can answer questions about intent, but details from 1990 may have faded. This is reverse-engineering work, not a modern codebase.

## Build and run

```sh
make                # build/waterfall.prg (64tass): standalone, unpacked
make run            # boot it in x64sc (PAL). Press SPACE at the intro, RESTORE to exit
make run-original   # boot the packed original (loads to $0801 via -basicload)
make capture        # headless check: skips the SPACE wait through the remote monitor, writes build/capture/fli{1,2}.png
make clean
```

`src/standalone.s` is a BASIC stub (`SYS 2061`) that reproduces the depacker's hand-off (`$01=$37`, `CLI`, `JMP $3620`). It then includes the depacked RAM byte for byte: `$0D00–$44FF` and `$9000–$90FF`, taken from `recovered/unpacked-analysis-ram.bin`. The effect code has **not** been reassembled from mnemonics yet. **Verified on 2026-11-03:** the original and the build run in x64sc, and `make capture` screenshots are byte-identical between them at the same moments. After any change, compare against the original with this check.

## Layout

- `original/`: the untouched source material. **Never modify these files.**
  - `pardy3.d64`: the full disk image. It's **gitignored and not distributed** (`*.d64`), because the disk holds other people's parts too. If it's missing locally, download it from CSDb (link in the README; release 30608) and check SHA-256 `cdd2305f2bfca195d565855c5840f429409c07a76bd7c7d294b990133ac40aa8`.
  - `11-chris-flimbo.prg`: the disk file `11.CHRIS..FLIMBO`, extracted by following its sector chain. Its PRG header says load address `$2800`, with a BASIC stub `SYS 2061` (`$080D`). It's a packed program meant to run after relocation to `$0801`.
- `recovered/`: analysis output.
  - `unpacked-analysis-ram.bin`: a 64 KiB flat dump of C64 RAM, taken after running the depacker in py65. Execution stopped at `$044A`, just before `CLI` / `JMP $3620`. File offset = C64 address. Some leftover packed bytes are still in it. It's **not** a VICE snapshot and **not** a runnable PRG.
  - `disassembly.txt`: an annotated listing with addresses of the display routine and the intro. It's partial and can't be reassembled as it stands.
  - `credits.txt`: the intro screen text, decoded from `$3200` exactly as it appears.
- `src/standalone.s`: the 64tass build source, described above.
- `tools/capture.py`: drives the VICE text remote monitor on `127.0.0.1:6510` to skip the SPACE wait and take screenshots. It uses only the standard library.
- `build/`: build output (gitignored).
- `README.md`: the provenance, recovery method, known limits and next steps.

## Memory map (from the RAM dump)

| Address | Contents |
|---|---|
| `$0D00` | Table that sets the scroll offset each frame. `$2177` reads it and writes the result into the operand at `$21C2`. |
| `$1000` | Music by Chris. `JMP $1048` is init and `JMP $1021` is play. The text "MUSIC BY CHRIS/XENTRIX" is in the header. |
| `$2000` | Effect init: calls CINT, initialises the music, sets VIC bank 1 (`$DD00=$96`), points NMI at `$9000`, IRQ at `$2033`. |
| `$2033` | Raster IRQ that runs the FLI. `$D011=$38` (bitmap mode), `$D016=$C8`. |
| `$2055–$20B9` | FLI kernel, cycle-exact: `$D018` is loaded from the table at `$2B00`, and `INC $D011` forces a badline on each line. NOP/BIT instructions pad the timing. |
| `$20E6` | Column updater. Copies 40 bytes from the colour data at `$293C+` (indexed via `$280A`) to offsets 0–39 of 14 screen pages (`$4400`–`$7800`). It then modifies its own operands. |
| `$21C1` | Rebuilds the `$D018` table at `$2B00` from the wave table at `$2C00`. |
| `$222C` | Sets the next raster line and IRQ vector, then exits through `JMP $EA81`. |
| `$2800–$2C00+` | Data: column indices, colour data, `$D018` table, wave table. |
| `$3200–$34FF` | Intro screen text (screen codes). |
| `$3500` | Intro: copies the text to `$0400`, runs the raster colour bars at `$3580`/`$35C0`, waits for SPACE (`$DC01==$EF`), then `JMP $2000`. |
| `$3620` | Entry point after decompression. Resets the self-modified counters and jumps to `$3500`. |
| `$4000–$7FFF` | VIC bank 1: the FLI screen pages. |
| `$9000` | NMI (RESTORE) handler that exits the part. |

The part depends on the KERNAL being mapped in (`$FF81`, `$E518`, `$FD02`, `$EA81`, IRQ through `$0314`). A standalone build needs to keep that, along with whatever state the original loader leaves behind.

## Working rules

- **Timing is sacred.** Don't change instruction choice, order, length or placement in `$2033–$20BB` (or anything branched to from there) until an unchanged rebuild has been checked against the original in a cycle-exact PAL emulator. NOP/`BIT $EA`/`BIT $EAEA` sequences are cycle padding, not dead code.
- The code modifies itself heavily (`$2144–$21BD`, `$217B`, `$2183`, `$3548`/`$3568`). Operand bytes in the dump are a snapshot taken at one moment, not necessarily their initial values. `$3620` resets some of them.
- Say plainly what has been verified and what is inferred. It has been checked in x64sc (PAL) only, not on real hardware or NTSC.
- The intro polls `$DC01` directly, so `-keybuf` can't press SPACE. Use the monitor (`r pc = 3559`), as `tools/capture.py` does.
- Homebrew VICE aborts with "No GSettings schemas" unless `XDG_DATA_DIRS=/opt/homebrew/share` is set. The Makefile exports it.
- Use C64/6502 conventions: `$` hex addresses and the PAL timing model (63 cycles per line).
- Keep generated helper files (venvs, scratch scripts) out of git; `.gitignore` already covers `.venv/` and `__pycache__/`. If a recovery script turns out to be worth keeping, commit it under a new `tools/` directory and document it here.

## Tooling

Installed with Homebrew (`brew install vice acme tass64`):

- **VICE 3.10.** Use `x64sc` for a cycle-exact C64 (PAL by default) and its monitor for breakpoints and memory dumps. `c1541` reads D64 images. `petcat` converts BASIC to and from text.
  - List the disk: `c1541 -attach original/pardy3.d64 -list`. Files on it: `pardy demo 3/xen`, `10.from.....case`, `11.chris..flimbo` (this part), `12.mad..betrayer`.
  - Extract this part: `c1541 -attach original/pardy3.d64 -read "11.chris..flimbo" out.prg`. The result is byte-identical to `original/11-chris-flimbo.prg`.
  - Run it: `x64sc -autostart original/pardy3.d64`. For a scripted capture, add `-moncommands <file>`, `-exitscreenshot <png>` or `-limitcycles <n>`.
- **Assemblers.** `64tass` 1.60 is the project assembler, used by the Makefile. `acme` 0.97 is also installed.
- **py65** is installed in `.venv/` (gitignored); run it as `.venv/bin/python`. Earlier recovery used it to run the depacker. That script and the hand-written D64 parser aren't in the repo.
- REA's binary analysis tools don't support D64 or 6510 targets, so work directly from the files.

## Next steps (from README)

1. ~~Run the part in a PAL emulator and capture the waterfall.~~ Done.
2. ~~Build a standalone PRG.~~ Done, as a binary include of the dump.
3. Turn `disassembly.txt` into real source code, covering the data tables and the `$9000` handler. Replace the `.binary` includes piece by piece, and check after each step that `build/waterfall.prg` stays byte-identical.
