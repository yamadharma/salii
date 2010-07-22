#!/bin/sh

echo "Simple bootstrap for debian\n\n"

apt-get install flex rsync uuid-dev ncurses-dev libreadline-dev gperf \
	pkg-config build-essential libglib2.0-dev libusb-dev gobject-introspection \
	libblkid-dev libudev-dev libdevmapper-dev libssl-dev libacl1-dev

apt-get build-dep udev
