
RSYNC_CONF_OPTS = --with-included-popt=no

include $(sort $(wildcard $(BR2_EXTERNAL_SALI)/package/*/*.mk))
