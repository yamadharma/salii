################################################################################
#
# lsscsi
#
################################################################################

LSSCSI_VERSION = 0.28
LSSCSI_SOURCE = lsscsi-$(LSSCSI_VERSION).tgz
LSSCSI_SITE = http://ftp.surfsara.nl/pub/sali/sources
LSSCSI_LICENSE = GPLv2
LSSCSI_LICENSE_FILES = COPYING

$(eval $(autotools-package))
