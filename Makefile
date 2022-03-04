BR2_VERSION=2021.02.1
SALII_DIR=$(shell pwd)
BUILD_DIR=$(SALII_DIR)/../build

prepare:
	mkdir -p $(BUILD_DIR)
	[[ -f "$(BUILD_DIR)/buildroot-$(BR2_VERSION).tar.bz2" ]] || wget https://buildroot.org/downloads/buildroot-$(BR2_VERSION).tar.bz2 -O "$(BUILD_DIR)/buildroot-$(BR2_VERSION).tar.bz2"
	tar xjvf "$(BUILD_DIR)/buildroot-$(BR2_VERSION).tar.bz2" -C "$(BUILD_DIR)"
	(cd "$(BUILD_DIR)/buildroot-$(BR2_VERSION)"; make BR2_EXTERNAL=$(SALII_DIR)/buildroot salii_x86_64_defconfig)

compile: prepare
	cd $(BUILD_DIR)/buildroot-$(BR2_VERSION)
	make

