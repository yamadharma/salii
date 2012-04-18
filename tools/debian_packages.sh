#!/bin/sh

PACKAGES="libusb-1.0-0-dev gperf pciutils libxml2-dev expat pkg-config libssl-dev libglib2.0-dev libacl1-dev gettext docbook-to-man flex libreadline-dev uuid-dev libblkid-dev libssl-dev zlib1g-dev gobject-introspection libreadline-dev libudev-dev libexpat1-dev"


aptitude update
aptitude install ${PACKAGES}
