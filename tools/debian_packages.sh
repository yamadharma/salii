#!/bin/sh

PACKAGES="libusb-1.0-0-dev gperf pciutils libxml2-dev expat pkg-config libssl-dev libglib2.0-dev libacl1-dev gettext docbook-to-man flex libreadline5-dev uuid-dev libblkid-dev"



apt-get install --yes ${PACKAGES}
