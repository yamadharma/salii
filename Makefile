BR2_VERSION=2023.08.2
SALII_DIR=$(shell pwd)
BUILD_DIR=$(SALII_DIR)/../build

all: prepare

prepare:
	mkdir -p $(BUILD_DIR)
	[[ -f "$(BUILD_DIR)/buildroot-$(BR2_VERSION).tar.xz" ]] || wget https://buildroot.org/downloads/buildroot-$(BR2_VERSION).tar.xz -O "$(BUILD_DIR)/buildroot-$(BR2_VERSION).tar.xz"
	tar xJvf "$(BUILD_DIR)/buildroot-$(BR2_VERSION).tar.xz" -C "$(BUILD_DIR)"
	(cd "$(BUILD_DIR)/buildroot-$(BR2_VERSION)"; make BR2_EXTERNAL=$(SALII_DIR)/buildroot salii_x86_64_defconfig)
	touch prepare

compile: prepare
	cd $(BUILD_DIR)/buildroot-$(BR2_VERSION)
	make

