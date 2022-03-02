# SALI project
This repository contains the 2.0.0 client and server code. Please note that this repository is a work in progress.

Please also check our page on our own website for bugtracking:
 - https://oss.trac.surfsara.nl/sali

## Development requirements
Only Linux is supported as OS for running the SALI tools

Requirements:
 * QEMU (client testing)
 * wget
 * Python 3 (server tools)

Recommendations:
 * Virtualenv and virtualenvwrapper

## File stucture
 * archive      : Contains the old-new Python code. Only used for reference
 * buildroot    : Contains the shell script code for the embbedded Linux environment
 * examples     : Contains examples configuration files for the SALI tools and buildroot env
 * sali         : Contains the SALI tools
 * CHANGELOG    : What has changed since version 1.0.0
 * README.md    : This file
 * sali-cli     : The main Python script for SALI tools
 * sali-test-client: A simple shell script for testing the buildroot env in qemu

## Client

### Building the buildroot for SALI
 1. Download buildroot and unpack it separate from this repository. In this example we will take `/tmp`
 2. `cd /tmp && wget https://buildroot.org/downloads/buildroot-2021.02.1.tar.gz`
 3. Unpack buildroot: `tar xvf buildroot-2021.02.1.tar.gz` and change directory to `cd buildroot-2021.02.1`
 4. Configure buildroot with the `sali_x86_64_defconfig` via the `BR2_EXTERNAL` method
    * `make BR2_EXTERNAL=/home/dennis/sali/buildroot sali_x86_64_defconfig`
 5. Now run `make`

After building the images are available in the `output/images` directory in the buildroot dir.

### Updating buildroot/linux/busybox config
We assume you have already downloaded, extract en configured the buildroot from the building instructions. Buildroot will update the corresnpoding files in the sali repository, so don't forget to commit them.

#### Updating buildroot configuration
 1. `make menuconfig`
 2. After modifying options, run `make savedefconfig`

#### Updating Linux configuration
 1. `make linux-menuconfig`
 2. After modifying options, run `make linux-update-defconfig`

 #### Updating Busybox configuration
 1. `make busybox-menuconfig`
 2. After modifying options, run `make busybox-update-config`

#### Running tests
 * Please not script only works on Linux
 * First start the server `./sali-test-client server`
 * Prepare the network (assumes you have a bridge device with name bridge0), `./sali-test-client network-prepare`
 * Run `./sali-test-client make-copy-run` to make buildroor, copy linux/initrd, start a virtual machine. (separate terminal)

#### Client file structure

These files are located in the rootfs_overlay in `buildroot/board/sali/common/rootfs_overlay`

```
/etc/sali
    - console_file              # The motd when we just open the console
    - default_variables         # new file which contains the default values for variables
    - error_file                # motd when installation fails
    - error_startup_file        # motd when startup failes
/etc/sali_version               # Just like Debian but then for SALI
/etc/init.d
    - functions                 # the main file to source for using the wrapper commands
/etc/startup.d
    - S1_network                # configure and start network
    - S2_preparation            # fetch master_script and start the monitoring
    - S3_sshd                   # start sshd (if needed)
/etc/installer.d
    - S1_prepare                # scrub the disk (when asked for) and fetch the post/pre installation scripts
    - S2_pre_installation       # run the pre-installation scripts
    - S3_partition              # partition the disks
    - S4_imaging                # fetch/extract image
    - S5_post_installation      # run the post-installation scripts
    - S6_finalize               # umount disks
/lib/sali/functions             # Files are show in the orde they are sourced in the functions file
    - general.sh                # Contains functions that are used in all other files
    - network.sh                # Network related functions
    - ssh.sh                    # Configure and start ssh functions
    - initialize.sh             # Intialize function for the embedded SALI environment
    - scripts.sh                # Fetch and run script functions
    - torrent.sh                # Fetch image via torrent functions
    - rsync.sh                  # Fetch image via rsync functions
    - imaging.sh                # Fetch image functions (uses the rsync and torrent functions)
    - disks.sh                  # Partition, lvm, mdadm functions
    - deprecated.sh             # This file contains all deprectaed functions that will be removed in a future release of SALI
```

Also during runtime some SALI specific files are created:
```
/var/log/messages               # The syslog, also contains the output from the stdout
/tmp/sali
    - installer_first_try       # To keep track if we already tried to fetch the master_script
    - master_script             # The actual master_script that has been downloaded
    - scripts/                  # A directory which contains the post and pre install scripts
    - variables                 # All variables of SALI are written here
```

## Server

### Requirements
 * Python 3.7+
 * Transmission 2.94+
 * Opentracker (see wiki for buildinstriuctions)

### Features
 * Create an image with rsync (uses ssh to start rsync on the golden-client)
 * Create a tar.gz image for bittorrent distribution
 * Generate a rsync daemon config
