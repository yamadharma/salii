# A simple todo list
 * logging
    * currently their is a "logic" with logging, but don't known anymore which logic. So needs to
      be redesigned (especially the different log-levels)
 * STATIC ip when starting SALI
    * missing some required options (ie default gw)
    * STATIC ip without knowing the interface name
 * Added support for UEFI
    * added some basic support UEFI, but need to be refined
    * Chroot mount efivars
 * Add support for LVM|MDADM with disks_part function
    * For now you will need to use the lvm and mdadm commands in the partition function in the master_script
 * run_script function assumes scripts/tools are executable, this must be more robust
 * chroot environment for shell debugging and running post-installation scripts