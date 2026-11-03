#!/usr/bin/env python3
"""One-shot generator: recovered RAM dump -> Turbo Macro Pro / TMPx source.

Writes src/*.s from recovered/unpacked-analysis-ram.bin. Known code regions
become labelled mnemonics; everything else becomes .byte data. The output
is meant to be hand-edited afterwards, so DO NOT re-run this over edited
sources (it refuses to overwrite unless --force is given).

Syntax is kept to the portable Turbo Assembler subset: lowercase labels of
at most 15 chars, no colons, `;` comments, `*=` and .byte/.word/.text and
.include only, no operator precedence reliance.

Usage: python3 -I tools/dump2tmp.py [--force] <repo-root>
Needs py65 only for its opcode table (run with .venv/bin/python).
"""
import os
import sys

from py65.devices.mpu6502 import MPU

LEN = {"imp": 1, "acc": 1, "imm": 2, "zpg": 2, "zpx": 2, "zpy": 2,
       "inx": 2, "iny": 2, "rel": 2, "abs": 3, "abx": 3, "aby": 3, "ind": 3}

# (start, end-exclusive, kind, file, comment)
REGIONS = [
    (0x0D00, 0x1000, "data", "tables.s", "tables below the music; $0d00 drives the wave scroll"),
    (0x1000, 0x18C8, "data", "music.s", "music by chris/xentrix: jmp init / jmp play header"),
    (0x2000, 0x2238, "code", "effect.s", "fli waterfall: init, raster irq, updaters"),
    (0x2238, 0x228A, "data", "effect.s", "unreferenced remnants of earlier irq-exit versions"),
    (0x2800, 0x3200, "data", "effect.s", "effect tables"),
    (0x3200, 0x3500, "text", "intro.s", "intro screen text (screen codes, 40 per row)"),
    (0x3500, 0x357C, "code", "intro.s", "intro: show text, colour bars, wait for space"),
    (0x357C, 0x3620, "data", "intro.s", "intro colour bar tables"),
    (0x3620, 0x362B, "code", "intro.s", "entry after depacking"),
    (0x4000, 0x4500, "data", "vicbank.s", "vic bank 1 data (role not yet identified)"),
    (0x9000, 0x9047, "code", "restore.s", "nmi/restore: back to the demo menu"),
    (0x9047, 0x9084, "code", "restore.s", "copied to $0100 and run there (position independent)"),
    (0x9084, 0x9100, "data", "restore.s", "padding"),
]
LAST_END = 0x9100

NAMES = {
    0x0D00: "scrolltab",
    0x1000: "music",
    0x2000: "init", 0x2030: "idle", 0x2033: "irq", 0x2055: "fliloop",
    0x20E6: "colupd", 0x2187: "colreset", 0x21C1: "mkd018", 0x222C: "nextirq",
    0x280A: "colidx", 0x293C: "colours", 0x2B00: "d018tab", 0x2C00: "wavetab",
    0x3200: "introtext", 0x3500: "intro", 0x3580: "bars1", 0x35C0: "bars2",
    0x3620: "entry",
    0x9000: "nmi", 0x9047: "bootstub",
}
# named data tables: label -> (start, end-exclusive) for symbolic operands
TABLES = {
    "scrolltab": (0x0D00, 0x0E00), "colidx": (0x280A, 0x2832),
    "colours": (0x293C, 0x2B00), "d018tab": (0x2B00, 0x2C00),
    "wavetab": (0x2C00, 0x2E00), "introtext": (0x3200, 0x3500),
    "bars1": (0x3580, 0x35C0), "bars2": (0x35C0, 0x3600),
}
EQUATES = {0x1048: "musinit", 0x1021: "musplay"}
CALLS = {
    0xFF81: "kernal cint", 0xE518: "init screen/keyboard",
    0xFD02: "check cart signature", 0xFDA3: "kernal ioinit",
    0xE5A0: "init vic", 0xE544: "clear screen", 0xEA81: "irq exit",
    0xA65E: "basic clr", 0xA68E: "basic reset txtptr", 0xA7AE: "basic run loop",
}
SELFMOD_NOTE = "self-modified"
SCREEN = "@abcdefghijklmnopqrstuvwxyz[\\]^_ !\"#$%&'()*+,-./0123456789:;<=>?"


