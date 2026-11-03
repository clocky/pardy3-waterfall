BUILD   := build
PRG     := $(BUILD)/waterfall.prg
ORIG    := original/11-chris-flimbo.prg

# Homebrew VICE needs this to find its GSettings schemas
export XDG_DATA_DIRS := /opt/homebrew/share

.PHONY: all run run-original capture clean

all: $(PRG)

$(PRG): src/standalone.s recovered/unpacked-analysis-ram.bin | $(BUILD)
	64tass --cbm-prg -a -Wall -o $@ -L $(BUILD)/waterfall.lst src/standalone.s

$(BUILD):
	mkdir -p $@

run: $(PRG)
	x64sc -pal -autostartprgmode 1 -autostart $(PRG)

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
