################################################################################
#
# aria2
#
################################################################################

ARIA2_VERSION = 1.20.0
ARIA2_SOURCE = aria2-$(ARIA2_VERSION).tar.xz
ARIA2_SITE = http://ftp.surfsara.nl/pub/sali/sources
ARIA2_DEPENDENCIES = zlib openssl libxml2
ARIA2_LICENSE = GPLv2
ARIA2_LICENSE_FILES = COPYING

$(eval $(autotools-package))