def main():
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv
    root = args[0] if args else "."
    ram = open(os.path.join(root, "recovered/unpacked-analysis-ram.bin"), "rb").read()
    ops = MPU().disassemble

    # pass 1: instruction starts and targets
    starts = set()
    for lo, hi, kind, *_ in REGIONS:
        if kind != "code":
            continue
        a = lo
        while a < hi:
            starts.add(a)
            a += LEN[ops[ram[a]][1]]
    labels = dict(NAMES)
    selfmod = set()
    code_ranges = [(lo, hi) for lo, hi, k, *_ in REGIONS if k == "code"]

    def in_code(t):
        return any(lo <= t < hi for lo, hi in code_ranges)

    def insn_start(t):
        while t not in starts:
            t -= 1
        return t

    for a in sorted(starts):
        mnem, mode = ops[ram[a]]
        if mode == "rel":
            off = ram[a + 1]
            t = a + 2 + (off - 256 if off > 127 else off)
            labels.setdefault(t, f"l{t:04x}")
        elif LEN[mode] == 3:
            t = ram[a + 1] | ram[a + 2] << 8
            if in_code(t):
                s = insn_start(t)
                labels.setdefault(s, f"l{s:04x}")
                if t != s and mnem in ("STA", "STX", "STY", "INC", "DEC"):
                    selfmod.add(s)

    def sym(t, mnem):
        if t in EQUATES:
            return EQUATES[t]
        if in_code(t):
            s = insn_start(t)
            return labels[s] if s == t else f"{labels[s]}+{t - s}"
        for name, (lo, hi) in TABLES.items():
            if lo <= t < hi:
                return name if t == lo else f"{name}+${t - lo:02x}"
        return f"${t:04x}"

    files = {}

    def out(fname, line=""):
        files.setdefault(fname, []).append(line)

    def put(fname, label, body, comment=None):
        line = f"{label + chr(32):<9}{body}" if label else f"         {body}"
        if comment:
            line = f"{line:<32}; {comment}"
        out(fname, line.rstrip())

    for lo, hi, kind, fname, comment in REGIONS:
        out(fname, "")
        out(fname, f"; ${lo:04x}-${hi - 1:04x}: {comment}")
        out(fname, "")
        out(fname, f"         *= ${lo:04x}")
        if kind == "code":
            a = lo
            while a < hi:
                mnem, mode = ops[ram[a]]
                n = LEN[mode]
                m = mnem.lower()
                b1 = ram[a + 1] if n > 1 else 0
                w = b1 | (ram[a + 2] << 8 if n > 2 else 0)
                if mode in ("imp", "acc"):
                    opnd = ""
                elif mode == "imm":
                    opnd = f"#${b1:02x}"
                elif mode in ("zpg", "zpx", "zpy"):
                    opnd = f"${b1:02x}" + {"zpg": "", "zpx": ",x", "zpy": ",y"}[mode]
                elif mode == "inx":
                    opnd = f"(${b1:02x},x)"
                elif mode == "iny":
                    opnd = f"(${b1:02x}),y"
                elif mode == "rel":
                    t = a + 2 + (b1 - 256 if b1 > 127 else b1)
                    opnd = labels[t]
                elif mode == "ind":
                    opnd = f"({sym(w, m)})"
                else:
                    opnd = sym(w, m) + {"abs": "", "abx": ",x", "aby": ",y"}[mode]
                note = None
                if mode in ("abs",) and m in ("jsr", "jmp") and w in CALLS:
                    note = CALLS[w]
                if a in selfmod:
                    note = SELFMOD_NOTE if not note else f"{note}; {SELFMOD_NOTE}"
                if a in labels and a != lo and labels[a] in NAMES.values():
                    out(fname, "")
                put(fname, labels.get(a, ""), f"{m} {opnd}".rstrip(), note)
                a += n
        else:
            label = labels.get(lo, "")
            a = lo
            while a < hi:
                if kind == "text" and (a - lo) % 40 == 0:
                    row = ram[a:a + 40]
                    txt = "".join(SCREEN[c] if c < 64 else "?" for c in row).rstrip()
                    out(fname, f"; {txt}" if txt else ";")
                # break lines at the next label so table names land exactly
                marks = [t for t in labels if a < t < hi]
                marks += [t for t, _ in TABLES.values() if a < t < hi]
                nxt = min(marks + [hi])
                # skip long zero runs (not at the very end of the image)
                z = a
                while z < nxt and ram[z] == 0:
                    z += 1
                if z - a >= 32 and not (z == hi == LAST_END) and kind != "text":
                    if z < hi:
                        out(fname, f"         *= ${z:04x}")
                    a = z
                    label = ""
                    continue
                n = min(8, nxt - a)
                if kind == "text":
                    n = min(n, 40 - (a - lo) % 40)
                chunk = ram[a:a + n]
                lab = labels.get(a, label if a == lo else "")
                for name, (tlo, _) in TABLES.items():
                    if tlo == a:
                        lab = name
                put(fname, lab, ".byte " + ",".join(f"${b:02x}" for b in chunk))
                a += n
                label = ""

    # equates for the music entry points live with the music
    out("music.s", "")
    out("music.s", "musinit  = $1048")
    out("music.s", "musplay  = $1021")

    srcdir = os.path.join(root, "src")
    os.makedirs(srcdir, exist_ok=True)
    header = {
        "tables.s": "data tables",
        "music.s": "music (chris/xentrix) as data; not disassembled",
        "effect.s": "the 40x24 fli waterfall (flimbo/xentrix)",
        "intro.s": "credits screen and post-depack entry",
        "vicbank.s": "vic bank 1 ($4000-$7fff) initial contents",
        "restore.s": "restore key handler",
    }
    for fname, lines in files.items():
        path = os.path.join(srcdir, fname)
        if os.path.exists(path) and not force:
            sys.exit(f"refusing to overwrite {path} (use --force)")
        with open(path, "w") as f:
            f.write(f"; pardy 3 fli waterfall - {header[fname]}\n")
            f.write("; generated by tools/dump2tmp.py, now hand-maintained\n")
            f.write("\n".join(lines) + "\n")
    print("wrote", ", ".join(sorted(files)))


if __name__ == "__main__":
    main()
