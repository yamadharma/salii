################################################################################
#
# diskscrub
#
################################################################################

SCRUB_VERSION = 2.6.1
SCRUB_SOURCE = scrub-$(SCRUB_VERSION).tar.gz
SCRUB_SITE = http://ftp.surfsara.nl/pub/sali/sources
SCRUB_LICENSE = GPLv2
SCRUB_LICENSE_FILES = COPYING

$(eval $(autotools-package))
