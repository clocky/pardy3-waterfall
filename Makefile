BUILD   := build
PRG     := $(BUILD)/waterfall.prg
REF     := $(BUILD)/reference.prg
ORIG    := original/11-chris-flimbo.prg
SRC     := src/waterfall.s $(wildcard src/*.s)

# Assembler: tmpx (Style's Turbo Macro Pro cross assembler, the authentic
# choice; `make tools` fetches it) or 64tass in Turbo Assembler mode.
TMPX    ?= $(firstword $(wildcard .tools/tmpx) $(shell command -v tmpx 2>/dev/null))
ASM     ?= $(if $(TMPX),tmpx,64tass)

# Homebrew VICE needs this to find its GSettings schemas
export XDG_DATA_DIRS := /opt/homebrew/share

.PHONY: all tools vscode verify run debug run-original capture clean

all: $(PRG)

$(BUILD):
	mkdir -p $@

ifeq ($(ASM),tmpx)
$(PRG): $(SRC) | $(BUILD)
	cd src && $(abspath $(TMPX)) -i waterfall.s -o ../$@ -l ../$(BUILD)/waterfall.lst
else
$(PRG): $(SRC) | $(BUILD)
	64tass -C -T -a -i -Wall -I src -o $@ -L $(BUILD)/waterfall.lst src/waterfall.s
endif

# Same source through the other assembler, for cross-checking
$(BUILD)/waterfall-64tass.prg: $(SRC) | $(BUILD)
	64tass -C -T -a -i -Wall -I src -o $@ src/waterfall.s
$(BUILD)/waterfall-tmpx.prg: $(SRC) | $(BUILD)
	cd src && $(abspath $(TMPX)) -i waterfall.s -o ../$@ >/dev/null  # not -q: TMPx 1.1.0 then writes nothing

# Byte-for-byte copy of the depacked RAM: the known-good image
$(REF): tools/reference.s recovered/unpacked-analysis-ram.bin | $(BUILD)
	64tass --cbm-prg -a -Wall -o $@ tools/reference.s

tools:
	tools/get-tmpx.sh

# Package and install the in-repo TMPx syntax extension into VS Code
VSIX := $(BUILD)/tmpx-syntax.vsix
vscode: | $(BUILD)
	cd tools/vscode-tmpx && npx --yes @vscode/vsce package --skip-license -o $(abspath $(VSIX))
	code --install-extension $(VSIX) --force

# Source must assemble to exactly the reference, with every available assembler
verify: $(REF) $(BUILD)/waterfall-64tass.prg $(if $(TMPX),$(BUILD)/waterfall-tmpx.prg)
	cmp $(REF) $(BUILD)/waterfall-64tass.prg && echo "64tass: identical to reference"
	$(if $(TMPX),cmp $(REF) $(BUILD)/waterfall-tmpx.prg && echo "tmpx:   identical to reference",@echo "tmpx:   not installed (make tools), skipped")

run: $(PRG)
	x64sc -pal -autostartprgmode 1 -autostart $(PRG)

# Same, with source labels loaded into the monitor (Cmd+Esc opens it)
$(BUILD)/waterfall.vs: $(SRC) | $(BUILD)
	64tass -C -T -a -i -I src --vice-labels -l $@ -o /dev/null src/waterfall.s >/dev/null
debug: $(PRG) $(BUILD)/waterfall.vs
	x64sc -pal -autostartprgmode 1 -autostart $(PRG) -moncommands $(BUILD)/waterfall.vs

# The packed original must load to BASIC start ($0801), not its header address ($2800)
run-original:
	x64sc -pal -basicload -autostartprgmode 1 -autostart $(ORIG)

# Headless check: boot the build, skip the SPACE wait via the remote monitor,
# and write screenshots to build/capture/
capture: $(PRG)
	mkdir -p $(BUILD)/capture
	x64sc -pal -autostartprgmode 1 -autostart $(PRG) -sounddev dummy \
	  -remotemonitor -remotemonitoraddress ip4://127.0.0.1:6510 >$(BUILD)/capture/vice.log 2>&1 & \
	  python3 -I tools/capture.py $(BUILD)/capture

clean:
	rm -rf $(BUILD)
