# CLAUDE.md

Recovery and preservation of a Commodore 64 demo part: the 40x24 FLI "waterfall" from **Pardy 3** (Xentrix, 1990). Code and graphics by Flimbo/Xentrix, music by Chris/Xentrix. The repo owner is Flimbo, the original author, so they can answer questions about intent, but details from 1990 may have faded. This is reverse-engineering work, not a modern codebase.

## Build and run

```sh
make                # assemble src/waterfall.s -> build/waterfall.prg (+ build/waterfall.lst)
make verify         # REQUIRED after any source edit: output must match the reference image byte for byte
make run            # boot it in x64sc (PAL). Press SPACE at the intro; RESTORE exits (see memory map)
make debug          # as run, with source labels loaded into the VICE monitor (Cmd+Esc)
make run-original   # boot the packed original (loads to $0801 via -basicload)
make capture        # headless: skips the SPACE wait through the remote monitor, writes build/capture/fli{1,2}.png
make tools          # fetch TMPx into .tools/ (checksummed)
make vscode         # package and install the in-repo TMPx syntax extension
make clean
```

The source is in **Turbo Macro Pro / TMPx syntax**, the Turbo Assembler family Flimbo used in 1990. Two assemblers build it:

- **TMPx 1.1.0** (Style, https://turbo.style64.org/) is the authentic one and the default when `.tools/tmpx` exists. There's no arm64 build, so on Apple Silicon it runs under Rosetta 2. Apple is phasing Rosetta out after macOS 27, so don't depend on TMPx alone. Known bug: with `-q` it exits 0 but writes **no output file**, so never pass `-q`.
- **64tass 1.60** in Turbo Assembler mode (`-C -T -a -i`) runs natively and is used when TMPx is missing. You can force it with `make ASM=64tass`.

`make verify` assembles the source with every assembler available and `cmp`s the result against `build/reference.prg`. That reference comes from `tools/reference.s`: a 64tass `.binary` copy of the depacked dump (`$0D00–$44FF`, `$9000–$90FF`) behind the same BASIC stub. **Verified 2026-11-03:** TMPx and 64tass output are both byte-identical to the reference. The reference itself runs the waterfall in x64sc, and its screenshots matched the packed original. A byte-identical build is the proof of correctness. Screenshots from `make capture` are taken by wall-clock time, so they land on different frames from run to run and aren't comparable by hash.

## Layout

- `original/`: the untouched source material. **Never modify these files.**
  - `pardy3.d64`: the full disk image. It's **gitignored** (`*.d64`) and not committed. It's freely available, so if it's missing locally, download it from CSDb (link in the README; release 30608) and check SHA-256 `cdd2305f2bfca195d565855c5840f429409c07a76bd7c7d294b990133ac40aa8`.
  - `11-chris-flimbo.prg`: the disk file `11.CHRIS..FLIMBO`, extracted by following its sector chain. Its PRG header says load address `$2800`, with a BASIC stub `SYS 2061` (`$080D`). It's a packed program meant to run after relocation to `$0801`.
- `recovered/`: analysis output.
  - `unpacked-analysis-ram.bin`: a 64 KiB flat dump of C64 RAM, taken after running the depacker in py65. Execution stopped at `$044A`, just before `CLI` / `JMP $3620`. File offset = C64 address. Some leftover packed bytes are still in it. It's **not** a VICE snapshot and **not** a runnable PRG.
  - `disassembly.txt`: an annotated listing with addresses of the display routine and the intro. It's partial and can't be reassembled as it stands.
  - `credits.txt`: the intro screen text, decoded from `$3200` exactly as it appears.
- `src/`: the TMP/TMPx source, hand-maintained from here on.
  - `waterfall.s`: the top level. It has the BASIC stub (`SYS 2061`) that reproduces the depacker's hand-off (`$01=$37`, `CLI`, `JMP entry`), then `.include`s the rest in address order.
  - `tables.s` `$0D00`, `music.s` `$1000` (Chris's player, still `.byte`), `effect.s` `$2000` + tables `$2800`, `intro.s` `$3200`, `vicbank.s` `$4000`, `restore.s` `$9000`.
  - Code regions are mnemonics with labels. Self-modified operands are written as `label+1` and marked `; self-modified`. Everything else is `.byte` data, 8 per line, with long zero runs skipped via `*=`.
- `tools/dump2tmp.py`: the **one-shot** generator that produced `src/*.s` from the dump. It refuses to overwrite without `--force`. Don't re-run it over hand-edited sources.
- `tools/reference.s`: the known-good image for `make verify`. Never edit it.
- `tools/get-tmpx.sh`: downloads TMPx and checks it against a pinned SHA-256.
- `tools/capture.py`: drives the VICE text remote monitor on `127.0.0.1:6510` to skip the SPACE wait and take screenshots. It uses only the standard library.
- `tools/vscode-tmpx/`: a TextMate grammar extension, language id `tmpx`. It doesn't claim `.s` globally; `.vscode/settings.json` maps `*.s` to it for this workspace only.
- `.vscode/`: build/verify/run tasks, with problem matchers for both assemblers' error formats, plus editor settings (rulers at columns 9, 32 and 40).
- `build/`, `.tools/`, `.venv/`: generated, gitignored.
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
| `$2238–$2289` | Unreferenced fragments of earlier IRQ-exit code, probably left over from editing in Turbo Assembler on the C64. Kept as `.byte`. |
| `$9000` | NMI (RESTORE) handler. It resets I/O, copies the stub at `$9047` to `$0100`, and runs it with `$01=$34`. The stub copies RAM `$A000–$FEFF` to `$0801+`, then BASIC CLR (`$A65E`), reset text pointer (`$A68E`) and RUN loop (`$A7AE`). That restores and re-runs the demo's BASIC menu, which the loader parked under ROM. **In the standalone build nothing is parked there, so RESTORE runs garbage.** |

The part depends on the KERNAL being mapped in (`$FF81`, `$E518`, `$FD02`, `$EA81`, IRQ through `$0314`). A standalone build needs to keep that, along with whatever state the original loader leaves behind.

## Working rules

- **Timing is sacred.** Don't change instruction choice, order, length or placement in `$2033–$20BB` (or anything branched to from there) until an unchanged rebuild has been checked against the original in a cycle-exact PAL emulator. NOP/`BIT $EA`/`BIT $EAEA` sequences are cycle padding, not dead code.
- The code modifies itself heavily (`$2144–$21BD`, `$217B`, `$2183`, `$3548`/`$3568`). The dump was taken just before `JMP $3620`, before any part code had run, so its operand bytes are the values as loaded. `$3620` resets the intro's counters.
- **Source dialect:** stay in the portable Turbo Assembler subset that both TMPx and 64tass `-T` accept, and that Turbo Macro Pro on a real C64 could mostly handle:
  - Labels: lowercase, at most 15 characters, starting in column 1, no colon.
  - Mnemonics: lowercase, at column 10.
  - Comments: `;`.
  - Directives: `*=`, `.byte`/`.word`/`.text`, `.include` only. No `.binary`, `.screen`, `.repeat`, `.logical` or 64tass-only syntax.
  - Expressions: there's no operator precedence (use parentheses). `.` is OR, `:` is EOR, and `!` forces 16-bit addressing (`lda !$02`).
  - Lines may go past TMP's 40-column limit only for comments.
- Every source edit must keep `make verify` passing until a deliberate behaviour change is agreed. Typical refactors: naming labels, turning immediates into `#<label`/`#>label`, and disassembling `.byte` regions into code.
- Say plainly what has been verified and what is inferred. It has been checked in x64sc (PAL) only, not on real hardware or NTSC.
- The intro polls `$DC01` directly, so `-keybuf` can't press SPACE. Use the monitor (`r pc = 3559`), as `tools/capture.py` does.
- **Measured timing** (x64sc PAL, 2026-11-03, monitor breakpoints; the cycle is the instruction's start cycle within the raster line as VICE reports it):
  - The IRQ enters `$2033` at line 46, cycle 38/39/40, which is 3 cycles of jitter. It isn't stabilised: it comes through the KERNAL `$0314` path from `jmp idle`, and that jitter carries straight into the FLI loop (first `sta $d018` at line 48, cycle 9–11).
  - Inside one frame each `$d011` write site lands on a fixed cycle (`$2069`:5, `$2073`:1, `$207e`/`$208a`:62 of the previous line, `$2098`:1, `$20a6`:3, `$20b3`:4). The exception is row 0, where `$2069` runs at cycle **14** (line 49).
  - The FLI loop ends at line 239. `colupd` runs from line 243 to line 21 of the next frame, and the IRQ ends at line 31–33. That's 13–15 lines of headroom before the next IRQ, and the screen writes all happen in the border.
  - The first ~4 IRQs after `init` land at random lines (startup transient: stale `$d019`, `$d012` not yet set). After that it locks.
- Homebrew VICE aborts with "No GSettings schemas" unless `XDG_DATA_DIRS=/opt/homebrew/share` is set. The Makefile exports it.
- Use C64/6502 conventions: `$` hex addresses and the PAL timing model (63 cycles per line).
- Keep generated helper files (venvs, scratch scripts) out of git; `.gitignore` already covers `.venv/` and `__pycache__/`. If a recovery script turns out to be worth keeping, commit it under a new `tools/` directory and document it here.

## Tooling

Installed with Homebrew (`brew install vice acme tass64`):

- **VICE 3.10.** Use `x64sc` for a cycle-exact C64 (PAL by default) and its monitor for breakpoints and memory dumps. `c1541` reads D64 images. `petcat` converts BASIC to and from text.
  - List the disk: `c1541 -attach original/pardy3.d64 -list`. Files on it: `pardy demo 3/xen`, `10.from.....case`, `11.chris..flimbo` (this part), `12.mad..betrayer`.
  - Extract this part: `c1541 -attach original/pardy3.d64 -read "11.chris..flimbo" out.prg`. The result is byte-identical to `original/11-chris-flimbo.prg`.
  - Run it: `x64sc -autostart original/pardy3.d64`. For a scripted capture, add `-moncommands <file>`, `-exitscreenshot <png>` or `-limitcycles <n>`.
- **Assemblers.** TMPx 1.1.0 lives in `.tools/tmpx` (`make tools`); Homebrew provides `64tass` 1.60 and `acme` 0.97 (unused). Error formats, for the VS Code matchers: TMPx gives `effect.s(105) : error 32: …` (path relative to `src/`), 64tass gives `src/effect.s:105:14: error: …`.
- **VS Code**: `code` is on PATH. `make vscode` packages the grammar with `npx @vscode/vsce` and installs it.
- **py65** is installed in `.venv/` (gitignored); run it as `.venv/bin/python`. Earlier recovery used it to run the depacker. That script and the hand-written D64 parser aren't in the repo.
- REA's binary analysis tools don't support D64 or 6510 targets, so work directly from the files.

## Next steps

1. ~~Run the part in a PAL emulator and capture the waterfall.~~ Done.
2. ~~Build a standalone PRG.~~ Done.
3. ~~Migrate to Turbo Assembler source.~~ Done: TMPx and 64tass `-T`, byte-identical.
4. Name the remaining `lxxxx` labels and the hardware registers, and work out what the `$0D00–$0FFF`, `$2800–$31FF` and `$4000–$44FF` data actually are. Check `make verify` after each step.
5. Disassemble Chris's player in `music.s` (code and data are mixed in it).
6. Optionally make RESTORE in the standalone build do something sensible, such as a soft reset. That's a behaviour change, so the reference would need updating on purpose.
